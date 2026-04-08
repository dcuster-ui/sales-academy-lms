"""Sales Academy — Main entry point."""

import streamlit as st
from db.database import init_db
from auth.auth import require_auth
from components.sidebar import render_sidebar

st.set_page_config(
    page_title="Sales Academy",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
    <style>
        .block-container { padding-top: 1rem; }
        [data-testid="stMetric"] {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 12px 16px;
        }
        [data-testid="stMetricValue"] { font-size: 1.8rem; }
        .stTabs [data-baseweb="tab-list"] { gap: 8px; }
        .stTabs [data-baseweb="tab"] {
            padding: 8px 16px;
            border-radius: 4px 4px 0 0;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize database on first run
init_db()

# Auth check
require_auth()

# Sidebar
render_sidebar()

# Redirect to dashboard
st.switch_page("pages/1_Dashboard.py")
