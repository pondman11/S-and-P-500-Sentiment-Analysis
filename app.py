"""Single-Security Sentiment Analysis Dashboard."""
import datetime as dt

import dash
from dash import dcc, html, Input, Output, State, callback, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

from sentiment import get_sentiment_over_range
from prices import get_prices

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SECURITIES = {
    "AAPL": "Apple Inc.",
}
DEFAULT_RANGE_DAYS = 7

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.DARKLY,
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap",
    ],
    title="Sentiment Analysis",
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
server = app.server

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
CUSTOM_CSS = """
body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    background: #0d1117 !important;
}
.card {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 24px rgba(0,0,0,0.3) !important;
}
.card-header {
    background: transparent !important;
    border-bottom: 1px solid #21262d !important;
    font-weight: 600 !important;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    font-size: 0.75rem;
    color: #8b949e !important;
    padding: 1rem 1.25rem 0.75rem !important;
}
.metric-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 1.25rem;
    text-align: center;
    transition: all 0.2s ease;
}
.metric-card:hover {
    border-color: #58a6ff;
    box-shadow: 0 0 20px rgba(88,166,255,0.1);
}
.metric-value {
    font-size: 2rem;
    font-weight: 700;
    line-height: 1.2;
}
.metric-label {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #8b949e;
    margin-top: 0.25rem;
}
.headline-row {
    padding: 0.6rem 0;
    border-bottom: 1px solid #21262d;
    transition: background 0.15s ease;
}
.headline-row:hover {
    background: rgba(88,166,255,0.04);
}
.headline-row a {
    color: #c9d1d9 !important;
    text-decoration: none !important;
    font-size: 0.875rem;
    line-height: 1.4;
}
.headline-row a:hover {
    color: #58a6ff !important;
}
.score-badge {
    display: inline-block;
    padding: 0.15rem 0.5rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
    font-family: 'SF Mono', 'Fira Code', monospace;
}
.score-pos { background: rgba(63,185,80,0.15); color: #3fb950; }
.score-neg { background: rgba(248,81,73,0.15); color: #f85149; }
.score-neu { background: rgba(139,148,158,0.15); color: #8b949e; }
.btn-primary {
    background: linear-gradient(135deg, #238636 0%, #2ea043 100%) !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    letter-spacing: 0.3px;
    padding: 0.6rem 1.5rem !important;
    transition: all 0.2s ease !important;
}
.btn-primary:hover {
    box-shadow: 0 4px 16px rgba(46,160,67,0.3) !important;
    transform: translateY(-1px);
}
.Select-control, .DateInput_input {
    background: #0d1117 !important;
    border-color: #30363d !important;
    border-radius: 8px !important;
}
h1 { font-weight: 700 !important; letter-spacing: -0.5px; }
"""

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
def _default_dates():
    end = dt.date.today() - dt.timedelta(days=1)
    start = end - dt.timedelta(days=DEFAULT_RANGE_DAYS - 1)
    return start, end

_start, _end = _default_dates()

controls = dbc.Card([
    dbc.CardHeader("Configuration"),
    dbc.CardBody([
        html.Label("Security", className="fw-bold mb-1",
                    style={"fontSize": "0.8rem", "color": "#8b949e"}),
        dcc.Dropdown(
            id="ticker-dropdown",
            options=[{"label": f"{t}  ·  {n}", "value": t} for t, n in SECURITIES.items()],
            value=list(SECURITIES.keys())[0],
            clearable=False,
            className="mb-3",
            style={"backgroundColor": "#0d1117"},
        ),
        html.Label("Date Range", className="fw-bold mb-1",
                    style={"fontSize": "0.8rem", "color": "#8b949e"}),
        dcc.DatePickerRange(
            id="date-range",
            start_date=_start,
            end_date=_end,
            max_date_allowed=dt.date.today(),
            display_format="MMM D, YYYY",
            className="mb-4",
            style={"width": "100%"},
        ),
        dbc.Button("⚡ Analyze", id="btn-analyze", color="primary",
                    className="w-100", n_clicks=0),
    ], style={"padding": "1.25rem"}),
])

