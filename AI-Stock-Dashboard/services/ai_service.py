"""Gemini AI service: chat with memory + utility summarization helpers."""
from __future__ import annotations
from typing import Optional
import streamlit as st

from config import GOOGLE_API_KEY, GEMINI_MODEL


def is_configured() -> bool:
    return bool(GOOGLE_API_KEY)


def _get_model():
    """Configure and return a Gemini GenerativeModel, or None on failure."""
    if not GOOGLE_API_KEY:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=GOOGLE_API_KEY)
        system_instruction = (
            "You are FinIQ, a friendly financial assistant inside an AI Stock Dashboard. "
            "Answer questions about stocks, markets, financial concepts, portfolio strategy, "
            "and investing in clear, concise language. Use bullet points when helpful. "
            "Never give guaranteed investment advice—include a brief disclaimer when relevant."
        )
        return genai.GenerativeModel(GEMINI_MODEL, system_instruction=system_instruction)
    except Exception:
        return None


def generate_text(prompt: str) -> Optional[str]:
    """Single-shot generation. Returns None on failure."""
    if not prompt or not prompt.strip():
        return None
    model = _get_model()
    if model is None:
        return None
    try:
        res = model.generate_content(prompt)
        return getattr(res, "text", None) or None
    except Exception:
        return None


def summarize_article(title: str, description: str = "", content: str = "") -> Optional[str]:
    body = (description or "") + "\n" + (content or "")
    prompt = (
        f"Summarize this financial news article in 3 concise bullet points "
        f"focused on market/business impact.\n\n"
        f"Title: {title}\n\nContent:\n{body[:4000]}"
    )
    return generate_text(prompt)


def chat_reply(history: list[dict], user_message: str) -> Optional[str]:
    """Multi-turn chat. `history` is a list of {role: 'user'|'assistant', content: str}."""
    model = _get_model()
    if model is None:
        return None
    try:
        # Convert history to Gemini format
        gem_history = []
        for msg in history:
            role = "user" if msg.get("role") == "user" else "model"
            content = msg.get("content", "")
            if content:
                gem_history.append({"role": role, "parts": [content]})
        chat = model.start_chat(history=gem_history)
        res = chat.send_message(user_message)
        return getattr(res, "text", None) or None
    except Exception:
        return None
