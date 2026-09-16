import urllib.request
import io
import requests
from PIL import Image

def create_image(color=(255,0,0), text=False):
    img = Image.new('RGB', (200, 200), color=color)
    byte_arr = io.BytesIO()
    img.save(byte_arr, format='JPEG')
    return byte_arr.getvalue()

tests = []
# 1. Valid lesion
try:
    with open(r"D:\full stack\dataset\ISIC2018_Task3_Test_Input\ISIC_0034524.jpg", "rb") as f:
        tests.append(("Valid ISIC Lesion", f.read()))
except Exception as e:
    print(f"Skipping valid lesion test: {e}")

# We already calibrated CLIP using real images in `calibrate_clip.py`, so testing dummy objects here is just for ensuring the pipeline returns the right JSON format.
tests.append(("Dummy Portrait (Solid Color)", create_image((200, 150, 150))))
tests.append(("Dummy Object (Solid Color)", create_image((50, 200, 50))))
tests.append(("Corrupted Image", b"not an image file content"))
tests.append(("Screenshot/Text (Blank white)", create_image((255, 255, 255), text=True)))

print("\n--- Running OOD Tests against localhost:8001 ---")
for test_name, img_bytes in tests:
    print(f"\n[Testing] {test_name}")
    try:
        response = requests.post(
            "http://127.0.0.1:8001/predict", 
            files={"file": ("test.jpg", img_bytes, "image/jpeg")}
        )
        status = response.status_code
        res_json = response.json()
        
        if status == 200:
            if res_json.get("accepted") is False:
                print(f"[REJECTED] (Expected): {res_json.get('message')}")
                print(f"  Skin Score: {res_json.get('clip_skin_score'):.4f} | Max Non-Skin: {res_json.get('clip_max_non_skin_score'):.4f}")
                print(f"  All Probs: {res_json.get('clip_probs')}")
            else:
                print(f"[ACCEPTED] Prediction: {res_json.get('disease_name')} (Conf: {res_json.get('confidence'):.4f})")
        elif status == 400:
            print(f"[REJECTED 400] (Expected): {res_json.get('detail')}")
        else:
            print(f"[UNEXPECTED] STATUS {status}: {res_json}")
    except Exception as e:
        print(f"[ERROR] during request: {e}")
