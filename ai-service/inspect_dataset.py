import os
import pandas as pd

DATASET = "../dataset"

csv_files = []

for root, dirs, files in os.walk(DATASET):
    for file in files:
        if file.endswith(".csv"):
            csv_files.append(os.path.join(root, file))

print("\nCSV FILES FOUND:")
for file in csv_files:
    print(file)

for file in csv_files:
    print("\n" + "=" * 60)
    print("FILE:", file)

    df = pd.read_csv(file)

    print("Rows:", len(df))
    print("Columns:", list(df.columns))

    print("\nFirst 5 rows:")
    print(df.head())
