"""S&P 500 Sentiment Analysis Dashboard."""
import datetime as dt
import json

import dash
from dash import dcc, html, Input, Output, State, callback, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from sp500 import get_top_earners, get_default_date, preload_prices
from sentiment import get_batch_sentiment

# ---------------------------------------------------------------------------
# App init
# ---------------------------------------------------------------------------
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    title="S&P 500 Sentiment Analysis",
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
server = app.server  # for gunicorn

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
controls = dbc.Card([
    dbc.CardHeader("Controls"),
    dbc.CardBody([
        html.Label("Reference Date", className="fw-bold mb-1"),
        dcc.DatePickerSingle(
            id="date-picker",
            date=get_default_date(),
            max_date_allowed=dt.date.today(),
            display_format="YYYY-MM-DD",
            className="mb-3",
            style={"width": "100%"},
        ),
        html.Label("Number of Companies", className="fw-bold mb-1"),
        dcc.Slider(
            id="n-companies",
            min=10, max=50, step=5, value=10,
            marks={i: str(i) for i in range(10, 55, 5)},
            className="mb-3",
        ),
        dbc.Button("Analyze", id="btn-analyze", color="primary",
                    className="w-100 mt-2", n_clicks=0),
    ]),
])

app.layout = dbc.Container([
    # Header
    dbc.Row(dbc.Col(html.Div([
        html.H1("S&P 500 Sentiment Analysis", className="mb-0"),
        html.P("Top earners sentiment from news headlines (VADER)",
               className="text-muted"),
    ]), width=12), className="my-3"),

    # Controls + main chart
    dbc.Row([
        dbc.Col(controls, md=3),
        dbc.Col([
            dcc.Loading(
                id="loading-main",
                type="circle",
                children=html.Div(id="main-chart-container"),
            ),
        ], md=9),
    ]),

    # Secondary charts row
    dbc.Row([
        dbc.Col(dcc.Loading(html.Div(id="pie-container")), md=4),
        dbc.Col(dcc.Loading(html.Div(id="scatter-container")), md=8),
    ], className="mt-3"),

    # Sector heatmap
    dbc.Row([
        dbc.Col(dcc.Loading(html.Div(id="heatmap-container")), md=12),
    ], className="mt-3 mb-5"),

    # Hidden store for full data
    dcc.Store(id="sentiment-data"),

    # Drill-through modal
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(id="modal-title")),
        dbc.ModalBody(id="modal-body"),
        dbc.ModalFooter(
            dbc.Button("Close", id="modal-close", className="ms-auto", n_clicks=0)
        ),
    ], id="modal", size="lg", is_open=False, scrollable=True),
], fluid=True)

# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

