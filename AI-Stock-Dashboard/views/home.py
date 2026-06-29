"""Home / Dashboard page: market overview, indices, heatmap, sectors, movers."""
from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from services import stock_service as svc
from utils.ui import section_header, metric_card
from utils.helpers import fmt_pct, fmt_number, fmt_large


def _movers_table(df: pd.DataFrame) -> None:
    if df is None or df.empty:
        st.caption("No data available right now.")
        return
    show = df[["ticker", "price", "change", "pct"]].copy()
    show.columns = ["Ticker", "Price", "Change", "% Change"]
    show["Price"] = show["Price"].map(lambda v: fmt_number(v, 2))
    show["Change"] = show["Change"].map(lambda v: fmt_number(v, 2))
    show["% Change"] = show["% Change"].map(lambda v: fmt_pct(v))
    st.dataframe(show, use_container_width=True, hide_index=True)


def _fear_greed_gauge(score: int, label: str) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={"font": {"size": 42, "color": "#E6EAF2"}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#8892A6",
                     "tickfont": {"color": "#8892A6"}},
            "bar": {"color": "#00D4A4", "thickness": 0.22},
            "bgcolor": "#0B0F1A",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 25], "color": "#7A1F2B"},
                {"range": [25, 45], "color": "#A8453A"},
                {"range": [45, 55], "color": "#7C7C8A"},
                {"range": [55, 75], "color": "#2A7F62"},
                {"range": [75, 100], "color": "#0E5C45"},
            ],
        },
        title={"text": f"<b style='color:#E6EAF2'>{label}</b>",
               "font": {"size": 16}},
    ))
    fig.update_layout(
        height=260, margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="#141A26", font={"color": "#E6EAF2"},
    )
    return fig


def _heatmap_figure(df: pd.DataFrame) -> go.Figure | None:
    if df is None or df.empty:
        return None
    df = df.copy()
    df["abs_pct"] = df["pct"].abs().clip(lower=0.2)
    df["pct_label"] = df["pct"].map(lambda v: f"{v:+.2f}%")
    df["label_text"] = df["name"] + "<br>" + df["pct_label"]
    fig = px.treemap(
        df, path=["label_text"], values="abs_pct", color="pct",
        color_continuous_scale=[(0, "#FF5C6C"), (0.5, "#2A2F3D"), (1, "#00D4A4")],
        color_continuous_midpoint=0,
        custom_data=["ticker", "pct", "price", "name"],
    )
    fig.update_traces(
        textposition="middle center",
        hovertemplate="<b>%{customdata[3]}</b> (%{customdata[0]})<br>"
                      "Price: %{customdata[2]:.2f}<br>"
                      "Change: %{customdata[1]:+.2f}%<extra></extra>",
    )
    fig.update_layout(
        height=380, margin=dict(l=8, r=8, t=8, b=8),
        paper_bgcolor="#141A26", font={"color": "#E6EAF2"},
    )
    return fig


def render() -> None:
    st.markdown("## Market Overview")
    st.caption("Live snapshot of global indices, sentiment, sectors and movers.")

    # ---- Indices grid ----
    section_header("Global Indices")
    idx_df = svc.get_indices_overview()
    if idx_df is None or idx_df.empty:
        st.warning("Market data is temporarily unavailable. Please retry in a moment.")
    else:
        # Render up to 8 cards in 4-column grid
        idx_df = idx_df.head(8)
        cols = st.columns(4)
        for i, row in idx_df.iterrows():
            with cols[i % 4]:
                metric_card(row["name"], fmt_number(row["price"], 2), row["pct"])

    # ---- Fear & Greed + Heatmap ----
    section_header("Sentiment & Sector Map")
    c1, c2 = st.columns([1, 2])
    with c1:
        fg = svc.get_fear_greed()
        if fg is None:
            st.info("Fear & Greed data unavailable")
        else:
            st.plotly_chart(_fear_greed_gauge(fg["score"], fg["label"]),
                            use_container_width=True, config={"displayModeBar": False})
            with st.expander("Component breakdown", expanded=False):
                for k, v in fg["components"].items():
                    st.write(f"**{k}** — {v}/100")
    with c2:
        sect = svc.get_sector_performance()
        fig = _heatmap_figure(sect)
        if fig is None:
            st.info("Sector performance unavailable.")
        else:
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ---- Sector performance bar ----
    section_header("Sector Performance (Daily)")
    if sect is not None and not sect.empty:
        fig = px.bar(sect, x="pct", y="name", orientation="h",
                     color="pct",
                     color_continuous_scale=[(0, "#FF5C6C"), (0.5, "#2A2F3D"), (1, "#00D4A4")],
                     color_continuous_midpoint=0, text=sect["pct"].map(lambda v: f"{v:+.2f}%"))
        fig.update_traces(textposition="outside")
        fig.update_layout(
            height=380, margin=dict(l=8, r=8, t=8, b=8),
            paper_bgcolor="#141A26", plot_bgcolor="#141A26",
            xaxis_title="% Change", yaxis_title="",
            yaxis=dict(autorange="reversed", color="#E6EAF2"),
            xaxis=dict(color="#8892A6", gridcolor="rgba(255,255,255,0.05)"),
            showlegend=False, coloraxis_showscale=False,
            font=dict(color="#E6EAF2"),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sector performance unavailable.")

    # ---- Movers ----
    section_header("Top Movers")
    t1, t2, t3, t4 = st.tabs(["📈 Top Gainers", "📉 Top Losers", "🔥 Most Active", "⚡ Trending"])
    with t1:
        _movers_table(svc.get_movers("gainers", limit=10))
    with t2:
        _movers_table(svc.get_movers("losers", limit=10))
    with t3:
        df = svc.get_movers("active", limit=10)
        if df is not None and not df.empty:
            df = df.copy()
            df["Volume"] = df["volume"].map(fmt_large)
            show = df[["ticker", "price", "pct", "Volume"]].copy()
            show.columns = ["Ticker", "Price", "% Change", "Volume"]
            show["Price"] = show["Price"].map(lambda v: fmt_number(v, 2))
            show["% Change"] = show["% Change"].map(lambda v: fmt_pct(v))
            st.dataframe(show, use_container_width=True, hide_index=True)
        else:
            st.caption("No data available right now.")
    with t4:
        _movers_table(svc.get_trending(limit=10))

    st.caption("Data via Yahoo Finance · Updates every 1–3 minutes (cached).")
