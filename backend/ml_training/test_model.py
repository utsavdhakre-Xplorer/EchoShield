import joblib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Load trained model and TF-IDF vectorizer
model = joblib.load(BASE_DIR / "scam_classifier.pkl")
tfidf = joblib.load(BASE_DIR / "tfidf_vectorizer.pkl")

# New messages for testing
messages = [
    "Your bank account will be blocked. Share your OTP immediately.",
    "Congratulations! You have won a lottery. Pay processing fees now.",
    "Hey, are you coming to college tomorrow?",
    "Your electricity bill payment is successful.",
    "You have won a free iPhone. Click this link to claim your prize."
]

# Convert messages into numerical features
features = tfidf.transform(messages)

# Predict labels and probabilities
predictions = model.predict(features)
probabilities = model.predict_proba(features)

print("\nECHOSHIELD SCAM CLASSIFIER RESULTS")
print("=" * 60)

for message, prediction, probability in zip(
    messages, predictions, probabilities
):
    result = "SPAM / SUSPICIOUS" if prediction == 1 else "LEGITIMATE"

    print("\nMessage:", message)
    print("Prediction:", result)
    print("Spam Probability:", round(probability[1] * 100, 2), "%")