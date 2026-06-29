"""Portfolio page: buy/sell, value tracking, allocation, history, delete."""
from __future__ import annotations
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from services import portfolio_service as ps
from services import stock_service as svc
from utils.ui import section_header, metric_card
from utils.helpers import fmt_number, fmt_pct, fmt_currency


def _enrich_holdings(holdings: pd.DataFrame) -> pd.DataFrame:
    if holdings.empty:
        return holdings
    out = holdings.copy()
    prices, day_pct = [], []
    for t in out["ticker"]:
        q = svc.get_quote(t)
        prices.append(q.get("price"))
        day_pct.append(q.get("pct"))
    out["current_price"] = prices
    out["day_pct"] = day_pct
    out["cost_basis"] = out["quantity"] * out["avg_price"]
    out["market_value"] = out["quantity"] * out["current_price"].fillna(0)
    out["pnl"] = out["market_value"] - out["cost_basis"]
    out["pnl_pct"] = (out["pnl"] / out["cost_basis"]) * 100
    return out


def _history_chart(user_id: int) -> go.Figure | None:
    """Approximate equity curve by replaying transactions against historical prices."""
    txs = ps.list_transactions(user_id, limit=1000)
    if txs.empty:
        return None
    try:
        txs = txs.copy()
        # Force tz-naive timestamps for consistent date arithmetic
        txs["executed_at"] = pd.to_datetime(txs["executed_at"], utc=False, errors="coerce")
        txs = txs.dropna(subset=["executed_at"])
        if txs.empty:
            return None
        if hasattr(txs["executed_at"].dt, "tz") and txs["executed_at"].dt.tz is not None:
            txs["executed_at"] = txs["executed_at"].dt.tz_localize(None)
        txs = txs.sort_values("executed_at")
        start = txs["executed_at"].min().normalize()
        end = pd.Timestamp.now().normalize()  # tz-naive
        if start >= end:
            start = end - pd.Timedelta(days=30)
        tickers = sorted(txs["ticker"].unique())

        # Build daily quantity series per ticker
        dates = pd.date_range(start=start, end=end, freq="D")
        qty_df = pd.DataFrame(0.0, index=dates, columns=tickers)
        for _, row in txs.iterrows():
            delta = row["quantity"] if row["action"] == "BUY" else -row["quantity"]
            qty_df.loc[row["executed_at"].normalize():, row["ticker"]] += delta

        # Fetch prices once per ticker, ffill onto daily grid
        value = pd.Series(0.0, index=dates)
        for t in tickers:
            hist = svc.get_history(t, period="2y")
            if hist.empty or "Close" not in hist.columns:
                continue
            closes = hist["Close"].copy()
            if closes.index.tz is not None:
                closes.index = closes.index.tz_localize(None)
            closes = closes.reindex(dates).ffill().bfill().fillna(0)
            value = value.add(qty_df[t] * closes, fill_value=0)

        fig = go.Figure(go.Scatter(
            x=value.index, y=value.values, mode="lines",
            fill="tozeroy", line=dict(color="#00D4A4", width=2),
            fillcolor="rgba(0,212,164,0.12)",
        ))
        fig.update_layout(
            height=300, margin=dict(l=8, r=8, t=8, b=8),
            paper_bgcolor="#141A26", plot_bgcolor="#141A26",
            font=dict(color="#E6EAF2"),
            xaxis=dict(color="#8892A6", gridcolor="rgba(255,255,255,0.05)"),
            yaxis=dict(title="Portfolio Value", color="#8892A6", gridcolor="rgba(255,255,255,0.05)"),
        )
        return fig
    except Exception:
        return None
    return fig


