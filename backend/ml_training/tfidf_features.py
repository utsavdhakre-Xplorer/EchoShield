import pandas as pd
import joblib

from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse import save_npz

BASE_DIR = Path(__file__).resolve().parent

# Load training and testing datasets
train_df = pd.read_csv(BASE_DIR / "train.csv")
test_df = pd.read_csv(BASE_DIR / "test.csv")

X_train = train_df["text"]
X_test = test_df["text"]

# Initialize TF-IDF
tfidf = TfidfVectorizer(
    ngram_range=(1, 2),
    min_df=2,
    max_df=0.95,
    sublinear_tf=True
)

# Learn vocabulary ONLY from training data
X_train_tfidf = tfidf.fit_transform(X_train)

# Transform test data using the same vocabulary
X_test_tfidf = tfidf.transform(X_test)

# Save extracted features
save_npz(BASE_DIR / "X_train_tfidf.npz", X_train_tfidf)
save_npz(BASE_DIR / "X_test_tfidf.npz", X_test_tfidf)

# Save vectorizer for future predictions
joblib.dump(tfidf, BASE_DIR / "tfidf_vectorizer.pkl")

print("TF-IDF Feature Extraction Completed!")

print("\nTraining Matrix Shape:", X_train_tfidf.shape)
print("Testing Matrix Shape:", X_test_tfidf.shape)

print("\nVocabulary Size:", len(tfidf.vocabulary_))

print("\nExample Features:")
print(list(tfidf.vocabulary_.keys())[:15])