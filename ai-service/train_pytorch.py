import os
import copy
import random
import numpy as np
import pandas as pd
from PIL import Image

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from torchvision.models import efficientnet_b0, EfficientNet_B0_Weights

from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import classification_report, confusion_matrix, f1_score

# ============================================================
# CONFIGURATION
# ============================================================

DATASET_DIR = "../dataset"

IMAGE_DIR = os.path.join(
    DATASET_DIR,
    "ISIC2018_Task3_Training_Input"
)

CSV_PATH = os.path.join(
    DATASET_DIR,
    "ISIC2018_Task3_Training_GroundTruth",
    "ISIC2018_Task3_Training_GroundTruth.csv"
)

MODEL_DIR = "models"
MODEL_PATH = os.path.join(
    MODEL_DIR,
    "best_efficientnetb0.pth"
)

IMG_SIZE = 224
BATCH_SIZE = 32
EPOCHS = 20
LEARNING_RATE = 1e-3
VAL_SIZE = 0.15
SEED = 42

CLASS_NAMES = [
    "MEL",
    "NV",
    "BCC",
    "AKIEC",
    "BKL",
    "DF",
    "VASC"
]

NUM_CLASSES = len(CLASS_NAMES)

os.makedirs(MODEL_DIR, exist_ok=True)

# ============================================================
# REPRODUCIBILITY
# ============================================================

random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
torch.cuda.manual_seed_all(SEED)

# ============================================================
# DEVICE
# ============================================================

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("\n========================================")
print("AI SKIN HEALTH SCREENING")
print("PyTorch + EfficientNet-B0")
print("========================================")

print("\nPyTorch version:", torch.__version__)
print("Device:", device)

if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))
    print(
        "GPU Memory:",
        round(
            torch.cuda.get_device_properties(0).total_memory / 1024**3,
            2
        ),
        "GB"
    )

# ============================================================
# DATASET
# ============================================================

class SkinDataset(Dataset):

    def __init__(self, dataframe, transform=None):

        self.dataframe = dataframe.reset_index(drop=True)
        self.transform = transform

    def __len__(self):
        return len(self.dataframe)

    def __getitem__(self, index):

        row = self.dataframe.iloc[index]

        image_path = row["path"]
        label = int(row["label"])

        image = Image.open(image_path).convert("RGB")

        if self.transform:
            image = self.transform(image)

        return image, label


# ============================================================
# LOAD CSV
# ============================================================

print("\nLoading dataset...")

df = pd.read_csv(CSV_PATH)

print("Total images:", len(df))

# Convert one-hot labels to class index

df["label"] = df[CLASS_NAMES].values.argmax(axis=1)

# Create image paths

df["path"] = df["image"].apply(
    lambda x: os.path.join(
        IMAGE_DIR,
        x + ".jpg"
    )
)

# ============================================================
# VERIFY FILES
# ============================================================

missing = df[
    ~df["path"].apply(os.path.exists)
]

if len(missing) > 0:

    print(
        "\nERROR: Missing images:",
        len(missing)
    )

    print(
        missing["image"].head(10).tolist()
    )

    raise FileNotFoundError(
        "Dataset contains missing images."
    )

print("All training images found.")

# ============================================================
# CLASS DISTRIBUTION
# ============================================================

print("\nClass distribution:")

for i, class_name in enumerate(CLASS_NAMES):

    count = int(
        (df["label"] == i).sum()
    )

    print(
        f"{class_name:6} -> {count}"
    )

# ============================================================
# TRAIN / VALIDATION SPLIT
# ============================================================

train_df, val_df = train_test_split(
    df,
    test_size=VAL_SIZE,
    random_state=SEED,
    stratify=df["label"]
)

print(
    "\nTraining images:",
    len(train_df)
)

print(
    "Validation images:",
    len(val_df)
)

# ============================================================
# TRANSFORMS
# ============================================================

weights = EfficientNet_B0_Weights.DEFAULT

imagenet_mean = [
    0.485,
    0.456,
    0.406
]

