"""Shared sidebar component."""

import streamlit as st
from auth.auth import logout, get_current_role
from utils.constants import ROLE_LABELS, ROLE_ICONS


def render_sidebar():
    """Render the sidebar with user info and navigation."""
    with st.sidebar:
        role = get_current_role()
        st.markdown(
            f"""
            <div style="padding: 0.5rem 0; border-bottom: 1px solid #ddd; margin-bottom: 1rem;">
                <div style="font-size: 0.85rem; color: #888;">Signed in as</div>
                <div style="font-size: 1.1rem; font-weight: 600;">{ROLE_ICONS.get(role, '')} {st.session_state.get('user_name', '')}</div>
                <div style="font-size: 0.8rem; color: #53A318; font-weight: 500;">{ROLE_LABELS.get(role, role)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("Sign Out", use_container_width=True):
            logout()
