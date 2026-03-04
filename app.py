"""Single-Security Sentiment Analysis Dashboard."""
import datetime as dt

import dash
from dash import dcc, html, Input, Output, State, callback, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd

from sentiment import get_sentiment_over_range

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SECURITIES = {
    "AAPL": "Apple Inc.", "ABBV": "AbbVie Inc.", "ABT": "Abbott Laboratories",
    "ACN": "Accenture plc", "ADBE": "Adobe Inc.", "ADI": "Analog Devices",
    "ADP": "Automatic Data Processing", "ADSK": "Autodesk Inc.", "AEP": "American Electric Power",
    "AFL": "Aflac Inc.", "AIG": "American Intl Group", "AMAT": "Applied Materials",
    "AMD": "Advanced Micro Devices", "AMGN": "Amgen Inc.", "AMZN": "Amazon.com Inc.",
    "ANET": "Arista Networks", "APD": "Air Products & Chemicals", "APH": "Amphenol Corp.",
    "AVGO": "Broadcom Inc.", "AXP": "American Express", "BA": "Boeing Co.",
    "BAC": "Bank of America", "BDX": "Becton Dickinson", "BIIB": "Biogen Inc.",
    "BK": "Bank of New York Mellon", "BKNG": "Booking Holdings", "BLK": "BlackRock Inc.",
    "BMY": "Bristol-Myers Squibb", "BSX": "Boston Scientific", "C": "Citigroup Inc.",
    "CAT": "Caterpillar Inc.", "CB": "Chubb Ltd.", "CCI": "Crown Castle Intl",
    "CDNS": "Cadence Design Systems", "CEG": "Constellation Energy", "CHTR": "Charter Communications",
    "CI": "Cigna Group", "CL": "Colgate-Palmolive", "CMCSA": "Comcast Corp.",
    "CME": "CME Group", "COF": "Capital One Financial", "COP": "ConocoPhillips",
    "COST": "Costco Wholesale", "CRM": "Salesforce Inc.", "CRWD": "CrowdStrike Holdings",
    "CSCO": "Cisco Systems", "CTAS": "Cintas Corp.", "CVS": "CVS Health",
    "CVX": "Chevron Corp.", "D": "Dominion Energy", "DASH": "DoorDash Inc.",
    "DE": "Deere & Co.", "DHR": "Danaher Corp.", "DIS": "Walt Disney Co.",
    "DOW": "Dow Inc.", "DUK": "Duke Energy", "ECL": "Ecolab Inc.",
    "EL": "Estée Lauder", "EMR": "Emerson Electric", "ENPH": "Enphase Energy",
    "EOG": "EOG Resources", "EQT": "EQT Corp.", "ETN": "Eaton Corp.",
    "EW": "Edwards Lifesciences", "EXC": "Exelon Corp.", "F": "Ford Motor Co.",
    "FANG": "Diamondback Energy", "FDX": "FedEx Corp.", "FI": "Fiserv Inc.",
    "FTNT": "Fortinet Inc.", "GD": "General Dynamics", "GE": "GE Aerospace",
    "GILD": "Gilead Sciences", "GM": "General Motors", "GOOG": "Alphabet (C)",
    "GOOGL": "Alphabet Inc.", "GS": "Goldman Sachs", "HD": "Home Depot",
    "HON": "Honeywell Intl", "IBM": "IBM Corp.", "ICE": "Intercontinental Exchange",
    "INTC": "Intel Corp.", "INTU": "Intuit Inc.", "ISRG": "Intuitive Surgical",
    "ITW": "Illinois Tool Works", "JNJ": "Johnson & Johnson", "JPM": "JPMorgan Chase",
    "KHC": "Kraft Heinz", "KLAC": "KLA Corp.", "KO": "Coca-Cola Co.",
    "LEN": "Lennar Corp.", "LHX": "L3Harris Technologies", "LIN": "Linde plc",
    "LLY": "Eli Lilly & Co.", "LMT": "Lockheed Martin", "LOW": "Lowe's Cos.",
    "LRCX": "Lam Research", "LULU": "Lululemon Athletica", "MA": "Mastercard Inc.",
    "MAR": "Marriott Intl", "MCD": "McDonald's Corp.", "MCHP": "Microchip Technology",
    "MCO": "Moody's Corp.", "MDLZ": "Mondelēz Intl", "MDT": "Medtronic plc",
    "MET": "MetLife Inc.", "META": "Meta Platforms", "MMM": "3M Co.",
    "MO": "Altria Group", "MPC": "Marathon Petroleum", "MRK": "Merck & Co.",
    "MRVL": "Marvell Technology", "MS": "Morgan Stanley", "MSCI": "MSCI Inc.",
    "MSFT": "Microsoft Corp.", "MU": "Micron Technology", "NEE": "NextEra Energy",
    "NFLX": "Netflix Inc.", "NKE": "Nike Inc.", "NOC": "Northrop Grumman",
    "NOW": "ServiceNow Inc.", "NSC": "Norfolk Southern", "NVDA": "NVIDIA Corp.",
    "ORCL": "Oracle Corp.", "OXY": "Occidental Petroleum", "PANW": "Palo Alto Networks",
    "PEP": "PepsiCo Inc.", "PFE": "Pfizer Inc.", "PG": "Procter & Gamble",
    "PGR": "Progressive Corp.", "PLTR": "Palantir Technologies", "PM": "Philip Morris Intl",
    "PNC": "PNC Financial", "PSA": "Public Storage", "PSX": "Phillips 66",
    "PYPL": "PayPal Holdings", "QCOM": "Qualcomm Inc.", "REGN": "Regeneron Pharmaceuticals",
    "ROP": "Roper Technologies", "ROST": "Ross Stores", "RTX": "RTX Corp.",
    "SBUX": "Starbucks Corp.", "SCHW": "Charles Schwab", "SHW": "Sherwin-Williams",
    "SLB": "Schlumberger Ltd.", "SMCI": "Super Micro Computer", "SNPS": "Synopsys Inc.",
    "SO": "Southern Co.", "SPG": "Simon Property Group", "SPGI": "S&P Global",
    "SPY": "S&P 500 ETF", "QQQ": "Nasdaq-100 ETF", "DIA": "Dow Jones ETF",
    "IWM": "Russell 2000 ETF", "SYK": "Stryker Corp.", "T": "AT&T Inc.",
    "TGT": "Target Corp.", "TJX": "TJX Companies", "TMO": "Thermo Fisher Scientific",
    "TMUS": "T-Mobile US", "TRV": "Travelers Cos.", "TSLA": "Tesla Inc.",
    "TXN": "Texas Instruments", "UNH": "UnitedHealth Group", "UNP": "Union Pacific",
    "UPS": "United Parcel Service", "URI": "United Rentals", "USB": "U.S. Bancorp",
    "V": "Visa Inc.", "VLO": "Valero Energy", "VRSK": "Verisk Analytics",
    "VRTX": "Vertex Pharmaceuticals", "VZ": "Verizon Communications", "WBA": "Walgreens Boots Alliance",
    "WFC": "Wells Fargo", "WM": "Waste Management", "WMT": "Walmart Inc.",
    "XOM": "Exxon Mobil", "ZTS": "Zoetis Inc.",
}
DEFAULT_RANGE_DAYS = 7

