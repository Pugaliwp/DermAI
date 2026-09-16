import os
import sys
import json
import time
import random
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image
from tqdm import tqdm

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
from torch.optim.lr_scheduler import ReduceLROnPlateau
import torchvision.transforms as transforms
import torchvision.models as models

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    balanced_accuracy_score, confusion_matrix, classification_report
)

# Fix random seed for reproducibility
def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

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
        label_idx = int(np.argmax(labels))
        
        return image, label_idx

class AttentionPooling(nn.Module):
    def __init__(self, in_dim):
        super().__init__()
        self.attention = nn.Sequential(
            nn.Linear(in_dim, in_dim // 2),
            nn.Tanh(),
            nn.Linear(in_dim // 2, 1)
        )

    def forward(self, x):
        # x: (B, N, D)
        attn_weights = self.attention(x) # (B, N, 1)
        attn_weights = torch.softmax(attn_weights, dim=1)
        pooled = torch.sum(x * attn_weights, dim=1) # (B, D)
        return pooled, attn_weights

class HybridModel(nn.Module):
    def __init__(self, num_classes=7, d_model=256, nhead=4, num_layers=2, dropout=0.2):
        super().__init__()
        # 1. EfficientNet-B0 Backbone (CNN)
        effnet = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.IMAGENET1K_V1)
        self.backbone = effnet.features
        
        # 2. Projection for Transformer
        in_channels = 1280 # EffNet-B0 output channels
        self.proj = nn.Conv2d(in_channels, d_model, kernel_size=1)
        
        # 3. Lightweight Transformer Encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, 
            nhead=nhead, 
            dim_feedforward=d_model * 4, 
            dropout=dropout,
            activation='gelu',
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        # Positional Encoding for 7x7 feature map (49 tokens)
        self.pos_embed = nn.Parameter(torch.randn(1, 49, d_model))
        
        # 4. Attention-based Fusion
        self.attn_pool = AttentionPooling(d_model)
        self.cnn_pool = nn.AdaptiveAvgPool2d(1)
        
        # 5. Classification Head
        self.classifier = nn.Sequential(
            nn.Linear(in_channels + d_model, 512),
            nn.BatchNorm1d(512),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(512, num_classes)
        )
        
    def forward(self, x):
        # CNN Features
        features = self.backbone(x) # (B, 1280, 7, 7)
        cnn_global = self.cnn_pool(features).flatten(1) # (B, 1280)
        
        # Prepare for Transformer
        tokens = self.proj(features) # (B, d_model, 7, 7)
        B, C, H, W = tokens.shape
        tokens = tokens.view(B, C, H * W).transpose(1, 2) # (B, 49, d_model)
        tokens = tokens + self.pos_embed
        
        # Transformer Features
        trans_out = self.transformer(tokens) # (B, 49, d_model)
        
        # Fusion
        trans_global, _ = self.attn_pool(trans_out) # (B, d_model)
        fused = torch.cat([cnn_global, trans_global], dim=1) # (B, 1280 + d_model)
        
        return self.classifier(fused)

class FocalLoss(nn.Module):
    def __init__(self, alpha=None, gamma=2.0, reduction='mean'):
        super(FocalLoss, self).__init__()
        self.gamma = gamma
        self.reduction = reduction
        if alpha is not None:
            self.alpha = torch.tensor(alpha, dtype=torch.float32) if not isinstance(alpha, torch.Tensor) else alpha
        else:
            self.alpha = None

    def forward(self, inputs, targets):
        log_probs = torch.log_softmax(inputs, dim=1)
        probs = torch.exp(log_probs)
        
        target_probs = probs.gather(1, targets.view(-1, 1)).squeeze(1)
        target_log_probs = log_probs.gather(1, targets.view(-1, 1)).squeeze(1)
        
        loss = - (1 - target_probs) ** self.gamma * target_log_probs
        
        if self.alpha is not None:
            if self.alpha.device != targets.device:
                self.alpha = self.alpha.to(targets.device)
            alpha_weights = self.alpha[targets]
            loss = alpha_weights * loss
            
        if self.reduction == 'mean':
            return loss.mean()
        elif self.reduction == 'sum':
            return loss.sum()
        else:
            return loss

def get_effective_class_weights(df, class_names, beta=0.999):
    counts = []
    for c in class_names:
        counts.append(df[c].sum())
    
    weights = []
    for count in counts:
        if count == 0:
            weights.append(1.0)
            continue
        effective_num = 1.0 - np.power(beta, count)
        weight = (1.0 - beta) / effective_num
        weights.append(weight)
        
    weights = np.array(weights)
    weights = weights / np.mean(weights)
    return torch.FloatTensor(weights)

def train_epoch(model, dataloader, criterion, optimizer, scaler, device):
    model.train()
    total_loss = 0.0
    all_preds, all_labels = [], []
    
    for images, labels in tqdm(dataloader, desc="Training"):
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()
        
        with torch.amp.autocast(device_type='cuda' if torch.cuda.is_available() else 'cpu'):
            outputs = model(images)
            loss = criterion(outputs, labels)
            
        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()
        
        total_loss += loss.item()
        preds = torch.argmax(outputs, dim=1)
        all_preds.extend(preds.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())
        
    return total_loss / len(dataloader), all_labels, all_preds

@torch.no_grad()
def validate_epoch(model, dataloader, criterion, device):
    model.eval()
    total_loss = 0.0
    all_preds, all_labels = [], []
    
    for images, labels in tqdm(dataloader, desc="Validation"):
        images, labels = images.to(device), labels.to(device)
        
        with torch.amp.autocast(device_type='cuda' if torch.cuda.is_available() else 'cpu'):
            outputs = model(images)
            loss = criterion(outputs, labels)
            
        total_loss += loss.item()
        preds = torch.argmax(outputs, dim=1)
        all_preds.extend(preds.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())
        
    return total_loss / len(dataloader), all_labels, all_preds

def calculate_metrics(labels, preds, class_names):
    report = classification_report(labels, preds, target_names=class_names, output_dict=True, zero_division=0)
    cm = confusion_matrix(labels, preds)
    
    metrics = {
        'accuracy': accuracy_score(labels, preds),
        'balanced_accuracy': balanced_accuracy_score(labels, preds),
        'macro_precision': precision_score(labels, preds, average='macro', zero_division=0),
        'macro_recall': recall_score(labels, preds, average='macro', zero_division=0),
        'macro_f1': f1_score(labels, preds, average='macro', zero_division=0),
        'report': report,
        'confusion_matrix': cm.tolist()
    }
    return metrics

def save_confusion_matrix(cm, class_names, filepath):
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=class_names, yticklabels=class_names)
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.title('Confusion Matrix')
    plt.tight_layout()
    plt.savefig(filepath)
    plt.close()

