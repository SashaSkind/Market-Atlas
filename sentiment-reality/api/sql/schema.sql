-- ============================================
-- H) alignment_daily - daily alignment results
-- ============================================
CREATE TABLE IF NOT EXISTS alignment_daily (
    ticker TEXT NOT NULL,
    date DATE NOT NULL,
    alignment_raw DOUBLE PRECISION NOT NULL,
    alignment_weight DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (ticker, date)
);

CREATE INDEX IF NOT EXISTS idx_alignment_daily_ticker_date
    ON alignment_daily(ticker, date);
-- Sentiment Reality Database Schema
--
-- Notes:
-- - All timestamps are stored in UTC (TIMESTAMPTZ)
-- - sentiment_score is normalized to [-1, +1]
-- - API is DB-only; jobs do fetching/scoring
-- - Run this against Supabase Postgres

-- ============================================
-- A) tracked_stocks - stocks we're monitoring
-- ============================================
CREATE TABLE IF NOT EXISTS tracked_stocks (
    ticker TEXT PRIMARY KEY,
    added_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_active BOOLEAN NOT NULL DEFAULT true
);

-- ============================================
-- B) tasks - job queue (polled by GitHub Actions worker)
-- ============================================
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_type TEXT NOT NULL,  -- BACKFILL_STOCK | REFRESH_STOCK | DAILY_UPDATE_ALL
    ticker TEXT NULL,         -- null for global tasks
    status TEXT NOT NULL DEFAULT 'PENDING',  -- PENDING | RUNNING | DONE | ERROR
    priority INT NOT NULL DEFAULT 0,
    payload JSONB NULL,
    attempts INT NOT NULL DEFAULT 0,
    error TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tasks_status_priority_created
    ON tasks(status, priority DESC, created_at ASC);
CREATE INDEX IF NOT EXISTS idx_tasks_ticker_status
    ON tasks(ticker, status);

-- ============================================
-- C) prices_daily - historical and daily prices
-- ============================================
CREATE TABLE IF NOT EXISTS prices_daily (
    ticker TEXT NOT NULL,
    date DATE NOT NULL,
    open DOUBLE PRECISION NULL,
    high DOUBLE PRECISION NULL,
    low DOUBLE PRECISION NULL,
    close DOUBLE PRECISION NOT NULL,
    adj_close DOUBLE PRECISION NULL,
    volume BIGINT NULL,
    return_1d DOUBLE PRECISION NULL,  -- computed by jobs
    PRIMARY KEY (ticker, date)
);

CREATE INDEX IF NOT EXISTS idx_prices_ticker_date
    ON prices_daily(ticker, date);

-- ============================================
-- D) items - raw articles/posts
-- ============================================
CREATE TABLE IF NOT EXISTS items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker TEXT NOT NULL,
    source TEXT NOT NULL,
    source_id TEXT NULL,
    published_at TIMESTAMPTZ NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    snippet TEXT NULL,
    current_price DOUBLE PRECISION NULL,
    price_timestamp TIMESTAMPTZ NULL,
    price_change DOUBLE PRECISION NULL,
    price_direction TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT unique_items_source_url UNIQUE (source, url)
);

CREATE INDEX IF NOT EXISTS idx_items_ticker_published
    ON items(ticker, published_at);

-- ============================================
-- E) item_scores - ML sentiment outputs (append-only per model)
-- ============================================
CREATE TABLE IF NOT EXISTS item_scores (
    item_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    model TEXT NOT NULL DEFAULT 'hf_fin_v1',
    sentiment_label TEXT NOT NULL,  -- POSITIVE | NEUTRAL | NEGATIVE
    sentiment_score DOUBLE PRECISION NOT NULL,  -- normalized to [-1, +1]
    confidence DOUBLE PRECISION NOT NULL,  -- 0..1
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT unique_item_model UNIQUE (item_id, model)
);

CREATE INDEX IF NOT EXISTS idx_item_scores_model_created
    ON item_scores(model, created_at);

-- ============================================
-- F) daily_agg - daily sentiment aggregates for charts
-- ============================================
CREATE TABLE IF NOT EXISTS daily_agg (
    ticker TEXT NOT NULL,
    date DATE NOT NULL,
    sentiment_avg DOUBLE PRECISION NOT NULL,
    article_count INT NOT NULL,
    positive_count INT NOT NULL,
    neutral_count INT NOT NULL,
    negative_count INT NOT NULL,
    PRIMARY KEY (ticker, date)
);

CREATE INDEX IF NOT EXISTS idx_daily_agg_ticker_date
    ON daily_agg(ticker, date);

-- ============================================
-- G) metrics_windowed - rolling metrics (e.g., 7-day)
-- ============================================
CREATE TABLE IF NOT EXISTS metrics_windowed (
    ticker TEXT NOT NULL,
    date_end DATE NOT NULL,
    window_days INT NOT NULL,
    corr DOUBLE PRECISION NULL,
    directional_match DOUBLE PRECISION NULL,
    alignment_score DOUBLE PRECISION NULL,
    misalignment_days INT NULL,
    interpretation TEXT NULL,
    PRIMARY KEY (ticker, date_end, window_days)
);

CREATE INDEX IF NOT EXISTS idx_metrics_ticker_end_window
    ON metrics_windowed(ticker, date_end, window_days);


-- Add current_prices table for hourly stock price updates
-- This table stores the most recent price for each tracked stock

CREATE TABLE IF NOT EXISTS current_prices (
    ticker TEXT PRIMARY KEY,
    current_price DOUBLE PRECISION NOT NULL,
    price_change DOUBLE PRECISION NULL,
    price_direction TEXT NULL,  -- 'up', 'down', 'neutral', 'unknown'
    price_timestamp TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_current_prices_updated_at
    ON current_prices(updated_at DESC);