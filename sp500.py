"""S&P 500 universe helpers - fetch constituents and top earners."""
import datetime as dt
import pandas as pd
import yfinance as yf
from cachetools import TTLCache

_constituents_cache = TTLCache(maxsize=1, ttl=86400)
_earners_cache = TTLCache(maxsize=64, ttl=3600)


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
    """Return the most recent completed trading day before ref_date."""
    d = ref_date - dt.timedelta(days=1)
    while d.weekday() >= 5:
        d -= dt.timedelta(days=1)
    return d


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
    start = trade_day - dt.timedelta(days=7)
    end = trade_day + dt.timedelta(days=1)

    tickers_str = " ".join(sp["ticker"].tolist())
    raw = yf.download(tickers_str, start=start, end=end,
                      group_by="ticker", threads=True, progress=False)

    records = []
    for _, row in sp.iterrows():
        tk = row["ticker"]
        try:
            hist = raw[tk]["Close"].dropna()
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
