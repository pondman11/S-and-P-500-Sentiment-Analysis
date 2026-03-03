# S&P 500 Sentiment Analysis Dashboard

Real-time sentiment analysis of top-performing S&P 500 stocks using news headlines.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Dash](https://img.shields.io/badge/Dash-2.18-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Features

- **Top Earners**: Automatically identifies the top N (10–50) S&P 500 gainers from the prior business day
- **Sentiment Analysis**: VADER-based NLP on Google News headlines for each company
- **Interactive Bar Chart**: Green (positive) above axis, red (negative) below — click any bar to drill through to actual headlines
- **Scatter Plot**: Price change vs. sentiment correlation with bubble sizing
- **Sector Breakdown**: Aggregated sentiment by GICS sector
- **Pie Chart**: Overall positive/negative/neutral distribution
- **Dark Theme**: GitHub-inspired dark UI

## Tech Stack

| Component | Library |
|-----------|---------|
| Dashboard | Plotly Dash + Bootstrap |
| Finance Data | yfinance |
| News | Google News RSS (feedparser) |
| Sentiment | VADER (vaderSentiment) |
| Deployment | Gunicorn |

## Quick Start

```bash
# Clone
git clone https://github.com/pondman11/sp500-sentiment-analysis.git
cd sp500-sentiment-analysis

# Install
pip install -r requirements.txt

# Run
python app.py
```

Open http://localhost:8050

## Deployment

Ready for Render, Railway, or Heroku:

```bash
# Procfile included
gunicorn app:server --bind 0.0.0.0:8050 --workers 2 --timeout 120
```

### Render (recommended)
1. Connect your GitHub repo
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `gunicorn app:server --bind 0.0.0.0:$PORT --workers 2 --timeout 120`

## How It Works

1. Fetches S&P 500 constituents from Wikipedia
2. Downloads price data via yfinance to find top gainers
3. Scrapes Google News RSS for headlines per company
4. Runs VADER sentiment scoring on each headline
5. Aggregates and visualizes with Plotly

## License

MIT
