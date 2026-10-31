import joblib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Locate the trained model files
BACKEND_DIR = Path(__file__).resolve().parents[2]
TRAINING_DIR = BACKEND_DIR / "ml_training"

MODEL_PATH = TRAINING_DIR / "scam_classifier.pkl"
VECTORIZER_PATH = TRAINING_DIR / "tfidf_vectorizer.pkl"

_model = None
_vectorizer = None


def load_trained_model():
    global _model, _vectorizer

    if _model is None or _vectorizer is None:

        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Model not found: {MODEL_PATH}")

        if not VECTORIZER_PATH.exists():
            raise FileNotFoundError(
                f"Vectorizer not found: {VECTORIZER_PATH}"
            )

        _model = joblib.load(MODEL_PATH)
        _vectorizer = joblib.load(VECTORIZER_PATH)

        logger.info("EchoShield trained scam model loaded successfully")

    return _model, _vectorizer


def predict_scam(text: str):
    if not text or not text.strip():
        return {
            "prediction": "SAFE",
            "scam_probability": 0.0,
            "model_available": True
        }

    model, vectorizer = load_trained_model()

    features = vectorizer.transform([text])

    prediction = int(model.predict(features)[0])
    probabilities = model.predict_proba(features)[0]

    return {
        "prediction": "SCAM" if prediction == 1 else "SAFE",
        "scam_probability": round(float(probabilities[1]), 4),
        "model_available": True
    }