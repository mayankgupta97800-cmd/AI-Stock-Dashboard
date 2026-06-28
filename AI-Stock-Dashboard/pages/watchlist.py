"""Watchlist page: add/remove tickers, live prices."""
from __future__ import annotations
import pandas as pd
import streamlit as st

from services import portfolio_service as ps
from services import stock_service as svc
from utils.ui import section_header
from utils.helpers import fmt_number, fmt_pct


def render() -> None:
    user = st.session_state.get("user")
    st.markdown("## Watchlist")
    if not user:
        st.warning("Please log in to use your watchlist.")
        return

    # Add form
    with st.form("watchlist_add", clear_on_submit=True):
        c1, c2 = st.columns([5, 1])
        with c1:
            ticker = st.text_input("Add ticker to watchlist",
                                   placeholder="e.g. NVDA, TCS.NS, ^NSEI")
        with c2:
            submitted = st.form_submit_button("Add", use_container_width=True)
        if submitted:
            ok, msg = ps.add_to_watchlist(user["id"], ticker)
            (st.success if ok else st.error)(msg)
            if ok:
                st.rerun()

    tickers = ps.list_watchlist(user["id"])
    if not tickers:
        st.info("Your watchlist is empty. Add a ticker above to get started.")
        return

    section_header(f"{len(tickers)} Tickers")
    quotes = svc.get_multi_quotes(tuple(tickers))

    if quotes.empty:
        st.warning("Could not load live prices right now.")
        return

    quotes = quotes.copy()
    quotes["Price"] = quotes["price"].map(lambda v: fmt_number(v, 2))
    quotes["Change"] = quotes["change"].map(lambda v: fmt_number(v, 2))
    quotes["% Change"] = quotes["pct"].map(lambda v: fmt_pct(v))
    display = quotes[["ticker", "Price", "Change", "% Change"]].rename(
        columns={"ticker": "Ticker"}
    )
    st.dataframe(display, use_container_width=True, hide_index=True)

    # Per-ticker remove buttons
    with st.expander("Manage watchlist"):
        for t in tickers:
            c1, c2 = st.columns([5, 1])
            with c1:
                st.write(f"**{t}**")
            with c2:
                if st.button("Remove", key=f"rm_{t}", use_container_width=True):
                    ps.remove_from_watchlist(user["id"], t)
                    st.rerun()
