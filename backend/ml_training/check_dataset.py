import pandas as pd
from pathlib import Path

# Get the folder where this Python file exists
BASE_DIR = Path(__file__).resolve().parent

# Dataset folder
dataset_folder = BASE_DIR / "dataset"

# Find the dataset file
files = list(dataset_folder.glob("SMSSpamCollection*"))

if not files:
    print("Dataset file not found!")
    print("Files present in dataset folder:")

    if dataset_folder.exists():
        for file in dataset_folder.iterdir():
            print(file.name)
    else:
        print("Dataset folder itself does not exist!")

else:
    dataset_path = files[0]

    df = pd.read_csv(
        dataset_path,
        sep="\t",
        header=None,
        names=["label", "text"]
    )

    print("Dataset loaded successfully!")
    print("\nDataset Shape:", df.shape)

    print("\nFirst 5 Messages:")
    print(df.head())

    print("\nLabel Distribution:")
    print(df["label"].value_counts())

    print("\nMissing Values:")
    print(df.isnull().sum())
    
    
    
    
print("\nDuplicate Records:", df.duplicated().sum())

print("\nMissing Values:")
print(df.isnull().sum())

print("\nUnique Labels:")
print(df["label"].unique())



