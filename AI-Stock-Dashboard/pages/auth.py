"""Authentication page: login + signup tabs."""
from __future__ import annotations
import streamlit as st

from services import portfolio_service as ps


def render() -> None:
    st.markdown("## Welcome to AI Stock Dashboard")
    st.caption("Sign in to track your portfolio, watchlist, and chat with FinIQ.")

    if st.session_state.get("user"):
        u = st.session_state["user"]
        st.success(f"You are logged in as **{u['username']}** ({u['email']}).")
        if st.button("Log out"):
            st.session_state.pop("user", None)
            st.session_state.pop("chat_history", None)
            st.rerun()
        return

    tab_login, tab_signup = st.tabs(["🔐 Log in", "✨ Sign up"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email or username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log in", use_container_width=True)
            if submitted:
                user = ps.authenticate(email, password)
                if user:
                    st.session_state["user"] = user
                    st.success(f"Welcome back, {user['username']}!")
                    st.rerun()
                else:
                    st.error("Invalid credentials.")

    with tab_signup:
        with st.form("signup_form"):
            username = st.text_input("Username", key="su_user")
            email = st.text_input("Email", key="su_email")
            password = st.text_input("Password (min 6 chars)", type="password", key="su_pw")
            password2 = st.text_input("Confirm password", type="password", key="su_pw2")
            submitted = st.form_submit_button("Create account", use_container_width=True)
            if submitted:
                if password != password2:
                    st.error("Passwords do not match.")
                else:
                    ok, msg = ps.create_user(username, email, password)
                    (st.success if ok else st.error)(msg)
