import pandas as pd
from pathlib import Path

# File paths
BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "dataset" / "SMSSpamCollection"
OUTPUT_PATH = BASE_DIR / "dataset" / "sms_cleaned.csv"

# Load original dataset
df = pd.read_csv(
    DATASET_PATH,
    sep="\t",
    header=None,
    names=["label", "text"]
)

print("Original Dataset:", df.shape)

# Check conflicting labels for identical messages
conflicts = (
    df.groupby("text")["label"]
    .nunique()
    .gt(1)
    .sum()
)

print("Messages with conflicting labels:", conflicts)

# Remove exact duplicate rows
df = df.drop_duplicates().copy()

# Remove empty messages, if any
df = df.dropna(subset=["text", "label"])
df["text"] = df["text"].astype(str).str.strip()
df = df[df["text"] != ""]

# Convert labels into numerical values
df["label"] = df["label"].map({
    "ham": 0,
    "spam": 1
})

# Save cleaned dataset
df.to_csv(OUTPUT_PATH, index=False)

print("\nCleaning Completed!")
print("Cleaned Dataset Shape:", df.shape)

print("\nLabel Distribution:")
print(df["label"].value_counts())

print("\nSaved File:", OUTPUT_PATH)