imagenet_std = [
    0.229,
    0.224,
    0.225
]

train_transform = transforms.Compose([

    transforms.Resize(
        (IMG_SIZE, IMG_SIZE)
    ),

    transforms.RandomHorizontalFlip(
        p=0.5
    ),

    transforms.RandomRotation(
        degrees=10
    ),

    transforms.RandomResizedCrop(
        IMG_SIZE,
        scale=(0.90, 1.0)
    ),

    transforms.ColorJitter(
        brightness=0.10,
        contrast=0.10,
        saturation=0.10
    ),

    transforms.ToTensor(),

    transforms.Normalize(
        mean=imagenet_mean,
        std=imagenet_std
    )
])

val_transform = transforms.Compose([

    transforms.Resize(
        (IMG_SIZE, IMG_SIZE)
    ),

    transforms.ToTensor(),

    transforms.Normalize(
        mean=imagenet_mean,
        std=imagenet_std
    )
])

# ============================================================
# DATASETS
# ============================================================

train_dataset = SkinDataset(
    train_df,
    transform=train_transform
)

val_dataset = SkinDataset(
    val_df,
    transform=val_transform
)

# ============================================================
# DATA LOADERS
# ============================================================

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=0,
    pin_memory=torch.cuda.is_available()
)

val_loader = DataLoader(
    val_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=0,
    pin_memory=torch.cuda.is_available()
)

print(
    "\nTraining batches:",
    len(train_loader)
)

print(
    "Validation batches:",
    len(val_loader)
)

# ============================================================
# CLASS WEIGHTS
# ============================================================

class_weights = compute_class_weight(
    class_weight="balanced",
    classes=np.arange(NUM_CLASSES),
    y=train_df["label"].values
)

class_weights = torch.tensor(
    class_weights,
    dtype=torch.float32
).to(device)

print("\nClass weights:")

for i, class_name in enumerate(CLASS_NAMES):

    print(
        f"{class_name:6} -> "
        f"{class_weights[i].item():.4f}"
    )

# ============================================================
# MODEL
# ============================================================

print("\nCreating EfficientNet-B0...")

model = efficientnet_b0(
    weights=EfficientNet_B0_Weights.DEFAULT
)

# Replace ImageNet classifier

in_features = model.classifier[1].in_features

model.classifier[1] = nn.Linear(
    in_features,
    NUM_CLASSES
)

model = model.to(device)

# ============================================================
# LOSS
# ============================================================

criterion = nn.CrossEntropyLoss(
    weight=class_weights
)

# ============================================================
# OPTIMIZER
# ============================================================

optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=LEARNING_RATE,
    weight_decay=1e-4
)

# ============================================================
# SCHEDULER
# ============================================================

scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
    optimizer,
    mode="max",
    factor=0.3,
    patience=2
)

# ============================================================
# MIXED PRECISION
# ============================================================

scaler = torch.amp.GradScaler(
    "cuda",
    enabled=torch.cuda.is_available()
)

# ============================================================
# TRAINING FUNCTION
# ============================================================

def train_one_epoch():

    model.train()

    running_loss = 0.0
    correct = 0
    total = 0

    for images, labels in train_loader:

        images = images.to(
            device,
            non_blocking=True
        )

        labels = labels.to(
            device,
            non_blocking=True
        )

        optimizer.zero_grad(
            set_to_none=True
        )

        with torch.amp.autocast(
            device_type="cuda",
            enabled=torch.cuda.is_available()
        ):

            outputs = model(images)

            loss = criterion(
                outputs,
                labels
            )

        scaler.scale(loss).backward()

        scaler.step(optimizer)

        scaler.update()

        running_loss += (
            loss.item() * images.size(0)
        )

        predictions = outputs.argmax(
            dim=1
        )

        correct += (
            predictions == labels
        ).sum().item()

        total += labels.size(0)

    epoch_loss = (
        running_loss / total
    )

    epoch_accuracy = (
        correct / total
    )

    return epoch_loss, epoch_accuracy


