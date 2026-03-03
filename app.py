"""S&P 500 Sentiment Analysis Dashboard."""
import datetime as dt
import json

import dash
from dash import dcc, html, Input, Output, State, callback, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd

from sp500 import get_top_earners
from sentiment import get_sentiment_for_company

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    title="S&P 500 Sentiment Analysis",
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
server = app.server  # For gunicorn

# ── Layout ──────────────────────────────────────────────────────────────────

app.layout = dbc.Container([
    dbc.Row(dbc.Col(html.H1("S&P 500 Sentiment Analysis ⚡",
                             className="text-center my-4"))),

    # Controls
    dbc.Row([
        dbc.Col([
            dbc.Label("Reference Date"),
            dcc.DatePickerSingle(
                id="date-picker",
                date=dt.date.today(),
                max_date_allowed=dt.date.today(),
                display_format="YYYY-MM-DD",
                className="mb-2",
            ),
        ], md=3),
        dbc.Col([
            dbc.Label(id="slider-label", children="Top 10 Earners"),
            dcc.Slider(
                id="n-slider", min=10, max=50, step=5, value=10,
                marks={i: str(i) for i in range(10, 55, 10)},
            ),
        ], md=5),
        dbc.Col([
            dbc.Button("Analyze", id="analyze-btn", color="primary",
                       size="lg", className="mt-4 w-100"),
        ], md=2),
        dbc.Col([
            dbc.Spinner(html.Div(id="status-text", className="mt-4"),
                        color="primary", size="sm"),
        ], md=2),
    ], className="mb-4 align-items-end"),

    # Main bar chart
    dbc.Row(dbc.Col(dcc.Graph(id="sentiment-bar", config={"displayModeBar": True}))),

    # Secondary row: pie chart + heatmap
    dbc.Row([
        dbc.Col(dcc.Graph(id="sentiment-pie"), md=4),
        dbc.Col(dcc.Graph(id="sentiment-heatmap"), md=8),
    ], className="mt-3"),

    # Drill-through modal
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(id="modal-title")),
        dbc.ModalBody(id="modal-body"),
        dbc.ModalFooter(dbc.Button("Close", id="modal-close", className="ms-auto")),
    ], id="headline-modal", size="lg", scrollable=True),

    # Hidden store for full sentiment data
    dcc.Store(id="sentiment-store"),
], fluid=True)


# ── Callbacks ───────────────────────────────────────────────────────────────

@callback(Output("slider-label", "children"), Input("n-slider", "value"))
def update_label(n):
    return f"Top {n} Earners"


@callback(
    Output("sentiment-store", "data"),
    Output("status-text", "children"),
    Input("analyze-btn", "n_clicks"),
    State("date-picker", "date"),
    State("n-slider", "value"),
    prevent_initial_call=True,
)
def run_analysis(n_clicks, date_str, n):
    ref = dt.date.fromisoformat(date_str) if date_str else dt.date.today()
    try:
        earners = get_top_earners(n=n, ref_date=ref)
    except Exception as e:
        return no_update, f"❌ Error fetching earners: {e}"

    results = []
    for _, row in earners.iterrows():
        data = get_sentiment_for_company(row["ticker"], row["name"])
        data["sector"] = row["sector"]
        data["close"] = row["close"]
        data["change_pct"] = row["change_pct"]
        results.append(data)

    return json.loads(json.dumps(results, default=str)), f"✅ {len(results)} companies analyzed"


