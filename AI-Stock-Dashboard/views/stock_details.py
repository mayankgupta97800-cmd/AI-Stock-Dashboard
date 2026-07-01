"""Stock details page: search, OHLC charts, indicators, fundamentals."""
from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from services import stock_service as svc
from services import portfolio_service as ps
from utils.ui import section_header, metric_card
from utils.helpers import fmt_currency, fmt_number, fmt_pct, fmt_large


def _candlestick_figure(df: pd.DataFrame, ticker: str) -> go.Figure:
    df = svc.add_moving_averages(df).copy()
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, row_heights=[0.75, 0.25],
        vertical_spacing=0.04, subplot_titles=("", "Volume"),
    )
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"], name=ticker,
        increasing_line_color="#00D4A4", decreasing_line_color="#FF5C6C",
    ), row=1, col=1)
    for w, color in zip((20, 50, 200), ("#F2C94C", "#56CCF2", "#BB6BD9")):
        if f"MA{w}" in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index, y=df[f"MA{w}"], mode="lines",
                name=f"MA {w}", line=dict(width=1.2, color=color),
            ), row=1, col=1)
    fig.add_trace(go.Bar(
        x=df.index, y=df["Volume"], name="Volume",
        marker_color="rgba(136,146,166,0.5)",
    ), row=2, col=1)
    fig.update_layout(
        height=560, margin=dict(l=8, r=8, t=8, b=8),
        paper_bgcolor="#141A26", plot_bgcolor="#141A26",
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        font=dict(color="#E6EAF2"),
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.05)", color="#8892A6")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.05)", color="#8892A6")
    return fig


def _rsi_figure(df: pd.DataFrame) -> go.Figure:
    rsi = svc.compute_rsi(df["Close"])
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=rsi, line=dict(color="#56CCF2", width=1.5), name="RSI(14)"))
    fig.add_hline(y=70, line=dict(color="#FF5C6C", dash="dot"))
    fig.add_hline(y=30, line=dict(color="#00D4A4", dash="dot"))
    fig.update_layout(
        height=220, margin=dict(l=8, r=8, t=24, b=8),
        paper_bgcolor="#141A26", plot_bgcolor="#141A26",
        font=dict(color="#E6EAF2"),
        yaxis=dict(range=[0, 100], color="#8892A6", gridcolor="rgba(255,255,255,0.05)"),
        xaxis=dict(color="#8892A6", gridcolor="rgba(255,255,255,0.05)"),
        showlegend=False, title="RSI (14)",
    )
    return fig


