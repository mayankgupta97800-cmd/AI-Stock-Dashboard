"""Stock & market data service backed by yfinance. All calls are defensive."""
from __future__ import annotations
from typing import Optional
import pandas as pd
import numpy as np
import yfinance as yf
import streamlit as st

from config import INDICES, SECTOR_ETFS, POPULAR_TICKERS


# ---------------- Core fetchers (cached) ----------------

@st.cache_data(ttl=5, show_spinner=False)
def get_history(ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """Return historical OHLCV. Empty DataFrame on failure."""
    if not ticker:
        return pd.DataFrame()
    try:
        df = yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=False)
        if df is None or df.empty:
            return pd.DataFrame()
        df = df.dropna(how="all")
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=30, show_spinner=False)
def get_info(ticker: str) -> dict:
    """Return ticker metadata. Empty dict on failure."""
    if not ticker:
        return {}
    try:
        info = yf.Ticker(ticker).info or {}
        return info if isinstance(info, dict) else {}
    except Exception:
        return {}


@st.cache_data(ttl=5, show_spinner=False)
def get_quote(ticker: str) -> dict:
    """Return a normalized lightweight quote: price, change, pct, prev_close, currency."""
    out = {"ticker": ticker, "price": None, "change": None, "pct": None,
           "prev_close": None, "currency": "USD", "name": ticker}
    if not ticker:
        return out
    df = get_history(ticker, period="5d", interval="1d")
    info = get_info(ticker)
    out["name"] = info.get("shortName") or info.get("longName") or ticker
    out["currency"] = info.get("currency") or ("INR" if ticker.upper().endswith((".NS", ".BO")) else "USD")
    if df is not None and not df.empty and "Close" in df.columns:
        closes = df["Close"].dropna()
        if len(closes) >= 1:
            out["price"] = float(closes.iloc[-1])
        if len(closes) >= 2:
            out["prev_close"] = float(closes.iloc[-2])
            out["change"] = out["price"] - out["prev_close"]
            if out["prev_close"]:
                out["pct"] = (out["change"] / out["prev_close"]) * 100.0
    return out


@st.cache_data(ttl=5, show_spinner=False)
def get_multi_quotes(tickers: tuple[str, ...]) -> pd.DataFrame:
    """Bulk-fetch latest closes & daily change for a list of tickers."""
    if not tickers:
        return pd.DataFrame(columns=["ticker", "name", "price", "change", "pct", "volume"])
    rows = []
    try:
        data = yf.download(
            list(tickers), period="5d", interval="1d",
            group_by="ticker", auto_adjust=False, progress=False, threads=True,
        )
    except Exception:
        data = None

    for t in tickers:
        try:
            if isinstance(data, pd.DataFrame) and not data.empty and isinstance(data.columns, pd.MultiIndex) and t in data.columns.get_level_values(0):
                df = data[t].dropna(how="all")
            elif isinstance(data, pd.DataFrame) and not data.empty and "Close" in data.columns and len(tickers) == 1:
                df = data.dropna(how="all")
            else:
                df = get_history(t, period="5d", interval="1d")
            if df is None or df.empty or "Close" not in df.columns:
                continue
            closes = df["Close"].dropna()
            vols = df["Volume"].dropna() if "Volume" in df.columns else pd.Series(dtype=float)
            if len(closes) < 1:
                continue
            price = float(closes.iloc[-1])
            prev = float(closes.iloc[-2]) if len(closes) >= 2 else price
            change = price - prev
            pct = (change / prev * 100.0) if prev else 0.0
            volume = float(vols.iloc[-1]) if not vols.empty else 0.0
            rows.append({"ticker": t, "name": t, "price": price, "change": change,
                         "pct": pct, "volume": volume})
        except Exception:
            continue
    return pd.DataFrame(rows)


# ---------------- Technical indicators ----------------

def add_moving_averages(df: pd.DataFrame, windows=(20, 50, 200)) -> pd.DataFrame:
    out = df.copy()
    if "Close" not in out.columns:
        return out
    for w in windows:
        out[f"MA{w}"] = out["Close"].rolling(window=w).mean()
    return out


def compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)


def compute_macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return macd_line, signal_line, hist


# ---------------- Market overview helpers ----------------

@st.cache_data(ttl=5, show_spinner=False)
def get_indices_overview() -> pd.DataFrame:
    df = get_multi_quotes(tuple(INDICES.keys()))
    if df.empty:
        return df
    df["name"] = df["ticker"].map(INDICES).fillna(df["ticker"])
    return df


@st.cache_data(ttl=5, show_spinner=False)
def get_sector_performance() -> pd.DataFrame:
    df = get_multi_quotes(tuple(SECTOR_ETFS.keys()))
    if df.empty:
        return df
    df["name"] = df["ticker"].map(SECTOR_ETFS).fillna(df["ticker"])
    return df.sort_values("pct", ascending=False).reset_index(drop=True)


