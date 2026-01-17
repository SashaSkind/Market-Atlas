// Sentiment label as specified in CLAUDE.md
export type SentimentLabel = 'POSITIVE' | 'NEUTRAL' | 'NEGATIVE'

// Individual news item with sentiment
export interface NewsItem {
  id: string
  title: string
  source: string
  published_at: string // ISO date string
  sentiment_score: number // [-1, +1]
  sentiment_label: SentimentLabel
  ticker?: string
}

// Daily aggregated sentiment
export interface DailySentiment {
  date: string // YYYY-MM-DD
  avg_score: number // [-1, +1]
  article_count: number
  positive_count: number
  neutral_count: number
  negative_count: number
}

// Price data point
export interface PricePoint {
  date: string // YYYY-MM-DD
  open: number
  high: number
  low: number
  close: number
  volume: number
}

// Alignment metric (sentiment vs price movement)
export interface AlignmentMetric {
  date: string
  sentiment_score: number // [-1, +1]
  price_return: number // percentage
  aligned: boolean // true if both positive or both negative
  alignment_score: number // correlation or simple match score
}

// Dashboard summary response
export interface DashboardData {
  ticker: string
  period: string // e.g., "7d", "30d"
  sentiment_summary: {
    current_score: number
    trend: 'up' | 'down' | 'stable'
    dominant_label: SentimentLabel
  }
  price_summary: {
    current_price: number
    period_return: number
  }
  alignment: {
    score: number // [-1, +1]
    misalignment_days: number
    interpretation: string
  }
  daily_data: Array<{
    date: string
    sentiment: DailySentiment
    price: PricePoint
    alignment: AlignmentMetric
  }>
}

// API response wrapper
export interface ApiResponse<T> {
  data: T
  success: boolean
  error?: string
}
