# Sentiment Analysis Dashboard

Single-security news sentiment analysis over a configurable date range.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Dash](https://img.shields.io/badge/Dash-2.18-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Features

- **Date-range sentiment**: Analyze news sentiment for a single security over any date range (default: 1 week)
- **Price overlay**: Daily close price alongside sentiment scores
- **Headline volume**: Stacked bar chart showing positive/negative/neutral headline counts per day
- **Top headlines table**: Ranked by sentiment strength with links to source articles
- **Pie chart**: Overall sentiment distribution
- **Dark theme**: GitHub-inspired dark UI

Currently configured for **AAPL** — expand the `SECURITIES` dict in `app.py` to add more tickers.

## Tech Stack

| Component | Library |
|-----------|---------|
| Dashboard | Plotly Dash + Bootstrap |
| Price Data | yfinance |
| News | Google News RSS (feedparser) |
| Sentiment | VADER (vaderSentiment) |
| Deployment | Gunicorn |

## Quick Start

```bash
pip install -r requirements.txt
python app.py
```

Open http://localhost:8050

## Deployment

```bash
gunicorn app:server --bind 0.0.0.0:8050 --workers 2 --timeout 120
```

## How It Works

1. Fetches Google News RSS headlines for the selected ticker within the date range
2. Runs VADER sentiment scoring on each headline
3. Aggregates daily and overlays with price data from yfinance
4. Visualizes trends with Plotly

## License

MIT
