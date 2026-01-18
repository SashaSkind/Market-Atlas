"""Headlines by date endpoint."""
from fastapi import APIRouter, Query
from schemas import NewsItem

router = APIRouter()

# Import DB, fall back gracefully
try:
    from db import query, is_configured
    DB_AVAILABLE = True
except Exception:
    DB_AVAILABLE = False
    def is_configured():
        return False


@router.get("/api/headlines/by-date", response_model=list[NewsItem])
@router.get("/headlines/by-date", response_model=list[NewsItem], include_in_schema=False)
def get_headlines_by_date(
    ticker: str = Query(...),
    date: str = Query(...),  # YYYY-MM-DD
    limit: int = Query(10, ge=1, le=50),
):
    """Get headlines for a specific ticker and date."""
    if not DB_AVAILABLE or not is_configured():
        return []

    rows = query("""
        SELECT
            i.id::text,
            i.title,
            i.source,
            i.published_at,
            s.sentiment_label,
            s.sentiment_score,
            s.confidence,
            i.snippet,
            i.url
        FROM items i
        LEFT JOIN item_scores s ON i.id = s.item_id AND s.model = 'hf_fin_v1'
        WHERE i.ticker = %s AND DATE(i.published_at) = %s
        ORDER BY i.published_at DESC
        LIMIT %s
    """, (ticker, date, limit))

    return [NewsItem(
        id=r.get("id"),
        title=r.get("title", "No title"),
        source=r.get("source"),
        published_at=str(r["published_at"]) if r.get("published_at") else None,
        sentiment_label=r.get("sentiment_label"),
        sentiment_score=float(r["sentiment_score"]) if r.get("sentiment_score") else None,
        confidence=float(r["confidence"]) if r.get("confidence") else None,
        snippet=r.get("snippet"),
        url=r.get("url"),
    ) for r in rows]