def _macd_figure(df: pd.DataFrame) -> go.Figure:
    macd, signal, hist = svc.compute_macd(df["Close"])
    colors = ["#00D4A4" if v >= 0 else "#FF5C6C" for v in hist.fillna(0)]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df.index, y=hist, marker_color=colors, name="Histogram"))
    fig.add_trace(go.Scatter(x=df.index, y=macd, line=dict(color="#56CCF2", width=1.4), name="MACD"))
    fig.add_trace(go.Scatter(x=df.index, y=signal, line=dict(color="#F2C94C", width=1.4), name="Signal"))
    fig.update_layout(
        height=240, margin=dict(l=8, r=8, t=24, b=8),
        paper_bgcolor="#141A26", plot_bgcolor="#141A26",
        font=dict(color="#E6EAF2"),
        yaxis=dict(color="#8892A6", gridcolor="rgba(255,255,255,0.05)"),
        xaxis=dict(color="#8892A6", gridcolor="rgba(255,255,255,0.05)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        title="MACD (12, 26, 9)",
    )
    return fig


def _div_yield_pct(info: dict) -> str:
    """Format dividend yield. yfinance v0.2.50+ returns it directly as percent."""
    dy = info.get("dividendYield")
    if dy is None:
        return "—"
    try:
        return fmt_pct(float(dy))
    except (TypeError, ValueError):
        return "—"


def _kv_row(label: str, value: str) -> str:
    return (f'<div style="display:flex;justify-content:space-between;'
            f'padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.05);">'
            f'<span style="color:#8892A6;font-size:0.85rem">{label}</span>'
            f'<span style="color:#E6EAF2;font-weight:500">{value}</span></div>')


def render() -> None:
    st.markdown("## Stock Details")
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=5000, key="stock_refresh")
    # Search bar
    default_ticker = st.session_state.get("selected_ticker", "AAPL")
    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input("Search ticker or company", value=default_ticker,
                              key="stock_search_q", placeholder="e.g. AAPL, RELIANCE.NS, NVDA")
    with col2:
        period = st.selectbox("Range", ["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"], index=3)

    ticker = (query or "").strip().upper()
    # If user typed company name, try to lookup
    if ticker and not any(c.isdigit() for c in ticker) and " " in ticker:
        results = svc.search_tickers(ticker, limit=1)
        if results:
            ticker = results[0]["symbol"]

    if not ticker:
        st.info("Enter a ticker symbol to begin.")
        return

    info = svc.get_info(ticker)
    quote = svc.get_quote(ticker)
    df = svc.get_history(ticker, period=period)

    if df is None or df.empty:
        st.warning(f"Could not load data for **{ticker}**. The symbol may be invalid or the data feed is temporarily unavailable.")
        return

    st.session_state["selected_ticker"] = ticker

    # Header block
    name = info.get("shortName") or info.get("longName") or ticker
    st.markdown(f"### {name} · `{ticker}`")
    exch = info.get("exchange") or info.get("fullExchangeName") or ""
    industry = info.get("industry") or info.get("sector") or ""
    st.caption(f"{exch}  ·  {industry}")

    # Quick KPI cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Price", fmt_currency(quote["price"], ticker), quote.get("pct"))
    with c2:
        metric_card("52W High", fmt_currency(info.get("fiftyTwoWeekHigh"), ticker))
    with c3:
        metric_card("52W Low", fmt_currency(info.get("fiftyTwoWeekLow"), ticker))
    with c4:
        metric_card("Market Cap", fmt_large(info.get("marketCap")))

    # Charts
    section_header("Price Chart (Candlestick + MAs + Volume)")
    st.plotly_chart(_candlestick_figure(df, ticker), use_container_width=True,
                    config={"displayModeBar": False})

    cA, cB = st.columns(2)
    with cA:
        st.plotly_chart(_rsi_figure(df), use_container_width=True, config={"displayModeBar": False})
    with cB:
        st.plotly_chart(_macd_figure(df), use_container_width=True, config={"displayModeBar": False})

    # Company profile + fundamentals
    section_header("Company & Fundamentals")
    cL, cR = st.columns([2, 1])
    with cL:
        summary = info.get("longBusinessSummary")
        if summary:
            st.write(summary)
        else:
            st.caption("No company summary available.")
    with cR:
        rows = [
            ("Sector", info.get("sector") or "—"),
            ("Industry", info.get("industry") or "—"),
            ("Country", info.get("country") or "—"),
            ("Employees", fmt_large(info.get("fullTimeEmployees"))),
            ("Market Cap", fmt_large(info.get("marketCap"))),
            ("Enterprise Value", fmt_large(info.get("enterpriseValue"))),
            ("PE (TTM)", fmt_number(info.get("trailingPE"))),
            ("Forward PE", fmt_number(info.get("forwardPE"))),
            ("PEG", fmt_number(info.get("pegRatio"))),
            ("Price / Book", fmt_number(info.get("priceToBook"))),
            ("EPS (TTM)", fmt_number(info.get("trailingEps"))),
            ("Dividend Yield", _div_yield_pct(info)),
            ("Beta", fmt_number(info.get("beta"))),
            ("Profit Margin", fmt_pct((info.get("profitMargins") or 0) * 100) if info.get("profitMargins") else "—"),
            ("ROE", fmt_pct((info.get("returnOnEquity") or 0) * 100) if info.get("returnOnEquity") else "—"),
        ]
        html = "".join(_kv_row(k, str(v)) for k, v in rows)
        st.markdown(html, unsafe_allow_html=True)

    # Analyst recommendation
    rec = info.get("recommendationKey") or info.get("recommendationMean")
    target_high = info.get("targetHighPrice")
    target_low = info.get("targetLowPrice")
    target_mean = info.get("targetMeanPrice")
    section_header("Analyst Recommendation")
    a1, a2, a3, a4 = st.columns(4)
    with a1:
        metric_card("Consensus", str(rec).upper() if rec else "—")
    with a2:
        metric_card("Target High", fmt_currency(target_high, ticker))
    with a3:
        metric_card("Target Mean", fmt_currency(target_mean, ticker))
    with a4:
        metric_card("Target Low", fmt_currency(target_low, ticker))

    # Watchlist action
    user = st.session_state.get("user")
    if user:
        if st.button("⭐ Add to Watchlist", key="add_wl_btn"):
            ok, msg = ps.add_to_watchlist(user["id"], ticker)
            (st.success if ok else st.error)(msg)
