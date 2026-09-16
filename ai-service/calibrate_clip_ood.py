import os
import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
import numpy as np

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

POSITIVE_PROMPTS = [
    "a close-up clinical photograph of a human skin lesion",
    "a dermoscopic photograph of a human skin lesion",
    "a close-up photograph of a mole on human skin",
    "a close-up photograph of an abnormal lesion on human body skin"
]
NEGATIVE_PROMPTS = [
    "a portrait of a person",
    "normal human skin without a lesion",
    "a plant or leaf",
    "an animal",
    "a landscape",
    "a road or vehicle",
    "an everyday object",
    "a screenshot or text",
    "a medical illustration",
    "a microscope or histology image"
]
ALL_PROMPTS = POSITIVE_PROMPTS + NEGATIVE_PROMPTS
NUM_POS = len(POSITIVE_PROMPTS)

dataset_dir = r"D:\full stack\dataset\ood_dev_set"
positive_dir = os.path.join(dataset_dir, "positive")
negative_dir = os.path.join(dataset_dir, "negative")

def process_dir(directory, is_positive):
    scores = []
    if not os.path.exists(directory):
        return scores
    for filename in os.listdir(directory):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            path = os.path.join(directory, filename)
            try:
                image = Image.open(path).convert("RGB")
                inputs = processor(text=ALL_PROMPTS, images=image, return_tensors="pt", padding=True)
                inputs = {k: v.to(device) for k, v in inputs.items()}
                
                with torch.no_grad():
                    outputs = model(**inputs)
                    probs = outputs.logits_per_image.softmax(dim=1).squeeze().tolist()
                
                pos_score = sum(probs[:NUM_POS])
                scores.append(pos_score)
                print(f"{'POS' if is_positive else 'NEG'} Image: {filename} -> Pos Score: {pos_score:.4f}")
            except Exception as e:
                print(f"Error processing {filename}: {e}")
    return scores

print("Processing positive images...")
pos_scores = process_dir(positive_dir, True)

print("\nProcessing negative images...")
neg_scores = process_dir(negative_dir, False)

print("\n--- Calibration Results ---")
print(f"Total Positive Images: {len(pos_scores)}")
print(f"Total Negative Images: {len(neg_scores)}")

if not pos_scores or not neg_scores:
    print("Not enough images to calibrate.")
    exit(1)

pos_scores = np.array(pos_scores)
neg_scores = np.array(neg_scores)

print("\nEvaluating thresholds...")
best_threshold = None
best_far = float('inf')
best_frr = float('inf')

for threshold in np.arange(0.0, 1.01, 0.05):
    # False Acceptance Rate: Negatives accepted (score >= threshold)
    far = np.mean(neg_scores >= threshold)
    # False Rejection Rate: Positives rejected (score < threshold)
    frr = np.mean(pos_scores < threshold)
    
    print(f"Threshold: {threshold:.2f} -> FAR (False Accept): {far*100:.1f}%, FRR (False Reject): {frr*100:.1f}%")
    
    # We want 0% FAR, and minimize FRR
    if far == 0.0:
        if best_threshold is None or frr < best_frr:
            best_threshold = threshold
            best_frr = frr

print("\n===============================")
if best_threshold is not None:
    print(f"Recommended Threshold (0% FAR): {best_threshold:.2f}")
    print(f"Resulting FRR on Dev Set: {best_frr*100:.1f}%")
else:
    print("Could not find a threshold with 0% FAR!")
print("===============================")
