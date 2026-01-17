"""Fetch daily prices using yfinance."""
import yfinance as yf
from datetime import datetime, timedelta

def fetch_daily_prices(ticker: str, days: int = 90) -> list[dict]:
    """
    Fetch daily price data for a ticker using yfinance.

    Returns list of dicts with: date, open, high, low, close, adj_close, volume
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days + 5)  # Buffer for weekends/holidays

    try:
        stock = yf.Ticker(ticker)
        df = stock.history(start=start_date.strftime("%Y-%m-%d"), end=end_date.strftime("%Y-%m-%d"))

        if df.empty:
            print(f"No price data found for {ticker}")
            return []

        results = []
        for date_idx, row in df.iterrows():
            results.append({
                "date": date_idx.strftime("%Y-%m-%d"),
                "open": float(row["Open"]) if row["Open"] else None,
                "high": float(row["High"]) if row["High"] else None,
                "low": float(row["Low"]) if row["Low"] else None,
                "close": float(row["Close"]),
                "adj_close": float(row["Close"]),  # yfinance returns adjusted by default
                "volume": int(row["Volume"]) if row["Volume"] else None,
            })

        return results[-days:]  # Return only requested days

    except Exception as e:
        print(f"Error fetching prices for {ticker}: {e}")
        return []