def render() -> None:
    user = st.session_state.get("user")
    st.markdown("## Portfolio")
    if not user:
        st.warning("Please log in to use your portfolio.")
        return

    holdings = ps.list_holdings(user["id"])
    enriched = _enrich_holdings(holdings)

    # Summary cards
    if enriched.empty:
        total_value = total_cost = total_pnl = 0.0
        total_pct = 0.0
    else:
        total_value = float(enriched["market_value"].sum())
        total_cost = float(enriched["cost_basis"].sum())
        total_pnl = total_value - total_cost
        total_pct = (total_pnl / total_cost * 100) if total_cost else 0.0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Portfolio Value", fmt_number(total_value, 2))
    with c2:
        metric_card("Total Invested", fmt_number(total_cost, 2))
    with c3:
        metric_card("Profit / Loss", fmt_number(total_pnl, 2), total_pct)
    with c4:
        metric_card("# Holdings", str(len(enriched)))

    # Buy / Sell form
    section_header("Trade")
    tab_buy, tab_sell = st.tabs(["🟢 Buy", "🔴 Sell"])
    with tab_buy:
        with st.form("buy_form", clear_on_submit=True):
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            with c1:
                ticker = st.text_input("Ticker", placeholder="AAPL").strip().upper()
            with c2:
                qty = st.number_input("Quantity", min_value=0.0, step=1.0, value=1.0, format="%.4f")
            with c3:
                use_live = st.checkbox("Live price", value=True)
            with c4:
                price = st.number_input("Price", min_value=0.0, value=0.0, format="%.2f",
                                        disabled=use_live)
            submitted = st.form_submit_button("Buy", use_container_width=True)
            if submitted:
                final_price = price
                if use_live and ticker:
                    q = svc.get_quote(ticker)
                    final_price = q.get("price") or 0.0
                if not ticker or qty <= 0 or not final_price:
                    st.error("Provide a valid ticker, quantity and price.")
                else:
                    ok, msg = ps.buy_stock(user["id"], ticker, qty, float(final_price))
                    (st.success if ok else st.error)(msg)
                    if ok:
                        st.rerun()

    with tab_sell:
        if enriched.empty:
            st.info("You have no holdings to sell.")
        else:
            with st.form("sell_form", clear_on_submit=True):
                c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                with c1:
                    ticker = st.selectbox("Holding", enriched["ticker"].tolist(), key="sell_pick")
                with c2:
                    max_qty = float(enriched.loc[enriched["ticker"] == ticker, "quantity"].iloc[0])
                    qty = st.number_input("Quantity", min_value=0.0, max_value=max_qty,
                                          value=min(1.0, max_qty), step=1.0, format="%.4f")
                with c3:
                    use_live = st.checkbox("Live price ", value=True, key="sell_live")
                with c4:
                    price = st.number_input("Price ", min_value=0.0, value=0.0,
                                            format="%.2f", disabled=use_live, key="sell_price")
                submitted = st.form_submit_button("Sell", use_container_width=True)
                if submitted:
                    final_price = price
                    if use_live and ticker:
                        q = svc.get_quote(ticker)
                        final_price = q.get("price") or 0.0
                    if qty <= 0 or not final_price:
                        st.error("Provide a valid quantity and price.")
                    else:
                        ok, msg = ps.sell_stock(user["id"], ticker, qty, float(final_price))
                        (st.success if ok else st.error)(msg)
                        if ok:
                            st.rerun()

    # Holdings table + actions
    section_header("Holdings")
    if enriched.empty:
        st.info("Your portfolio is empty. Buy your first stock above.")
    else:
        display = enriched[["ticker", "quantity", "avg_price", "current_price",
                            "market_value", "pnl", "pnl_pct", "day_pct"]].copy()
        display.columns = ["Ticker", "Qty", "Avg Cost", "Price",
                           "Mkt Value", "P&L", "P&L %", "Day %"]
        for col in ["Avg Cost", "Price", "Mkt Value", "P&L"]:
            display[col] = display[col].map(lambda v: fmt_number(v, 2) if pd.notna(v) else "—")
        display["P&L %"] = display["P&L %"].map(lambda v: fmt_pct(v) if pd.notna(v) else "—")
        display["Day %"] = display["Day %"].map(lambda v: fmt_pct(v) if pd.notna(v) else "—")
        st.dataframe(display, use_container_width=True, hide_index=True)

        # Delete UI
        with st.expander("🗑️ Delete a holding"):
            del_options = enriched["ticker"].tolist()
            sel = st.selectbox("Holding to delete", del_options, key="del_pick")
            if st.button("Delete holding", key="del_btn"):
                row = enriched[enriched["ticker"] == sel].iloc[0]
                if ps.delete_holding(user["id"], int(row["id"])):
                    st.success(f"Deleted {sel} from portfolio.")
                    st.rerun()
                else:
                    st.error("Could not delete holding.")

        # Allocation pie
        section_header("Allocation")
        cL, cR = st.columns(2)
        with cL:
            alloc = enriched[["ticker", "market_value"]].copy()
            alloc = alloc[alloc["market_value"] > 0]
            if alloc.empty:
                st.info("No market value to chart yet.")
            else:
                fig = px.pie(alloc, names="ticker", values="market_value", hole=0.55,
                             color_discrete_sequence=px.colors.qualitative.Set3)
                fig.update_traces(textinfo="label+percent",
                                  hovertemplate="%{label}: %{value:,.2f}<extra></extra>")
                fig.update_layout(
                    height=340, margin=dict(l=8, r=8, t=8, b=8),
                    paper_bgcolor="#141A26", font=dict(color="#E6EAF2"),
                    showlegend=False,
                )
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        with cR:
            fig = _history_chart(user["id"])
            if fig is None:
                st.info("No transaction history yet.")
            else:
                st.markdown("**Equity Curve**")
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Transactions
    section_header("Transactions")
    tx = ps.list_transactions(user["id"], limit=50)
    if tx.empty:
        st.caption("No transactions yet.")
    else:
        tx = tx.copy()
        tx["price"] = tx["price"].map(lambda v: fmt_number(v, 2))
        tx.columns = ["Ticker", "Action", "Qty", "Price", "Executed At"]
        st.dataframe(tx, use_container_width=True, hide_index=True)
