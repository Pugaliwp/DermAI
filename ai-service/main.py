import os
import io
import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image, UnidentifiedImageError
from transformers import CLIPProcessor, CLIPModel

# --- Architecture Definition (Must exactly match train_hybrid.py) ---
class AttentionPooling(nn.Module):
    def __init__(self, in_dim):
        super().__init__()
        self.attention = nn.Sequential(
            nn.Linear(in_dim, in_dim // 2),
            nn.Tanh(),
            nn.Linear(in_dim // 2, 1)
        )

    def forward(self, x):
        attn_weights = self.attention(x)
        attn_weights = torch.softmax(attn_weights, dim=1)
        pooled = torch.sum(x * attn_weights, dim=1)
        return pooled, attn_weights

class HybridModel(nn.Module):
    def __init__(self, num_classes=7, d_model=256, nhead=4, num_layers=2, dropout=0.1):
        super().__init__()
        effnet = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.IMAGENET1K_V1)
        self.backbone = effnet.features
        
        in_channels = 1280
        self.proj = nn.Conv2d(in_channels, d_model, kernel_size=1)
        
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, 
            nhead=nhead, 
            dim_feedforward=d_model * 4, 
            dropout=dropout,
            activation='gelu',
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        self.pos_embed = nn.Parameter(torch.randn(1, 49, d_model))
        
        self.attn_pool = AttentionPooling(d_model)
        self.cnn_pool = nn.AdaptiveAvgPool2d(1)
        
        self.classifier = nn.Sequential(
            nn.Linear(in_channels + d_model, 512),
            nn.BatchNorm1d(512),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(512, num_classes)
        )
        
    def forward(self, x):
        features = self.backbone(x)
        cnn_global = self.cnn_pool(features).flatten(1)
        
        tokens = self.proj(features)
        B, C, H, W = tokens.shape
        tokens = tokens.view(B, C, H * W).transpose(1, 2)
        tokens = tokens + self.pos_embed
        
        trans_out = self.transformer(tokens)
        
        trans_global, _ = self.attn_pool(trans_out)
        fused = torch.cat([cnn_global, trans_global], dim=1)
        
        return self.classifier(fused)
# --------------------------------------------------------------------

app = FastAPI(title="DermAI Inference API", version="1.0.0")

# Enable CORS for existing frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
model = None
device = None
class_names = ['MEL', 'NV', 'BCC', 'AKIEC', 'BKL', 'DF', 'VASC']
disease_names = {
    'MEL': 'Melanoma',
    'NV': 'Melanocytic nevus',
    'BCC': 'Basal cell carcinoma',
    'AKIEC': 'Actinic keratosis / intraepithelial carcinoma',
    'BKL': 'Benign keratosis',
    'DF': 'Dermatofibroma',
    'VASC': 'Vascular lesion'
}

clip_model = None
clip_processor = None
POSITIVE_PROMPTS = [
    "dermoscopic image of a skin lesion",
    "clinical photograph of a skin lesion",
    "dermoscopy photograph of a mole",
    "dermoscopic photograph of abnormal skin lesion"
]
NEGATIVE_PROMPTS = [
    "portrait",
    "normal human skin without lesion",
    "plant or leaf",
    "animal",
    "vehicle or road",
    "everyday object",
    "screenshot",
    "medical illustration",
    "histology/microscopy image"
]
CLIP_PROMPTS = POSITIVE_PROMPTS + NEGATIVE_PROMPTS

# Image Preprocessing (matching val_transform from train_hybrid.py)
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

@app.on_event("startup")
async def load_model():
    global model, device, clip_model, clip_processor
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Loading model on device: {device}")
    
    print("Loading CLIP zero-shot model...")
    clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
    clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    
    model = HybridModel(num_classes=len(class_names)).to(device)
    model_path = r"D:\full stack\ai-service\models\hybrid\best_model.pth"
    
    if not os.path.exists(model_path):
        print(f"Error: Model checkpoint not found at {model_path}")
        return
        
    checkpoint = torch.load(model_path, map_location=device, weights_only=True)
    model.load_state_dict(checkpoint)
    model.eval()
    print("Model loaded successfully.")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "device": str(device)
    }

@app.post("/predict")
async def predict(file: UploadFile = File(None)):
    if not file:
        raise HTTPException(status_code=400, detail="Missing file")
        
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File is not an image")
        
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Corrupted or invalid image file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading image: {str(e)}")
        
    # --- CLIP Input Relevance Gate ---
    try:
        clip_inputs = clip_processor(text=CLIP_PROMPTS, images=image, return_tensors="pt", padding=True)
        clip_inputs = {k: v.to(device) for k, v in clip_inputs.items()}
        
        with torch.no_grad():
            clip_outputs = clip_model(**clip_inputs)
            clip_probs = clip_outputs.logits_per_image.softmax(dim=1).squeeze().tolist()
            
        skin_score = sum(clip_probs[:len(POSITIVE_PROMPTS)])
        
        # DIAGNOSTIC LOGGING
        print("--- CLIP OOD GATE DIAGNOSTICS ---")
        for i, prompt in enumerate(CLIP_PROMPTS):
            score_type = "POS" if i < len(POSITIVE_PROMPTS) else "NEG"
            print(f"[{score_type}] {prompt}: {clip_probs[i]:.4f}")
        print(f"Aggregated POS score: {skin_score:.4f}")
        neg_score = sum(clip_probs[len(POSITIVE_PROMPTS):])
        print(f"Aggregated NEG score: {neg_score:.4f}")
        print(f"Threshold: 0.85")
        decision = "ACCEPT" if skin_score >= 0.85 else "REJECT"
        print(f"Decision: {decision}")
        print("---------------------------------")
        
        # Strict threshold from OOD calibration (0.85 allows dermoscopic but rejects histology)
        if skin_score < 0.85:
            return JSONResponse(content={
                "accepted": False,
                "error_code": "INVALID_IMAGE_TYPE",
                "message": "Please upload a clear close-up photograph of a skin lesion on human skin.",
                "skin_score": float(skin_score)
            })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OOD validation error: {str(e)}")

    # Preprocess
    input_tensor = transform(image).unsqueeze(0).to(device)
    
    # Predict
    with torch.no_grad():
        with torch.amp.autocast(device_type='cuda' if torch.cuda.is_available() else 'cpu'):
            output = model(input_tensor)
            probabilities = torch.softmax(output, dim=1).squeeze().tolist()
            
    # Find max probability
    max_idx = probabilities.index(max(probabilities))
    pred_class_code = class_names[max_idx]
    confidence = probabilities[max_idx]
    
    # Format probabilities
    probs_dict = {class_names[i]: float(probabilities[i]) for i in range(len(class_names))}
    
    return JSONResponse(content={
        "accepted": True,
        "predicted_class_code": pred_class_code,
        "disease_name": disease_names[pred_class_code],
        "confidence": float(confidence),
        "probabilities": probs_dict,
        "model_name": "DermAI Hybrid V1",
        "device": str(device),
        "skin_score": float(skin_score)
    })
