# Sentiment Reality

Analyze when market sentiment diverges from actual market performance.

## Quick Start

```bash
# From the sentiment-reality/ directory (not market-sentiment-analysis/)
cd sentiment-reality

# One-time setup
make get

# Run frontend + backend together
make run
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API docs: http://localhost:8000/docs

## Make Commands

| Command | Description |
|---------|-------------|
| `make get` | Install all dependencies (run once) |
| `make run` | Run frontend + backend together |
| `make frontend` | Run only frontend (port 3000) |
| `make backend` | Run only backend (port 8000) |
| `make worker` | Run background job worker |
| `make add ticker=TSLA` | Add a stock to track |
| `make refresh ticker=TSLA` | Trigger stock data refresh |
| `make health` | Check if backend is running |
| `make help` | Show all available commands |

## Mock Data Mode

By default, the API runs in **mock data mode** (no database required). This is useful for frontend development.

To connect to Supabase:
1. Copy `api/.env.example` to `api/.env`
2. Add your Supabase credentials

## Project Structure

```
sentiment-reality/
├── web/                  # Next.js frontend (TypeScript)
│   ├── app/              # Pages (layout, page, dashboard)
│   ├── components/       # React components
│   │   └── charts/       # PriceChart, SentimentChart, AlignmentChart
│   ├── lib/              # Utilities
│   │   ├── types.ts      # TypeScript interfaces
│   │   └── api.ts        # API client
│   └── styles/           # CSS (currently disabled)
│
├── api/                  # FastAPI backend (Python)
│   ├── main.py           # App entry point
│   ├── routers/          # Route handlers (health, dashboard, stocks)
│   ├── db.py             # Database connection helpers
│   ├── schemas.py        # Pydantic models
│   ├── sql/schema.sql    # Database schema (run in Supabase)
│   └── requirements.txt
│
├── jobs/                 # Background jobs (Python)
│   ├── worker.py         # Task queue processor
│   ├── providers.py      # Data fetchers (Yahoo Finance, news)
│   ├── ml.py             # Sentiment scoring (HuggingFace)
│   ├── compute.py        # Aggregation logic
│   └── requirements.txt
│
└── Makefile              # Development commands
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/dashboard/{ticker}` | GET | Dashboard data for a ticker |
| `/stocks` | POST | Add a stock to track (creates backfill task) |
| `/stocks/refresh` | POST | Trigger refresh for a stock |

## Data Types

Sentiment scores are normalized to `[-1, +1]` with labels:
- `POSITIVE` (> 0.1)
- `NEUTRAL` (-0.1 to 0.1)
- `NEGATIVE` (< -0.1)

See `web/lib/types.ts` for full TypeScript interfaces.

## Architecture Rules

1. **No ML in API** - All sentiment scoring runs in `jobs/`, API only reads precomputed data
2. **Frontend fetches only** - No computation or scraping in frontend
3. **Supabase is source of truth** - No local databases

See `CLAUDE.md` for full project guidelines.
