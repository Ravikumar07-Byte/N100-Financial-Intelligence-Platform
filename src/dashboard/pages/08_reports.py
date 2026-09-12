import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DB_PATH = PROJECT_ROOT / "nifty100.db"


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Annual Reports",
    page_icon="📄",
    layout="wide",
)


# ============================================================
# TITLE
# ============================================================

st.title("📄 Annual Reports")

st.caption(
    "Search Nifty 100 companies and access available "
    "annual report documents."
)


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data(ttl=600)
def load_report_data():

    connection = sqlite3.connect(
        DB_PATH
    )

    companies = pd.read_sql_query(
        """
        SELECT
            id AS company_id,
            company_name
        FROM companies
        ORDER BY company_name
        """,
        connection,
    )

    documents = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            annual_report
        FROM documents
        ORDER BY year DESC
        """,
        connection,
    )

    connection.close()

    return companies, documents


companies, documents = load_report_data()


# ============================================================
# SIDEBAR SEARCH
# ============================================================

st.sidebar.markdown(
    "## 🔎 Company Search"
)


search_text = st.sidebar.text_input(
    "Search company or ticker",
    placeholder="Example: INFY or Infosys",
)


# ============================================================
# SEARCH
# ============================================================

filtered_companies = companies.copy()


if search_text.strip():

    query = (
        search_text
        .strip()
        .lower()
    )

    mask = (
        filtered_companies["company_id"]
        .astype(str)
        .str.lower()
        .str.contains(
            query,
            na=False,
        )
        |
        filtered_companies["company_name"]
        .astype(str)
        .str.lower()
        .str.contains(
            query,
            na=False,
        )
    )

    filtered_companies = (
        filtered_companies[mask]
    )


if filtered_companies.empty:

    st.warning(
        "Ticker not found — please try another."
    )

    st.stop()


# ============================================================
# COMPANY SELECTOR
# ============================================================

filtered_companies = (
    filtered_companies.copy()
)


filtered_companies["display_name"] = (
    filtered_companies["company_name"]
    .astype(str)
    + " ("
    + filtered_companies["company_id"]
    .astype(str)
    + ")"
)


selected_display = st.sidebar.selectbox(
    "Select Company",
    filtered_companies[
        "display_name"
    ].tolist(),
)


selected_company = filtered_companies[
    filtered_companies["display_name"]
    == selected_display
].iloc[0]


selected_company_id = (
    selected_company["company_id"]
)


selected_company_name = (
    selected_company["company_name"]
)


# ============================================================
# HEADER
# ============================================================

st.subheader(
    selected_company_name
)

st.caption(
    f"Ticker / Company ID: {selected_company_id}"
)


# ============================================================
# REPORT DATA
# ============================================================

company_reports = documents[
    documents["company_id"].astype(str)
    == str(selected_company_id)
].copy()


if company_reports.empty:

    st.info(
        "No annual reports are available "
        "for this company."
    )

    st.stop()


# ============================================================
# NORMALIZE YEAR
# ============================================================

company_reports["year_display"] = (
    company_reports["year"]
    .astype(str)
    .str[:4]
)


company_reports = (
    company_reports
    .sort_values(
        "year_display",
        ascending=False,
    )
)


# ============================================================
# SUMMARY
# ============================================================

available_year_count = (
    company_reports[
        "year_display"
    ]
    .nunique()
)


st.metric(
    "Available Report Years",
    available_year_count,
)


# ============================================================
# REPORT LIST
# ============================================================

st.subheader(
    "📚 Available Annual Reports"
)


for _, report in company_reports.iterrows():

    year = report["year_display"]

    url = report["annual_report"]


    if pd.isna(url):

        url = ""


    url = str(url).strip()


    col1, col2, col3 = st.columns(
        [1, 5, 2]
    )


    # --------------------------------------------------------
    # YEAR
    # --------------------------------------------------------

    with col1:

        st.markdown(
            f"### {year}"
        )


    # --------------------------------------------------------
    # DESCRIPTION
    # --------------------------------------------------------

    with col2:

        if url:

            st.markdown(
                f"**Annual Report {year}**"
            )

            st.caption(
                "BSE / company annual-report document"
            )

        else:

            st.markdown(
                "**Annual Report unavailable**"
            )


    # --------------------------------------------------------
    # LINK
    # --------------------------------------------------------

    with col3:

        if url:

            st.link_button(
                "📄 Open PDF",
                url,
                use_container_width=True,
            )

        else:

            st.error(
                "Report unavailable"
            )


    st.divider()


# ============================================================
# REPORT DATA
# ============================================================

with st.expander(
    "📋 View Report Data"
):

    display_df = company_reports[
        [
            "company_id",
            "year_display",
            "annual_report",
        ]
    ].copy()


    display_df = display_df.rename(
        columns={
            "company_id": "Company ID",
            "year_display": "Year",
            "annual_report": "Report URL",
        }
    )


    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )