import pandas as pd
import joblib

from pathlib import Path
from scipy.sparse import load_npz

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)

BASE_DIR = Path(__file__).resolve().parent

# Load TF-IDF features
X_train = load_npz(BASE_DIR / "X_train_tfidf.npz")
X_test = load_npz(BASE_DIR / "X_test_tfidf.npz")

# Load labels
train_df = pd.read_csv(BASE_DIR / "train.csv")
test_df = pd.read_csv(BASE_DIR / "test.csv")

y_train = train_df["label"]
y_test = test_df["label"]

# Initialize Logistic Regression
model = LogisticRegression(
    max_iter=1000,
    class_weight="balanced",
    random_state=42
)

# Train model
print("Training model...")

model.fit(X_train, y_train)

print("Training completed!")

# Make predictions
y_pred = model.predict(X_test)

# Evaluate model
accuracy = accuracy_score(y_test, y_pred)

print("\nModel Evaluation")
print("-------------------------")

print("Accuracy:", round(accuracy * 100, 2), "%")

print("\nClassification Report:")
print(classification_report(
    y_test,
    y_pred,
    target_names=["Legitimate", "Spam"]
))

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))

# Save trained model
joblib.dump(model, BASE_DIR / "scam_classifier.pkl")

print("\nTrained model saved successfully!")