import json
import csv
import os

v1_path = r'D:\full stack\ai-service\models\hybrid\best_metrics.json'
v2_path = r'D:\full stack\ai-service\models\hybrid_v2\classification_report.csv'
output_csv = r'D:\full stack\ai-service\models\v1_v2_comparison.csv'

classes = ['MEL', 'NV', 'BCC', 'AKIEC', 'BKL', 'DF', 'VASC']

# Load V1
with open(v1_path, 'r') as f:
    v1_data = json.load(f)
v1_report = v1_data['report']

# Load V2
v2_data = {}
with open(v2_path, 'r', newline='') as f:
    reader = csv.reader(f)
    header = next(reader)
    # header is likely: ['', 'precision', 'recall', 'f1-score', 'support']
    for row in reader:
        if not row: continue
        cls_name = row[0]
        if cls_name in classes or cls_name in ['accuracy', 'macro avg', 'weighted avg']:
            v2_data[cls_name] = {
                'precision': float(row[1]),
                'recall': float(row[2]),
                'f1-score': float(row[3]),
                'support': float(row[4]) if len(row)>4 else 0.0
            }

# Build comparison data
comparison_data = []

improved_classes = []
worsened_classes = []

minority_classes = ['MEL', 'BCC', 'AKIEC', 'BKL', 'DF', 'VASC']

v1_minority_f1_sum = 0
v2_minority_f1_sum = 0

for cls in classes:
    v1_prec = v1_report[cls]['precision']
    v1_rec = v1_report[cls]['recall']
    v1_f1 = v1_report[cls]['f1-score']

    v2_prec = v2_data[cls]['precision']
    v2_rec = v2_data[cls]['recall']
    v2_f1 = v2_data[cls]['f1-score']

    diff_prec = v2_prec - v1_prec
    diff_rec = v2_rec - v1_rec
    diff_f1 = v2_f1 - v1_f1

    if diff_f1 > 0:
        better_model = 'V2'
        improved_classes.append(cls)
    elif diff_f1 < 0:
        better_model = 'V1'
        worsened_classes.append(cls)
    else:
        better_model = 'Tie'

    if cls in minority_classes:
        v1_minority_f1_sum += v1_f1
        v2_minority_f1_sum += v2_f1

    comparison_data.append({
        'Class': cls,
        'V1_Precision': v1_prec,
        'V2_Precision': v2_prec,
        'Diff_Precision': diff_prec,
        'V1_Recall': v1_rec,
        'V2_Recall': v2_rec,
        'Diff_Recall': diff_rec,
        'V1_F1': v1_f1,
        'V2_F1': v2_f1,
        'Diff_F1': diff_f1,
        'Better_Model_By_F1': better_model
    })

# Write output CSV
headers = [
    'Class', 'V1_Precision', 'V2_Precision', 'Diff_Precision', 
    'V1_Recall', 'V2_Recall', 'Diff_Recall', 
    'V1_F1', 'V2_F1', 'Diff_F1', 'Better_Model_By_F1'
]

with open(output_csv, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=headers)
    writer.writeheader()
    writer.writerows(comparison_data)

print("Saved comparison to:", output_csv)
print("-" * 120)
# Print table-like output manually since we dropped pandas
header_row = f"{'Class':<8} | {'V1_P':<8} | {'V2_P':<8} | {'Diff_P':<8} | {'V1_R':<8} | {'V2_R':<8} | {'Diff_R':<8} | {'V1_F1':<8} | {'V2_F1':<8} | {'Diff_F1':<8} | {'Better':<8}"
print(header_row)
print("-" * len(header_row))
for row in comparison_data:
    print(f"{row['Class']:<8} | {row['V1_Precision']:<8.4f} | {row['V2_Precision']:<8.4f} | {row['Diff_Precision']:<8.4f} | {row['V1_Recall']:<8.4f} | {row['V2_Recall']:<8.4f} | {row['Diff_Recall']:<8.4f} | {row['V1_F1']:<8.4f} | {row['V2_F1']:<8.4f} | {row['Diff_F1']:<8.4f} | {row['Better_Model_By_F1']:<8}")
print("-" * 120)

v1_minority_f1_avg = v1_minority_f1_sum / len(minority_classes)
v2_minority_f1_avg = v2_minority_f1_sum / len(minority_classes)

mel_v1_recall = v1_report['MEL']['recall']
mel_v2_recall = v2_data['MEL']['recall']

v1_macro_f1 = v1_report['macro avg']['f1-score']
v2_macro_f1 = v2_data['macro avg']['f1-score']
if v2_macro_f1 > v1_macro_f1:
    best_overall = "V2"
else:
    best_overall = "V1"

print(f"CONCLUSION:")
print(f"Best overall validation model (by Macro F1): {best_overall} (V1: {v1_macro_f1:.4f}, V2: {v2_macro_f1:.4f})")
print(f"Classes improved by V2 (F1): {', '.join(improved_classes)}")
print(f"Classes worsened by V2 (F1): {', '.join(worsened_classes)}")
print(f"MEL recall comparison: V1={mel_v1_recall:.4f}, V2={mel_v2_recall:.4f} (Diff: {mel_v2_recall - mel_v1_recall:.4f})")
print(f"Minority-class average F1 comparison: V1={v1_minority_f1_avg:.4f}, V2={v2_minority_f1_avg:.4f} (Diff: {v2_minority_f1_avg - v1_minority_f1_avg:.4f})")
