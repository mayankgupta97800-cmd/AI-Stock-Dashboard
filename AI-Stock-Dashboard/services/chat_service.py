"""Chat conversation persistence: SQLite-backed multi-thread history per user."""
from __future__ import annotations
from typing import Optional

from database.db import cursor


# ---------------- Conversations ----------------

def list_conversations(user_id: int) -> list[dict]:
    """Return user's conversations ordered by most-recently-updated."""
    with cursor() as c:
        c.execute(
            "SELECT id, title, created_at, updated_at FROM conversations "
            "WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,),
        )
        return [dict(r) for r in c.fetchall()]


def create_conversation(user_id: int, title: str = "New chat") -> int:
    """Create a new conversation. Returns the conversation id."""
    title = (title or "New chat").strip()[:80] or "New chat"
    with cursor() as c:
        c.execute(
            "INSERT INTO conversations (user_id, title) VALUES (?, ?)",
            (user_id, title),
        )
        return int(c.lastrowid)


def rename_conversation(user_id: int, conversation_id: int, title: str) -> bool:
    title = (title or "").strip()[:80]
    if not title:
        return False
    try:
        with cursor() as c:
            c.execute(
                "UPDATE conversations SET title = ?, "
                "updated_at = CURRENT_TIMESTAMP "
                "WHERE id = ? AND user_id = ?",
                (title, conversation_id, user_id),
            )
        return True
    except Exception:
        return False


def delete_conversation(user_id: int, conversation_id: int) -> bool:
    try:
        with cursor() as c:
            c.execute(
                "DELETE FROM conversations WHERE id = ? AND user_id = ?",
                (conversation_id, user_id),
            )
        return True
    except Exception:
        return False


def touch_conversation(conversation_id: int) -> None:
    """Bump updated_at so it floats to the top of the conversation list."""
    try:
        with cursor() as c:
            c.execute(
                "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (conversation_id,),
            )
    except Exception:
        pass


# ---------------- Messages ----------------

def list_messages(conversation_id: int) -> list[dict]:
    """Return chronological list of {role, content} for a conversation."""
    with cursor() as c:
        c.execute(
            "SELECT role, content FROM chat_messages "
            "WHERE conversation_id = ? ORDER BY id ASC",
            (conversation_id,),
        )
        return [dict(r) for r in c.fetchall()]


def add_message(conversation_id: int, role: str, content: str) -> Optional[int]:
    if role not in ("user", "assistant"):
        return None
    content = (content or "").strip()
    if not content:
        return None
    try:
        with cursor() as c:
            c.execute(
                "INSERT INTO chat_messages (conversation_id, role, content) "
                "VALUES (?, ?, ?)",
                (conversation_id, role, content),
            )
            mid = int(c.lastrowid)
        touch_conversation(conversation_id)
        return mid
    except Exception:
        return None


def auto_title_from_message(message: str) -> str:
    """Build a short, presentable title from the user's first message."""
    msg = (message or "").strip().replace("\n", " ")
    if not msg:
        return "New chat"
    # Keep first ~6 words and cap to 60 chars
    words = msg.split()
    title = " ".join(words[:8])
    if len(title) > 60:
        title = title[:60].rstrip() + "…"
    return title or "New chat"


def conversation_owned_by(user_id: int, conversation_id: int) -> bool:
    with cursor() as c:
        c.execute(
            "SELECT 1 FROM conversations WHERE id = ? AND user_id = ?",
            (conversation_id, user_id),
        )
        return c.fetchone() is not None
