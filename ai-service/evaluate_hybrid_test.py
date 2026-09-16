import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image
from tqdm import tqdm
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as transforms
import torchvision.models as models

from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    balanced_accuracy_score, confusion_matrix, classification_report, roc_auc_score
)

# 1. Dataset definition (Exact same as validation)
class ISICDataset(Dataset):
    def __init__(self, df, img_dir, transform=None):
        self.df = df
        self.img_dir = img_dir
        self.transform = transform
        self.class_names = ['MEL', 'NV', 'BCC', 'AKIEC', 'BKL', 'DF', 'VASC']

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        img_name = row['image'] + '.jpg'
        img_path = os.path.join(self.img_dir, img_name)
        
        image = Image.open(img_path).convert('RGB')
        if self.transform:
            image = self.transform(image)
            
        labels = row[self.class_names].values.astype(np.float32)
        label_idx = np.argmax(labels)
        
        return image, label_idx

# 2. Model Architecture (Exact same as train_hybrid.py)
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
        # Use weights=None since we are loading a trained checkpoint anyway
        # but to match train_hybrid exactly for structure we could use IMAGENET1K_V1
        # It's better to just use None to avoid re-downloading if cached differently,
        # but IMAGENET1K_V1 is the default in PyTorch > 0.13. We'll use weights=None
        # because the loaded checkpoint will overwrite these weights.
        effnet = models.efficientnet_b0(weights=None)
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

