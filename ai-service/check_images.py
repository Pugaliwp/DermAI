import os
from PIL import Image

DATASET_DIR = "../dataset"

folders = [
    "ISIC2018_Task3_Training_Input",
    "ISIC2018_Task3_Validation_Input",
    "ISIC2018_Task3_Test_Input"
]

print("=" * 60)
print("CHECKING IMAGE FILES IN DATASET DIRECTORY")
print("=" * 60)

total_images = 0

for folder in folders:
    folder_path = os.path.join(DATASET_DIR, folder)
    if not os.path.exists(folder_path):
        print(f"\n[!] Folder not found: {folder_path}")
        continue
    
    images = [f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    num_images = len(images)
    total_images += num_images
    print(f"\nFolder: {folder}")
    print(f"Total Image Files Found: {num_images}")
    
    if num_images > 0:
        sample_img_path = os.path.join(folder_path, images[0])
        try:
            with Image.open(sample_img_path) as img:
                print(f"Sample Image: {images[0]} | Dimensions: {img.size} (WxH) | Format: {img.format} | Mode: {img.mode}")
        except Exception as e:
            print(f"Error opening sample image {images[0]}: {e}")

print("\n" + "=" * 60)
print(f"TOTAL IMAGES ACROSS ALL INPUT FOLDERS: {total_images}")
print("=" * 60)
