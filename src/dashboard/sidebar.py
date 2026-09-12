"""
N100 Analytics - Sprint 4
Custom Institutional-Style Sidebar
"""

import streamlit as st


# ============================================================
# SIDEBAR CSS
# ============================================================

SIDEBAR_CSS = """
<style>

/* =========================================================
   SIDEBAR CONTAINER
   ========================================================= */

section[data-testid="stSidebar"] {
    background: #080f1f !important;
    border-right: 1px solid #1b2638 !important;
    min-width: 255px !important;
    max-width: 255px !important;
}

section[data-testid="stSidebar"] > div:first-child {
    padding: 18px 17px 15px 17px !important;
}


/* =========================================================
   BRAND
   ========================================================= */

.n100-brand {
    padding: 3px 1px 17px 1px;
    margin-bottom: 16px;
    border-bottom: 1px solid #1b2638;
}

.n100-brand-title {
    color: #ffffff !important;
    font-size: 15px !important;
    font-weight: 800 !important;
    line-height: 1.2 !important;
    margin: 0 !important;
    padding: 0 !important;
}

.n100-brand-subtitle {
    color: #61718a !important;
    font-size: 8px !important;
    font-weight: 600 !important;
    letter-spacing: 0.07em !important;
    margin-top: 5px !important;
    line-height: 1.3 !important;
}

.n100-status {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    margin-top: 13px;
    padding: 5px 10px;
    border: 1px solid rgba(0, 201, 149, 0.25);
    border-radius: 999px;
    background: rgba(0, 201, 149, 0.07);
    color: #00c995 !important;
    font-size: 8px !important;
    font-weight: 700 !important;
    line-height: 1 !important;
}

.n100-status-dot {
    width: 6px;
    height: 6px;
    min-width: 6px;
    border-radius: 50%;
    background: #00c995;
}


/* =========================================================
   SECTION TITLES
   ========================================================= */

.n100-section-title {
    color: #52627b !important;
    font-size: 8px !important;
    font-weight: 800 !important;
    letter-spacing: 0.09em !important;
    margin: 13px 2px 5px 2px !important;
    line-height: 1.2 !important;
}


/* =========================================================
   STREAMLIT PAGE LINKS
   ========================================================= */

section[data-testid="stSidebar"] .stPageLink {
    margin: 2px 0 !important;
    padding: 0 !important;
}

section[data-testid="stSidebar"] .stPageLink a {
    width: 100% !important;
    min-height: 35px !important;
    box-sizing: border-box !important;

    padding: 0 11px !important;
    margin: 0 !important;

    border-radius: 7px !important;

    background: transparent !important;
    color: #8190a8 !important;

    text-decoration: none !important;

    font-size: 12px !important;
    font-weight: 500 !important;

    transition:
        background 0.15s ease,
        color 0.15s ease !important;
}


/* =========================================================
   NAVIGATION TEXT
   ========================================================= */

section[data-testid="stSidebar"] .stPageLink a span {
    color: #8190a8 !important;
    font-size: 12px !important;
    font-weight: 500 !important;
}


/* =========================================================
   NAVIGATION ICONS
   ========================================================= */

section[data-testid="stSidebar"] .stPageLink a svg {
    width: 15px !important;
    height: 15px !important;

    margin-right: 9px !important;

    color: #7890ad !important;
    fill: currentColor !important;
}


/* =========================================================
   HOVER STATE
   ========================================================= */

section[data-testid="stSidebar"] .stPageLink a:hover {
    background: rgba(45, 109, 243, 0.12) !important;
}

section[data-testid="stSidebar"] .stPageLink a:hover span {
    color: #ffffff !important;
}

section[data-testid="stSidebar"] .stPageLink a:hover svg {
    color: #ffffff !important;
    fill: currentColor !important;
}


/* =========================================================
   ACTIVE PAGE
   BLUE BACKGROUND
   WHITE TEXT
   WHITE ICON
   ========================================================= */

section[data-testid="stSidebar"] .stPageLink a[aria-current="page"] {
    background: #5b8def !important;
    color: #ffffff !important;

    border-radius: 7px !important;

    font-weight: 700 !important;

    box-shadow: 0 2px 8px rgba(45, 109, 243, 0.28) !important;
}

section[data-testid="stSidebar"] .stPageLink a[aria-current="page"] span {
    color: #ffffff !important;
    font-weight: 700 !important;
}

section[data-testid="stSidebar"] .stPageLink a[aria-current="page"] svg {
    color: #ffffff !important;
    fill: currentColor !important;
}


/* =========================================================
   DIVIDER
   ========================================================= */

.n100-divider {
    height: 1px;
    width: 100%;

    background: #1b2638;

    margin: 14px 0;
}


/* =========================================================
   YEAR LABEL
   ========================================================= */

.n100-year-label {
    color: #52627b !important;
    font-size: 8px !important;
    font-weight: 800 !important;

    letter-spacing: 0.09em !important;

    margin: 8px 2px 6px 2px !important;
}


/* =========================================================
   YEAR SELECTBOX
   ========================================================= */

section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
    background: #101a2d !important;

    border: 1px solid #26344b !important;

    border-radius: 6px !important;

    min-height: 34px !important;
}

section[data-testid="stSidebar"] div[data-baseweb="select"] span {
    color: #cbd5e1 !important;

    font-size: 11px !important;
}


/* =========================================================
   FOOTER
   ========================================================= */

.n100-footer {
    margin-top: 14px;

    padding: 13px 2px 4px 2px;

    border-top: 1px solid #1b2638;

    color: #64748b !important;

    font-size: 8px !important;

    line-height: 1.65 !important;
}

.n100-footer-title {
    color: #aeb9ca !important;

    font-size: 8px !important;

    font-weight: 800 !important;
}

.n100-version {
    display: inline-block;

    margin-top: 6px;

    padding: 2px 5px;

    border-radius: 3px;

    background: #18243a;

    color: #aeb9ca !important;

    font-size: 7px !important;

    font-weight: 700 !important;
}


/* =========================================================
   REMOVE DEFAULT STREAMLIT SIDEBAR ELEMENTS
   ========================================================= */

section[data-testid="stSidebar"] [data-testid="stSidebarNav"] {
    display: none !important;
}

</style>
"""


