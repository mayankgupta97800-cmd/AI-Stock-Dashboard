"""Auth + Portfolio + Watchlist business logic on top of SQLite."""
from __future__ import annotations
from typing import Optional
import bcrypt
import pandas as pd

from database.db import cursor


# ---------------- Users ----------------

def create_user(username: str, email: str, password: str) -> tuple[bool, str]:
    username = (username or "").strip()
    email = (email or "").strip().lower()
    if not username or not email or not password:
        return False, "All fields are required."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    try:
        with cursor() as c:
            c.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                (username, email, pw_hash),
            )
        return True, "Account created. Please log in."
    except Exception as e:
        msg = str(e).lower()
        if "unique" in msg:
            return False, "Username or email already exists."
        return False, "Could not create account."


def authenticate(email_or_username: str, password: str) -> Optional[dict]:
    if not email_or_username or not password:
        return None
    key = email_or_username.strip().lower()
    try:
        with cursor() as c:
            c.execute(
                "SELECT id, username, email, password_hash FROM users "
                "WHERE lower(email) = ? OR lower(username) = ?",
                (key, key),
            )
            row = c.fetchone()
        if not row:
            return None
        if bcrypt.checkpw(password.encode("utf-8"), row["password_hash"]):
            return {"id": row["id"], "username": row["username"], "email": row["email"]}
        return None
    except Exception:
        return None


# ---------------- Portfolio ----------------

def list_holdings(user_id: int) -> pd.DataFrame:
    with cursor() as c:
        c.execute(
            "SELECT id, ticker, quantity, avg_price, created_at FROM portfolio "
            "WHERE user_id = ? ORDER BY ticker",
            (user_id,),
        )
        rows = [dict(r) for r in c.fetchall()]
    return pd.DataFrame(rows)


def buy_stock(user_id: int, ticker: str, quantity: float, price: float) -> tuple[bool, str]:
    ticker = (ticker or "").strip().upper()
    if not ticker or quantity <= 0 or price <= 0:
        return False, "Provide a valid ticker, quantity and price."
    try:
        with cursor() as c:
            c.execute(
                "SELECT id, quantity, avg_price FROM portfolio WHERE user_id = ? AND ticker = ?",
                (user_id, ticker),
            )
            row = c.fetchone()
            if row:
                new_qty = row["quantity"] + quantity
                new_avg = ((row["quantity"] * row["avg_price"]) + (quantity * price)) / new_qty
                c.execute(
                    "UPDATE portfolio SET quantity = ?, avg_price = ? WHERE id = ?",
                    (new_qty, new_avg, row["id"]),
                )
            else:
                c.execute(
                    "INSERT INTO portfolio (user_id, ticker, quantity, avg_price) VALUES (?, ?, ?, ?)",
                    (user_id, ticker, quantity, price),
                )
            c.execute(
                "INSERT INTO transactions (user_id, ticker, action, quantity, price) "
                "VALUES (?, ?, 'BUY', ?, ?)",
                (user_id, ticker, quantity, price),
            )
        return True, f"Bought {quantity} {ticker} @ {price:.2f}"
    except Exception:
        return False, "Could not record buy."


def sell_stock(user_id: int, ticker: str, quantity: float, price: float) -> tuple[bool, str]:
    ticker = (ticker or "").strip().upper()
    if not ticker or quantity <= 0 or price <= 0:
        return False, "Provide a valid ticker, quantity and price."
    try:
        with cursor() as c:
            c.execute(
                "SELECT id, quantity, avg_price FROM portfolio WHERE user_id = ? AND ticker = ?",
                (user_id, ticker),
            )
            row = c.fetchone()
            if not row:
                return False, f"You don't hold any {ticker}."
            if quantity > row["quantity"] + 1e-9:
                return False, f"You only hold {row['quantity']} {ticker}."
            new_qty = row["quantity"] - quantity
            if new_qty <= 1e-9:
                c.execute("DELETE FROM portfolio WHERE id = ?", (row["id"],))
            else:
                c.execute("UPDATE portfolio SET quantity = ? WHERE id = ?", (new_qty, row["id"]))
            c.execute(
                "INSERT INTO transactions (user_id, ticker, action, quantity, price) "
                "VALUES (?, ?, 'SELL', ?, ?)",
                (user_id, ticker, quantity, price),
            )
        return True, f"Sold {quantity} {ticker} @ {price:.2f}"
    except Exception:
        return False, "Could not record sell."


def delete_holding(user_id: int, holding_id: int) -> bool:
    try:
        with cursor() as c:
            c.execute("DELETE FROM portfolio WHERE id = ? AND user_id = ?", (holding_id, user_id))
        return True
    except Exception:
        return False


def list_transactions(user_id: int, limit: int = 50) -> pd.DataFrame:
    with cursor() as c:
        c.execute(
            "SELECT ticker, action, quantity, price, executed_at FROM transactions "
            "WHERE user_id = ? ORDER BY executed_at DESC LIMIT ?",
            (user_id, limit),
        )
        rows = [dict(r) for r in c.fetchall()]
    return pd.DataFrame(rows)


# ---------------- Watchlist ----------------

def list_watchlist(user_id: int) -> list[str]:
    with cursor() as c:
        c.execute(
            "SELECT ticker FROM watchlist WHERE user_id = ? ORDER BY added_at DESC",
            (user_id,),
        )
        return [r["ticker"] for r in c.fetchall()]


def add_to_watchlist(user_id: int, ticker: str) -> tuple[bool, str]:
    ticker = (ticker or "").strip().upper()
    if not ticker:
        return False, "Provide a valid ticker."
    try:
        with cursor() as c:
            c.execute(
                "INSERT OR IGNORE INTO watchlist (user_id, ticker) VALUES (?, ?)",
                (user_id, ticker),
            )
        return True, f"{ticker} added to watchlist."
    except Exception:
        return False, "Could not add to watchlist."


def remove_from_watchlist(user_id: int, ticker: str) -> bool:
    ticker = (ticker or "").strip().upper()
    try:
        with cursor() as c:
            c.execute(
                "DELETE FROM watchlist WHERE user_id = ? AND ticker = ?",
                (user_id, ticker),
            )
        return True
    except Exception:
        return False
