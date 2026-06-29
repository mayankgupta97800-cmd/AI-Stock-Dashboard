"""AI Stock Dashboard - main entrypoint.

Run with:
    streamlit run app.py
"""
from __future__ import annotations
import streamlit as st

from config import APP_NAME, APP_ICON
from database.db import init_db
from utils.ui import load_css

# Page-render modules (callables)
from views import home, stock_details, compare, news, chatbot, portfolio, watchlist, auth


# ---------------- Streamlit setup ----------------
st.set_page_config(
    page_title=APP_NAME,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com",
        "Report a bug": "https://github.com",
        "About": f"## {APP_NAME}\nAI-powered stock market dashboard built with Streamlit.",
    },
)

# Initialize DB and styles once
@st.cache_resource
def _bootstrap() -> bool:
    init_db()
    return True

_bootstrap()
load_css()


# ---------------- Sidebar (header + auth status) ----------------
with st.sidebar:
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:10px;padding:6px 0 14px 0;">
            <div style="width:34px;height:34px;border-radius:9px;
                        background:linear-gradient(135deg,#00D4A4,#005C45);
                        display:flex;align-items:center;justify-content:center;
                        font-size:18px;">{APP_ICON}</div>
            <div>
                <div class="brand-title">AI Stock</div>
                <div class="brand-sub">Dashboard</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    user = st.session_state.get("user")
    if user:
        st.markdown(
            f"""
            <div style="background:#141A26;border:1px solid rgba(255,255,255,0.06);
                        border-radius:10px;padding:10px;margin-bottom:8px;">
                <div style="font-size:0.7rem;color:#8892A6;letter-spacing:0.6px;
                            text-transform:uppercase;">Signed in as</div>
                <div style="color:#E6EAF2;font-weight:600;margin-top:2px;">{user['username']}</div>
                <div style="color:#8892A6;font-size:0.78rem;">{user['email']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("🚪 Log out", use_container_width=True):
            st.session_state.pop("user", None)
            st.session_state.pop("chat_history", None)
            st.session_state.pop("active_conversation_id", None)
            st.session_state.pop("anon_chat", None)
            st.session_state.pop("rename_target", None)
            st.rerun()
    else:
        st.caption("👋 Log in to unlock portfolio & watchlist.")

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)


# ---------------- Navigation ----------------
nav_groups = {
    "Markets": [
        st.Page(home.render, title="Dashboard", icon="📊", default=True, url_path=""),
        st.Page(stock_details.render, title="Stock Details", icon="🔎", url_path="stock"),
        st.Page(compare.render, title="Compare", icon="📐", url_path="compare"),
        st.Page(news.render, title="News", icon="📰", url_path="news"),
    ],
    "Personal": [
        st.Page(portfolio.render, title="Portfolio", icon="💼", url_path="portfolio"),
        st.Page(watchlist.render, title="Watchlist", icon="⭐", url_path="watchlist"),
    ],
    "AI": [
        st.Page(chatbot.render, title="AI Chatbot", icon="🤖", url_path="chat"),
    ],
    "Account": [
        st.Page(auth.render, title="Account", icon="🔐", url_path="account"),
    ],
}

pg = st.navigation(nav_groups, position="sidebar")
pg.run()

# Footer
st.sidebar.markdown(
    """
    <div style="margin-top:18px;padding-top:14px;border-top:1px solid rgba(255,255,255,0.06);
                color:#5C6478;font-size:0.72rem;line-height:1.5;">
        Built with Streamlit · Plotly · yfinance · Gemini
        <br/>Educational use only — not investment advice.
    </div>
    """,
    unsafe_allow_html=True,
)