@callback(
    Output("sentiment-bar", "figure"),
    Output("sentiment-pie", "figure"),
    Output("sentiment-heatmap", "figure"),
    Input("sentiment-store", "data"),
)
def update_charts(data):
    if not data:
        empty = go.Figure()
        empty.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)")
        return empty, empty, empty

    df = pd.DataFrame(data)
    tickers = df["ticker"].tolist()
    names = df["name"].tolist()
    labels = [f"{t}<br>{n[:20]}" for t, n in zip(tickers, names)]

    # ── Bar chart: positive (green) + negative (red, shown below axis) ──
    bar_fig = go.Figure()
    bar_fig.add_trace(go.Bar(
        x=labels, y=df["positive_count"],
        name="Positive", marker_color="#00c853",
        customdata=df["ticker"],
        hovertemplate="%{x}<br>Positive: %{y}<extra></extra>",
    ))
    bar_fig.add_trace(go.Bar(
        x=labels, y=-df["negative_count"],
        name="Negative", marker_color="#ff1744",
        customdata=df["ticker"],
        hovertemplate="%{x}<br>Negative: %{customdata}<extra></extra>",
    ))
    bar_fig.update_layout(
        barmode="overlay",
        title="Sentiment Counts by Company (click bars to drill through)",
        xaxis_title="Company", yaxis_title="Headline Count",
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=1.12),
        height=500,
    )

    # ── Pie chart: overall sentiment split ──
    total_pos = int(df["positive_count"].sum())
    total_neg = int(df["negative_count"].sum())
    total_neu = int(df["neutral_count"].sum())
    pie_fig = go.Figure(go.Pie(
        labels=["Positive", "Negative", "Neutral"],
        values=[total_pos, total_neg, total_neu],
        marker_colors=["#00c853", "#ff1744", "#ffd600"],
        hole=0.4,
    ))
    pie_fig.update_layout(
        title="Overall Sentiment Split",
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
        height=400,
    )

    # ── Heatmap: companies × sentiment ──
    heat_fig = go.Figure(go.Heatmap(
        z=[df["positive_count"], df["neutral_count"], df["negative_count"]],
        x=tickers,
        y=["Positive", "Neutral", "Negative"],
        colorscale=[[0, "#1a1a2e"], [0.5, "#ffd600"], [1, "#00c853"]],
        hovertemplate="Company: %{x}<br>%{y}: %{z}<extra></extra>",
    ))
    heat_fig.update_layout(
        title="Sentiment Heatmap",
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=300,
    )

    return bar_fig, pie_fig, heat_fig


@callback(
    Output("headline-modal", "is_open"),
    Output("modal-title", "children"),
    Output("modal-body", "children"),
    Input("sentiment-bar", "clickData"),
    Input("modal-close", "n_clicks"),
    State("sentiment-store", "data"),
    State("headline-modal", "is_open"),
    prevent_initial_call=True,
)
def toggle_modal(click_data, close_clicks, data, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update, no_update, no_update

    trigger = ctx.triggered[0]["prop_id"]
    if "modal-close" in trigger:
        return False, "", ""

    if not click_data or not data:
        return no_update, no_update, no_update

    point = click_data["points"][0]
    curve = point.get("curveNumber", 0)
    idx = point.get("pointIndex", 0)

    if idx >= len(data):
        return no_update, no_update, no_update

    company = data[idx]
    sentiment_type = "positive" if curve == 0 else "negative"
    headlines = company.get(f"{sentiment_type}_headlines", [])
    color = "#00c853" if sentiment_type == "positive" else "#ff1744"

    title = f"{company['name']} ({company['ticker']}) — {sentiment_type.title()} Headlines"

    if not headlines:
        body = html.P("No headlines found.", className="text-muted")
    else:
        rows = []
        for h in headlines[:15]:
            rows.append(html.Tr([
                html.Td(html.A(h["title"], href=h["link"], target="_blank",
                               style={"color": color})),
                html.Td(h.get("source", ""), style={"whiteSpace": "nowrap"}),
                html.Td(f"{h['compound']:+.3f}", style={"fontFamily": "monospace"}),
            ]))
        body = dbc.Table([
            html.Thead(html.Tr([html.Th("Headline"), html.Th("Source"), html.Th("Score")])),
            html.Tbody(rows),
        ], bordered=True, dark=True, hover=True, size="sm")

    return True, title, body


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
