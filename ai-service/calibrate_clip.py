import urllib.request
import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
import io

print("Loading CLIP...")
device = "cuda" if torch.cuda.is_available() else "cpu"
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
print("Model loaded.")

urls = {
    "lesion_1": "https://upload.wikimedia.org/wikipedia/commons/6/6c/Melanoma.jpg",
    "lesion_2": "https://upload.wikimedia.org/wikipedia/commons/d/d4/Basal_cell_carcinoma_1.jpg",
    "portrait": "https://upload.wikimedia.org/wikipedia/commons/a/a0/Pierre-Person.jpg",
    "object": "https://upload.wikimedia.org/wikipedia/commons/4/4c/Bananas.jpg",
    "landscape": "https://upload.wikimedia.org/wikipedia/commons/3/35/Neckertal_20150527-6384.jpg",
    "screenshot": "https://upload.wikimedia.org/wikipedia/commons/6/6f/GNOME_Web_43_screenshot.png"
}

prompts = [
    "a close-up photo of a skin lesion or skin disease",
    "a portrait of a person's face",
    "a landscape or scenery",
    "a random everyday object",
    "a screenshot or text"
]

def fetch_image(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    response = urllib.request.urlopen(req)
    return Image.open(io.BytesIO(response.read())).convert("RGB")

for name, url in urls.items():
    print(f"\n--- Testing {name} ---")
    try:
        image = fetch_image(url)
    except Exception as e:
        print(f"Failed to fetch {name}: {e}")
        continue
        
    inputs = processor(text=prompts, images=image, return_tensors="pt", padding=True)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    
    with torch.no_grad():
        outputs = model(**inputs)
        logits_per_image = outputs.logits_per_image
        probs = logits_per_image.softmax(dim=1).squeeze().tolist()
        
    skin_score = probs[0]
    non_skin_scores = probs[1:]
    max_non_skin_score = max(non_skin_scores)
    
    print(f"Skin score: {skin_score:.4f}")
    print(f"Strongest non-skin score: {max_non_skin_score:.4f} ({prompts[probs.index(max_non_skin_score)]})")
    print("All probs:")
    for p, pr in zip(prompts, probs):
        print(f"  {pr:.4f} : {p}")