app.layout = dbc.Container([
    html.Style(CUSTOM_CSS),

    # Header
    dbc.Row(dbc.Col(html.Div([
        html.Div([
            html.Span("📰", style={"fontSize": "2rem", "marginRight": "0.75rem"}),
            html.Div([
                html.H1("Sentiment Analysis", className="mb-0",
                         style={"fontSize": "1.75rem"}),
                html.P("News sentiment tracking · powered by VADER",
                       style={"color": "#484f58", "fontSize": "0.85rem", "margin": 0}),
            ]),
        ], style={"display": "flex", "alignItems": "center"}),
    ]), width=12), className="my-4"),

    # Controls + metrics + main chart
    dbc.Row([
        dbc.Col(controls, lg=3, md=4),
        dbc.Col([
            # Metric cards row
            html.Div(id="metrics-container"),
            # Main chart
            dcc.Loading(
                id="loading-main", type="dot",
                color="#58a6ff",
                children=html.Div(id="main-chart-container",
                                  style={"minHeight": "400px"}),
            ),
        ], lg=9, md=8),
    ]),

    # Bottom row: sentiment donut + headlines
    dbc.Row([
        dbc.Col(dcc.Loading(html.Div(id="donut-container"), type="dot",
                            color="#58a6ff"), lg=3, md=4),
        dbc.Col(dcc.Loading(html.Div(id="headline-container"), type="dot",
                            color="#58a6ff"), lg=9, md=8),
    ], className="mt-4 mb-5"),

    dcc.Store(id="sentiment-data"),
], fluid=True, style={"maxWidth": "1400px"})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
CHART_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", size=12),
    margin=dict(l=50, r=20, t=40, b=30),
    xaxis=dict(gridcolor="rgba(48,54,61,0.5)", zeroline=False),
    yaxis=dict(gridcolor="rgba(48,54,61,0.5)", zeroline=False),
)


def _metric_card(value, label, color="#c9d1d9"):
    return html.Div([
        html.Div(value, className="metric-value", style={"color": color}),
        html.Div(label, className="metric-label"),
    ], className="metric-card")


def _score_badge(score):
    if score >= 0.05:
        cls = "score-pos"
    elif score <= -0.05:
        cls = "score-neg"
    else:
        cls = "score-neu"
    return html.Span(f"{score:+.3f}", className=f"score-badge {cls}")


