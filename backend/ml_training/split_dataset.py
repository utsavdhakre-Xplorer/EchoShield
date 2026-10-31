import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split

BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "dataset" / "sms_cleaned.csv"

# Load cleaned dataset
df = pd.read_csv(DATASET_PATH)

# Separate input and output
X = df["text"]
y = df["label"]

# Split dataset (80% training, 20% testing)
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

# Save training data
train_df = pd.DataFrame({
    "text": X_train,
    "label": y_train
})

test_df = pd.DataFrame({
    "text": X_test,
    "label": y_test
})

train_df.to_csv(BASE_DIR / "train.csv", index=False)
test_df.to_csv(BASE_DIR / "test.csv", index=False)

print("Dataset Split Completed!")

print("\nTraining Dataset:", len(train_df))
print("Testing Dataset:", len(test_df))

print("\nTraining Labels:")
print(y_train.value_counts())

print("\nTesting Labels:")
print(y_test.value_counts())