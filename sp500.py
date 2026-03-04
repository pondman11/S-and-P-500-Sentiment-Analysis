"""S&P 500 universe helpers - fetch constituents and top earners."""
import datetime as dt
import io
import time
import requests
import pandas as pd
import yfinance as yf
from cachetools import TTLCache

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

_constituents_cache = TTLCache(maxsize=1, ttl=86400)
_earners_cache = TTLCache(maxsize=64, ttl=3600)
_price_cache = TTLCache(maxsize=4, ttl=3600)  # cache raw price data


def get_sp500_tickers() -> pd.DataFrame:
    """Scrape current S&P 500 constituents from Wikipedia."""
    if "tickers" in _constituents_cache:
        return _constituents_cache["tickers"]
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    resp.raise_for_status()
    tables = pd.read_html(io.StringIO(resp.text))
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


def _download_individually(tickers: list[str], start, end,
                           max_retries: int = 3, delay: float = 0.4) -> dict:
    """Download price data one ticker at a time to avoid rate limiting."""
    all_data = {}
    for idx, tk in enumerate(tickers):
        for attempt in range(max_retries):
            try:
                ticker_obj = yf.Ticker(tk)
                hist = ticker_obj.history(start=start, end=end, auto_adjust=True)
                if hist is not None and not hist.empty:
                    all_data[tk] = hist
                break  # success (even if empty)
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2 * (attempt + 1))
                else:
                    print(f"Failed to download {tk} after {max_retries} attempts: {e}")
        # Rate-limit: small delay between requests
        if idx < len(tickers) - 1:
            time.sleep(delay)
    return all_data


def _get_price_data(tickers: list[str], trade_day: dt.date) -> dict:
    """Fetch price data with caching."""
    cache_key = trade_day.isoformat()
    if cache_key in _price_cache:
        return _price_cache[cache_key]

    start = trade_day - dt.timedelta(days=7)
    end = trade_day + dt.timedelta(days=1)

    data = _download_individually(tickers, start=start, end=end)
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