# ---------------------------------------------------------------------------
# Main callback
# ---------------------------------------------------------------------------
@callback(
    Output("sentiment-data", "data"),
    Output("metrics-container", "children"),
    Output("main-chart-container", "children"),
    Output("donut-container", "children"),
    Output("headline-container", "children"),
    Input("btn-analyze", "n_clicks"),
    State("ticker-dropdown", "value"),
    State("date-range", "start_date"),
    State("date-range", "end_date"),
    prevent_initial_call=True,
)
def run_analysis(n_clicks, ticker, start_str, end_str):
    start = dt.date.fromisoformat(start_str)
    end = dt.date.fromisoformat(end_str)
    name = SECURITIES.get(ticker, ticker)

    sent = get_sentiment_over_range(ticker, name, start, end)
    prices = get_prices(ticker, start, end)

    if not sent["headlines"] and not prices:
        msg = dbc.Alert("No data found for that range.", color="warning",
                        style={"borderRadius": "8px"})
        return None, "", msg, "", ""

    daily_df = pd.DataFrame(sent["daily"])
    price_df = pd.DataFrame(prices) if prices else pd.DataFrame()
    s = sent["summary"]

    # --- Metrics ---
    avg_color = "#3fb950" if s["avg_compound"] >= 0.05 else "#f85149" if s["avg_compound"] <= -0.05 else "#8b949e"
    price_change = ""
    if not price_df.empty and len(price_df) >= 2:
        pc = ((price_df.iloc[-1]["close"] - price_df.iloc[0]["close"]) / price_df.iloc[0]["close"]) * 100
        pc_color = "#3fb950" if pc >= 0 else "#f85149"
        price_change = _metric_card(f"{pc:+.1f}%", "Price Change", pc_color)

    metrics = dbc.Row([
        dbc.Col(_metric_card(f"{s['avg_compound']:+.3f}", "Avg Sentiment", avg_color), width=3),
        dbc.Col(_metric_card(str(s["total"]), "Headlines"), width=3),
        dbc.Col(_metric_card(
            f"{s['positive']}/{s['negative']}",
            "Positive / Negative",
            "#3fb950" if s["positive"] > s["negative"] else "#f85149",
        ), width=3),
        dbc.Col(price_change if price_change else _metric_card("—", "Price Change"), width=3),
    ], className="mb-3 g-3")

    # --- Main chart ---
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        row_heights=[0.6, 0.4],
        vertical_spacing=0.08,
    )

    # Price
    if not price_df.empty:
        fig.add_trace(go.Scatter(
            x=price_df["date"], y=price_df["close"],
            mode="lines", name="Close",
            line=dict(color="#58a6ff", width=2.5, shape="spline"),
            fill="tozeroy",
            fillcolor="rgba(88,166,255,0.06)",
            hovertemplate="<b>%{x}</b><br>$%{y:.2f}<extra></extra>",
        ), row=1, col=1)

    # Sentiment bars
    daily_with_data = daily_df[daily_df["avg_compound"].notna()]
    if not daily_with_data.empty:
        colors = [
            "rgba(63,185,80,0.8)" if v >= 0 else "rgba(248,81,73,0.8)"
            for v in daily_with_data["avg_compound"]
        ]
        fig.add_trace(go.Bar(
            x=daily_with_data["date"], y=daily_with_data["avg_compound"],
            name="Sentiment", marker_color=colors,
            marker_line_width=0,
            hovertemplate="<b>%{x}</b><br>%{y:+.3f}<extra></extra>",
        ), row=2, col=1)
        fig.add_hline(y=0, line_color="#30363d", line_width=1, row=2, col=1)

    fig.update_layout(
        **CHART_LAYOUT,
        height=480,
        showlegend=False,
        yaxis=dict(title="Price ($)", gridcolor="rgba(48,54,61,0.3)", zeroline=False),
        yaxis2=dict(title="Sentiment", gridcolor="rgba(48,54,61,0.3)", zeroline=False),
        xaxis2=dict(gridcolor="rgba(48,54,61,0.3)"),
    )

    chart_card = dbc.Card([
        dbc.CardHeader(f"{name} ({ticker})  ·  {start.strftime('%b %d')} — {end.strftime('%b %d, %Y')}"),
        dbc.CardBody(dcc.Graph(figure=fig, config={"displayModeBar": False}),
                     style={"padding": "0.5rem"}),
    ])

    # --- Donut ---
    fig_donut = go.Figure(go.Pie(
        labels=["Positive", "Neutral", "Negative"],
        values=[s["positive"], s["neutral"], s["negative"]],
        marker=dict(
            colors=["#3fb950", "#30363d", "#f85149"],
            line=dict(color="#161b22", width=3),
        ),
        hole=0.65,
        textinfo="percent",
        textfont=dict(size=13, family="Inter"),
        hovertemplate="<b>%{label}</b><br>%{value} headlines<br>%{percent}<extra></extra>",
    ))
    fig_donut.update_layout(
        **CHART_LAYOUT,
        height=340,
        showlegend=True,
        legend=dict(
            orientation="h", yanchor="top", y=-0.05,
            xanchor="center", x=0.5,
            font=dict(size=11),
        ),
        annotations=[dict(
            text=f"<b>{s['avg_compound']:+.2f}</b>",
            x=0.5, y=0.5, font_size=24,
            font_color=avg_color,
            showarrow=False,
        )],
    )

    donut_card = dbc.Card([
        dbc.CardHeader("Sentiment Split"),
        dbc.CardBody(dcc.Graph(figure=fig_donut, config={"displayModeBar": False}),
                     style={"padding": "0.5rem"}),
    ])

    # --- Headlines ---
    sorted_hl = sorted(
        sent["headlines"],
        key=lambda h: abs(h["sentiment"]["compound"]),
        reverse=True,
    )[:20]

    hl_items = []
    for h in sorted_hl:
        sc = h["sentiment"]["compound"]
        date_str = h["date"].strftime("%b %d") if h.get("date") else ""
        hl_items.append(html.Div([
            html.Div([
                html.Div([
                    _score_badge(sc),
                    html.Span(f"  {date_str}", style={"color": "#484f58", "fontSize": "0.75rem",
                                                        "marginLeft": "0.5rem"}),
                ], style={"marginBottom": "0.25rem"}),
                html.A(h["title"], href=h["link"], target="_blank"),
                html.Div(h["source"], style={"color": "#484f58", "fontSize": "0.75rem",
                                              "marginTop": "0.15rem"}),
            ]),
        ], className="headline-row"))

    headline_card = dbc.Card([
        dbc.CardHeader("Top Headlines"),
        dbc.CardBody(hl_items if hl_items else [html.P("No headlines found.", className="text-muted")],
                     style={"padding": "0.75rem 1.25rem", "maxHeight": "500px", "overflowY": "auto"}),
    ])

    store = {"ticker": ticker, "name": name, "summary": s, "daily": sent["daily"]}

    return store, metrics, chart_card, donut_card, headline_card


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
