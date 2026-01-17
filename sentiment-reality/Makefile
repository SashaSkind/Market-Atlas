# ============================================
# Sentiment Reality - Makefile
# ============================================
# Standardized commands for development
#
# Usage:
#   make get       - One-time setup (install deps)
#   make run       - Run frontend + backend dev servers
#   make worker    - Run background job worker
#   make refresh ticker=TSLA - Trigger stock refresh
#   make help      - Show available commands
# ============================================

.PHONY: get run worker refresh help frontend backend stop

# Default target
.DEFAULT_GOAL := help

# ============================================
# get - One-time setup for new developers
# ============================================
# Installs all dependencies (idempotent - safe to run multiple times)
get:
	@echo "📦 Installing frontend dependencies..."
	cd web && npm install
	@echo ""
	@echo "🐍 Setting up Python virtual environment..."
	@if [ ! -d "api/.venv" ]; then \
		python3 -m venv api/.venv; \
		echo "Created new virtual environment at api/.venv"; \
	else \
		echo "Virtual environment already exists"; \
	fi
	@echo ""
	@echo "📚 Installing backend dependencies..."
	. api/.venv/bin/activate && pip install -r api/requirements.txt
	@echo ""
	@echo "📚 Installing jobs dependencies..."
	. api/.venv/bin/activate && pip install -r jobs/requirements.txt
	@echo ""
	@echo "✅ Setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Copy .env.example to .env and add your credentials"
	@echo "  2. Run 'make run' to start development servers"

# ============================================
# run - Run frontend + backend dev servers
# ============================================
# Starts both servers concurrently. Ctrl+C stops everything.
run:
	@echo "🚀 Starting development servers..."
	@echo ""
	@echo "  Frontend → http://localhost:3000"
	@echo "  Backend  → http://localhost:8000"
	@echo "  API Docs → http://localhost:8000/docs"
	@echo ""
	@echo "Press Ctrl+C to stop all servers"
	@echo "============================================"
	@trap 'kill 0' INT; \
	(cd web && npm run dev) & \
	(. api/.venv/bin/activate && cd api && uvicorn main:app --reload --port 8000) & \
	wait

# ============================================
# frontend - Run only the frontend
# ============================================
frontend:
	@echo "🌐 Starting frontend server..."
	@echo "  → http://localhost:3000"
	cd web && npm run dev

# ============================================
# backend - Run only the backend
# ============================================
backend:
	@echo "⚡ Starting backend server..."
	@echo "  → http://localhost:8000"
	@echo "  → http://localhost:8000/docs (API docs)"
	. api/.venv/bin/activate && cd api && uvicorn main:app --reload --port 8000

# ============================================
# worker - Run the background job worker
# ============================================
# For testing ingestion/sentiment/aggregation locally
worker:
	@echo "⚙️  Starting background job worker..."
	@echo "Worker will poll for tasks and process them"
	@echo "Press Ctrl+C to stop"
	@echo "============================================"
	. api/.venv/bin/activate && cd jobs && python worker.py

# ============================================
# refresh - Trigger manual stock refresh
# ============================================
# Usage: make refresh ticker=TSLA
refresh:
ifndef ticker
	@echo "❌ Error: ticker is required"
	@echo ""
	@echo "Usage: make refresh ticker=TSLA"
	@exit 1
else
	@echo "🔄 Triggering refresh for $(ticker)..."
	@curl -s -X POST http://localhost:8000/stocks/refresh \
		-H "Content-Type: application/json" \
		-d '{"ticker": "$(ticker)"}' | python3 -m json.tool || echo "Failed - is the backend running?"
endif

# ============================================
# add - Add a new stock to track
# ============================================
# Usage: make add ticker=AAPL
add:
ifndef ticker
	@echo "❌ Error: ticker is required"
	@echo ""
	@echo "Usage: make add ticker=AAPL"
	@exit 1
else
	@echo "➕ Adding $(ticker) to tracked stocks..."
	@curl -s -X POST http://localhost:8000/stocks \
		-H "Content-Type: application/json" \
		-d '{"ticker": "$(ticker)"}' | python3 -m json.tool || echo "Failed - is the backend running?"
endif

# ============================================
# health - Check if backend is running
# ============================================
health:
	@echo "🏥 Checking backend health..."
	@curl -s http://localhost:8000/health | python3 -m json.tool || echo "Backend not running"

# ============================================
# help - Show available commands
# ============================================
help:
	@echo "============================================"
	@echo "Sentiment Reality - Available Commands"
	@echo "============================================"
	@echo ""
	@echo "Setup:"
	@echo "  make get              Install all dependencies (run once)"
	@echo ""
	@echo "Development:"
	@echo "  make run              Run frontend + backend together"
	@echo "  make frontend         Run only frontend (port 3000)"
	@echo "  make backend          Run only backend (port 8000)"
	@echo "  make worker           Run background job worker"
	@echo ""
	@echo "Stock Management:"
	@echo "  make add ticker=TSLA      Add stock to track (backfill)"
	@echo "  make refresh ticker=TSLA  Refresh stock data"
	@echo ""
	@echo "Utilities:"
	@echo "  make health           Check if backend is running"
	@echo "  make help             Show this help message"
	@echo ""
