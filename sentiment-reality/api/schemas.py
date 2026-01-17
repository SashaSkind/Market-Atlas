"""Pydantic models for API requests/responses."""
from pydantic import BaseModel
from typing import Optional
from datetime import date

# ========== Price Data ==========
class PricePoint(BaseModel):
    date: str  # YYYY-MM-DD
    close: float
    adj_close: Optional[float] = None
    volume: Optional[int] = None

# ========== Sentiment Data ==========
class DailySentiment(BaseModel):
    date: str  # YYYY-MM-DD
    avg_score: float  # [-1, +1]
    article_count: int
    positive_count: int
    neutral_count: int
    negative_count: int

# ========== Metrics ==========
class WindowMetric(BaseModel):
    date_end: str  # YYYY-MM-DD
    corr: Optional[float] = None
    directional_match: Optional[float] = None
    alignment_score: Optional[float] = None
    misalignment_days: Optional[int] = None
    interpretation: Optional[str] = None

# ========== Dashboard Summaries ==========
class SentimentSummary(BaseModel):
    current_score: Optional[float] = None
    trend: Optional[str] = None  # up | down | stable
    dominant_label: Optional[str] = None  # POSITIVE | NEUTRAL | NEGATIVE

class PriceSummary(BaseModel):
    current_price: Optional[float] = None
    period_return: Optional[float] = None

class AlignmentSummary(BaseModel):
    score: Optional[float] = None
    misalignment_days: Optional[int] = None
    interpretation: Optional[str] = None

# ========== Daily Data Point (combined) ==========
class DailyDataPoint(BaseModel):
    date: str
    price: Optional[PricePoint] = None
    sentiment: Optional[DailySentiment] = None
    metric: Optional[WindowMetric] = None

# ========== Dashboard Response ==========
class DashboardData(BaseModel):
    ticker: str
    period: int
    sentiment_summary: SentimentSummary
    price_summary: PriceSummary
    alignment: AlignmentSummary
    daily_data: list[DailyDataPoint]

# ========== Stock Requests ==========
class AddStockRequest(BaseModel):
    ticker: str

class RefreshStockRequest(BaseModel):
    ticker: str

class TaskResponse(BaseModel):
    queued: bool
    task_type: str
    ticker: str
