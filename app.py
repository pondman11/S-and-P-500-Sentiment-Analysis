"""Single-Security Sentiment Analysis Dashboard."""
import datetime as dt
import json

import dash
from dash import dcc, html, Input, Output, State, callback, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

from sentiment import get_sentiment_over_range
from prices import get_prices

# ---------------------------------------------------------------------------
# Config — expand this list as you add more securities
# ---------------------------------------------------------------------------
SECURITIES = {
    "AAPL": "Apple Inc.",
}

DEFAULT_RANGE_DAYS = 7

# ---------------------------------------------------------------------------
# App init
# ---------------------------------------------------------------------------
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    title="Sentiment Analysis",
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
server = app.server  # for gunicorn


def _default_dates():
    end = dt.date.today() - dt.timedelta(days=1)
    start = end - dt.timedelta(days=DEFAULT_RANGE_DAYS - 1)
    return start, end


_start, _end = _default_dates()

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
controls = dbc.Card([
    dbc.CardHeader("Controls"),
    dbc.CardBody([
        html.Label("Security", className="fw-bold mb-1"),
        dcc.Dropdown(
            id="ticker-dropdown",
            options=[{"label": f"{t} — {n}", "value": t} for t, n in SECURITIES.items()],
            value=list(SECURITIES.keys())[0],
            clearable=False,
            className="mb-3",
        ),
        html.Label("Date Range", className="fw-bold mb-1"),
        dcc.DatePickerRange(
            id="date-range",
            start_date=_start,
            end_date=_end,
            max_date_allowed=dt.date.today(),
            display_format="YYYY-MM-DD",
            className="mb-3",
            style={"width": "100%"},
        ),
        dbc.Button("Analyze", id="btn-analyze", color="primary",
                    className="w-100 mt-2", n_clicks=0),
    ]),
])

app.layout = dbc.Container([
    dbc.Row(dbc.Col(html.Div([
        html.H1("📰 Sentiment Analysis", className="mb-0"),
        html.P("Single-security news sentiment over time (VADER)",
               className="text-muted"),
    ]), width=12), className="my-3"),

    dbc.Row([
        dbc.Col(controls, md=3),
        dbc.Col([
            dcc.Loading(id="loading-main", type="circle",
                        children=html.Div(id="main-chart-container")),
        ], md=9),
    ]),

    dbc.Row([
        dbc.Col(dcc.Loading(html.Div(id="pie-container")), md=4),
        dbc.Col(dcc.Loading(html.Div(id="headline-table-container")), md=8),
    ], className="mt-3 mb-5"),

    dcc.Store(id="sentiment-data"),

    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(id="modal-title")),
        dbc.ModalBody(id="modal-body"),
        dbc.ModalFooter(
            dbc.Button("Close", id="modal-close", className="ms-auto", n_clicks=0)
        ),
    ], id="modal", size="lg", is_open=False, scrollable=True),
], fluid=True)

# ---------------------------------------------------------------------------
# Main analysis callback
# ---------------------------------------------------------------------------

@callback(
    Output("sentiment-data", "data"),
    Output("main-chart-container", "children"),
    Output("pie-container", "children"),
    Output("headline-table-container", "children"),
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

    # Fetch sentiment + prices
    sent = get_sentiment_over_range(ticker, name, start, end)
    prices = get_prices(ticker, start, end)

    if not sent["headlines"] and not prices:
        msg = dbc.Alert("No data found for that range.", color="warning")
        return None, msg, "", ""

    # --- Combined chart: price + sentiment over time ---
    daily_df = pd.DataFrame(sent["daily"])
    price_df = pd.DataFrame(prices) if prices else pd.DataFrame()

    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True,
        row_heights=[0.5, 0.25, 0.25],
        vertical_spacing=0.06,
        subplot_titles=[
            f"{name} ({ticker}) — Close Price",
            "Daily Sentiment (Avg Compound)",
            "Headline Volume by Sentiment",
        ],
    )

    # Price line
    if not price_df.empty:
        fig.add_trace(go.Scatter(
            x=price_df["date"], y=price_df["close"],
            mode="lines+markers", name="Close",
            line=dict(color="#58a6ff", width=2),
            hovertemplate="%{x}<br>$%{y:.2f}<extra></extra>",
        ), row=1, col=1)

    # Sentiment line
    daily_with_data = daily_df[daily_df["avg_compound"].notna()]
    if not daily_with_data.empty:
        colors = ["#3fb950" if v >= 0 else "#f85149" for v in daily_with_data["avg_compound"]]
        fig.add_trace(go.Bar(
            x=daily_with_data["date"], y=daily_with_data["avg_compound"],
            name="Avg Sentiment", marker_color=colors,
            hovertemplate="%{x}<br>Score: %{y:.3f}<extra></extra>",
        ), row=2, col=1)
        fig.add_hline(y=0, line_color="#8b949e", line_width=1, row=2, col=1)

    # Stacked bar: headline counts
    if not daily_df.empty:
        fig.add_trace(go.Bar(
            x=daily_df["date"], y=daily_df["positive"],
            name="Positive", marker_color="#3fb950",
        ), row=3, col=1)
        fig.add_trace(go.Bar(
            x=daily_df["date"], y=daily_df["neutral"],
            name="Neutral", marker_color="#8b949e",
        ), row=3, col=1)
        fig.add_trace(go.Bar(
            x=daily_df["date"], y=daily_df["negative"],
            name="Negative", marker_color="#f85149",
        ), row=3, col=1)

    fig.update_layout(
        barmode="stack",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=750,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=80),
    )

    # --- Pie chart ---
    s = sent["summary"]
    fig_pie = go.Figure(go.Pie(
        labels=["Positive", "Negative", "Neutral"],
        values=[s["positive"], s["negative"], s["neutral"]],
        marker_colors=["#3fb950", "#f85149", "#8b949e"],
        hole=0.4,
    ))
    fig_pie.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        title=f"Overall: {s['total']} headlines | Avg: {s['avg_compound']:+.3f}",
        height=400,
    )

    # --- Top headlines table ---
    sorted_hl = sorted(
        sent["headlines"],
        key=lambda h: abs(h["sentiment"]["compound"]),
        reverse=True,
    )[:25]

    table_rows = []
    for h in sorted_hl:
        sc = h["sentiment"]["compound"]
        color = "#3fb950" if sc >= 0.05 else "#f85149" if sc <= -0.05 else "#8b949e"
        table_rows.append(html.Tr([
            html.Td(h.get("date", "").isoformat() if h.get("date") else "—",
                     style={"whiteSpace": "nowrap"}),
            html.Td(html.A(h["title"], href=h["link"], target="_blank",
                           style={"color": "#c9d1d9"})),
            html.Td(h["source"], className="text-muted"),
            html.Td(f"{sc:+.3f}", style={"color": color, "fontWeight": "bold"}),
        ]))

    headline_table = dbc.Table(
        [html.Thead(html.Tr([
            html.Th("Date"), html.Th("Headline"), html.Th("Source"), html.Th("Score"),
        ]))] + [html.Tbody(table_rows)],
        bordered=True, dark=True, hover=True, responsive=True, striped=True,
        size="sm",
    )

    # Serialize for store
    store = {
        "ticker": ticker,
        "name": name,
        "summary": s,
        "daily": sent["daily"],
        "headline_count": len(sent["headlines"]),
    }

    return (
        store,
        dcc.Graph(figure=fig),
        dcc.Graph(figure=fig_pie),
        html.Div([
            html.H5("Top Headlines by Sentiment Strength", className="mb-2"),
            headline_table,
        ]),
    )


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
