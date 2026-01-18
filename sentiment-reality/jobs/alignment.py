from db import execute
import numpy as np
import query_db as qdb
from db import fetch_all

def normalize(num1, num2):
    if num1 is None or num2 is None or num2 == 0:
        return None
    try:
        normalized = np.log(num1 / num2)
        normalized = np.tanh(5 * normalized)
        return normalized
    except Exception:
        return None
    
def volume_attention(curr_vol, prev_vol, cap=2.0):
    """
    Returns a 0–1 attention score based on volume change.
    cap = how many times 'normal' volume counts as max attention
    """
    if curr_vol is None or prev_vol is None or prev_vol <= 0:
        return 0.0

    ratio = curr_vol / prev_vol
    return float(np.clip(ratio, 0, cap) / cap)

#WORK ON THIS FUNCTION
'''def aggregate(ticker,time_series):
    #  Σ(alignment_raw × weight) / Σ(weight)
    alignment_raws 
    weights = []
    
    pass
'''

'''
Returns a dictionary with:
    - today_close: float or None
    - today_volume: int or None
    - yesterday_close: float or None
    - yesterday_volume: int or None
    - avg_sentiment: float or None
    - article_count: int

'''
def alignment(info:dict):
    print("[alignment] input info:", info)
    todays_close = info.get("today_close")
    yesterdays_close = info.get("yesterday_close")
    s = info.get("avg_sentiment")  # match key from get_daily_summary
    yesterdays_volume = info.get("yesterday_volume")
    today_volume = info.get("today_volume")
    today_article_count = info.get("today_article_count")
    yesterday_article_count = info.get("yesterday_article_count")

    print(f"  todays_close={todays_close}, yesterdays_close={yesterdays_close}, s={s}")
    print(f"  today_volume={today_volume}, yesterdays_volume={yesterdays_volume}")
    print(f"  today_article_count={today_article_count}, yesterday_article_count={yesterday_article_count}")

    p = normalize(todays_close, yesterdays_close)
    av_norm = volume_attention(today_article_count, yesterday_article_count)
    v_norm = volume_attention(today_volume, yesterdays_volume)

    print(f"  p={p}, av_norm={av_norm}, v_norm={v_norm}")

    if (
        p is None or s is None or av_norm is None or v_norm is None
        or np.isnan(p) or np.isnan(av_norm) or np.isnan(v_norm)
    ):
        print("  [alignment] Required value is None or NaN, returning None.")
        return {"alignment_raw": None, "alignment_weight": None}

    dirr = 1 if np.sign(p) == np.sign(s) else -1
    mag = 1 - np.abs(np.abs(p) - np.abs(s))  # 1 - | |p| - |s| |
    alignment_raw = dirr * mag

    try:
        alignment_weight = np.sqrt(av_norm * v_norm)
    except Exception as e:
        print(f"  [alignment] Exception in sqrt: {e}")
        alignment_weight = None

    print(f"  alignment_raw={alignment_raw}, alignment_weight={alignment_weight}")
    return {"alignment_raw": alignment_raw, "alignment_weight": alignment_weight}

    
def insert_alignment_result(ticker: str, date: str):
    """
    Compute and insert alignment result into alignment_daily table for a ticker and date.
    Calls get_daily_summary and alignment(), then inserts the result.
    """
    try:
        info = qdb.get_daily_summary(ticker, date)
        alignment_dict = alignment(info)
        alignment_raw = alignment_dict.get("alignment_raw")
        alignment_weight = alignment_dict.get("alignment_weight")
        # Convert numpy floats to native Python floats
        if alignment_raw is not None and hasattr(alignment_raw, 'item'):
            alignment_raw = float(alignment_raw)
        if alignment_weight is not None and hasattr(alignment_weight, 'item'):
            alignment_weight = float(alignment_weight)
        rowcount = execute(
            """
            INSERT INTO alignment_daily (ticker, date, alignment_raw, alignment_weight)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (ticker, date) DO UPDATE
                SET alignment_raw = EXCLUDED.alignment_raw,
                    alignment_weight = EXCLUDED.alignment_weight,
                    created_at = now()
            """,
            (ticker, date, alignment_raw, alignment_weight)
        )
        print(f"✓ DB insert/update for {ticker} on {date} (rowcount={rowcount})")
    except Exception as e:
        print(f"❌ ERROR inserting alignment result for {ticker} on {date}: {e}")
        import traceback
        traceback.print_exc()
        return False
    return True

if __name__ == "__main__":
    import sys
    from datetime import datetime

    if len(sys.argv) < 2:
        print("Usage: python alignment.py <TICKER> [YYYY-MM-DD]")
        print("Example: python alignment.py TSLA 2026-01-18")
        sys.exit(1)

    ticker = sys.argv[1].upper()
    if len(sys.argv) > 2:
        date = sys.argv[2]
    else:
        date = datetime.utcnow().strftime("%Y-%m-%d")

    print(f"\n=== Inserting alignment result for {ticker} on {date} ===\n")
    insert_alignment_result(ticker, date)
    print("Done. Check the alignment_daily table for results.\n")