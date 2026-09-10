"""
N100 Financial Intelligence Platform
Sprint 4 - Day 23
Home Dashboard
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

import streamlit as st
import pandas as pd
import plotly.express as px

from dashboard.utils.db import (
    get_companies,
    get_ratios,
    get_sectors,
)


st.set_page_config(
    page_title="Nifty 100 Analytics",
    layout="wide",
)


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

companies = get_companies()
sectors = get_sectors()


# ---------------------------------------------------------
# SIDEBAR YEAR SELECTOR
# ---------------------------------------------------------

st.sidebar.header("Dashboard Filters")

selected_year = st.sidebar.selectbox(
    "Select Year",
    list(range(2019, 2025)),
    index=5,
)


# ---------------------------------------------------------
# LOAD RATIO DATA FOR SELECTED YEAR
# ---------------------------------------------------------

ratio_frames = []

for ticker in companies["id"].dropna().unique():
    try:
        df = get_ratios(ticker, selected_year)

        if not df.empty:
            ratio_frames.append(df)

    except Exception:
        continue


if ratio_frames:
    ratios = pd.concat(ratio_frames, ignore_index=True)
else:
    ratios = pd.DataFrame()


# ---------------------------------------------------------
# HELPER FUNCTION
# ---------------------------------------------------------

def find_column(df, possible_names):
    """Find a column using several possible names."""
    lookup = {str(col).lower(): col for col in df.columns}

    for name in possible_names:
        if name.lower() in lookup:
            return lookup[name.lower()]

    return None


def safe_median(df, column):
    if column and column in df.columns:
        values = pd.to_numeric(df[column], errors="coerce").dropna()
        if not values.empty:
            return values.median()
    return 0


def safe_mean(df, column):
    if column and column in df.columns:
        values = pd.to_numeric(df[column], errors="coerce").dropna()
        if not values.empty:
            return values.mean()
    return 0


# ---------------------------------------------------------
# IDENTIFY RATIO COLUMNS
# ---------------------------------------------------------

roe_col = find_column(
    ratios,
    ["roe", "roe_percentage", "return_on_equity"],
)

pe_col = find_column(
    ratios,
    ["pe", "pe_ratio", "p_e", "price_earnings"],
)

de_col = find_column(
    ratios,
    ["de", "d_e", "debt_equity", "debt_to_equity"],
)

revenue_cagr_col = find_column(
    ratios,
    [
        "revenue_cagr_5yr",
        "revenue_cagr_5y",
        "revenue_cagr_5",
        "revenue_cagr",
    ],
)

composite_col = find_column(
    ratios,
    [
        "composite_score",
        "composite_quality_score",
        "quality_score",
    ],
)


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

st.title("Nifty 100 Analytics")
st.caption(
    f"Financial Intelligence Dashboard — Year {selected_year}"
)


# ---------------------------------------------------------
# KPI VALUES
# ---------------------------------------------------------

average_roe = safe_mean(ratios, roe_col)
median_pe = safe_median(ratios, pe_col)
median_de = safe_median(ratios, de_col)

total_companies = len(companies)

median_revenue_cagr = safe_median(
    ratios,
    revenue_cagr_col,
)

if de_col and not ratios.empty:
    de_values = pd.to_numeric(
        ratios[de_col],
        errors="coerce",
    )

    debt_free_count = int(
        (de_values.fillna(-1) == 0).sum()
    )
else:
    debt_free_count = 0


# ---------------------------------------------------------
# SIX KPI TILES
# ---------------------------------------------------------

k1, k2, k3, k4, k5, k6 = st.columns(6)

k1.metric(
    "Average ROE",
    f"{average_roe:.2f}%",
)

k2.metric(
    "Median P/E",
    f"{median_pe:.2f}",
)

k3.metric(
    "Median D/E",
    f"{median_de:.2f}",
)

k4.metric(
    "Total Companies",
    total_companies,
)

k5.metric(
    "Median Revenue CAGR 5yr",
    f"{median_revenue_cagr:.2f}%",
)

k6.metric(
    "Debt-Free Companies",
    debt_free_count,
)


st.divider()


# ---------------------------------------------------------
# SECTOR BREAKDOWN
# ---------------------------------------------------------

left, right = st.columns([1, 1])


with left:

    st.subheader("Sector Breakdown")

    if not sectors.empty:

        sector_col = find_column(
            sectors,
            ["broad_sector", "sector"],
        )

        if sector_col:

            sector_counts = (
                sectors[sector_col]
                .dropna()
                .value_counts()
                .reset_index()
            )

            sector_counts.columns = [
                "Sector",
                "Companies",
            ]

            fig = px.pie(
                sector_counts,
                names="Sector",
                values="Companies",
                hole=0.55,
                title="Companies by Sector",
            )

            fig.update_layout(
                legend_title="Sector",
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

        else:
            st.warning(
                "Sector column was not found."
            )

    else:
        st.info("No sector data available.")


# ---------------------------------------------------------
# TOP 5 COMPANIES
# ---------------------------------------------------------

with right:

    st.subheader(
        "Top 5 Companies by Composite Quality Score"
    )

    if (
        not ratios.empty
        and composite_col
    ):

        top5 = ratios.copy()

        top5[composite_col] = pd.to_numeric(
            top5[composite_col],
            errors="coerce",
        )

        top5 = (
            top5
            .dropna(subset=[composite_col])
            .sort_values(
                composite_col,
                ascending=False,
            )
            .head(5)
        )

        company_name_map = companies.set_index(
            "id"
        )["company_name"].to_dict()

        top5["Company"] = (
            top5["company_id"]
            .map(company_name_map)
            .fillna(top5["company_id"])
        )

        display_cols = [
            "Company",
            "company_id",
            composite_col,
        ]

        display_cols = [
            col
            for col in display_cols
            if col in top5.columns
        ]

        st.dataframe(
            top5[display_cols],
            hide_index=True,
            use_container_width=True,
        )

    else:

        st.info(
            "Composite quality score data is not available yet."
        )


# ---------------------------------------------------------
# DATA SUMMARY
# ---------------------------------------------------------

st.divider()

st.subheader("Dashboard Status")

c1, c2, c3 = st.columns(3)

c1.info(
    f"Company universe: {total_companies} companies"
)

c2.info(
    f"Selected financial year: {selected_year}"
)

c3.info(
    "Dashboard data refresh: 10 minutes"
)
