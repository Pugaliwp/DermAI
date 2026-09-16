import os
import numpy as np
import pandas as pd
import tensorflow as tf

from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.applications import EfficientNetB0
from tensorflow.keras import mixed_precision
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight

# =========================
# GPU DETECTION & CONFIGURATION
# =========================

print("\nTensorFlow version:", tf.__version__)

gpus = tf.config.list_physical_devices("GPU")

if gpus:
    print("\nGPU DETECTED:")
    for gpu in gpus:
        print(gpu)
    try:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        print("GPU memory growth enabled.")
    except RuntimeError as e:
        print("GPU memory configuration warning:", e)
    mixed_precision.set_global_policy("mixed_float16")
    print("Mixed precision enabled: mixed_float16")
else:
    print("\nWARNING: No GPU detected. Training will use CPU.")
    mixed_precision.set_global_policy("float32")
    print("Using float32 precision on CPU.")

# =========================
# CONFIGURATION
# =========================

DATASET_DIR = "../dataset"

TRAIN_IMAGE_DIR = os.path.join(
    DATASET_DIR,
    "ISIC2018_Task3_Training_Input"
)

TRAIN_CSV = os.path.join(
    DATASET_DIR,
    "ISIC2018_Task3_Training_GroundTruth",
    "ISIC2018_Task3_Training_GroundTruth.csv"
)

MODEL_DIR = "models"

IMG_SIZE = 224
BATCH_SIZE = 32
EPOCHS = 20
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

# =========================
# REPRODUCIBILITY
# =========================

np.random.seed(SEED)
tf.random.set_seed(SEED)

print("\n========================================")
print("AI SKIN HEALTH SCREENING")
print("EfficientNetB0 Training")
print("========================================")

# =========================
# LOAD CSV
# =========================

print("\nLoading dataset...")

df = pd.read_csv(TRAIN_CSV)

print("Total images:", len(df))

# =========================
# CONVERT ONE-HOT LABELS
# =========================

df["label"] = df[CLASS_NAMES].values.argmax(axis=1)

print("\nClass distribution:")

for i, class_name in enumerate(CLASS_NAMES):
    count = int((df["label"] == i).sum())
    print(f"{i}: {class_name:6} -> {count}")

# =========================
# CREATE IMAGE PATHS
# =========================

df["path"] = df["image"].apply(
    lambda x: os.path.join(TRAIN_IMAGE_DIR, x + ".jpg")
)

# Check missing files

missing = df[~df["path"].apply(os.path.exists)]

if len(missing) > 0:
    print("\nERROR: Missing images:", len(missing))
    print(missing["image"].head(10).tolist())
    raise FileNotFoundError("Some dataset images are missing.")

print("\nAll training images found.")

# =========================
# STRATIFIED TRAIN/VALIDATION SPLIT
# =========================

train_df, val_df = train_test_split(
    df,
    test_size=0.15,
    random_state=SEED,
    stratify=df["label"]
)

print("\nTraining images:", len(train_df))
print("Validation images:", len(val_df))

# =========================
# DATA GENERATORS
# =========================

def load_image(path, label):
    image = tf.io.read_file(path)
    image = tf.image.decode_jpeg(
        image,
        channels=3
    )

    image = tf.image.resize(
        image,
        [IMG_SIZE, IMG_SIZE]
    )

    image = tf.cast(image, tf.float32)

    return image, label


def create_dataset(dataframe, training=False):

    paths = dataframe["path"].values
    labels = dataframe["label"].values

    dataset = tf.data.Dataset.from_tensor_slices(
        (paths, labels)
    )

    dataset = dataset.map(
        load_image,
        num_parallel_calls=tf.data.AUTOTUNE
    )

    if training:
        dataset = dataset.shuffle(
            buffer_size=2048,
            seed=SEED
        )

    dataset = dataset.batch(BATCH_SIZE)
    dataset = dataset.prefetch(tf.data.AUTOTUNE)

    return dataset


train_ds = create_dataset(
    train_df,
    training=True
)

val_ds = create_dataset(
    val_df,
    training=False
)

# =========================
# DATA AUGMENTATION
# =========================

data_augmentation = keras.Sequential(
    [
        layers.RandomFlip(
            "horizontal"
        ),
        layers.RandomRotation(
            0.05
        ),
        layers.RandomZoom(
            0.10
        ),
        layers.RandomTranslation(
            0.05,
            0.05
        ),
        layers.RandomContrast(
            0.10
        ),
    ],
    name="data_augmentation"
)

# =========================
# CLASS WEIGHTS
# =========================

classes = np.arange(NUM_CLASSES)

weights = compute_class_weight(
    class_weight="balanced",
    classes=classes,
    y=train_df["label"]
)

class_weights = {
    i: float(weights[i])
    for i in classes
}

print("\nClass weights:")

for i, class_name in enumerate(CLASS_NAMES):
    print(
        f"{class_name:6} -> "
        f"{class_weights[i]:.4f}"
    )

# =========================
# EFFICIENTNETB0
# =========================

print("\nCreating EfficientNetB0...")

base_model = EfficientNetB0(
    include_top=False,
    weights="imagenet",
    input_shape=(
        IMG_SIZE,
        IMG_SIZE,
        3
    )
)

# Freeze pretrained layers

base_model.trainable = False

# =========================
# MODEL
# =========================

inputs = keras.Input(
    shape=(
        IMG_SIZE,
        IMG_SIZE,
        3
    )
)

x = data_augmentation(inputs)

x = base_model(
    x,
    training=False
)

x = layers.GlobalAveragePooling2D()(x)

x = layers.Dropout(
    0.3
)(x)

outputs = layers.Dense(
    NUM_CLASSES,
    activation="softmax",
    dtype="float32"
)(x)

model = keras.Model(
    inputs,
    outputs,
    name="EfficientNetB0_Skin"
)

# =========================
# COMPILE
# =========================

model.compile(
    optimizer=keras.optimizers.Adam(
        learning_rate=1e-3
    ),
    loss="sparse_categorical_crossentropy",
    metrics=[
        "accuracy"
    ]
)

model.summary()

# =========================
# CALLBACKS
# =========================

callbacks = [

    keras.callbacks.ModelCheckpoint(
        filepath=os.path.join(
            MODEL_DIR,
            "best_efficientnetb0.keras"
        ),
        monitor="val_accuracy",
        save_best_only=True,
        mode="max",
        verbose=1
    ),

    keras.callbacks.EarlyStopping(
        monitor="val_loss",
        patience=5,
        restore_best_weights=True,
        verbose=1
    ),

    keras.callbacks.ReduceLROnPlateau(
        monitor="val_loss",
        factor=0.3,
        patience=2,
        min_lr=1e-7,
        verbose=1
    )
]

# =========================
# TRAIN
# =========================

print("\nTraining device:")
if gpus:
    print("NVIDIA GPU:", gpus[0])
else:
    print("CPU")

print("\nStarting training...\n")

history = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=EPOCHS,
    class_weight=class_weights,
    callbacks=callbacks
)

# =========================
# SAVE FINAL MODEL
# =========================

final_model_path = os.path.join(
    MODEL_DIR,
    "efficientnetb0_skin_final.keras"
)

model.save(final_model_path)

print("\n========================================")
print("TRAINING COMPLETE")
print("========================================")
print("Final model:")
print(final_model_path)
