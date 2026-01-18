// Sentiment label as specified in CLAUDE.md
export type SentimentLabel = 'POSITIVE' | 'NEUTRAL' | 'NEGATIVE'

// ========== Price Data ==========
export interface PricePoint {
  date: string // YYYY-MM-DD
  close: number
  adj_close?: number | null
  volume?: number | null
}

// ========== Sentiment Data ==========
export interface DailySentiment {
  date: string // YYYY-MM-DD
  avg_score: number // [-1, +1]
  article_count: number
  positive_count: number
  neutral_count: number
  negative_count: number
}

// ========== Window Metrics ==========
export interface WindowMetric {
  date_end: string // YYYY-MM-DD
  corr?: number | null // correlation
  directional_match?: number | null // fraction of days signs match
  alignment_score?: number | null // composite [-1, +1]
  misalignment_days?: number | null
  interpretation?: string | null // 'Aligned' | 'Noisy' | 'Misleading'
}

// ========== Dashboard Summaries ==========
export interface SentimentSummary {
  current_score?: number | null
  trend?: 'up' | 'down' | 'stable' | null
  dominant_label?: SentimentLabel | null
}

export interface PriceSummary {
  current_price?: number | null
  period_return?: number | null
}

export interface AlignmentSummary {
  score?: number | null
  misalignment_days?: number | null
  interpretation?: string | null
}

// ========== Daily Data Point (combined) ==========
export interface DailyDataPoint {
  date: string
  price?: PricePoint | null
  sentiment?: DailySentiment | null
  metric?: WindowMetric | null
}

// ========== Headlines ==========
export interface NewsItem {
  id?: string
  title: string
  source?: string | null
  published_at?: string | null
  sentiment_label?: SentimentLabel | null
  sentiment_score?: number | null
  confidence?: number | null
  snippet?: string | null
  url?: string | null
}

// ========== Coverage ==========
export interface Coverage {
  sentiment_days_available: number
  sentiment_period_requested: number
  sentiment_period_used: number
  coverage_start: string | null
  coverage_end: string | null
}

// ========== Dashboard Response ==========
export interface DashboardData {
  ticker: string
  period: number
  sentiment_summary: SentimentSummary
  price_summary: PriceSummary
  alignment: AlignmentSummary
  daily_data: DailyDataPoint[]
  headlines: NewsItem[]
  coverage?: Coverage | null
}

// ========== Stock Management ==========
export interface Stock {
  ticker: string
  is_active: boolean
}

export interface TaskResponse {
  queued: boolean
  task_type: string
  ticker: string
  task_id?: string | null
}

// ========== API Response Wrapper ==========
export interface ApiResponse<T> {
  data: T
  success: boolean
  error?: string
}
