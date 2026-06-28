"""Generic helper utilities."""
from __future__ import annotations
import math
from datetime import datetime


def fmt_currency(value: float | int | None, ticker: str = "") -> str:
    """Format value as currency. INR symbol for NSE/BSE tickers, USD otherwise."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "—"
    symbol = "₹" if ticker.upper().endswith((".NS", ".BO")) else "$"
    try:
        return f"{symbol}{value:,.2f}"
    except (TypeError, ValueError):
        return "—"


def fmt_number(value, decimals: int = 2) -> str:
    if value is None:
        return "—"
    try:
        if isinstance(value, float) and math.isnan(value):
            return "—"
        return f"{value:,.{decimals}f}"
    except (TypeError, ValueError):
        return "—"


def fmt_pct(value: float | None, decimals: int = 2) -> str:
    if value is None:
        return "—"
    try:
        if math.isnan(value):
            return "—"
        return f"{value:+.{decimals}f}%"
    except (TypeError, ValueError):
        return "—"


def fmt_large(value) -> str:
    """Format large numbers as e.g. 1.23B, 456.78M."""
    if value is None:
        return "—"
    try:
        v = float(value)
        if math.isnan(v):
            return "—"
    except (TypeError, ValueError):
        return "—"
    abs_v = abs(v)
    if abs_v >= 1e12:
        return f"{v/1e12:.2f}T"
    if abs_v >= 1e9:
        return f"{v/1e9:.2f}B"
    if abs_v >= 1e6:
        return f"{v/1e6:.2f}M"
    if abs_v >= 1e3:
        return f"{v/1e3:.2f}K"
    return f"{v:.2f}"


def parse_date(value) -> str:
    if not value:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%b %d, %Y")
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).strftime("%b %d, %Y · %H:%M")
    except Exception:
        return str(value)


def simple_sentiment(text: str) -> str:
    """Very lightweight keyword-based sentiment. Returns 'positive', 'negative', or 'neutral'."""
    if not text:
        return "neutral"
    t = text.lower()
    pos = ["surge", "rally", "gain", "beat", "record", "growth", "strong", "rise",
           "upgrade", "buy", "bull", "soar", "jump", "profit", "win", "boost",
           "outperform", "high", "positive"]
    neg = ["fall", "drop", "plunge", "loss", "miss", "downgrade", "sell", "bear",
           "decline", "crash", "weak", "cut", "slump", "tumble", "warning", "risk",
           "lawsuit", "investigation", "bankruptcy", "layoff", "negative"]
    p = sum(1 for w in pos if w in t)
    n = sum(1 for w in neg if w in t)
    if p > n:
        return "positive"
    if n > p:
        return "negative"
    return "neutral"
