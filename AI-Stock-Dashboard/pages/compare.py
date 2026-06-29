"""Compare up to 4 stocks: normalized performance + key metrics table."""
from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from services import stock_service as svc
from utils.ui import section_header
from utils.helpers import fmt_number, fmt_pct, fmt_large, fmt_currency


PALETTE = ["#00D4A4", "#56CCF2", "#F2C94C", "#BB6BD9"]


def _normalized_chart(tickers: list[str], period: str) -> go.Figure | None:
    fig = go.Figure()
    plotted = False
    for i, t in enumerate(tickers):
        df = svc.get_history(t, period=period)
        if df is None or df.empty or "Close" not in df.columns:
            continue
        closes = df["Close"].dropna()
        if closes.empty:
            continue
        base = closes.iloc[0]
        norm = (closes / base - 1) * 100
        fig.add_trace(go.Scatter(
            x=norm.index, y=norm, mode="lines", name=t,
            line=dict(width=1.8, color=PALETTE[i % len(PALETTE)]),
        ))
        plotted = True
    if not plotted:
        return None
    fig.update_layout(
        height=440, margin=dict(l=8, r=8, t=60, b=8),
        paper_bgcolor="#141A26", plot_bgcolor="#141A26",
        font=dict(color="#E6EAF2"),
        yaxis=dict(title="% Return", color="#8892A6", gridcolor="rgba(255,255,255,0.05)"),
        xaxis=dict(color="#8892A6", gridcolor="rgba(255,255,255,0.05)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.35),
        title=dict(text=f"Normalized Performance ({period})", x=0.01, xanchor="left",
                   font=dict(size=14)),
    )
    return fig


def _div_yield(info: dict) -> str:
    dy = info.get("dividendYield")
    if dy is None:
        return "—"
    try:
        return fmt_pct(float(dy))
    except (TypeError, ValueError):
        return "—"


def _metrics_table(tickers: list[str]) -> pd.DataFrame:
    rows = []
    for t in tickers:
        info = svc.get_info(t)
        q = svc.get_quote(t)
        rows.append({
            "Ticker": t,
            "Price": fmt_currency(q.get("price"), t),
            "Day %": fmt_pct(q.get("pct")),
            "Market Cap": fmt_large(info.get("marketCap")),
            "PE (TTM)": fmt_number(info.get("trailingPE")),
            "Fwd PE": fmt_number(info.get("forwardPE")),
            "PEG": fmt_number(info.get("pegRatio")),
            "P/B": fmt_number(info.get("priceToBook")),
            "EPS": fmt_number(info.get("trailingEps")),
            "Dividend %": _div_yield(info),
            "Beta": fmt_number(info.get("beta")),
            "52W High": fmt_currency(info.get("fiftyTwoWeekHigh"), t),
            "52W Low": fmt_currency(info.get("fiftyTwoWeekLow"), t),
        })
    return pd.DataFrame(rows)


def render() -> None:
    st.markdown("## Compare Stocks")
    st.caption("Compare up to 4 stocks side-by-side: performance, valuation, fundamentals.")

    c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 2])
    with c1:
        t1 = st.text_input("Stock 1", value="AAPL").strip().upper()
    with c2:
        t2 = st.text_input("Stock 2", value="MSFT").strip().upper()
    with c3:
        t3 = st.text_input("Stock 3", value="GOOGL").strip().upper()
    with c4:
        t4 = st.text_input("Stock 4 (optional)", value="").strip().upper()
    with c5:
        period = st.selectbox("Period", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=3)

    tickers = [t for t in [t1, t2, t3, t4] if t]
    if len(tickers) < 2:
        st.info("Enter at least 2 tickers to compare.")
        return

    section_header("Performance")
    fig = _normalized_chart(tickers, period)
    if fig is None:
        st.warning("Could not load data for the selected tickers.")
        return
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    section_header("Key Metrics")
    df = _metrics_table(tickers)
    st.dataframe(df, use_container_width=True, hide_index=True)
