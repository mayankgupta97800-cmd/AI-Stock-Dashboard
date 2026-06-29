"""Gemini-powered chatbot with multi-conversation history persisted in SQLite.

Layout: left column = conversation list + "New chat" button.
        right column = active conversation messages + input.

Anonymous (logged-out) users still get a single in-memory session thread.
"""
from __future__ import annotations
import streamlit as st

from services import ai_service as ai
from services import chat_service as chat


WELCOME = ("Hi! I'm **FinIQ** — ask me anything about stocks, markets, valuations, "
           "or portfolio strategy. (Educational use only, not investment advice.)")


# ---------------- Anonymous (in-memory) flow ----------------

def _render_anonymous() -> None:
    st.info("💡 Log in to save your conversations across sessions.")
    if "anon_chat" not in st.session_state:
        st.session_state.anon_chat = [{"role": "assistant", "content": WELCOME}]

    c1, c2 = st.columns([6, 1])
    with c2:
        if st.button("🔄 Reset", use_container_width=True, key="anon_reset"):
            st.session_state.anon_chat = [{"role": "assistant", "content": WELCOME}]
            st.rerun()

    for msg in st.session_state.anon_chat:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("Ask about a stock, market trend, or financial concept...")
    if not prompt:
        return

    st.session_state.anon_chat.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            reply = ai.chat_reply(st.session_state.anon_chat[:-1], prompt)
        if not reply:
            reply = "I couldn't reach Gemini right now. Please try again."
        st.markdown(reply)
    st.session_state.anon_chat.append({"role": "assistant", "content": reply})


# ---------------- Authenticated (persisted) flow ----------------

def _ensure_active_conversation(user_id: int) -> int:
    """Return active conversation id; create one if none exist or none selected."""
    convos = chat.list_conversations(user_id)
    active = st.session_state.get("active_conversation_id")
    if active and any(c["id"] == active for c in convos):
        return active
    if convos:
        st.session_state["active_conversation_id"] = convos[0]["id"]
        return convos[0]["id"]
    # No conversations yet → create the first one
    new_id = chat.create_conversation(user_id, "New chat")
    chat.add_message(new_id, "assistant", WELCOME)
    st.session_state["active_conversation_id"] = new_id
    return new_id


def _render_sidebar_list(user_id: int, active_id: int) -> None:
    """Render the conversation list on the left."""
    if st.button("➕ New chat", use_container_width=True, key="new_chat_btn"):
        new_id = chat.create_conversation(user_id, "New chat")
        chat.add_message(new_id, "assistant", WELCOME)
        st.session_state["active_conversation_id"] = new_id
        st.session_state.pop("rename_target", None)
        st.rerun()

    st.markdown(
        "<div class='section-h' style='margin-top:14px'>History</div>",
        unsafe_allow_html=True,
    )

    convos = chat.list_conversations(user_id)
    if not convos:
        st.caption("No conversations yet.")
        return

    for c in convos:
        is_active = c["id"] == active_id
        cols = st.columns([5, 1])
        with cols[0]:
            label = ("● " if is_active else "  ") + c["title"]
            if st.button(label, key=f"open_conv_{c['id']}",
                         use_container_width=True,
                         type="primary" if is_active else "secondary"):
                st.session_state["active_conversation_id"] = c["id"]
                st.session_state.pop("rename_target", None)
                st.rerun()
        with cols[1]:
            if st.button("🗑", key=f"del_conv_{c['id']}",
                         help="Delete conversation", use_container_width=True):
                chat.delete_conversation(user_id, c["id"])
                if st.session_state.get("active_conversation_id") == c["id"]:
                    st.session_state.pop("active_conversation_id", None)
                st.rerun()


def _render_thread(user_id: int, conversation_id: int) -> None:
    """Render messages + input for the active conversation."""
    convos = chat.list_conversations(user_id)
    current = next((c for c in convos if c["id"] == conversation_id), None)

    # Header: title + rename
    title = current["title"] if current else "New chat"
    th1, th2 = st.columns([6, 1])
    with th1:
        st.markdown(f"### 💬 {title}")
    with th2:
        if st.button("✏️ Rename", use_container_width=True, key="rename_btn"):
            st.session_state["rename_target"] = conversation_id

    if st.session_state.get("rename_target") == conversation_id:
        with st.form("rename_form", clear_on_submit=True):
            new_title = st.text_input("New title", value=title, max_chars=80)
            r1, r2 = st.columns([1, 1])
            with r1:
                save = st.form_submit_button("Save", use_container_width=True)
            with r2:
                cancel = st.form_submit_button("Cancel", use_container_width=True)
            if save and new_title.strip():
                chat.rename_conversation(user_id, conversation_id, new_title)
                st.session_state.pop("rename_target", None)
                st.rerun()
            if cancel:
                st.session_state.pop("rename_target", None)
                st.rerun()

    # Render past messages
    messages = chat.list_messages(conversation_id)
    if not messages:
        with st.chat_message("assistant"):
            st.markdown(WELCOME)

    for m in messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    prompt = st.chat_input("Ask about a stock, market trend, or financial concept...")
    if not prompt:
        return

    # First user message → auto-title the conversation if still default
    if current and current["title"] == "New chat":
        chat.rename_conversation(user_id, conversation_id,
                                 chat.auto_title_from_message(prompt))

    chat.add_message(conversation_id, "user", prompt)
    with st.chat_message("user"):
        st.markdown(prompt)

    history = chat.list_messages(conversation_id)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            reply = ai.chat_reply(history[:-1], prompt)
        if not reply:
            reply = ("I couldn't reach Gemini right now. Please double-check your API key "
                     "and try again.")
        st.markdown(reply)
    chat.add_message(conversation_id, "assistant", reply)
    st.rerun()


# ---------------- Entry point ----------------

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

    user = st.session_state.get("user")
    if not user:
        _render_anonymous()
        return

    active_id = _ensure_active_conversation(user["id"])

    left, right = st.columns([1, 3], gap="large")
    with left:
        _render_sidebar_list(user["id"], active_id)
    with right:
        _render_thread(user["id"], active_id)
