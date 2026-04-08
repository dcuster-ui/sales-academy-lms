"""Session-based authentication for Sales Academy."""

import streamlit as st
from db.database import query


def login_page():
    """Render the login page and handle user selection."""
    st.markdown(
        """
        <div style="text-align:center; padding: 2rem 0 1rem 0;">
            <h1 style="color:#53A318; font-size:2.5rem;">Groupon Onboarding</h1>
            <p style="color:#666; font-size:1.1rem;">Sales Academy</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    users = query("SELECT id, full_name, email, role FROM users WHERE is_active = 1 ORDER BY role, full_name")
    if not users:
        st.error("No users found. Database may not be initialized.")
        return

    # Group users by role for the selector
    user_options = {}
    for u in users:
        label = f"{u['full_name']} ({u['role'].title()})"
        user_options[label] = u

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### Sign In")
        selected_label = st.selectbox(
            "Select your name",
            options=list(user_options.keys()),
            index=None,
            placeholder="Choose your account...",
        )

        if st.button("Sign In", type="primary", use_container_width=True):
            if selected_label:
                user = user_options[selected_label]
                st.session_state["authenticated"] = True
                st.session_state["user_id"] = user["id"]
                st.session_state["user_name"] = user["full_name"]
                st.session_state["user_email"] = user["email"]
                st.session_state["user_role"] = user["role"]

                # Get manager_id for reps
                full_user = query(
                    "SELECT manager_id FROM users WHERE id = ?", (user["id"],), one=True
                )
                st.session_state["manager_id"] = full_user["manager_id"] if full_user else None

                st.rerun()
            else:
                st.warning("Please select your name to sign in.")


def require_auth():
    """Check if user is authenticated. If not, show login and stop."""
    if not st.session_state.get("authenticated"):
        login_page()
        st.stop()


def require_role(allowed_roles):
    """Check if current user has an allowed role. If not, show error and stop."""
    require_auth()
    if st.session_state.get("user_role") not in allowed_roles:
        st.error("You don't have permission to access this page.")
        st.stop()


def logout():
    """Clear session state and rerun."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


def get_current_user_id():
    return st.session_state.get("user_id")


def get_current_role():
    return st.session_state.get("user_role")


def is_admin():
    return get_current_role() == "admin"


def is_manager():
    return get_current_role() == "manager"


def is_rep():
    return get_current_role() == "rep"