@callback(
    Output("sentiment-data", "data"),
    Output("main-chart-container", "children"),
    Output("pie-container", "children"),
    Output("scatter-container", "children"),
    Output("heatmap-container", "children"),
    Input("btn-analyze", "n_clicks"),
    State("date-picker", "date"),
    State("n-companies", "value"),
    prevent_initial_call=True,
)
def run_analysis(n_clicks, date_str, n_companies):
    ref_date = dt.date.fromisoformat(date_str)
    earners = get_top_earners(n=n_companies, ref_date=ref_date)

    if earners.empty:
        msg = html.Div(
            dbc.Alert("No data found for that date. Markets may have been closed.",
                      color="warning"),
        )
        return None, msg, "", "", ""

    companies = earners.to_dict("records")
    results = get_batch_sentiment(companies)

    # Store serializable data
    store_data = []
    for r in results:
        store_data.append({
            "ticker": r["ticker"],
            "name": r["name"],
            "sector": r["sector"],
            "close": r["close"],
            "change_pct": r["change_pct"],
            "positive_count": r["positive_count"],
            "negative_count": r["negative_count"],
            "neutral_count": r["neutral_count"],
            "avg_compound": r["avg_compound"],
            "total_headlines": r["total_headlines"],
            "headlines": r["headlines"],
        })

    df = pd.DataFrame(store_data)

    # --- Main bar chart: positive (green) above axis, negative (red) below ---
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=df["ticker"],
        y=df["positive_count"],
        name="Positive",
        marker_color="#3fb950",
        customdata=df["ticker"],
        hovertemplate="<b>%{x}</b><br>Positive: %{y}<extra></extra>",
    ))
    fig_bar.add_trace(go.Bar(
        x=df["ticker"],
        y=[-v for v in df["negative_count"]],
        name="Negative",
        marker_color="#f85149",
        customdata=df["ticker"],
        hovertemplate="<b>%{x}</b><br>Negative: %{customdata}<extra></extra>",
    ))
    fig_bar.update_layout(
        barmode="overlay",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        title=f"Sentiment: Top {n_companies} S&P 500 Earners ({ref_date})",
        xaxis_title="Company",
        yaxis_title="Headline Count",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        height=500,
    )
    fig_bar.add_hline(y=0, line_color="#8b949e", line_width=1)

    # --- Pie chart: aggregate sentiment split ---
    total_pos = int(df["positive_count"].sum())
    total_neg = int(df["negative_count"].sum())
    total_neu = int(df["neutral_count"].sum())
    fig_pie = go.Figure(go.Pie(
        labels=["Positive", "Negative", "Neutral"],
        values=[total_pos, total_neg, total_neu],
        marker_colors=["#3fb950", "#f85149", "#8b949e"],
        hole=0.4,
    ))
    fig_pie.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        title="Overall Sentiment Split",
        height=400,
    )

    # --- Scatter: sentiment vs price change ---
    fig_scatter = go.Figure(go.Scatter(
        x=df["change_pct"],
        y=df["avg_compound"],
        mode="markers+text",
        text=df["ticker"],
        textposition="top center",
        marker=dict(
            size=df["total_headlines"].clip(lower=5) * 2,
            color=df["avg_compound"],
            colorscale=[[0, "#f85149"], [0.5, "#8b949e"], [1, "#3fb950"]],
            showscale=True,
            colorbar=dict(title="Sentiment"),
        ),
        hovertemplate="<b>%{text}</b><br>Price Δ: %{x:.2f}%<br>Sentiment: %{y:.3f}<extra></extra>",
    ))
    fig_scatter.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        title="Price Change vs News Sentiment",
        xaxis_title="Price Change (%)",
        yaxis_title="Avg Compound Score",
        height=400,
    )

    # --- Heatmap: sector aggregation ---
    sector_df = df.groupby("sector").agg(
        avg_sentiment=("avg_compound", "mean"),
        total_positive=("positive_count", "sum"),
        total_negative=("negative_count", "sum"),
        companies=("ticker", "count"),
    ).reset_index()

    fig_heatmap = go.Figure(go.Bar(
        x=sector_df["sector"],
        y=sector_df["avg_sentiment"],
        marker_color=[
            "#3fb950" if v >= 0 else "#f85149"
            for v in sector_df["avg_sentiment"]
        ],
        hovertemplate="<b>%{x}</b><br>Avg Sentiment: %{y:.3f}<extra></extra>",
    ))
    fig_heatmap.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        title="Average Sentiment by Sector",
        xaxis_title="Sector",
        yaxis_title="Avg Compound Score",
        height=350,
    )

    return (
        store_data,
        dcc.Graph(id="main-bar", figure=fig_bar),
        dcc.Graph(figure=fig_pie),
        dcc.Graph(figure=fig_scatter),
        dcc.Graph(figure=fig_heatmap),
    )


@callback(
    Output("modal", "is_open"),
    Output("modal-title", "children"),
    Output("modal-body", "children"),
    Input("main-bar", "clickData"),
    Input("modal-close", "n_clicks"),
    State("sentiment-data", "data"),
    State("modal", "is_open"),
    prevent_initial_call=True,
)
def handle_bar_click(click_data, close_clicks, data, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update, no_update, no_update

    trigger = ctx.triggered[0]["prop_id"]

    if "modal-close" in trigger:
        return False, no_update, no_update

    if click_data is None or data is None:
        return no_update, no_update, no_update

    point = click_data["points"][0]
    ticker = point["x"]
    curve = point["curveNumber"]  # 0 = positive, 1 = negative

    # Find company data
    company = None
    for d in data:
        if d["ticker"] == ticker:
            company = d
            break
    if company is None:
        return no_update, no_update, no_update

    sentiment_type = "positive" if curve == 0 else "negative"
    headlines = [
        h for h in company["headlines"]
        if h["sentiment"]["label"] == sentiment_type
    ]
    headlines.sort(key=lambda h: abs(h["sentiment"]["compound"]), reverse=True)

    title = f"{company['name']} ({ticker}) — {sentiment_type.title()} Headlines"

    body_items = []
    for h in headlines[:20]:
        score = h["sentiment"]["compound"]
        css_class = f"headline-{sentiment_type}"
        body_items.append(html.Div([
            html.Div([
                html.A(h["title"], href=h["link"], target="_blank",
                       className="fw-bold"),
                html.Span(f"  ({score:+.3f})", className="text-muted ms-2"),
            ]),
            html.Small(f"{h['source']} • {h['published']}",
                       className="text-muted"),
        ], className=css_class + " mb-2 py-1"))

    if not body_items:
        body_items = [html.P(f"No {sentiment_type} headlines found.", className="text-muted")]

    return True, title, html.Div(body_items)


# ---------------------------------------------------------------------------
# Preload price cache on startup
# ---------------------------------------------------------------------------
print("Preloading S&P 500 price data...")
preload_prices()
print("Price data cached.")

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
