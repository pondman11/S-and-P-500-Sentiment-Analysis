"""Sentiment analysis via news headlines using VADER + Google News RSS."""
import re
import feedparser
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from cachetools import TTLCache

_analyzer = SentimentIntensityAnalyzer()
_headline_cache = TTLCache(maxsize=256, ttl=1800)  # 30 min


def fetch_headlines(ticker: str, company_name: str, max_results: int = 30) -> list[dict]:
    """
    Fetch recent news headlines for a company from Google News RSS.
    Returns list of dicts: {title, link, source, published}
    """
    cache_key = f"{ticker}:{company_name}"
    if cache_key in _headline_cache:
        return _headline_cache[cache_key]

    query = quote(f"{company_name} stock {ticker}")
    url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"

    try:
        feed = feedparser.parse(url)
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

        headlines.append({
            "title": title,
            "link": entry.get("link", ""),
            "source": source,
            "published": entry.get("published", ""),
        })

    _headline_cache[cache_key] = headlines
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


def get_company_sentiment(ticker: str, company_name: str) -> dict:
    """
    Fetch headlines and run sentiment analysis for a single company.
    Returns: {
        ticker, name, headlines: [{title, link, source, published, sentiment}],
        positive_count, negative_count, neutral_count, avg_compound
    }
    """
    headlines = fetch_headlines(ticker, company_name)
    analyzed = []
    pos = neg = neu = 0
    compounds = []

    for h in headlines:
        sent = analyze_sentiment(h["title"])
        analyzed.append({**h, "sentiment": sent})
        compounds.append(sent["compound"])
        if sent["label"] == "positive":
            pos += 1
        elif sent["label"] == "negative":
            neg += 1
        else:
            neu += 1

    avg = sum(compounds) / len(compounds) if compounds else 0.0

    return {
        "ticker": ticker,
        "name": company_name,
        "headlines": analyzed,
        "positive_count": pos,
        "negative_count": neg,
        "neutral_count": neu,
        "avg_compound": round(avg, 4),
        "total_headlines": len(analyzed),
    }


def get_batch_sentiment(companies: list[dict]) -> list[dict]:
    """
    Run sentiment analysis for a batch of companies.
    Input: list of dicts with 'ticker' and 'name' keys.
    """
    results = []
    for co in companies:
        result = get_company_sentiment(co["ticker"], co["name"])
        result["sector"] = co.get("sector", "")
        result["change_pct"] = co.get("change_pct", 0)
        result["close"] = co.get("close", 0)
        results.append(result)
    return results