@st.cache_data(ttl=5, show_spinner=False)
def get_movers(kind: str = "gainers", limit: int = 10) -> pd.DataFrame:
    """Return top gainers / losers / most active from the curated universe."""
    df = get_multi_quotes(tuple(POPULAR_TICKERS))
    if df.empty:
        return df
    if kind == "gainers":
        df = df.sort_values("pct", ascending=False)
    elif kind == "losers":
        df = df.sort_values("pct", ascending=True)
    elif kind == "active":
        df["dollar_vol"] = df["price"] * df["volume"]
        df = df.sort_values("dollar_vol", ascending=False)
    else:
        df = df.sort_values("pct", ascending=False)
    return df.head(limit).reset_index(drop=True)


@st.cache_data(ttl=300, show_spinner=False)
def get_trending(limit: int = 10) -> pd.DataFrame:
    """Trending = highest absolute % move in the curated universe."""
    df = get_multi_quotes(tuple(POPULAR_TICKERS))
    if df.empty:
        return df
    df["abs_pct"] = df["pct"].abs()
    return df.sort_values("abs_pct", ascending=False).head(limit).reset_index(drop=True)


# ---------------- Fear & Greed (calculated proxy) ----------------

def _scale01(value: float, lo: float, hi: float) -> float:
    if hi == lo:
        return 50.0
    v = (value - lo) / (hi - lo)
    return max(0.0, min(1.0, v)) * 100.0


@st.cache_data(ttl=600, show_spinner=False)
def get_fear_greed() -> Optional[dict]:
    """Compute a 0-100 Fear & Greed index from public market data.

    Components:
      * S&P 500 momentum vs 125-day SMA
      * Inverse VIX (lower VIX = greedier)
      * Safe-haven demand (SPY vs TLT 20-day return)
      * Market breadth (mean 1m return across sector ETFs)
    """
    try:
        spx = get_history("^GSPC", period="1y")
        vix = get_history("^VIX", period="3mo")
        spy = get_history("SPY", period="3mo")
        tlt = get_history("TLT", period="3mo")
        sectors = get_multi_quotes(tuple(SECTOR_ETFS.keys()))

        if spx.empty or vix.empty:
            return None

        # 1. Momentum vs 125d SMA -> -10%..+10% mapped to 0..100
        sma125 = spx["Close"].rolling(125).mean().iloc[-1]
        last = spx["Close"].iloc[-1]
        momentum_pct = ((last - sma125) / sma125) * 100.0 if sma125 else 0.0
        momentum_score = _scale01(momentum_pct, -10.0, 10.0)

        # 2. VIX inverse: 40 (fear) -> 0, 10 (greed) -> 100
        vix_last = float(vix["Close"].iloc[-1])
        vix_score = _scale01(40.0 - vix_last, 0.0, 30.0)

        # 3. Safe haven: SPY 20d return minus TLT 20d return; +5% -> greed
        if not spy.empty and not tlt.empty and len(spy) > 21 and len(tlt) > 21:
            spy_ret = (spy["Close"].iloc[-1] / spy["Close"].iloc[-21] - 1) * 100
            tlt_ret = (tlt["Close"].iloc[-1] / tlt["Close"].iloc[-21] - 1) * 100
            safe_haven_score = _scale01(spy_ret - tlt_ret, -5.0, 5.0)
        else:
            safe_haven_score = 50.0

        # 4. Breadth: average daily % across sectors mapped to -3..+3
        breadth_score = _scale01(float(sectors["pct"].mean()) if not sectors.empty else 0.0,
                                 -3.0, 3.0)

        score = round((momentum_score + vix_score + safe_haven_score + breadth_score) / 4)
        if score < 25:
            label = "Extreme Fear"
        elif score < 45:
            label = "Fear"
        elif score < 55:
            label = "Neutral"
        elif score < 75:
            label = "Greed"
        else:
            label = "Extreme Greed"
        return {
            "score": int(score),
            "label": label,
            "components": {
                "Momentum (S&P vs 125D SMA)": round(momentum_score),
                "Volatility (Inverse VIX)": round(vix_score),
                "Safe Haven (SPY-TLT 1M)": round(safe_haven_score),
                "Market Breadth (Sectors)": round(breadth_score),
            },
        }
    except Exception:
        return None


# ---------------- Search ----------------

@st.cache_data(ttl=600, show_spinner=False)
def search_tickers(query: str, limit: int = 10) -> list[dict]:
    """Search for tickers using yfinance's lookup. Returns list of {symbol, name, exchange}."""
    if not query or len(query.strip()) < 1:
        return []
    try:
        from yfinance import Search
        res = Search(query, max_results=limit).quotes or []
        out = []
        for r in res:
            sym = r.get("symbol")
            if not sym:
                continue
            out.append({
                "symbol": sym,
                "name": r.get("shortname") or r.get("longname") or sym,
                "exchange": r.get("exchange") or "",
                "type": r.get("quoteType") or "",
            })
        return out
    except Exception:
        # Fallback: simple match against curated universe
        q = query.upper().strip()
        return [{"symbol": t, "name": t, "exchange": "", "type": "EQUITY"}
                for t in POPULAR_TICKERS if q in t][:limit]
