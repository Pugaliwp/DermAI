import os
import pandas as pd

DATASET = "../dataset"

splits = {
    "TRAIN": "ISIC2018_Task3_Training_GroundTruth",
    "VALIDATION": "ISIC2018_Task3_Validation_GroundTruth",
    "TEST": "ISIC2018_Task3_Test_GroundTruth"
}

classes = ["MEL", "NV", "BCC", "AKIEC", "BKL", "DF", "VASC"]

for split, folder in splits.items():

    csv_path = os.path.join(
        DATASET,
        folder,
        folder + ".csv"
    )

    df = pd.read_csv(csv_path)

    print("\n" + "=" * 45)
    print(split)
    print("=" * 45)

    for cls in classes:
        count = int(df[cls].sum())
        print(f"{cls:6} : {count}")

    print(f"TOTAL  : {len(df)}")