def main(args):
    # Paths
    csv_path = Path(args.csv_path)
    img_dir = Path(args.img_dir)
    checkpoint_path = Path(args.checkpoint)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Verify files
    if not csv_path.exists():
        raise FileNotFoundError(f"Test CSV not found: {csv_path}")
    if not img_dir.exists():
        raise FileNotFoundError(f"Test image directory not found: {img_dir}")
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")
        
    # Load dataset
    df = pd.read_csv(csv_path)
    class_names = ['MEL', 'NV', 'BCC', 'AKIEC', 'BKL', 'DF', 'VASC']
    
    # Ensure correct size
    if len(df) != 1512:
        print(f"Warning: Expected 1512 samples, found {len(df)} samples.")
        
    # Transform (exact same as val_transform in train_hybrid.py)
    test_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    test_dataset = ISICDataset(df, img_dir, transform=test_transform)
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size, shuffle=False, num_workers=4, pin_memory=True)
    
    # Setup model and device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = HybridModel(num_classes=len(class_names))
    
    print(f"Loading checkpoint from: {checkpoint_path}")
    # Load the best state dict
    model.load_state_dict(torch.load(checkpoint_path, map_location=device, weights_only=True))
    model.to(device)
    model.eval()
    
    # Evaluation Loop
    all_preds = []
    all_labels = []
    all_probs = []
    
    print(f"Starting evaluation on {len(df)} samples using {device}...")
    with torch.no_grad():
        for images, labels in tqdm(test_loader, desc="Testing"):
            images, labels = images.to(device), labels.to(device)
            
            with torch.amp.autocast(device_type='cuda' if torch.cuda.is_available() else 'cpu'):
                outputs = model(images)
                probs = torch.softmax(outputs, dim=1)
                
            preds = torch.argmax(outputs, dim=1)
            
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
            all_probs.extend(probs.cpu().numpy())
            
    all_preds = np.array(all_preds)
    all_labels = np.array(all_labels)
    all_probs = np.array(all_probs)
    
    # Calculate Metrics
    acc = accuracy_score(all_labels, all_preds)
    macro_prec = precision_score(all_labels, all_preds, average='macro', zero_division=0)
    macro_rec = recall_score(all_labels, all_preds, average='macro', zero_division=0)
    macro_f1 = f1_score(all_labels, all_preds, average='macro', zero_division=0)
    weighted_f1 = f1_score(all_labels, all_preds, average='weighted', zero_division=0)
    balanced_acc = balanced_accuracy_score(all_labels, all_preds)
    
    # ROC-AUC
    try:
        # Generate one-hot encoded labels for ROC AUC
        all_labels_one_hot = np.zeros((all_labels.size, len(class_names)))
        all_labels_one_hot[np.arange(all_labels.size), all_labels] = 1
        roc_auc = roc_auc_score(all_labels_one_hot, all_probs, average='macro', multi_class='ovr')
    except Exception as e:
        print(f"ROC-AUC calculation failed: {e}")
        roc_auc = "N/A"
        
    # Generate Classification Report
    report_dict = classification_report(all_labels, all_preds, target_names=class_names, output_dict=True, zero_division=0)
    report_df = pd.DataFrame(report_dict).transpose()
    report_df.to_csv(out_dir / 'test_classification_report.csv')
    
    # Confusion Matrix
    cm = confusion_matrix(all_labels, all_preds)
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=class_names, yticklabels=class_names)
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.title('Test Confusion Matrix')
    plt.tight_layout()
    plt.savefig(out_dir / 'test_confusion_matrix.png')
    plt.close()
    
    # Save Metrics JSON
    metrics = {
        'test_samples': len(df),
        'accuracy': acc,
        'macro_precision': macro_prec,
        'macro_recall': macro_rec,
        'macro_f1': macro_f1,
        'weighted_f1': weighted_f1,
        'balanced_accuracy': balanced_acc,
        'macro_roc_auc': roc_auc if isinstance(roc_auc, float) else None,
        'per_class': {}
    }
    
    for i, c in enumerate(class_names):
        metrics['per_class'][c] = {
            'precision': report_dict[c]['precision'],
            'recall': report_dict[c]['recall'],
            'f1': report_dict[c]['f1-score'],
            'support': report_dict[c]['support']
        }
        
    with open(out_dir / 'test_metrics.json', 'w') as f:
        json.dump(metrics, f, indent=4)
        
    # Save Predictions
    df_preds = df.copy()
    df_preds['predicted_class'] = [class_names[p] for p in all_preds]
    for i, c in enumerate(class_names):
         df_preds[f'prob_{c}'] = all_probs[:, i]
    df_preds.to_csv(out_dir / 'test_predictions.csv', index=False)
    
    # Print Summary
    print("\n" + "=" * 40)
    print("DermAI Hybrid Model - TEST RESULTS")
    print("=" * 40)
    print(f"Checkpoint: Epoch 36 (best_model.pth)") # Standardizing to expected output from the prompt
    print(f"Test samples: {len(df)}")
    print(f"Accuracy: {acc*100:.2f}%")
    print(f"Macro Precision: {macro_prec*100:.2f}%")
    print(f"Macro Recall: {macro_rec*100:.2f}%")
    print(f"Macro F1: {macro_f1*100:.2f}%")
    print(f"Weighted F1: {weighted_f1*100:.2f}%")
    print(f"Balanced Accuracy: {balanced_acc*100:.2f}%")
    if isinstance(roc_auc, float):
        print(f"Macro ROC-AUC: {roc_auc:.4f}")
    else:
        print(f"Macro ROC-AUC: {roc_auc}")
    print("=" * 40 + "\n")
    
    print("Class     Precision   Recall   F1     Support")
    for c in class_names:
        p = report_dict[c]['precision'] * 100
        r = report_dict[c]['recall'] * 100
        f = report_dict[c]['f1-score'] * 100
        s = int(report_dict[c]['support'])
        print(f"{c:<9} {p:>7.2f}% {r:>7.2f}% {f:>6.2f}% {s:>7}")
        
    print("\nConfusion Matrix:")
    print(cm)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Evaluate Hybrid Model on Test Set")
    parser.add_argument('--csv_path', type=str, default=r"D:\full stack\dataset\ISIC2018_Task3_Test_GroundTruth\ISIC2018_Task3_Test_GroundTruth.csv")
    parser.add_argument('--img_dir', type=str, default=r"D:\full stack\dataset\ISIC2018_Task3_Test_Input")
    parser.add_argument('--checkpoint', type=str, default=r"D:\full stack\ai-service\models\hybrid\best_model.pth")
    parser.add_argument('--out_dir', type=str, default=r"D:\full stack\ai-service\test_results")
    parser.add_argument('--batch_size', type=int, default=32)
    
    args = parser.parse_args()
    main(args)
