"""
Sentiment Model Predictor

Loads the trained financial sentiment model
and predicts sentiment for a news headline.
"""

from pathlib import Path
import joblib


BASE_DIR = Path(__file__).resolve().parents[3]
MODEL_DIR = BASE_DIR / "models"

MODEL_PATH = MODEL_DIR / "sentiment_model.pkl"
VECTORIZER_PATH = MODEL_DIR / "tfidf_vectorizer.pkl"
ENCODER_PATH = MODEL_DIR / "label_encoder.pkl"


if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"Sentiment model not found: {MODEL_PATH}"
    )

if not VECTORIZER_PATH.exists():
    raise FileNotFoundError(
        f"TF-IDF vectorizer not found: {VECTORIZER_PATH}"
    )

if not ENCODER_PATH.exists():
    raise FileNotFoundError(
        f"Label encoder not found: {ENCODER_PATH}"
    )


model = joblib.load(MODEL_PATH)
vectorizer = joblib.load(VECTORIZER_PATH)
label_encoder = joblib.load(ENCODER_PATH)


def predict_sentiment(headline: str):
    """
    Predict sentiment for one headline.
    """

    if not headline or not headline.strip():
        return "neutral"

    vector = vectorizer.transform(
        [headline.strip()]
    )

    prediction = model.predict(vector)

    sentiment = label_encoder.inverse_transform(
        prediction
    )

    return str(
        sentiment[0]
    ).lower()