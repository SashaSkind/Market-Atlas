"""
Query price, volume, sentiment, and article count for a given stock symbol and date.
"""
from datetime import datetime, timedelta
from db import fetch_all, is_configured

def get_daily_summary(symbol: str, date: str) -> dict:
	"""
	Returns a dictionary with:
		- today_close: float or None
		- today_volume: int or None
		- yesterday_close: float or None
		- yesterday_volume: int or None
		- avg_sentiment: float or None
		- article_count: int

	Args:
		symbol: Stock ticker (e.g., 'TSLA')
		date: Date string in 'YYYY-MM-DD' format (UTC)
	"""
	if not is_configured():
		raise RuntimeError("Database not configured. Set DATABASE_URL in .env")

	# Parse date and get yesterday
	dt = datetime.strptime(date, "%Y-%m-%d")
	yesterday = (dt - timedelta(days=1)).strftime("%Y-%m-%d")

	# Query today's price/volume
	today_result = fetch_all(
		"""
		SELECT close, volume FROM prices_daily
		WHERE ticker = %s AND date = %s
		LIMIT 1
		""",
		(symbol, date)
	)
	today_close = today_result[0]["close"] if today_result else None
	today_volume = today_result[0]["volume"] if today_result else None

	# Query yesterday's price/volume
	yest_result = fetch_all(
		"""
		SELECT close, volume FROM prices_daily
		WHERE ticker = %s AND date = %s
		LIMIT 1
		""",
		(symbol, yesterday)
	)
	yesterday_close = yest_result[0]["close"] if yest_result else None
	yesterday_volume = yest_result[0]["volume"] if yest_result else None

	# Query daily sentiment aggregate for today
	sentiment_result = fetch_all(
		"""
		SELECT sentiment_avg, article_count FROM daily_agg
		WHERE ticker = %s AND date = %s
		LIMIT 1
		""",
		(symbol, date)
	)
	avg_sentiment = sentiment_result[0]["sentiment_avg"] if sentiment_result else None
	article_count = sentiment_result[0]["article_count"] if sentiment_result else 0

	# Query daily sentiment aggregate for yesterday (for article count)
	yest_sentiment_result = fetch_all(
		"""
		SELECT article_count FROM daily_agg
		WHERE ticker = %s AND date = %s
		LIMIT 1
		""",
		(symbol, yesterday)
	)
	yesterday_article_count = yest_sentiment_result[0]["article_count"] if yest_sentiment_result else 0

	return {
		"today_close": today_close,
		"today_volume": today_volume,
		"yesterday_close": yesterday_close,
		"yesterday_volume": yesterday_volume,
		"avg_sentiment": avg_sentiment,
		"article_count": article_count,
		"yesterday_article_count": yesterday_article_count,
	}

if __name__ == "__main__":
	import sys
	from datetime import datetime

	if len(sys.argv) < 2:
		print("Usage: python query_db.py <TICKER> [YYYY-MM-DD]")
		print("Example: python query_db.py TSLA 2026-01-17")
		sys.exit(1)

	symbol = sys.argv[1].upper()
	if len(sys.argv) > 2:
		date = sys.argv[2]
	else:
		date = datetime.utcnow().strftime("%Y-%m-%d")

	print(f"\n=== Querying daily summary for {symbol} on {date} ===\n")
	result = get_daily_summary(symbol, date)
	for k, v in result.items():
		print(f"  {k}: {v}")
	print()