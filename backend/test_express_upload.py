import requests
import os
import json

base_url = "http://127.0.0.1:5000"

print("1. Logging into Node.js Express backend...")
login_res = requests.post(f"{base_url}/api/auth/login", json={
    "email": "jane@example.com",
    "password": "admin123"
})

if login_res.status_code != 200:
    print("Login failed:", login_res.text)
    exit(1)

token = login_res.json().get("token")
print("Login successful! Token acquired.")

print("\n2. Finding a test image...")
img_dir = r"D:\full stack\dataset\ISIC2018_Task3_Training_Input"
test_img_path = os.path.join(img_dir, "ISIC_0024306.jpg")
if not os.path.exists(test_img_path):
    for f in os.listdir(img_dir):
        if f.endswith('.jpg'):
            test_img_path = os.path.join(img_dir, f)
            break

print(f"Using image: {test_img_path}")

print("\n3. Sending image to /api/screening/upload...")
headers = {
    "Authorization": f"Bearer {token}"
}

with open(test_img_path, "rb") as f:
    files = {"image": (os.path.basename(test_img_path), f, "image/jpeg")}
    upload_res = requests.post(f"{base_url}/api/screening/upload", headers=headers, files=files)

print("\nComplete JSON Response from Node.js backend:")
print(json.dumps(upload_res.json(), indent=2))
