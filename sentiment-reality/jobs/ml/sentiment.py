"""Sentiment scoring using HuggingFace model."""
from transformers import pipeline
from functools import lru_cache

MODEL_NAME = "mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis"

@lru_cache(maxsize=1)
def get_sentiment_pipeline():
    """Load the sentiment model (cached)."""
    print(f"Loading sentiment model: {MODEL_NAME}")
    return pipeline("sentiment-analysis", model=MODEL_NAME)


def score_text(text: str) -> dict:
    """
    Score a single text for sentiment.

    Returns: {
        "label": "POSITIVE" | "NEUTRAL" | "NEGATIVE",
        "confidence": 0.0-1.0,
        "sentiment_score": -1.0 to +1.0
    }
    """
    if not text or not text.strip():
        return {
            "label": "NEUTRAL",
            "confidence": 0.0,
            "sentiment_score": 0.0,
        }

    try:
        pipe = get_sentiment_pipeline()
        result = pipe(text[:512])[0]  # Truncate to model max length

        label = result["label"].upper()
        confidence = result["score"]

        # Normalize to [-1, +1]
        # Model outputs: positive, negative, neutral
        if label == "POSITIVE":
            sentiment_score = confidence
        elif label == "NEGATIVE":
            sentiment_score = -confidence
        else:  # NEUTRAL
            sentiment_score = 0.0

        # Ensure label is one of our standard labels
        if label not in ("POSITIVE", "NEUTRAL", "NEGATIVE"):
            label = "NEUTRAL"

        return {
            "label": label,
            "confidence": round(confidence, 4),
            "sentiment_score": round(sentiment_score, 4),
        }

    except Exception as e:
        print(f"Error scoring text: {e}")
        return {
            "label": "NEUTRAL",
            "confidence": 0.0,
            "sentiment_score": 0.0,
        }


def score_batch(texts: list[str]) -> list[dict]:
    """Score multiple texts efficiently."""
    return [score_text(t) for t in texts]