def main(args):
    set_seed(args.seed)
    
    # Print at startup
    print("=" * 50)
    print("Hybrid V2 Training Configuration")
    print("=" * 50)
    print(f"PyTorch Version: {torch.__version__}")
    print(f"CUDA Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU Name: {torch.cuda.get_device_name(0)}")
        
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    csv_path = args.csv_path
    img_dir = args.img_dir
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    if not os.path.exists(img_dir):
        raise FileNotFoundError(f"Image directory not found: {img_dir}")
        
    df = pd.read_csv(csv_path)
    class_names = ['MEL', 'NV', 'BCC', 'AKIEC', 'BKL', 'DF', 'VASC']
    
    for c in class_names:
        if c not in df.columns:
            raise ValueError(f"Class column {c} missing from CSV.")
            
    print("\nOverall Dataset Class Distribution:")
    class_distribution = df[class_names].sum()
    print(class_distribution)
    
    labels = np.argmax(df[class_names].values, axis=1)
    
    # 85/15 stratified split
    train_df, val_df = train_test_split(df, test_size=0.15, random_state=args.seed, stratify=labels)
    print(f"\nTrain size: {len(train_df)}, Validation size: {len(val_df)}")
    
    train_transform = transforms.Compose([
        transforms.RandomResizedCrop(224, scale=(0.8, 1.0)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.1, hue=0.05),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    train_dataset = ISICDataset(train_df, img_dir, transform=train_transform)
    val_dataset = ISICDataset(val_df, img_dir, transform=val_transform)
    
    # Calculate class-balanced alpha weights from the TRAINING split only
    alpha_weights = get_effective_class_weights(train_df, class_names, beta=0.999)
    print(f"\nCalculated Alpha Weights (normalized, beta=0.999) from Training Split:")
    for c_name, w in zip(class_names, alpha_weights):
        print(f"  {c_name}: {w:.4f}")
        
    print(f"\nFocal Loss Gamma: {args.gamma}")
    
    # WeightedRandomSampler for the TRAINING loader only
    train_counts = [train_df[c].sum() for c in class_names]
    class_weights_for_sampler = [1.0 / count if count > 0 else 0 for count in train_counts]
    
    sample_weights = []
    for idx in range(len(train_df)):
        row = train_df.iloc[idx]
        label_idx = int(np.argmax(row[class_names].values))
        sample_weights.append(class_weights_for_sampler[label_idx])
        
    sample_weights = torch.DoubleTensor(sample_weights)
    sampler = WeightedRandomSampler(weights=sample_weights, num_samples=len(sample_weights), replacement=True)
    print("\nSampler Status: WeightedRandomSampler applied to TRAINING loader.")
    
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, sampler=sampler, num_workers=4, pin_memory=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, num_workers=4, pin_memory=True)
    
    model = HybridModel(num_classes=len(class_names), dropout=args.dropout).to(device)
    
    param_count = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Model Parameter Count: {param_count:,}")
    print("=" * 50)
    
    criterion = FocalLoss(alpha=alpha_weights, gamma=args.gamma)
    optimizer = optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    scheduler = ReduceLROnPlateau(optimizer, mode='max', factor=0.5, patience=3)
    scaler = torch.amp.GradScaler('cuda' if torch.cuda.is_available() else 'cpu')
    
    best_macro_f1 = 0.0
    best_epoch = 0
    best_val_metrics = None
    val_df_preds = None
    patience_counter = 0
    os.makedirs(args.out_dir, exist_ok=True)
    history = []
    
    for epoch in range(1, args.epochs + 1):
        print(f"\nEpoch {epoch}/{args.epochs}")
        epoch_start_time = time.time()
        
        train_loss, train_labels, train_preds = train_epoch(model, train_loader, criterion, optimizer, scaler, device)
        val_loss, val_labels, val_preds = validate_epoch(model, val_loader, criterion, device)
        
        epoch_time = time.time() - epoch_start_time
        current_lr = optimizer.param_groups[0]['lr']
        
        val_metrics = calculate_metrics(val_labels, val_preds, class_names)
        
        print(f"Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f}")
        print(f"Val Accuracy: {val_metrics['accuracy']:.4f} | Val Macro F1: {val_metrics['macro_f1']:.4f} | Val Balanced Acc: {val_metrics['balanced_accuracy']:.4f}")
        print(f"Learning Rate: {current_lr:.6f} | Time: {epoch_time:.2f}s")
        
        scheduler.step(val_metrics['macro_f1'])
        
        history.append({
            'epoch': epoch,
            'train_loss': train_loss,
            'val_loss': val_loss,
            'val_accuracy': val_metrics['accuracy'],
            'macro_precision': val_metrics['macro_precision'],
            'macro_recall': val_metrics['macro_recall'],
            'macro_f1': val_metrics['macro_f1'],
            'balanced_accuracy': val_metrics['balanced_accuracy'],
            'learning_rate': current_lr,
            'epoch_time': epoch_time
        })
        
        if val_metrics['macro_f1'] > best_macro_f1:
            best_macro_f1 = val_metrics['macro_f1']
            best_epoch = epoch
            best_val_metrics = val_metrics
            patience_counter = 0
            
            torch.save(model.state_dict(), os.path.join(args.out_dir, 'best_model.pth'))
            
            val_df_preds = val_df.copy()
            val_df_preds['predicted_class'] = [class_names[p] for p in val_preds]
            
            print(f">>> New best model saved (Macro F1: {best_macro_f1:.4f})")
        else:
            patience_counter += 1
            if patience_counter >= args.patience:
                print(f"Early stopping triggered after {epoch} epochs.")
                break
                
    # Save artifacts at the end of training
    if best_val_metrics is not None:
        with open(os.path.join(args.out_dir, 'history.json'), 'w') as f:
            json.dump(history, f, indent=4)
            
        with open(os.path.join(args.out_dir, 'metrics.json'), 'w') as f:
            json.dump(best_val_metrics, f, indent=4)
            
        if val_df_preds is not None:
            val_df_preds.to_csv(os.path.join(args.out_dir, 'validation_predictions.csv'), index=False)
            
        save_confusion_matrix(
            np.array(best_val_metrics['confusion_matrix']), 
            class_names, 
            os.path.join(args.out_dir, 'confusion_matrix.png')
        )
        
        report_df = pd.DataFrame(best_val_metrics['report']).transpose()
        report_df.to_csv(os.path.join(args.out_dir, 'classification_report.csv'))
        
        config = {
            'model': 'HybridModel_V2',
            'backbone': 'EfficientNet-B0',
            'transformer': '2-layer, 4-head, d_model=256',
            'dropout': args.dropout,
            'focal_loss_gamma': args.gamma,
            'optimizer': 'AdamW',
            'learning_rate': args.lr,
            'weight_decay': args.weight_decay,
            'sampler': 'WeightedRandomSampler',
            'parameters': param_count,
            'input_shape': [1, 3, 224, 224],
            'best_epoch': best_epoch,
            'best_macro_f1': best_macro_f1,
            'random_seed': args.seed,
            'args': vars(args)
        }
        with open(os.path.join(args.out_dir, 'model_config.json'), 'w') as f:
            json.dump(config, f, indent=4)
            
    print("\n" + "=" * 50)
    print("Training Complete - Summary")
    print("=" * 50)
    if best_val_metrics:
        print(f"Best Epoch: {best_epoch}")
        print(f"Best Validation Accuracy: {best_val_metrics['accuracy']:.4f}")
        print(f"Best Validation Macro-F1: {best_macro_f1:.4f}")
        print(f"Best Validation Balanced Accuracy: {best_val_metrics['balanced_accuracy']:.4f}")
        print(f"Checkpoint Path: {os.path.join(args.out_dir, 'best_model.pth')}")
    else:
        print("No improvement observed during training.")
    print("=" * 50)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Train Hybrid Model V2 for DermAI")
    parser.add_argument('--csv_path', type=str, default=r"D:\full stack\dataset\ISIC2018_Task3_Training_GroundTruth\ISIC2018_Task3_Training_GroundTruth.csv")
    parser.add_argument('--img_dir', type=str, default=r"D:\full stack\dataset\ISIC2018_Task3_Training_Input")
    parser.add_argument('--out_dir', type=str, default=r"D:\full stack\ai-service\models\hybrid_v2")
    parser.add_argument('--batch_size', type=int, default=32)
    parser.add_argument('--epochs', type=int, default=50)
    parser.add_argument('--lr', type=float, default=1e-4)
    parser.add_argument('--weight_decay', type=float, default=1e-4)
    parser.add_argument('--dropout', type=float, default=0.2)
    parser.add_argument('--gamma', type=float, default=2.0)
    parser.add_argument('--patience', type=int, default=10)
    parser.add_argument('--seed', type=int, default=42)
    
    args = parser.parse_args()
    main(args)
