"""Fetch news headlines - minimal stub for hackathon."""
from datetime import datetime, timedelta
import random

def fetch_headlines(ticker: str, days: int = 7, since_ts: datetime = None) -> list[dict]:
    """
    Fetch news headlines for a ticker.

    For hackathon: returns mock data. In production, use:
    - NewsAPI
    - GDELT
    - RSS feeds (Yahoo Finance, Reuters, etc.)

    Returns list of dicts with: source, source_id, published_at, title, url, snippet
    """
    # TODO: Implement real news fetching
    # For now, generate mock headlines for demo

    if since_ts is None:
        since_ts = datetime.now() - timedelta(days=days)

    mock_headlines = _generate_mock_headlines(ticker, days)
    return mock_headlines


def _generate_mock_headlines(ticker: str, days: int) -> list[dict]:
    """Generate mock headlines for demo purposes."""
    templates = {
        "positive": [
            f"{ticker} shares surge on strong earnings beat",
            f"Analysts upgrade {ticker} citing growth momentum",
            f"{ticker} announces expansion plans, stock rises",
            f"Investors bullish on {ticker} ahead of product launch",
            f"{ticker} outperforms market expectations",
        ],
        "negative": [
            f"{ticker} drops amid broader market selloff",
            f"Concerns grow over {ticker} supply chain issues",
            f"{ticker} faces headwinds from regulatory scrutiny",
            f"Analysts cut {ticker} price target on slowing growth",
            f"{ticker} misses revenue estimates, shares fall",
        ],
        "neutral": [
            f"{ticker} trading flat ahead of Fed decision",
            f"Market watches {ticker} for earnings guidance",
            f"{ticker} holds steady despite sector volatility",
            f"Investors await {ticker} quarterly report",
            f"{ticker} maintains position in mixed trading session",
        ],
    }

    results = []
    base_date = datetime.now()

    for i in range(days * 3):  # ~3 articles per day
        day_offset = i // 3
        sentiment = random.choice(["positive", "negative", "neutral"])
        title = random.choice(templates[sentiment])

        results.append({
            "source": random.choice(["Reuters", "Bloomberg", "Yahoo Finance", "MarketWatch"]),
            "source_id": f"mock_{ticker}_{i}",
            "published_at": (base_date - timedelta(days=day_offset, hours=random.randint(0, 12))).isoformat(),
            "title": title,
            "url": f"https://example.com/news/{ticker.lower()}/{i}",
            "snippet": f"Full article about {ticker}...",
        })

    return results
