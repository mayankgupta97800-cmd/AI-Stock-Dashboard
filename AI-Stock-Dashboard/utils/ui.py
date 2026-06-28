"""Reusable Streamlit UI helpers."""
from __future__ import annotations
from pathlib import Path
import streamlit as st
from utils.helpers import fmt_pct


def load_css() -> None:
    """Inject the project's stylesheet exactly once per session."""
    css_path = Path(__file__).resolve().parent.parent / "assets" / "styles.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


def section_header(label: str) -> None:
    st.markdown(f'<div class="section-h">{label}</div>', unsafe_allow_html=True)


def metric_card(label: str, value: str, delta_pct: float | None = None) -> None:
    """Render a single metric card with optional percentage delta."""
    if delta_pct is None:
        delta_html = ""
    elif delta_pct > 0:
        delta_html = f'<div class="metric-delta-pos">▲ {fmt_pct(delta_pct)}</div>'
    elif delta_pct < 0:
        delta_html = f'<div class="metric-delta-neg">▼ {fmt_pct(delta_pct)}</div>'
    else:
        delta_html = '<div class="metric-delta-flat">0.00%</div>'
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def sentiment_badge(sentiment: str) -> str:
    s = (sentiment or "neutral").lower()
    if s == "positive":
        return '<span class="sent-pos">▲ POSITIVE</span>'
    if s == "negative":
        return '<span class="sent-neg">▼ NEGATIVE</span>'
    return '<span class="sent-neu">● NEUTRAL</span>'


def info_banner(message: str) -> None:
    st.info(message, icon="ℹ️")


def warn_banner(message: str) -> None:
    st.warning(message, icon="⚠️")
