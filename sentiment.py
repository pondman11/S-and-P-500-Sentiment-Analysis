"""Sentiment analysis via news headlines using VADER + Google News RSS."""
import datetime as dt
import feedparser
import requests
from bs4 import BeautifulSoup
from email.utils import parsedate_to_datetime
from urllib.parse import quote
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

_analyzer = SentimentIntensityAnalyzer()


def _parse_pub_date(raw: str) -> dt.date | None:
    """Try to parse an RSS pubDate string into a date."""
    if not raw:
        return None
    try:
        return parsedate_to_datetime(raw).date()
    except Exception:
        return None


def fetch_headlines(ticker: str, company_name: str,
                    start_date: dt.date, end_date: dt.date,
                    max_results: int = 100) -> list[dict]:
    """
    Fetch news headlines from Google News RSS for a company,
    filtered to [start_date, end_date].
    """
    query = quote(f"{company_name} stock {ticker}")
    # Use Google News date-range params (after/before)
    after = start_date.strftime("%Y-%m-%d")
    before = (end_date + dt.timedelta(days=1)).strftime("%Y-%m-%d")
    url = (
        f"https://news.google.com/rss/search?"
        f"q={query}+after:{after}+before:{before}&hl=en-US&gl=US&ceid=US:en"
    )

    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
        feed = feedparser.parse(resp.content)
    except Exception:
        return []

    headlines = []
    for entry in feed.entries[:max_results]:
        title = BeautifulSoup(entry.get("title", ""), "html.parser").get_text()
        source = ""
        if " - " in title:
            parts = title.rsplit(" - ", 1)
            title = parts[0].strip()
            source = parts[1].strip()

        pub_date = _parse_pub_date(entry.get("published", ""))

        headlines.append({
            "title": title,
            "link": entry.get("link", ""),
            "source": source,
            "published": entry.get("published", ""),
            "date": pub_date,
        })

    return headlines


def analyze_sentiment(text: str) -> dict:
    """Return VADER sentiment scores for text."""
    scores = _analyzer.polarity_scores(text)
    if scores["compound"] >= 0.05:
        label = "positive"
    elif scores["compound"] <= -0.05:
        label = "negative"
    else:
        label = "neutral"
    return {"compound": scores["compound"], "label": label, **scores}


def get_sentiment_over_range(
    ticker: str,
    company_name: str,
    start_date: dt.date,
    end_date: dt.date,
) -> dict:
    """
    Fetch headlines in [start_date, end_date], score each, and aggregate by day.

    Returns: {
        ticker, name, start_date, end_date,
        headlines: [...],
        daily: [{date, avg_compound, pos, neg, neu, count}, ...],
        summary: {avg_compound, total, pos, neg, neu}
    }
    """
    headlines = fetch_headlines(ticker, company_name, start_date, end_date)

    # Score each headline
    scored = []
    for h in headlines:
        sent = analyze_sentiment(h["title"])
        scored.append({**h, "sentiment": sent})

    # Group by date
    from collections import defaultdict
    by_day: dict[dt.date, list] = defaultdict(list)
    undated = []
    for h in scored:
        if h["date"] and start_date <= h["date"] <= end_date:
            by_day[h["date"]].append(h)
        elif h["date"] is None:
            undated.append(h)

    # Build daily summaries
    daily = []
    d = start_date
    while d <= end_date:
        day_headlines = by_day.get(d, [])
        compounds = [h["sentiment"]["compound"] for h in day_headlines]
        pos = sum(1 for h in day_headlines if h["sentiment"]["label"] == "positive")
        neg = sum(1 for h in day_headlines if h["sentiment"]["label"] == "negative")
        neu = sum(1 for h in day_headlines if h["sentiment"]["label"] == "neutral")
        daily.append({
            "date": d.isoformat(),
            "avg_compound": round(sum(compounds) / len(compounds), 4) if compounds else None,
            "positive": pos,
            "negative": neg,
            "neutral": neu,
            "count": len(day_headlines),
        })
        d += dt.timedelta(days=1)

    # Overall summary
    all_compounds = [h["sentiment"]["compound"] for h in scored]
    total_pos = sum(1 for h in scored if h["sentiment"]["label"] == "positive")
    total_neg = sum(1 for h in scored if h["sentiment"]["label"] == "negative")
    total_neu = sum(1 for h in scored if h["sentiment"]["label"] == "neutral")

    return {
        "ticker": ticker,
        "name": company_name,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "headlines": scored,
        "daily": daily,
        "summary": {
            "avg_compound": round(sum(all_compounds) / len(all_compounds), 4) if all_compounds else 0,
            "total": len(scored),
            "positive": total_pos,
            "negative": total_neg,
            "neutral": total_neu,
        },
    }
