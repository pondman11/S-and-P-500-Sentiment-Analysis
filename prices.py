"""Price data helpers using yfinance."""
import datetime as dt
import requests
import yfinance as yf

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def _make_session() -> requests.Session:
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    try:
        session.get("https://finance.yahoo.com/", timeout=10)
    except Exception:
        pass
    return session


def get_prices(ticker: str, start_date: dt.date, end_date: dt.date) -> list[dict]:
    """
    Fetch daily OHLCV for a single ticker over [start_date, end_date].
    Returns list of {date, open, high, low, close, volume}.
    """
    session = _make_session()
    # Pad one extra day on each side for change calc
    dl_start = start_date - dt.timedelta(days=5)
    dl_end = end_date + dt.timedelta(days=1)

    try:
        hist = yf.download(
            ticker,
            start=dl_start,
            end=dl_end,
            progress=False,
            threads=False,
            session=session,
            timeout=15,
        )
    except Exception as e:
        print(f"[prices] Failed to fetch {ticker}: {e}")
        return []

    if hist is None or hist.empty:
        return []

    records = []
    for idx, row in hist.iterrows():
        d = idx.date() if hasattr(idx, "date") else idx
        if start_date <= d <= end_date:
            records.append({
                "date": d.isoformat(),
                "open": round(float(row["Open"].iloc[0]) if hasattr(row["Open"], "iloc") else float(row["Open"]), 2),
                "high": round(float(row["High"].iloc[0]) if hasattr(row["High"], "iloc") else float(row["High"]), 2),
                "low": round(float(row["Low"].iloc[0]) if hasattr(row["Low"], "iloc") else float(row["Low"]), 2),
                "close": round(float(row["Close"].iloc[0]) if hasattr(row["Close"], "iloc") else float(row["Close"]), 2),
                "volume": int(row["Volume"].iloc[0]) if hasattr(row["Volume"], "iloc") else int(row["Volume"]),
            })
    return records
