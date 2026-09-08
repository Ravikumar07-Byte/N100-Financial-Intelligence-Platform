"""
N100 Financial Intelligence Platform
Sprint 4 - Day 22
Main Streamlit application.
"""

import streamlit as st

from utils.db import get_database_info


# -------------------------------------------------------------------
# PAGE CONFIGURATION
# -------------------------------------------------------------------

st.set_page_config(
    page_title="Nifty 100 Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# -------------------------------------------------------------------
# SIDEBAR
# -------------------------------------------------------------------

st.sidebar.title("Nifty 100 Analytics")

st.sidebar.markdown(
    """
    ### Navigation

    Use the pages below to explore the N100
    Financial Intelligence Platform.
    """
)

st.sidebar.divider()

st.sidebar.info(
    "Sprint 4 — Dashboard & Valuation Module"
)


# -------------------------------------------------------------------
# HOME / SCAFFOLD LANDING PAGE
# -------------------------------------------------------------------

st.title("Nifty 100 Analytics")

st.subheader("Financial Intelligence Platform")

st.markdown(
    """
    Welcome to the **N100 Financial Intelligence Platform**.

    This Streamlit application provides a unified interface for:

    - Company profiles
    - Financial screening
    - Peer comparison
    - Trend analysis
    - Sector analysis
    - Capital allocation
    - Annual reports
    - Valuation analytics
    """
)

st.divider()


# -------------------------------------------------------------------
# DATABASE STATUS
# -------------------------------------------------------------------

st.subheader("System Status")

try:
    db_info = get_database_info()

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Companies",
            db_info["company_count"]
        )

    with col2:
        st.metric(
            "Database Tables",
            len(db_info["tables"])
        )

    st.success(
        "SQLite database connected successfully."
    )

except Exception as exc:
    st.error(
        f"Database connection failed: {exc}"
    )


st.divider()

st.caption(
    "Sprint 4 • Day 22 • Streamlit Application Scaffold"
)