# ============================================================
# SIDEBAR RENDER FUNCTION
# ============================================================

def render_sidebar(
    home_page,
    profile_page,
    screener_page,
    peers_page,
    trends_page,
    sectors_page,
    capital_page,
    reports_page,
):
    """
    Render the complete N100 Analytics sidebar.

    This file is responsible only for:
    - Sidebar styling
    - Sidebar branding
    - Navigation links
    - Financial year selector
    - Sidebar footer
    """

    # --------------------------------------------------------
    # Inject CSS
    # --------------------------------------------------------

    st.markdown(
        SIDEBAR_CSS,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # Sidebar
    # --------------------------------------------------------

    with st.sidebar:

        # ====================================================
        # BRAND
        # ====================================================

        st.markdown(
            """
<div class="n100-brand">
    <div class="n100-brand-title">N100 ANALYTICS</div>
    <div class="n100-brand-subtitle">FINANCIAL INTELLIGENCE PLATFORM</div>
    <div class="n100-status"><span class="n100-status-dot"></span>System Online</div>
</div>
""",
            unsafe_allow_html=True,
        )

        # ====================================================
        # MAIN
        # ====================================================

        st.markdown(
            '<div class="n100-section-title">MAIN</div>',
            unsafe_allow_html=True,
        )

        st.page_link(
            home_page,
            label="Home",
            icon=":material/home:",
        )

        st.page_link(
            screener_page,
            label="Company Screener",
            icon=":material/tune:",
        )

        st.page_link(
            profile_page,
            label="Company Profile",
            icon=":material/business:",
        )

        # ====================================================
        # ANALYSIS
        # ====================================================

        st.markdown(
            '<div class="n100-section-title">ANALYSIS</div>',
            unsafe_allow_html=True,
        )

        st.page_link(
            peers_page,
            label="Peer Comparison",
            icon=":material/compare_arrows:",
        )

        st.page_link(
            trends_page,
            label="Trend Analysis",
            icon=":material/trending_up:",
        )

        st.page_link(
            sectors_page,
            label="Sector Analysis",
            icon=":material/pie_chart:",
        )

        st.page_link(
            capital_page,
            label="Capital Allocation",
            icon=":material/payments:",
        )

        # ====================================================
        # REPORTS
        # ====================================================

        st.markdown(
            '<div class="n100-section-title">REPORTS</div>',
            unsafe_allow_html=True,
        )

        st.page_link(
            reports_page,
            label="Annual Reports",
            icon=":material/article:",
        )

        # ====================================================
        # DIVIDER
        # ====================================================

        st.markdown(
            '<div class="n100-divider"></div>',
            unsafe_allow_html=True,
        )

        # ====================================================
        # FINANCIAL YEAR
        # ====================================================

        st.markdown(
            '<div class="n100-year-label">FINANCIAL YEAR</div>',
            unsafe_allow_html=True,
        )

        st.selectbox(
            "Financial Year",
            options=list(range(2019, 2025)),
            index=5,
            key="dashboard_year",
            label_visibility="collapsed",
        )

        selected_year = st.session_state.get(
            "dashboard_year",
            2024,
        )

        # ====================================================
        # FOOTER
        # ====================================================

        st.markdown(
            f"""
<div class="n100-footer">
    <div class="n100-footer-title">NIFTY 100 UNIVERSE</div>
    92 Companies Tracked<br>
    Financial Year: {selected_year}<br>
    Last Updated: Sep 12, 2026<br>
    <span class="n100-version">v3.2.1</span>
</div>
""",
            unsafe_allow_html=True,
        )