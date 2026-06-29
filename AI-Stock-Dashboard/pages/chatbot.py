"""Gemini-powered chatbot with conversation memory."""
from __future__ import annotations
import streamlit as st

from services import ai_service as ai


def _seed_history() -> list[dict]:
    return [
        {"role": "assistant",
         "content": ("Hi! I'm **FinIQ** — ask me anything about stocks, "
                     "markets, valuations, or portfolio strategy. "
                     "(Educational use only, not investment advice.)")},
    ]


def _ensure_history() -> list[dict]:
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = _seed_history()
    return st.session_state.chat_history


def render() -> None:
    st.markdown("## AI Chatbot")
    st.caption("Chat with Gemini about markets, stocks, and finance.")

    if not ai.is_configured():
        st.warning(
            "🔑 **Gemini API key not configured.** Add `GOOGLE_API_KEY` to your `.env` "
            "file to enable the chatbot. Get one at https://aistudio.google.com/apikey."
        )
        with st.expander("How to add the key"):
            st.code(
                "# .env\nGOOGLE_API_KEY=your_gemini_api_key\nNEWSAPI_KEY=your_newsapi_key\n",
                language="bash",
            )
        return

    history = _ensure_history()

    c1, c2 = st.columns([6, 1])
    with c2:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.chat_history = _seed_history()
            st.rerun()

    # Render past messages
    for msg in history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("Ask about a stock, market trend, or financial concept...")
    if not prompt:
        return

    history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            reply = ai.chat_reply(history[:-1], prompt)
        if not reply:
            reply = ("I couldn't reach Gemini right now. Please double-check your API key "
                     "and try again.")
        st.markdown(reply)

    history.append({"role": "assistant", "content": reply})
