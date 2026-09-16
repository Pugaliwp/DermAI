import time
import requests
import subprocess
import json
import os

dataset_dir = r"D:\full stack\dataset\ood_dev_set"
pos_dir = os.path.join(dataset_dir, "positive")
neg_dir = os.path.join(dataset_dir, "negative")

test_cases = [
    # 1. ISIC lesion -> ACCEPT
    {"name": "ISIC lesion", "path": os.path.join(pos_dir, "ISIC_0024306.jpg"), "expected": "ACCEPT"},
    # 2. Dermoscopic lesion -> ACCEPT
    {"name": "Dermoscopic lesion", "path": os.path.join(pos_dir, "pos_dermoscopic_1789565668648.jpg"), "expected": "ACCEPT"},
    # 3. Portrait -> REJECT
    {"name": "Portrait", "path": os.path.join(neg_dir, "neg_portrait_1789565688385.jpg"), "expected": "REJECT"},
    # 4. Normal arm/hand skin without lesion -> REJECT
    {"name": "Normal arm/hand skin without lesion", "path": os.path.join(neg_dir, "neg_normal_skin_1789565704273.jpg"), "expected": "REJECT"},
    # 5. Leaf -> REJECT
    {"name": "Leaf", "path": os.path.join(neg_dir, "neg_leaf_1789565730993.jpg"), "expected": "REJECT"},
    # 6. Bus -> REJECT
    {"name": "Bus", "path": os.path.join(neg_dir, "neg_bus_1789565768507.jpg"), "expected": "REJECT"},
    # 7. Road -> REJECT
    {"name": "Road", "path": os.path.join(neg_dir, "neg_road_1789565788895.jpg"), "expected": "REJECT"},
    # 8. Animal -> REJECT
    {"name": "Animal", "path": os.path.join(neg_dir, "neg_animal_1789565745801.jpg"), "expected": "REJECT"},
    # 9. Object -> REJECT
    {"name": "Object", "path": os.path.join(neg_dir, "neg_object_1789565824364.jpg"), "expected": "REJECT"},
    # 10. Screenshot -> REJECT
    {"name": "Screenshot", "path": os.path.join(neg_dir, "neg_screenshot_1789565840835.jpg"), "expected": "REJECT"},
    # 11. Medical diagram -> REJECT
    {"name": "Medical diagram", "path": os.path.join(neg_dir, "neg_medical_diagram_1789565919921.jpg"), "expected": "REJECT"},
    # 12. Histology image -> REJECT
    {"name": "Histology image", "path": os.path.join(neg_dir, "neg_histology_1789565935821.jpg"), "expected": "REJECT"}
]

print("Starting FastAPI server in the background for Strict Gate verification...")
server_process = subprocess.Popen(["python", "-m", "uvicorn", "main:app", "--port", "8001"])

try:
    print("Waiting for server to start...")
    # Poll until server is healthy
    server_ready = False
    for _ in range(60): # Wait up to 60 seconds
        try:
            r = requests.get("http://127.0.0.1:8001/health", timeout=2)
            if r.status_code == 200:
                server_ready = True
                break
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
        
    if not server_ready:
        print("Server failed to start in time.")
        exit(1)
        
    print("\nStarting Strict Gate Verification Tests...\n")
    
    for case in test_cases:
        if not os.path.exists(case["path"]):
            print(f"[{case['name']}] Error: File not found {case['path']}")
            continue
            
        with open(case["path"], "rb") as f:
            files = {"file": (os.path.basename(case["path"]), f, "image/jpeg")}
            response = requests.post("http://127.0.0.1:8001/predict", files=files)
        
        data = response.json()
        
        actual = "REJECT" if data.get("accepted") is False else "ACCEPT"
        
        print(f"--- Test: {case['name']} ---")
        if actual == "REJECT":
            print(f"Decision: REJECT (Matches Expected: {case['expected'] == 'REJECT'})")
            print(f"Message: {data.get('message')}")
        else:
            print(f"Decision: ACCEPT (Matches Expected: {case['expected'] == 'ACCEPT'})")
            print(f"Predicted Class: {data.get('predicted_class_code')} (Confidence: {data.get('confidence'):.2f})")
            
        print("")

finally:
    print("\nShutting down server...")
    server_process.terminate()
