"""News page powered by NewsAPI with optional Gemini summarization."""
from __future__ import annotations
import streamlit as st

from services import news_service as news
from services import ai_service as ai
from utils.ui import section_header, sentiment_badge
from utils.helpers import simple_sentiment, parse_date


CATEGORIES = ["business", "technology", "general", "science", "health", "sports", "entertainment"]


def _render_article(article: dict, idx: int) -> None:
    title = article.get("title") or "Untitled"
    desc = article.get("description") or ""
    src = (article.get("source") or {}).get("name") or "Unknown"
    url = article.get("url") or "#"
    image = article.get("urlToImage")
    published = parse_date(article.get("publishedAt"))
    sentiment = simple_sentiment(f"{title} {desc}")

    with st.container():
        col_img, col_body = st.columns([1, 3]) if image else (None, st)
        if image:
            with col_img:
                st.image(image, use_container_width=True)
            target = col_body
        else:
            target = st

        target.markdown(
            f'<div class="news-meta">{src} · {published} &nbsp; {sentiment_badge(sentiment)}</div>'
            f'<div class="news-title">{title}</div>'
            f'<div class="news-desc">{desc}</div>',
            unsafe_allow_html=True,
        )
        b1, b2 = target.columns([1, 1])
        with b1:
            target.link_button("Open Full Article ↗", url, use_container_width=True)
        with b2:
            if target.button("✨ Gemini AI Summary", key=f"sum_{idx}", use_container_width=True):
                if not ai.is_configured():
                    target.warning("Set `GOOGLE_API_KEY` in your .env to enable AI summaries.")
                else:
                    with st.spinner("Summarizing..."):
                        summary = ai.summarize_article(title, desc, article.get("content") or "")
                    if summary:
                        target.success(summary)
                    else:
                        target.warning("Could not generate summary right now.")
        target.divider()


def render() -> None:
    st.markdown("## Market News")
    st.caption("Latest financial headlines. Powered by NewsAPI.")

    if not news.is_configured():
        st.warning(
            "🔑 **NewsAPI key not configured.** Add `NEWSAPI_KEY` to your `.env` file "
            "(get a free key at https://newsapi.org). The rest of the dashboard works "
            "without it."
        )
        with st.expander("How to add the key"):
            st.code(
                "# .env\nGOOGLE_API_KEY=your_gemini_key\nNEWSAPI_KEY=your_newsapi_key\n",
                language="bash",
            )
        return

    c1, c2, c3 = st.columns([3, 1, 1])
    with c1:
        query = st.text_input("Search news", placeholder="e.g. Apple earnings, NVIDIA, oil prices", key="news_q")
    with c2:
        category = st.selectbox("Category", CATEGORIES, index=0, key="news_cat")
    with c3:
        country = st.selectbox("Country", ["us", "in", "gb", "ca", "au"], index=0, key="news_country")

    res = news.fetch_news(query=query or None, category=category, country=country)
    if res["status"] == "error":
        st.error(f"News fetch failed: {res['error']}")
        return
    articles = res.get("articles") or []
    if not articles:
        st.info("No articles found for your query. Try different keywords.")
        return

    section_header(f"{len(articles)} Articles")
    for i, a in enumerate(articles):
        _render_article(a, i)
