"""
Sentiment scoring using HuggingFace model with proper 512-token chunking.

Model: mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis
"""
from functools import lru_cache
from transformers import pipeline, AutoTokenizer

# Model configuration
MODEL_NAME = "mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis"
MAX_TOKENS = 512
CHUNK_OVERLAP = 64
MAX_CHUNKS = 6
BATCH_SIZE = 16


@lru_cache(maxsize=1)
def get_tokenizer():
    """Load the tokenizer (cached)."""
    return AutoTokenizer.from_pretrained(MODEL_NAME)


@lru_cache(maxsize=1)
def get_sentiment_pipeline():
    """Load the sentiment model pipeline (cached)."""
    print(f"Loading sentiment model: {MODEL_NAME}")
    return pipeline("sentiment-analysis", model=MODEL_NAME)


def chunk_text_to_512_tokens(text: str) -> list[str]:
    """
    Split text into chunks of max 512 tokens using the model's tokenizer.

    Args:
        text: Input text to chunk

    Returns:
        List of text chunks, each fitting within 512 tokens
    """
    if not text or not text.strip():
        return []

    tokenizer = get_tokenizer()

    # Tokenize without special tokens to get raw token count
    token_ids = tokenizer.encode(text, add_special_tokens=False)

    # If text fits in one chunk, return as-is
    if len(token_ids) <= MAX_TOKENS:
        return [text]

    # Calculate step size with overlap
    step = MAX_TOKENS - CHUNK_OVERLAP

    chunks = []
    for i in range(0, len(token_ids), step):
        chunk_ids = token_ids[i:i + MAX_TOKENS]
        chunk_text = tokenizer.decode(chunk_ids, skip_special_tokens=True)
        chunks.append(chunk_text)

        # Stop at MAX_CHUNKS to prevent super long articles from taking too long
        if len(chunks) >= MAX_CHUNKS:
            break

    return chunks


def score_chunks(chunks: list[str]) -> list[dict]:
    """
    Score multiple text chunks in a batch.

    Args:
        chunks: List of text chunks

    Returns:
        List of raw model outputs (label + score for each chunk)
    """
    if not chunks:
        return []

    pipe = get_sentiment_pipeline()

    # Run the pipeline on all chunks at once
    results = pipe(
        chunks,
        truncation=True,
        max_length=MAX_TOKENS,
        batch_size=min(BATCH_SIZE, len(chunks))
    )

    return results


def label_to_signed_score(label: str, confidence: float) -> float:
    """
    Convert model label + confidence to signed score in [-1, +1].

    POSITIVE => +confidence
    NEGATIVE => -confidence
    NEUTRAL => 0
    """
    label_upper = label.upper()
    if label_upper == "POSITIVE":
        return confidence
    elif label_upper == "NEGATIVE":
        return -confidence
    else:  # NEUTRAL or unknown
        return 0.0


def aggregate_chunk_scores(results: list[dict]) -> dict:
    """
    Aggregate multiple chunk scores into a single article score.

    Aggregation rule:
    - For each chunk: signed = +conf / -conf / 0 based on label
    - Weighted average by confidence: final_score = sum(signed_i * conf_i) / sum(conf_i)
    - Final label thresholds: >+0.1 POSITIVE, <-0.1 NEGATIVE, else NEUTRAL
    - Final confidence: mean of all chunk confidences

    Args:
        results: List of model outputs with 'label' and 'score' keys

    Returns:
        Dict with sentiment_label, sentiment_score, confidence, chunks_used
    """
    if not results:
        return {
            "sentiment_label": "NEUTRAL",
            "sentiment_score": 0.0,
            "confidence": 0.0,
            "chunks_used": 0,
        }

    # Calculate weighted average
    weighted_sum = 0.0
    confidence_sum = 0.0

    for r in results:
        label = r.get("label", "NEUTRAL")
        conf = r.get("score", 0.0)
        signed = label_to_signed_score(label, conf)
        weighted_sum += signed * conf
        confidence_sum += conf

    # Final score
    if confidence_sum > 0:
        final_score = weighted_sum / confidence_sum
    else:
        final_score = 0.0

    # Final label based on thresholds
    if final_score > 0.1:
        final_label = "POSITIVE"
    elif final_score < -0.1:
        final_label = "NEGATIVE"
    else:
        final_label = "NEUTRAL"

    # Final confidence: mean of chunk confidences
    final_confidence = confidence_sum / len(results)

    return {
        "sentiment_label": final_label,
        "sentiment_score": round(final_score, 4),
        "confidence": round(final_confidence, 4),
        "chunks_used": len(results),
    }


def score_text(text: str) -> dict:
    """
    Score a single text for sentiment using proper 512-token chunking.

    Args:
        text: Text to score

    Returns:
        Dict with:
        - sentiment_label: "POSITIVE" | "NEUTRAL" | "NEGATIVE"
        - sentiment_score: -1.0 to +1.0
        - confidence: 0.0 to 1.0
        - chunks_used: number of chunks processed
    """
    if not text or not text.strip():
        return {
            "sentiment_label": "NEUTRAL",
            "sentiment_score": 0.0,
            "confidence": 0.0,
            "chunks_used": 0,
        }

    try:
        # Chunk the text
        chunks = chunk_text_to_512_tokens(text)

        if not chunks:
            return {
                "sentiment_label": "NEUTRAL",
                "sentiment_score": 0.0,
                "confidence": 0.0,
                "chunks_used": 0,
            }

        # Score all chunks
        results = score_chunks(chunks)

        # Aggregate into final score
        return aggregate_chunk_scores(results)

    except Exception as e:
        print(f"Error scoring text: {e}")
        return {
            "sentiment_label": "NEUTRAL",
            "sentiment_score": 0.0,
            "confidence": 0.0,
            "chunks_used": 0,
        }


def score_batch(texts: list[str]) -> list[dict]:
    """Score multiple texts. Each text is chunked and aggregated independently."""
    return [score_text(t) for t in texts]


# Legacy aliases for compatibility
def score_text_legacy(text: str) -> dict:
    """Legacy interface - returns label/confidence/sentiment_score."""
    result = score_text(text)
    return {
        "label": result["sentiment_label"],
        "confidence": result["confidence"],
        "sentiment_score": result["sentiment_score"],
    }


if __name__ == "__main__":
    # Test the sentiment scoring
    print("Testing sentiment scoring with chunking...\n")

    test_texts = [
        "Apple stock soars after strong earnings report.",
        "Tesla faces challenges amid increasing competition.",
        "The market remained relatively stable today.",
        "",  # Empty text
        "A" * 5000,  # Long text to test chunking
    ]

    for i, text in enumerate(test_texts):
        preview = text[:50] + "..." if len(text) > 50 else text
        print(f"Text {i + 1}: {preview!r}")
        result = score_text(text)
        print(f"  Label: {result['sentiment_label']}")
        print(f"  Score: {result['sentiment_score']}")
        print(f"  Confidence: {result['confidence']}")
        print(f"  Chunks: {result['chunks_used']}")
        print()
