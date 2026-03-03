"""S&P 500 universe helpers - fetch constituents and top earners."""
import datetime as dt
import time
import pandas as pd
import yfinance as yf
from cachetools import TTLCache

_constituents_cache = TTLCache(maxsize=1, ttl=86400)
_earners_cache = TTLCache(maxsize=64, ttl=3600)
_price_cache = TTLCache(maxsize=4, ttl=3600)  # cache raw price data


def get_sp500_tickers() -> pd.DataFrame:
    """Scrape current S&P 500 constituents from Wikipedia."""
    if "tickers" in _constituents_cache:
        return _constituents_cache["tickers"]
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    tables = pd.read_html(url)
    df = tables[0][["Symbol", "Security", "GICS Sector"]].copy()
    df.columns = ["ticker", "name", "sector"]
    df["ticker"] = df["ticker"].str.replace(".", "-", regex=False)
    _constituents_cache["tickers"] = df
    return df


def _previous_business_day(ref_date: dt.date) -> dt.date:
    """Return the most recent completed trading day on or before ref_date."""
    d = ref_date
    # If today and market hasn't closed yet (before 16:30 ET roughly),
    # go back one more day - but for simplicity, always go back if today
    if d == dt.date.today():
        d -= dt.timedelta(days=1)
    while d.weekday() >= 5:
        d -= dt.timedelta(days=1)
    return d


def get_default_date() -> dt.date:
    """Return the prior business day (for use as default date picker value)."""
    return _previous_business_day(dt.date.today())


def _download_in_batches(tickers: list[str], start, end,
                         batch_size: int = 50, max_retries: int = 3) -> dict:
    """Download price data in small batches to avoid rate limiting."""
    all_data = {}
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i + batch_size]
        tickers_str = " ".join(batch)

        for attempt in range(max_retries):
            try:
                raw = yf.download(tickers_str, start=start, end=end,
                                  group_by="ticker", threads=True,
                                  progress=False)
                if raw is not None and not raw.empty:
                    # For single ticker, yf.download doesn't nest by ticker
                    if len(batch) == 1:
                        all_data[batch[0]] = raw
                    else:
                        for tk in batch:
                            try:
                                tk_data = raw[tk]
                                if tk_data is not None and not tk_data.empty:
                                    all_data[tk] = tk_data
                            except (KeyError, TypeError):
                                pass
                break  # success
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2 * (attempt + 1))
                else:
                    print(f"Batch download failed after {max_retries} attempts: {e}")

        # Small delay between batches to avoid rate limits
        if i + batch_size < len(tickers):
            time.sleep(1)

    return all_data


def _get_price_data(tickers: list[str], trade_day: dt.date) -> dict:
    """Fetch price data with caching."""
    cache_key = trade_day.isoformat()
    if cache_key in _price_cache:
        return _price_cache[cache_key]

    start = trade_day - dt.timedelta(days=7)
    end = trade_day + dt.timedelta(days=1)

    data = _download_in_batches(tickers, start=start, end=end)
    _price_cache[cache_key] = data
    return data


def preload_prices(ref_date: dt.date = None):
    """Pre-load and cache price data for all S&P 500 tickers."""
    if ref_date is None:
        ref_date = get_default_date()
    sp = get_sp500_tickers()
    trade_day = _previous_business_day(ref_date)
    _get_price_data(sp["ticker"].tolist(), trade_day)


def get_top_earners(n: int = 10, ref_date: dt.date = None) -> pd.DataFrame:
    """
    Return top-n S&P 500 gainers for the prior business day.
    Columns: ticker, name, sector, close, change_pct
    """
    if ref_date is None:
        ref_date = dt.date.today()
    cache_key = (n, ref_date.isoformat())
    if cache_key in _earners_cache:
        return _earners_cache[cache_key]

    sp = get_sp500_tickers()
    trade_day = _previous_business_day(ref_date)
    all_data = _get_price_data(sp["ticker"].tolist(), trade_day)

    records = []
    for _, row in sp.iterrows():
        tk = row["ticker"]
        try:
            tk_data = all_data.get(tk)
            if tk_data is None:
                continue
            hist = tk_data["Close"].dropna()
            if len(hist) < 2:
                continue
            prev_close = hist.iloc[-2]
            last_close = hist.iloc[-1]
            pct = ((last_close - prev_close) / prev_close) * 100
            records.append({
                "ticker": tk, "name": row["name"], "sector": row["sector"],
                "close": round(float(last_close), 2),
                "change_pct": round(float(pct), 2),
            })
        except (KeyError, IndexError):
            continue

    df = (pd.DataFrame(records)
          .sort_values("change_pct", ascending=False)
          .head(n)
          .reset_index(drop=True))
    _earners_cache[cache_key] = df
    return df
