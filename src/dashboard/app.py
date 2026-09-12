"""
N100 Financial Intelligence Platform
Sprint 4 - Main Streamlit Application

Main Streamlit entry point for the N100 Financial Intelligence
Platform.

Sprint 4 includes:

1. Home
2. Company Profile
3. Company Screener
4. Peer Comparison
5. Trend Analysis
6. Sector Analysis
7. Capital Allocation
8. Annual Reports

The visual design follows the institutional-style N100 Analytics
reference while all data and functionality remain connected to
the existing Streamlit application.
"""

from pathlib import Path
import sys

import streamlit as st


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Nifty 100 Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# GLOBAL APPLICATION CSS
# ============================================================

GLOBAL_CSS = """
<style>

/* ============================================================
   N100 DESIGN SYSTEM
   ============================================================ */

:root {
    --page: #f5f7fa;
    --card: #ffffff;
    --border: #dfe6ef;

    --text: #111a2d;
    --muted: #68778e;

    --blue: #2563eb;
    --blue-active: #2d6df3;

    --green: #00b889;
    --red: #ef5350;

    --sidebar: #080f1f;
    --sidebar-border: #1b2638;
}


/* ============================================================
   GLOBAL FONT
   ============================================================ */

html,
body,
[class*="css"] {
    font-family:
        Inter,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        Roboto,
        Helvetica,
        Arial,
        sans-serif;
}


/* ============================================================
   APPLICATION BACKGROUND
   ============================================================ */

.stApp {
    background: var(--page) !important;
}

[data-testid="stAppViewContainer"] {
    background: var(--page) !important;
}

.main {
    background: var(--page) !important;
}


/* ============================================================
   MAIN CONTENT CONTAINER
   ============================================================ */

.block-container {
    max-width: 1500px !important;

    padding-top: 28px !important;
    padding-bottom: 40px !important;

    padding-left: 28px !important;
    padding-right: 28px !important;
}


/* ============================================================
   HIDE DEFAULT STREAMLIT MENU / FOOTER
   ============================================================ */

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}


/* ============================================================
   STREAMLIT HEADER
   ============================================================ */

header[data-testid="stHeader"] {
    background: transparent !important;
}


/* ============================================================
   REMOVE DEFAULT NAVIGATION AREA
   ============================================================ */

/*
The actual navigation is handled by:

    st.navigation(..., position="hidden")

and the visible links are rendered by sidebar.py.
*/


/* ============================================================
   GENERAL HEADINGS
   ============================================================ */

h1,
h2,
h3,
h4,
h5,
h6 {
    color: var(--text);
}


/* ============================================================
   STREAMLIT METRIC CARDS
   ============================================================ */

[data-testid="stMetric"] {

    background: #ffffff !important;

    border:
        1px solid
        var(--border) !important;

    border-radius:
        10px !important;

    padding:
        13px !important;

    min-height:
        105px !important;

    box-shadow:
        0 1px 3px
        rgba(15, 23, 42, 0.025) !important;
}


/* Metric label */

[data-testid="stMetricLabel"] {

    color:
        #5c6c83 !important;

    font-size:
        9px !important;

    font-weight:
        800 !important;
}


/* Metric value */

[data-testid="stMetricValue"] {

    color:
        #111a2d !important;

    font-size:
        24px !important;

    font-weight:
        800 !important;
}


/* Metric delta */

[data-testid="stMetricDelta"] {

    font-size:
        9px !important;
}


/* ============================================================
   DATAFRAME
   ============================================================ */

[data-testid="stDataFrame"] {

    border:
        1px solid
        var(--border) !important;

    border-radius:
        9px !important;

    overflow:
        hidden !important;
}


/* ============================================================
   PLOTLY CHART CONTAINER
   ============================================================ */

[data-testid="stPlotlyChart"] {

    background:
        #ffffff !important;

    border:
        1px solid
        var(--border) !important;

    border-radius:
        10px !important;

    padding:
        3px !important;

    box-shadow:
        0 1px 3px
        rgba(15, 23, 42, 0.025) !important;

    overflow:
        hidden !important;
}


/* ============================================================
   INPUTS
   ============================================================ */

div[data-baseweb="select"] > div {

    border-radius:
        7px !important;

    border-color:
        var(--border) !important;

    background:
        #ffffff !important;
}


div[data-baseweb="input"] > div {

    border-radius:
        7px !important;

    border-color:
        var(--border) !important;

    background:
        #ffffff !important;
}


/* ============================================================
   TEXT INPUT
   ============================================================ */

.stTextInput input {

    color:
        #111a2d !important;

    background:
        #ffffff !important;

    border-radius:
        7px !important;
}


/* ============================================================
   SELECTBOX TEXT
   ============================================================ */

div[data-baseweb="select"] span {

    color:
        #111a2d;
}


/* ============================================================
   BUTTONS
   ============================================================ */

.stButton > button {

    border:
        1px solid
        #dbe3ee !important;

    border-radius:
        7px !important;

    background:
        #ffffff !important;

    color:
        #334155 !important;

    font-weight:
        650 !important;

    min-height:
        36px !important;
}


.stButton > button:hover {

    border-color:
        #b9c7da !important;

    background:
        #f8fafc !important;
}


/* ============================================================
   DOWNLOAD BUTTON
   ============================================================ */

.stDownloadButton > button {

    border-radius:
        7px !important;

    font-weight:
        650 !important;
}


/* ============================================================
   EXPANDERS
   ============================================================ */

[data-testid="stExpander"] {

    background:
        #ffffff !important;

    border:
        1px solid
        var(--border) !important;

    border-radius:
        9px !important;
}


/* ============================================================
   ALERTS
   ============================================================ */

[data-testid="stAlert"] {

    border-radius:
        8px !important;
}


/* ============================================================
   LINKS
   ============================================================ */

a {
    color:
        var(--blue);
}


/* ============================================================
   HORIZONTAL RULE
   ============================================================ */

hr {

    border:
        none !important;

    border-top:
        1px solid
        var(--border) !important;

    margin:
        18px 0 !important;
}


/* ============================================================
   RESPONSIVE
   ============================================================ */

@media (max-width: 1000px) {

    .block-container {

        padding-left:
            16px !important;

        padding-right:
            16px !important;
    }
}

</style>
"""


