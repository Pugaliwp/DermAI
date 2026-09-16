import time
import requests
import subprocess
import json
import os

print("Starting FastAPI server in the background...")
# Use absolute path for uvicorn or rely on virtualenv, here we just use python -m uvicorn to ensure it runs in current env
server_process = subprocess.Popen(["python", "-m", "uvicorn", "main:app", "--port", "8000"])

try:
    print("Waiting for server to start...")
    time.sleep(10) # wait a bit longer for model to load
    
    print("\nTesting /health endpoint:")
    health_response = requests.get("http://127.0.0.1:8000/health")
    print(health_response.json())
    
    # Find a test image
    img_dir = r"D:\full stack\dataset\ISIC2018_Task3_Training_Input"
    test_img_path = os.path.join(img_dir, "ISIC_0024306.jpg")
    
    if not os.path.exists(test_img_path):
        for f in os.listdir(img_dir):
            if f.endswith('.jpg'):
                test_img_path = os.path.join(img_dir, f)
                break
                
    if os.path.exists(test_img_path):
        print(f"\nTesting /predict endpoint with image: {test_img_path}")
        with open(test_img_path, "rb") as img_file:
            files = {"file": (os.path.basename(test_img_path), img_file, "image/jpeg")}
            predict_response = requests.post("http://127.0.0.1:8000/predict", files=files)
            
        print("\nComplete JSON Response:")
        print(json.dumps(predict_response.json(), indent=2))
    else:
        print("\nNo test image found to test /predict")
    
finally:
    print("\nShutting down server...")
    server_process.terminate()