# Colors
C_BG = "#0a0e14"
C_CARD = "#131922"
C_BORDER = "#1e2a3a"
C_ACCENT = "#58a6ff"
C_GREEN = "#3fb950"
C_RED = "#f85149"
C_MUTED = "#6e7681"
C_TEXT = "#e6edf3"

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.DARKLY,
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap",
        "https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&display=swap",
    ],
    title="Sentiment · Dashboard",
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
server = app.server

# ---------------------------------------------------------------------------
# Inject CSS via index_string (html.Style doesn't exist in Dash)
# ---------------------------------------------------------------------------
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            * { box-sizing: border-box; }
            body {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
                background: ''' + C_BG + ''' !important;
                color: ''' + C_TEXT + ''' !important;
                -webkit-font-smoothing: antialiased;
            }
            ::-webkit-scrollbar { width: 6px; }
            ::-webkit-scrollbar-track { background: transparent; }
            ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
            ::-webkit-scrollbar-thumb:hover { background: #484f58; }

            .card {
                background: ''' + C_CARD + ''' !important;
                border: 1px solid ''' + C_BORDER + ''' !important;
                border-radius: 16px !important;
                box-shadow: 0 8px 32px rgba(0,0,0,0.4) !important;
                overflow: hidden;
            }
            .card-header {
                background: transparent !important;
                border-bottom: 1px solid ''' + C_BORDER + ''' !important;
                font-weight: 600 !important;
                letter-spacing: 1px;
                text-transform: uppercase;
                font-size: 0.7rem;
                color: ''' + C_MUTED + ''' !important;
                padding: 1rem 1.5rem 0.75rem !important;
            }

            .metric-card {
                background: ''' + C_CARD + ''';
                border: 1px solid ''' + C_BORDER + ''';
                border-radius: 16px;
                padding: 1.5rem 1rem;
                text-align: center;
                transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
                position: relative;
                overflow: hidden;
            }
            .metric-card::before {
                content: '';
                position: absolute;
                top: 0; left: 0; right: 0;
                height: 2px;
                background: linear-gradient(90deg, transparent, ''' + C_ACCENT + ''', transparent);
                opacity: 0;
                transition: opacity 0.25s ease;
            }
            .metric-card:hover {
                border-color: rgba(88,166,255,0.3);
                box-shadow: 0 8px 32px rgba(88,166,255,0.08);
                transform: translateY(-2px);
            }
            .metric-card:hover::before { opacity: 1; }
            .metric-value {
                font-size: 1.75rem;
                font-weight: 800;
                font-family: 'JetBrains Mono', monospace;
                line-height: 1.2;
            }
            .metric-label {
                font-size: 0.65rem;
                text-transform: uppercase;
                letter-spacing: 1.5px;
                color: ''' + C_MUTED + ''';
                margin-top: 0.5rem;
                font-weight: 500;
            }

            .headline-row {
                padding: 0.75rem 0;
                border-bottom: 1px solid rgba(30,42,58,0.5);
                transition: all 0.15s ease;
            }
            .headline-row:last-child { border-bottom: none; }
            .headline-row:hover {
                background: rgba(88,166,255,0.03);
                padding-left: 0.5rem;
            }
            .headline-row a {
                color: ''' + C_TEXT + ''' !important;
                text-decoration: none !important;
                font-size: 0.85rem;
                line-height: 1.5;
                font-weight: 400;
            }
            .headline-row a:hover { color: ''' + C_ACCENT + ''' !important; }

            .score-badge {
                display: inline-block;
                padding: 0.2rem 0.6rem;
                border-radius: 8px;
                font-size: 0.7rem;
                font-weight: 600;
                font-family: 'JetBrains Mono', monospace;
                letter-spacing: 0.3px;
            }
            .score-pos { background: rgba(63,185,80,0.12); color: #3fb950; }
            .score-neg { background: rgba(248,81,73,0.12); color: #f85149; }
            .score-neu { background: rgba(110,118,129,0.12); color: #8b949e; }

            .analyze-btn {
                background: linear-gradient(135deg, #238636 0%, #2ea043 100%) !important;
                border: none !important;
                border-radius: 12px !important;
                font-weight: 700 !important;
                letter-spacing: 0.5px;
                padding: 0.75rem 1.5rem !important;
                font-size: 0.85rem !important;
                transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
                text-transform: uppercase;
            }
            .analyze-btn:hover {
                box-shadow: 0 8px 24px rgba(46,160,67,0.35) !important;
                transform: translateY(-2px);
            }
            .analyze-btn:active { transform: translateY(0); }

            /* Dropdown styling */
            .Select-control {
                background: #0d1117 !important;
                border-color: ''' + C_BORDER + ''' !important;
                border-radius: 10px !important;
            }
            .Select-menu-outer, .VirtualizedSelectOption {
                background: #0d1117 !important;
                color: ''' + C_TEXT + ''' !important;
            }
            .VirtualizedSelectOption:hover,
            .VirtualizedSelectFocusedOption {
                background: ''' + C_BORDER + ''' !important;
                color: #fff !important;
            }
            .Select-option {
                background: #0d1117 !important;
                color: ''' + C_TEXT + ''' !important;
            }
            .Select-option:hover, .Select-option.is-focused {
                background: ''' + C_BORDER + ''' !important;
            }
            .Select-value-label {
                color: ''' + C_TEXT + ''' !important;
            }
            .Select-input input {
                color: ''' + C_TEXT + ''' !important;
            }
            .Select-placeholder {
                color: ''' + C_MUTED + ''' !important;
            }
            /* Dash dropdown overrides */
            .dash-dropdown .Select-menu-outer {
                background: #0d1117 !important;
                border-color: ''' + C_BORDER + ''' !important;
            }
            .dash-dropdown .VirtualizedSelectOption {
                background: #0d1117 !important;
                color: ''' + C_TEXT + ''' !important;
            }
            .dash-dropdown .VirtualizedSelectFocusedOption {
                background: ''' + C_BORDER + ''' !important;
                color: #fff !important;
            }
            .date-filter-indicator {
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
                padding: 0.3rem 0.75rem;
                border-radius: 8px;
                font-size: 0.75rem;
                font-weight: 600;
                background: rgba(88,166,255,0.1);
                color: ''' + C_ACCENT + ''';
                border: 1px solid rgba(88,166,255,0.2);
                cursor: pointer;
                transition: all 0.15s ease;
            }
            .date-filter-indicator:hover {
                background: rgba(88,166,255,0.2);
            }
            .DateInput_input {
                background: #0d1117 !important;
                border-color: ''' + C_BORDER + ''' !important;
                border-radius: 10px !important;
                color: ''' + C_TEXT + ''' !important;
                font-family: 'Inter', sans-serif !important;
                font-size: 0.85rem !important;
            }

            h1 { font-weight: 800 !important; letter-spacing: -1px; }

            .empty-state {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                min-height: 400px;
                color: ''' + C_MUTED + ''';
            }
            .empty-state .icon { font-size: 3rem; margin-bottom: 1rem; opacity: 0.5; }
            .empty-state p { font-size: 0.9rem; max-width: 300px; text-align: center; line-height: 1.6; }

            .header-badge {
                display: inline-block;
                padding: 0.25rem 0.75rem;
                border-radius: 20px;
                font-size: 0.7rem;
                font-weight: 600;
                letter-spacing: 0.5px;
                background: rgba(88,166,255,0.1);
                color: ''' + C_ACCENT + ''';
                border: 1px solid rgba(88,166,255,0.2);
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

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
        html.Label("Security", className="fw-semibold mb-2",
                    style={"fontSize": "0.75rem", "color": C_MUTED, "letterSpacing": "0.5px",
                           "textTransform": "uppercase"}),
        dcc.Dropdown(
            id="ticker-dropdown",
            options=[{"label": f"{t}  ·  {n}", "value": t, "search": f"{t} {n}"}
                     for t, n in sorted(SECURITIES.items(), key=lambda x: x[0])],
            value="AAPL",
            clearable=False,
            searchable=True,
            placeholder="Search by ticker or company name...",
            className="mb-4",
            style={"backgroundColor": "#0d1117"},
        ),
        html.Label("Date Range", className="fw-semibold mb-2",
                    style={"fontSize": "0.75rem", "color": C_MUTED, "letterSpacing": "0.5px",
                           "textTransform": "uppercase"}),
        dcc.DatePickerRange(
            id="date-range",
            start_date=_start,
            end_date=_end,
            max_date_allowed=dt.date.today(),
            display_format="MMM D, YYYY",
            className="mb-4",
            style={"width": "100%"},
        ),

        # Quick range buttons
        html.Div([
            html.Label("Quick Select", className="fw-semibold mb-2",
                        style={"fontSize": "0.75rem", "color": C_MUTED, "letterSpacing": "0.5px",
                               "textTransform": "uppercase", "display": "block"}),
            html.Div([
                dbc.Button("7D", id="btn-7d", size="sm", outline=True, color="secondary",
                           className="me-2", style={"borderRadius": "8px", "fontSize": "0.75rem"}),
                dbc.Button("14D", id="btn-14d", size="sm", outline=True, color="secondary",
                           className="me-2", style={"borderRadius": "8px", "fontSize": "0.75rem"}),
                dbc.Button("30D", id="btn-30d", size="sm", outline=True, color="secondary",
                           style={"borderRadius": "8px", "fontSize": "0.75rem"}),
            ]),
        ], className="mb-4"),

        dbc.Button("Analyze", id="btn-analyze", className="analyze-btn w-100",
                    n_clicks=0),
    ], style={"padding": "1.5rem"}),
])

# Initial empty state
empty_state = html.Div([
    html.Div("📊", className="icon"),
    html.P("Select a security and date range, then click Analyze to get started."),
], className="empty-state")

app.layout = dbc.Container([
    # Header
    dbc.Row(dbc.Col(html.Div([
        html.Div([
            html.Div([
                html.H1("Sentiment", className="mb-0",
                         style={"fontSize": "2rem", "color": C_TEXT}),
                html.Span("Dashboard", style={
                    "fontSize": "2rem", "fontWeight": "300", "color": C_MUTED,
                    "marginLeft": "0.5rem",
                }),
            ], style={"display": "flex", "alignItems": "baseline"}),
            html.Div([
                html.Span("VADER", className="header-badge me-2"),
                html.Span("Google News", className="header-badge"),
            ], style={"marginTop": "0.5rem"}),
        ]),
    ]), width=12), className="mt-4 mb-4"),

    # Controls + main content
    dbc.Row([
        dbc.Col(controls, lg=3, md=4, className="mb-4"),
        dbc.Col([
            html.Div(id="metrics-container"),
            dcc.Loading(
                id="loading-main", type="dot", color=C_ACCENT,
                children=html.Div(id="main-chart-container", children=empty_state),
            ),
        ], lg=9, md=8),
    ]),

    # Bottom row: donut + headlines
    dbc.Row([
        dbc.Col(dcc.Loading(html.Div(id="donut-container"), type="dot",
                            color=C_ACCENT), lg=3, md=4, className="mb-4"),
        dbc.Col(dcc.Loading(html.Div(id="headline-container"), type="dot",
                            color=C_ACCENT), lg=9, md=8, className="mb-4"),
    ], className="mt-3"),

    # Footer
    html.Div(
        html.P("Built with Dash · Data from Google News",
               style={"color": C_MUTED, "fontSize": "0.7rem", "textAlign": "center",
                      "padding": "2rem 0 1rem"}),
    ),

    dcc.Store(id="sentiment-data"),
    dcc.Store(id="headline-data"),
    dcc.Store(id="selected-date"),
    dcc.Store(id="selected-sentiment"),
], fluid=True, style={"maxWidth": "1440px"})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
CHART_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", size=12, color=C_TEXT),
    margin=dict(l=50, r=20, t=40, b=30),
    xaxis=dict(gridcolor="rgba(30,42,58,0.6)", zeroline=False),
    yaxis=dict(gridcolor="rgba(30,42,58,0.6)", zeroline=False),
)


def _metric_card(value, label, color=C_TEXT):
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
# Quick-select date range callbacks
# ---------------------------------------------------------------------------
for btn_id, days in [("btn-7d", 7), ("btn-14d", 14), ("btn-30d", 30)]:
    @callback(
        Output("date-range", "start_date", allow_duplicate=True),
        Output("date-range", "end_date", allow_duplicate=True),
        Input(btn_id, "n_clicks"),
        prevent_initial_call=True,
        _days=days,
    )
    def _set_range(n, _days=days):
        end = dt.date.today() - dt.timedelta(days=1)
        start = end - dt.timedelta(days=_days - 1)
        return start, end


# ---------------------------------------------------------------------------
# Main callback
# ---------------------------------------------------------------------------
@callback(
    Output("sentiment-data", "data"),
    Output("headline-data", "data"),
    Output("metrics-container", "children"),
    Output("main-chart-container", "children"),
    Output("donut-container", "children"),
    Output("selected-date", "data"),
    Output("selected-sentiment", "data"),
    Input("btn-analyze", "n_clicks"),
    State("ticker-dropdown", "value"),
    State("date-range", "start_date"),
    State("date-range", "end_date"),
)
def run_analysis(n_clicks, ticker, start_str, end_str):
    start = dt.date.fromisoformat(start_str)
    end = dt.date.fromisoformat(end_str)
    name = SECURITIES.get(ticker, ticker)

    sent = get_sentiment_over_range(ticker, name, start, end)

    if not sent["headlines"]:
        msg = dbc.Card(
            dbc.CardBody(html.Div([
                html.Div("🔍", className="icon"),
                html.P(f"No data found for {name} ({ticker}) in this range. Try a different date range or security.",
                       style={"color": C_MUTED, "maxWidth": "400px", "textAlign": "center", "lineHeight": "1.6"}),
            ], className="empty-state", style={"minHeight": "300px"})),
        )
        return None, None, "", msg, "", None, None

    daily_df = pd.DataFrame(sent["daily"])
    s = sent["summary"]

    # --- Metrics ---
    avg_color = C_GREEN if s["avg_compound"] >= 0.05 else C_RED if s["avg_compound"] <= -0.05 else C_MUTED

    metrics = dbc.Row([
        dbc.Col(_metric_card(f"{s['avg_compound']:+.3f}", "Avg Sentiment", avg_color), width=3),
        dbc.Col(_metric_card(str(s["total"]), "Headlines"), width=3),
        dbc.Col(_metric_card(
            f"{s['positive']}/{s['negative']}",
            "Bullish / Bearish",
            C_GREEN if s["positive"] > s["negative"] else C_RED if s["negative"] > s["positive"] else C_MUTED,
        ), width=3),
        dbc.Col(_metric_card(str(s["neutral"]), "Neutral"), width=3),
    ], className="mb-3 g-3")

    # --- Main chart (sentiment only) ---
    daily_with_data = daily_df[daily_df["avg_compound"].notna()]
    fig = go.Figure()

    if not daily_with_data.empty:
        colors = [
            "rgba(63,185,80,0.85)" if v >= 0 else "rgba(248,81,73,0.85)"
            for v in daily_with_data["avg_compound"]
        ]
        fig.add_trace(go.Bar(
            x=daily_with_data["date"], y=daily_with_data["avg_compound"],
            name="Sentiment", marker_color=colors,
            marker_line_width=0,
            hovertemplate="<b>%{x}</b><br>Sentiment: %{y:+.3f}<extra></extra>",
        ))
        fig.add_hline(y=0, line_color=C_BORDER, line_width=1)

    fig.update_layout(
        **CHART_LAYOUT,
        height=420,
        showlegend=False,
        yaxis_title="Sentiment Score",
        yaxis_gridcolor="rgba(30,42,58,0.4)",
        yaxis_zeroline=False,
        yaxis_title_font=dict(size=11, color=C_MUTED),
        hoverlabel=dict(
            bgcolor=C_CARD, bordercolor=C_BORDER,
            font=dict(family="Inter", size=12, color=C_TEXT),
        ),
    )

    chart_card = dbc.Card([
        dbc.CardHeader(
            html.Div([
                html.Span(f"{name} ({ticker})", style={"fontWeight": "600", "color": C_TEXT,
                          "textTransform": "none", "fontSize": "0.85rem", "letterSpacing": "0"}),
                html.Span(f"{start.strftime('%b %d')} — {end.strftime('%b %d, %Y')}",
                          style={"color": C_MUTED, "fontSize": "0.7rem", "float": "right",
                                 "letterSpacing": "0.5px", "marginTop": "2px"}),
            ])
        ),
        dbc.CardBody(dcc.Graph(id="sentiment-chart", figure=fig,
                              config={"displayModeBar": False}),
                     style={"padding": "0.5rem 0.75rem"}),
    ])

    # --- Donut ---
    fig_donut = go.Figure(go.Pie(
        labels=["Bullish", "Neutral", "Bearish"],
        values=[s["positive"], s["neutral"], s["negative"]],
        marker=dict(
            colors=[C_GREEN, "#1e2a3a", C_RED],
            line=dict(color=C_CARD, width=4),
        ),
        hole=0.7,
        textinfo="percent",
        textfont=dict(size=12, family="JetBrains Mono"),
        hovertemplate="<b>%{label}</b><br>%{value} headlines<br>%{percent}<extra></extra>",
    ))
    fig_donut.update_layout(
        **CHART_LAYOUT,
        height=340,
        showlegend=True,
        legend=dict(
            orientation="h", yanchor="top", y=-0.02,
            xanchor="center", x=0.5,
            font=dict(size=11, color=C_MUTED),
        ),
        hoverlabel=dict(bgcolor=C_CARD, bordercolor=C_BORDER,
                        font=dict(family="Inter", size=12, color=C_TEXT)),
        annotations=[dict(
            text=f"<b>{s['avg_compound']:+.2f}</b>",
            x=0.5, y=0.5, font_size=22,
            font_color=avg_color,
            font_family="JetBrains Mono",
            showarrow=False,
        )],
    )

    donut_card = dbc.Card([
        dbc.CardHeader("Sentiment Split"),
        dbc.CardBody(dcc.Graph(id="donut-chart", figure=fig_donut,
                              config={"displayModeBar": False}),
                     style={"padding": "0.5rem"}),
    ])

    # --- Serialize headlines for store ---
    hl_serialized = []
    for h in sent["headlines"]:
        hl_serialized.append({
            "title": h["title"],
            "link": h["link"],
            "source": h["source"],
            "date": h["date"].isoformat() if h.get("date") else None,
            "compound": h["sentiment"]["compound"],
        })

    store = {"ticker": ticker, "name": name, "summary": s, "daily": sent["daily"]}
    return store, hl_serialized, metrics, chart_card, donut_card, None, None


# ---------------------------------------------------------------------------
# Helpers for sentiment classification
# ---------------------------------------------------------------------------
def _classify(compound):
    if compound >= 0.05:
        return "Bullish"
    elif compound <= -0.05:
        return "Bearish"
    return "Neutral"


SENTIMENT_COLORS = {"Bullish": C_GREEN, "Neutral": "#1e2a3a", "Bearish": C_RED}
SENTIMENT_COLORS_ALPHA = {
    "Bullish": "rgba(63,185,80,0.85)",
    "Bearish": "rgba(248,81,73,0.85)",
    "Neutral": "rgba(110,118,129,0.5)",
}
SENTIMENT_COLORS_DIM = {
    "Bullish": "rgba(63,185,80,0.15)",
    "Bearish": "rgba(248,81,73,0.15)",
    "Neutral": "rgba(110,118,129,0.1)",
}


# ---------------------------------------------------------------------------
# Click on bar → toggle date filter
# ---------------------------------------------------------------------------
@callback(
    Output("selected-date", "data", allow_duplicate=True),
    Input("sentiment-chart", "clickData"),
    State("selected-date", "data"),
    prevent_initial_call=True,
)
def toggle_date_filter(click_data, current_date):
    if not click_data or not click_data.get("points"):
        return no_update
    clicked_date = click_data["points"][0]["x"]
    if current_date == clicked_date:
        return None
    return clicked_date


# ---------------------------------------------------------------------------
# Click on donut slice → toggle sentiment filter
# ---------------------------------------------------------------------------
@callback(
    Output("selected-sentiment", "data", allow_duplicate=True),
    Input("donut-chart", "clickData"),
    State("selected-sentiment", "data"),
    prevent_initial_call=True,
)
def toggle_sentiment_filter(click_data, current_sentiment):
    if not click_data or not click_data.get("points"):
        return no_update
    label = click_data["points"][0]["label"]
    if current_sentiment == label:
        return None
    return label


# ---------------------------------------------------------------------------
# Update bar chart when sentiment filter changes (highlight matching days)
# ---------------------------------------------------------------------------
@callback(
    Output("sentiment-chart", "figure"),
    Input("selected-sentiment", "data"),
    State("sentiment-data", "data"),
    prevent_initial_call=True,
)
def update_chart_highlight(selected_sentiment, store):
    if not store or not store.get("daily"):
        return no_update

    daily_df = pd.DataFrame(store["daily"])
    daily_with_data = daily_df[daily_df["avg_compound"].notna()]

    fig = go.Figure()
    if not daily_with_data.empty:
        if selected_sentiment:
            colors = []
            for v in daily_with_data["avg_compound"]:
                cat = _classify(v)
                if cat == selected_sentiment:
                    colors.append(SENTIMENT_COLORS_ALPHA[cat])
                else:
                    colors.append(SENTIMENT_COLORS_DIM[cat])
        else:
            colors = [
                "rgba(63,185,80,0.85)" if v >= 0 else "rgba(248,81,73,0.85)"
                for v in daily_with_data["avg_compound"]
            ]

        fig.add_trace(go.Bar(
            x=daily_with_data["date"], y=daily_with_data["avg_compound"],
            name="Sentiment", marker_color=colors,
            marker_line_width=0,
            hovertemplate="<b>%{x}</b><br>Sentiment: %{y:+.3f}<extra></extra>",
        ))
        fig.add_hline(y=0, line_color=C_BORDER, line_width=1)

    fig.update_layout(
        **CHART_LAYOUT,
        height=420,
        showlegend=False,
        yaxis=dict(title="Sentiment Score", gridcolor="rgba(30,42,58,0.4)", zeroline=False,
                   title_font=dict(size=11, color=C_MUTED)),
        hoverlabel=dict(
            bgcolor=C_CARD, bordercolor=C_BORDER,
            font=dict(family="Inter", size=12, color=C_TEXT),
        ),
    )
    return fig


# ---------------------------------------------------------------------------
# Update donut to show selection state
# ---------------------------------------------------------------------------
@callback(
    Output("donut-chart", "figure"),
    Input("selected-sentiment", "data"),
    State("sentiment-data", "data"),
    prevent_initial_call=True,
)
def update_donut_highlight(selected_sentiment, store):
    if not store or not store.get("summary"):
        return no_update

    s = store["summary"]
    labels = ["Bullish", "Neutral", "Bearish"]
    values = [s["positive"], s["neutral"], s["negative"]]
    base_colors = [C_GREEN, "#1e2a3a", C_RED]

    if selected_sentiment:
        # Dim unselected slices
        colors = []
        pull = []
        for i, lbl in enumerate(labels):
            if lbl == selected_sentiment:
                colors.append(base_colors[i])
                pull.append(0.08)
            else:
                colors.append("rgba(30,42,58,0.3)")
                pull.append(0)
    else:
        colors = base_colors
        pull = [0, 0, 0]

    avg = s["avg_compound"]
    avg_color = C_GREEN if avg >= 0.05 else C_RED if avg <= -0.05 else C_MUTED

    fig_donut = go.Figure(go.Pie(
        labels=labels,
        values=values,
        marker=dict(
            colors=colors,
            line=dict(color=C_CARD, width=4),
        ),
        hole=0.7,
        pull=pull,
        textinfo="percent",
        textfont=dict(size=12, family="JetBrains Mono"),
        hovertemplate="<b>%{label}</b><br>%{value} headlines<br>%{percent}<extra></extra>",
    ))

    center_text = f"<b>{avg:+.2f}</b>"
    if selected_sentiment:
        center_text = f"<b>{selected_sentiment}</b>"
        avg_color = SENTIMENT_COLORS.get(selected_sentiment, C_ACCENT)
        if selected_sentiment == "Neutral":
            avg_color = "#8b949e"

    fig_donut.update_layout(
        **CHART_LAYOUT,
        height=340,
        showlegend=True,
        legend=dict(
            orientation="h", yanchor="top", y=-0.02,
            xanchor="center", x=0.5,
            font=dict(size=11, color=C_MUTED),
        ),
        hoverlabel=dict(bgcolor=C_CARD, bordercolor=C_BORDER,
                        font=dict(family="Inter", size=12, color=C_TEXT)),
        annotations=[dict(
            text=center_text,
            x=0.5, y=0.5, font_size=18 if selected_sentiment else 22,
            font_color=avg_color,
            font_family="JetBrains Mono",
            showarrow=False,
        )],
    )
    return fig_donut


# ---------------------------------------------------------------------------
# Render headlines based on stored data + date filter + sentiment filter
# ---------------------------------------------------------------------------
@callback(
    Output("headline-container", "children"),
    Input("headline-data", "data"),
    Input("selected-date", "data"),
    Input("selected-sentiment", "data"),
)
def render_headlines(hl_data, selected_date, selected_sentiment):
    if not hl_data:
        return ""

    filtered = hl_data

    # Filter by date
    if selected_date:
        filtered = [h for h in filtered if h.get("date") and h["date"] == selected_date]

    # Filter by sentiment category
    if selected_sentiment:
        filtered = [h for h in filtered if _classify(h["compound"]) == selected_sentiment]

    sorted_hl = sorted(filtered, key=lambda h: abs(h["compound"]), reverse=True)[:25]

    hl_items = []
    for h in sorted_hl:
        sc = h["compound"]
        date_str = ""
        if h.get("date"):
            d = dt.date.fromisoformat(h["date"])
            date_str = d.strftime("%b %d")

        if sc >= 0.05:
            cls = "score-pos"
        elif sc <= -0.05:
            cls = "score-neg"
        else:
            cls = "score-neu"

        hl_items.append(html.Div([
            html.Div([
                html.Div([
                    html.Span(f"{sc:+.3f}", className=f"score-badge {cls}"),
                    html.Span(f"  {date_str}",
                              style={"color": C_MUTED, "fontSize": "0.7rem",
                                     "marginLeft": "0.5rem", "fontFamily": "JetBrains Mono"}),
                    html.Span(f"  {h['source']}",
                              style={"color": "#484f58", "fontSize": "0.7rem",
                                     "marginLeft": "0.5rem"}),
                ], style={"marginBottom": "0.3rem"}),
                html.A(h["title"], href=h["link"], target="_blank"),
            ]),
        ], className="headline-row"))

    # Header with active filter indicators
    header_children = [html.Span("Top Headlines by Impact")]
    filter_pills = []

    if selected_sentiment:
        sent_color = SENTIMENT_COLORS.get(selected_sentiment, C_ACCENT)
        if selected_sentiment == "Neutral":
            sent_color = "#8b949e"
        filter_pills.append(
            html.Span([
                html.Span(f"{selected_sentiment}"),
                html.Span(" ✕", style={"marginLeft": "0.25rem"}),
            ], className="date-filter-indicator",
               style={"borderColor": sent_color, "color": sent_color,
                       "background": f"rgba({','.join(str(int(sent_color.lstrip('#')[i:i+2], 16)) for i in (0,2,4))},0.1)" if sent_color.startswith('#') else "rgba(88,166,255,0.1)"},
               id="reset-sentiment-filter")
        )

    if selected_date:
        d = dt.date.fromisoformat(selected_date)
        filter_pills.append(
            html.Span([
                html.Span(f"{d.strftime('%b %d, %Y')}"),
                html.Span(" ✕", style={"marginLeft": "0.25rem"}),
            ], className="date-filter-indicator",
               id="reset-date-filter")
        )

    if not filter_pills:
        filter_pills.append(
            html.Span("All dates", style={"fontSize": "0.7rem", "color": C_MUTED,
                                           "letterSpacing": "0.5px"})
        )

    header_children.append(
        html.Div(filter_pills, style={"float": "right", "display": "flex", "gap": "0.5rem"})
    )

    return dbc.Card([
        dbc.CardHeader(html.Div(header_children)),
        dbc.CardBody(
            hl_items if hl_items else [
                html.P("No headlines match these filters.", style={"color": C_MUTED})
            ],
            style={"padding": "0.75rem 1.5rem", "maxHeight": "500px", "overflowY": "auto"},
        ),
    ])


# ---------------------------------------------------------------------------
# Reset filters via indicator buttons
# ---------------------------------------------------------------------------
@callback(
    Output("selected-date", "data", allow_duplicate=True),
    Input("reset-date-filter", "n_clicks"),
    prevent_initial_call=True,
)
def reset_date_filter(n):
    return None


@callback(
    Output("selected-sentiment", "data", allow_duplicate=True),
    Input("reset-sentiment-filter", "n_clicks"),
    prevent_initial_call=True,
)
def reset_sentiment_filter(n):
    return None


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
