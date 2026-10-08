import os
import requests
import statistics
import time

dataset_dir = r"D:\full stack\dataset\ood_dev_set"
pos_dir = os.path.join(dataset_dir, "positive")
neg_dir = os.path.join(dataset_dir, "negative")

def evaluate_folder(folder_path):
    scores = []
    files = [f for f in os.listdir(folder_path) if f.endswith('.jpg') or f.endswith('.jpeg')]
    for file in files:
        file_path = os.path.join(folder_path, file)
        with open(file_path, "rb") as f:
            resp = requests.post("http://127.0.0.1:8001/predict", files={"file": (file, f, "image/jpeg")})
            
        data = resp.json()
        if "skin_score" in data:
            scores.append((file, data["skin_score"]))
        else:
            print(f"Error for {file}: {data}")
            
    return scores

import subprocess
import sys

print("Starting server on port 8001...")
server_proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "main:app", "--port", "8001"])

print("Waiting for server to be ready...")
while True:
    try:
        r = requests.get("http://127.0.0.1:8001/health")
        if r.status_code == 200:
            break
    except:
        pass
    time.sleep(1)
print("Server ready. Testing positive images (ISIC/dermoscopic)...")
pos_scores = evaluate_folder(pos_dir)

print(f"Tested {len(pos_scores)} positive images.")
if pos_scores:
    pos_values = [s[1] for s in pos_scores]
    print(f"Min: {min(pos_values):.4f}")
    print(f"Max: {max(pos_values):.4f}")
    print(f"Mean: {statistics.mean(pos_values):.4f}")
    print(f"Median: {statistics.median(pos_values):.4f}")

print("\nTesting negative images (OOD)...")
neg_scores = evaluate_folder(neg_dir)

print(f"Tested {len(neg_scores)} negative images.")
if neg_scores:
    neg_values = [s[1] for s in neg_scores]
    print(f"Min: {min(neg_values):.4f}")
    print(f"Max: {max(neg_values):.4f}")
    print(f"Mean: {statistics.mean(neg_values):.4f}")
    print(f"Median: {statistics.median(neg_values):.4f}")

print("\n--- DETAILED SCORES ---")
print("POSITIVE:")
for f, s in pos_scores:
    print(f"  {f}: {s:.4f}")
    
print("\nNEGATIVE:")
for f, s in neg_scores:
    print(f"  {f}: {s:.4f}")

server_proc.terminate()
print('Done.')