st.markdown(
    GLOBAL_CSS,
    unsafe_allow_html=True,
)


# ============================================================
# PAGE DEFINITIONS
# ============================================================

# ------------------------------------------------------------
# 1. HOME
# ------------------------------------------------------------

home_page = st.Page(
    "pages/01_home.py",
    title="Home",
    icon=":material/home:",
    url_path="home",
)


# ------------------------------------------------------------
# 2. COMPANY PROFILE
# ------------------------------------------------------------

profile_page = st.Page(
    "pages/02_profile.py",
    title="Company Profile",
    icon=":material/business:",
    url_path="profile",
)


# ------------------------------------------------------------
# 3. COMPANY SCREENER
# ------------------------------------------------------------

screener_page = st.Page(
    "pages/03_screener.py",
    title="Company Screener",
    icon=":material/tune:",
    url_path="screener",
)


# ------------------------------------------------------------
# 4. PEER COMPARISON
# ------------------------------------------------------------

peers_page = st.Page(
    "pages/04_peers.py",
    title="Peer Comparison",
    icon=":material/compare_arrows:",
    url_path="peers",
)


# ------------------------------------------------------------
# 5. TREND ANALYSIS
# ------------------------------------------------------------

trends_page = st.Page(
    "pages/05_trends.py",
    title="Trend Analysis",
    icon=":material/trending_up:",
    url_path="trends",
)


# ------------------------------------------------------------
# 6. SECTOR ANALYSIS
# ------------------------------------------------------------

sectors_page = st.Page(
    "pages/06_sectors.py",
    title="Sector Analysis",
    icon=":material/pie_chart:",
    url_path="sectors",
)


# ------------------------------------------------------------
# 7. CAPITAL ALLOCATION
# ------------------------------------------------------------

capital_page = st.Page(
    "pages/07_capital.py",
    title="Capital Allocation",
    icon=":material/payments:",
    url_path="capital",
)


# ------------------------------------------------------------
# 8. ANNUAL REPORTS
# ------------------------------------------------------------

reports_page = st.Page(
    "pages/08_reports.py",
    title="Annual Reports",
    icon=":material/article:",
    url_path="reports",
)


# ============================================================
# NAVIGATION REGISTRY
# ============================================================

pages = {

    "MAIN": [
        home_page,
        screener_page,
        profile_page,
    ],

    "ANALYSIS": [
        peers_page,
        trends_page,
        sectors_page,
        capital_page,
    ],

    "REPORTS": [
        reports_page,
    ],
}


# ============================================================
# HIDDEN STREAMLIT NAVIGATION
# ============================================================

"""
We hide Streamlit's default navigation because we are rendering
our own institutional-style navigation inside sidebar.py.
"""

pg = st.navigation(
    pages,
    position="hidden",
)


# ============================================================
# IMPORT CUSTOM SIDEBAR
# ============================================================

from dashboard.sidebar import render_sidebar


# ============================================================
# RENDER CUSTOM SIDEBAR
# ============================================================

render_sidebar(
    home_page=home_page,
    profile_page=profile_page,
    screener_page=screener_page,
    peers_page=peers_page,
    trends_page=trends_page,
    sectors_page=sectors_page,
    capital_page=capital_page,
    reports_page=reports_page,
)


# ============================================================
# RUN SELECTED PAGE
# ============================================================

pg.run()