# ============================================================
# VALIDATION FUNCTION
# ============================================================

def validate():

    model.eval()

    running_loss = 0.0
    correct = 0
    total = 0

    all_labels = []
    all_predictions = []

    with torch.no_grad():

        for images, labels in val_loader:

            images = images.to(
                device,
                non_blocking=True
            )

            labels = labels.to(
                device,
                non_blocking=True
            )

            with torch.amp.autocast(
                device_type="cuda",
                enabled=torch.cuda.is_available()
            ):

                outputs = model(images)

                loss = criterion(
                    outputs,
                    labels
                )

            running_loss += (
                loss.item() * images.size(0)
            )

            predictions = outputs.argmax(
                dim=1
            )

            correct += (
                predictions == labels
            ).sum().item()

            total += labels.size(0)

            all_labels.extend(
                labels.cpu().numpy()
            )

            all_predictions.extend(
                predictions.cpu().numpy()
            )

    epoch_loss = (
        running_loss / total
    )

    epoch_accuracy = (
        correct / total
    )

    macro_f1 = f1_score(
        all_labels,
        all_predictions,
        average="macro",
        zero_division=0
    )

    return (
        epoch_loss,
        epoch_accuracy,
        macro_f1,
        all_labels,
        all_predictions
    )


# ============================================================
# TRAINING LOOP
# ============================================================

best_f1 = 0.0
best_model = None
patience = 5
patience_counter = 0

print("\n========================================")
print("STARTING TRAINING")
print("========================================")

for epoch in range(EPOCHS):

    print(
        f"\nEpoch {epoch + 1}/{EPOCHS}"
    )

    train_loss, train_accuracy = (
        train_one_epoch()
    )

    (
        val_loss,
        val_accuracy,
        val_f1,
        val_labels,
        val_predictions
    ) = validate()

    scheduler.step(val_f1)

    print(
        f"Train Loss: {train_loss:.4f}"
    )

    print(
        f"Train Accuracy: "
        f"{train_accuracy:.4f}"
    )

    print(
        f"Val Loss: {val_loss:.4f}"
    )

    print(
        f"Val Accuracy: "
        f"{val_accuracy:.4f}"
    )

    print(
        f"Val Macro F1: "
        f"{val_f1:.4f}"
    )

    if val_f1 > best_f1:

        best_f1 = val_f1

        best_model = copy.deepcopy(
            model.state_dict()
        )

        torch.save(
            {
                "model_state_dict": best_model,
                "class_names": CLASS_NAMES,
                "img_size": IMG_SIZE,
                "best_val_f1": best_f1
            },
            MODEL_PATH
        )

        print(
            "\nBest model saved!"
        )

        patience_counter = 0

    else:

        patience_counter += 1

        print(
            "No improvement:",
            patience_counter,
            "/",
            patience
        )

    if patience_counter >= patience:

        print(
            "\nEarly stopping."
        )

        break

# ============================================================
# LOAD BEST MODEL
# ============================================================

if best_model is not None:

    model.load_state_dict(
        best_model
    )

# ============================================================
# FINAL VALIDATION REPORT
# ============================================================

(
    final_loss,
    final_accuracy,
    final_f1,
    final_labels,
    final_predictions
) = validate()

print("\n========================================")
print("FINAL VALIDATION RESULTS")
print("========================================")

print(
    f"Loss: {final_loss:.4f}"
)

print(
    f"Accuracy: {final_accuracy:.4f}"
)

print(
    f"Macro F1: {final_f1:.4f}"
)

print("\nClassification Report:\n")

print(
    classification_report(
        final_labels,
        final_predictions,
        target_names=CLASS_NAMES,
        zero_division=0
    )
)

print("\nConfusion Matrix:\n")

print(
    confusion_matrix(
        final_labels,
        final_predictions
    )
)

print("\n========================================")
print("TRAINING COMPLETE")
print("========================================")

print(
    "Best model:",
    MODEL_PATH
)

print(
    "Best validation Macro F1:",
    f"{best_f1:.4f}"
)
