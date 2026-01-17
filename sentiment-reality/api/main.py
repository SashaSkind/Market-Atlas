"""Sentiment Reality API - FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import health, dashboard, stocks

app = FastAPI(title="Sentiment Reality API")

# Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(dashboard.router)
app.include_router(stocks.router)
