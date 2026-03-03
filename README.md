# S&P 500 Sentiment Analysis Dashboard

Real-time sentiment analysis of the top-performing S&P 500 stocks using news headlines.

![Python](https://img.shields.io/badge/python-3.12-blue)
![Dash](https://img.shields.io/badge/dash-2.18-green)
![License](https://img.shields.io/badge/license-MIT-yellow)

## Features

- **Top Earners**: Automatically identifies the top N gainers from the S&P 500 for any given business day via Yahoo Finance
- **Sentiment Analysis**: Scores Google News headlines using VADER sentiment analysis
- **Interactive Bar Chart**: Green (positive) above axis, red (negative) below — click to drill through to actual headlines
- **Sentiment Heatmap**: Visual overview of positive/neutral/negative distribution across companies
- **Donut Chart**: Aggregate sentiment breakdown
- **Configurable**: Date picker + slider to select 10–50 companies
- **Deployment-ready**: Includes Dockerfile, Procfile, and Render config

## Quick Start

```bash
pip install -r requirements.txt
python app.py
```

Open http://localhost:8050

## Deploy

### Render
Connect the repo and it auto-detects `render.yaml`.

### Docker
```bash
docker build -t sp500-sentiment .
docker run -p 8050:8050 sp500-sentiment
```

### Railway / Heroku
Uses `Procfile` + `runtime.txt` automatically.

## Architecture

| Module | Purpose |
|--------|---------|
| `sp500.py` | S&P 500 constituents + top earners via yfinance |
| `sentiment.py` | Google News RSS headlines + VADER sentiment scoring |
| `app.py` | Plotly Dash dashboard with drill-through modals |

## Tech Stack

- **Dash + Plotly** — Interactive visualizations
- **yfinance** — Market data
- **VADER** — Rule-based sentiment analysis (fast, no API key)
- **feedparser** — Google News RSS parsing
- **dash-bootstrap-components** — Dark theme UI

## License

MIT
