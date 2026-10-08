import os
import random
import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Loading CLIP model on {device}...")
clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

POSITIVE_PROMPTS = [
    "a dermoscopic image of a skin lesion",
    "a dermatoscopic photograph of a skin lesion",
    "a clinical image of a skin lesion",
    "a medical photograph of a cutaneous lesion",
    "a photograph of an abnormal skin lesion",
    "a dermoscopy image used for skin lesion classification",
    "a close-up medical image of a pigmented skin lesion"
]

NEGATIVE_PROMPTS = [
    "a bus or vehicle",
    "a road or landscape",
    "a plant or leaf",
    "an animal",
    "a portrait of a person without a skin lesion",
    "normal human skin without a lesion",
    "an everyday object",
    "a screenshot or computer screen",
    "a diagram or illustration",
    "a histology or microscopy image",
    "a skincare product",
    "clothing or fabric"
]
CLIP_PROMPTS = POSITIVE_PROMPTS + NEGATIVE_PROMPTS

def get_skin_score(image_path):
    try:
        image = Image.open(image_path).convert("RGB")
        clip_inputs = clip_processor(text=CLIP_PROMPTS, images=image, return_tensors="pt", padding=True)
        clip_inputs = {k: v.to(device) for k, v in clip_inputs.items()}
        
        with torch.no_grad():
            clip_outputs = clip_model(**clip_inputs)
            clip_probs = clip_outputs.logits_per_image.softmax(dim=1).squeeze().tolist()
            
        skin_score = sum(clip_probs[:len(POSITIVE_PROMPTS)])
        return skin_score
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return None

print("Building dataset...")
# Get 200 random positive ISIC images
pos_dir = r"D:\full stack\dataset\ISIC2018_Task3_Training_Input"
all_pos = [f for f in os.listdir(pos_dir) if f.endswith('.jpg')]
random.seed(42)
selected_pos = random.sample(all_pos, min(200, len(all_pos)))
pos_paths = [(os.path.join(pos_dir, f), "POSITIVE") for f in selected_pos]

# Get negative OOD images
neg_dir = r"D:\full stack\dataset\ood_dev_set\negative"
neg_paths = []
if os.path.exists(neg_dir):
    all_neg = [f for f in os.listdir(neg_dir) if f.endswith('.jpg') or f.endswith('.jpeg') or f.endswith('.png')]
    neg_paths = [(os.path.join(neg_dir, f), "NEGATIVE") for f in all_neg]

dataset = pos_paths + neg_paths
print(f"Total positive: {len(pos_paths)}, Total negative: {len(neg_paths)}")

results = []
print("Evaluating images...")
for i, (path, label) in enumerate(dataset):
    score = get_skin_score(path)
    if score is not None:
        results.append({
            "image": os.path.basename(path),
            "label": label,
            "skin_score": score
        })
    if (i + 1) % 50 == 0:
        print(f"Processed {i + 1}/{len(dataset)}...")

df = pd.DataFrame(results)

print("\n--- RESULTS ---")
pos_df = df[df['label'] == 'POSITIVE']
neg_df = df[df['label'] == 'NEGATIVE']

print(f"Positive count: {len(pos_df)}")
if not pos_df.empty:
    print(f"Min Pos: {pos_df['skin_score'].min():.4f}")
    print(f"Max Pos: {pos_df['skin_score'].max():.4f}")
    print(f"Mean Pos: {pos_df['skin_score'].mean():.4f}")

print(f"\nNegative count: {len(neg_df)}")
if not neg_df.empty:
    print(f"Min Neg: {neg_df['skin_score'].min():.4f}")
    print(f"Max Neg: {neg_df['skin_score'].max():.4f}")
    print(f"Mean Neg: {neg_df['skin_score'].mean():.4f}")

print("\n--- THRESHOLD CALIBRATION ---")
thresholds = [0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.92, 0.93, 0.94, 0.95, 0.98, 0.99]
for t in thresholds:
    pos_accepted = len(pos_df[pos_df['skin_score'] >= t])
    pos_acc_rate = pos_accepted / len(pos_df) if len(pos_df) > 0 else 0
    
    neg_rejected = len(neg_df[neg_df['skin_score'] < t])
    neg_rej_rate = neg_rejected / len(neg_df) if len(neg_df) > 0 else 0
    
    print(f"T={t:.2f} | Pos Accept: {pos_acc_rate*100:.1f}% ({pos_accepted}/{len(pos_df)}) | Neg Reject: {neg_rej_rate*100:.1f}% ({neg_rejected}/{len(neg_df)})")

print("\nDetailed Negatives:")
for _, row in neg_df.iterrows():
    print(f"{row['image']}: {row['skin_score']:.4f}")
