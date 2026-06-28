"""NewsAPI integration. Falls back to a friendly message when key is missing."""
from __future__ import annotations
from typing import Optional
import streamlit as st
from config import NEWSAPI_KEY


def is_configured() -> bool:
    return bool(NEWSAPI_KEY)


@st.cache_data(ttl=300, show_spinner=False)
def fetch_news(query: Optional[str] = None, category: Optional[str] = None,
               country: str = "us", page_size: int = 24) -> dict:
    """Return dict with keys: status, articles, error.

    Uses 'everything' when a search query is provided, otherwise 'top-headlines'
    filtered to business category.
    """
    if not NEWSAPI_KEY:
        return {"status": "missing_key", "articles": [], "error": "NEWSAPI_KEY not set"}

    try:
        from newsapi import NewsApiClient
        client = NewsApiClient(api_key=NEWSAPI_KEY)
        if query and query.strip():
            res = client.get_everything(
                q=query.strip(),
                language="en",
                sort_by="publishedAt",
                page_size=page_size,
            )
        else:
            res = client.get_top_headlines(
                category=category or "business",
                country=country,
                page_size=page_size,
            )
        articles = res.get("articles", []) if isinstance(res, dict) else []
        return {"status": "ok", "articles": articles, "error": None}
    except Exception as e:
        return {"status": "error", "articles": [], "error": str(e)}
