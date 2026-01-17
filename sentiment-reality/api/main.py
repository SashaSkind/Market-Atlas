from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Sentiment Reality API")

# Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/dashboard/{ticker}")
def get_dashboard(ticker: str, period: str = "7d"):
    # Mock data for now
    return {
        "ticker": ticker,
        "period": period,
        "sentiment_summary": {
            "current_score": 0.35,
            "trend": "up",
            "dominant_label": "POSITIVE"
        },
        "price_summary": {
            "current_price": 450.25,
            "period_return": 2.3
        },
        "alignment": {
            "score": 0.6,
            "misalignment_days": 2,
            "interpretation": "Mostly aligned"
        },
        "daily_data": [
            {
                "date": "2025-01-10",
                "sentiment": {"date": "2025-01-10", "avg_score": 0.2, "article_count": 15, "positive_count": 8, "neutral_count": 5, "negative_count": 2},
                "price": {"date": "2025-01-10", "open": 445.0, "high": 448.0, "low": 443.0, "close": 447.0, "volume": 1000000},
                "alignment": {"date": "2025-01-10", "sentiment_score": 0.2, "price_return": 0.5, "aligned": True, "alignment_score": 0.7}
            },
            {
                "date": "2025-01-11",
                "sentiment": {"date": "2025-01-11", "avg_score": 0.4, "article_count": 20, "positive_count": 12, "neutral_count": 6, "negative_count": 2},
                "price": {"date": "2025-01-11", "open": 447.0, "high": 451.0, "low": 446.0, "close": 450.25, "volume": 1200000},
                "alignment": {"date": "2025-01-11", "sentiment_score": 0.4, "price_return": 0.7, "aligned": True, "alignment_score": 0.8}
            }
        ]
    }
