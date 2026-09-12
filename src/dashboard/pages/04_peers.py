"""
N100 Financial Intelligence Platform
Sprint 4 - Day 24
Peer Comparison Dashboard

Features:
- All 11 peer groups
- Benchmark company selection
- 8-metric radar chart
- Peer-group average
- Side-by-side KPI comparison
- Benchmark row highlighting
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


# =========================================================
# PROJECT PATH
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


# =========================================================
# DATABASE FUNCTIONS
# =========================================================

from dashboard.utils.db import (
    get_companies,
    get_all_ratios,
    get_peers,
    get_peer_groups,
)


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Peer Comparison",
    page_icon="👥",
    layout="wide",
)


# =========================================================
# PAGE HEADER
# =========================================================

st.title("👥 Peer Comparison")

st.caption(
    "Compare Nifty 100 companies against their "
    "assigned peer groups."
)


# =========================================================
# LOAD DATA
# =========================================================

companies = get_companies()

ratios = get_all_ratios(2024)

peer_groups = get_peer_groups()

peer_data = get_peers()


if companies.empty:
    st.error("Company data is unavailable.")
    st.stop()


if ratios.empty:
    st.error("Financial ratio data is unavailable.")
    st.stop()


if not peer_groups:
    st.error("No peer groups are available.")
    st.stop()


if peer_data.empty:
    st.error("Peer assignment data is unavailable.")
    st.stop()


# =========================================================
# COMPANY INFORMATION
# =========================================================

company_info = companies[
    [
        "id",
        "company_name",
    ]
].copy()

company_info = company_info.rename(
    columns={
        "id": "company_id"
    }
)

company_info["company_id"] = (
    company_info["company_id"]
    .astype(str)
)


ratios["company_id"] = (
    ratios["company_id"]
    .astype(str)
)


# =========================================================
# SECTOR INFORMATION
# =========================================================

try:

    import sqlite3

    connection = sqlite3.connect(
        str(PROJECT_ROOT / "nifty100.db")
    )

    sector_data = pd.read_sql_query(
        """
        SELECT
            company_id,
            broad_sector,
            sub_sector
        FROM sectors
        """,
        connection,
    )

    connection.close()

    sector_data["company_id"] = (
        sector_data["company_id"]
        .astype(str)
    )

    sector_data = sector_data.drop_duplicates(
        subset=["company_id"]
    )

except Exception:

    sector_data = pd.DataFrame(
        columns=[
            "company_id",
            "broad_sector",
            "sub_sector",
        ]
    )


# =========================================================
# MERGE COMPANY + RATIO DATA
# =========================================================

df = ratios.merge(
    company_info,
    on="company_id",
    how="left",
)


df = df.merge(
    sector_data,
    on="company_id",
    how="left",
)


# =========================================================
# PEER GROUP SELECTOR
# =========================================================

st.sidebar.header("👥 Peer Group")

selected_group = st.sidebar.selectbox(
    "Select Peer Group",
    peer_groups,
)


# =========================================================
# GET SELECTED PEER GROUP
# =========================================================

selected_peer_data = peer_data[
    peer_data["peer_group_name"]
    == selected_group
].copy()


if selected_peer_data.empty:

    st.warning(
        "No companies are assigned to this peer group."
    )

    st.stop()


# =========================================================
# PEER COMPANY IDS
# =========================================================

selected_peer_data["company_id"] = (
    selected_peer_data["company_id"]
    .astype(str)
)


peer_company_ids = (
    selected_peer_data["company_id"]
    .unique()
    .tolist()
)


group_df = df[
    df["company_id"].isin(
        peer_company_ids
    )
].copy()


if group_df.empty:

    st.warning(
        "Financial data is unavailable for this peer group."
    )

    st.stop()


# =========================================================
# BENCHMARK INFORMATION
# =========================================================

benchmark_rows = selected_peer_data[
    selected_peer_data["is_benchmark"] == 1
]


if benchmark_rows.empty:

    benchmark_rows = selected_peer_data.iloc[:1]


benchmark_ids = (
    benchmark_rows["company_id"]
    .astype(str)
    .tolist()
)


# =========================================================
# COMPANY DISPLAY NAMES
# =========================================================

name_lookup = {}

for _, row in group_df.iterrows():

    ticker = str(
        row["company_id"]
    )

    company_name = row.get(
        "company_name",
        ticker,
    )

    if pd.isna(company_name):

        company_name = ticker

    name_lookup[ticker] = (
        f"{ticker} — {company_name}"
    )


# =========================================================
# COMPANY SELECTOR
# =========================================================

default_company = benchmark_ids[0]

if default_company not in name_lookup:

    default_company = list(
        name_lookup.keys()
    )[0]


selected_company = st.sidebar.selectbox(
    "Select Benchmark Company",
    list(name_lookup.keys()),
    index=list(
        name_lookup.keys()
    ).index(default_company),
    format_func=lambda ticker:
        name_lookup[ticker],
)


# =========================================================
# SELECTED COMPANY DATA
# =========================================================

selected_rows = group_df[
    group_df["company_id"]
    == selected_company
]


if selected_rows.empty:

    st.error(
        "Selected company financial data is unavailable."
    )

    st.stop()


selected_row = selected_rows.iloc[0]


# =========================================================
# RADAR METRICS
# =========================================================

RADAR_METRICS = {

    "ROE": (
        "return_on_equity_pct",
        False,
    ),

    "ROCE": (
        "return_on_capital_employed_pct",
        False,
    ),

    "NPM": (
        "net_profit_margin_pct",
        False,
    ),

    "D/E": (
        "debt_to_equity",
        True,
    ),

    "FCF": (
        "free_cash_flow_cr",
        False,
    ),

    "PAT CAGR": (
        "pat_cagr_5yr",
        False,
    ),

    "Revenue CAGR": (
        "revenue_cagr_5yr",
        False,
    ),

    "Composite Score": (
        "composite_quality_score",
        False,
    ),
}


# =========================================================
# NUMERIC CONVERSION
# =========================================================

for metric_column, _ in RADAR_METRICS.values():

    group_df[metric_column] = pd.to_numeric(
        group_df[metric_column],
        errors="coerce",
    )


# =========================================================
# RADAR VALUES
# =========================================================

selected_values = []

average_values = []

radar_labels = list(
    RADAR_METRICS.keys()
)


for metric_name, (
    column,
    inverse,
) in RADAR_METRICS.items():

    series = group_df[column]

    selected_value = pd.to_numeric(
        selected_row[column],
        errors="coerce",
    )

    average_value = series.mean()

    # -----------------------------------------------------
    # D/E IS INVERSE QUALITY
    # -----------------------------------------------------

    if inverse:

        valid = series.dropna()

        if (
            not valid.empty
            and valid.max() != valid.min()
        ):

            maximum = valid.max()

            selected_value = (
                maximum - selected_value
            )

            average_value = (
                maximum - average_value
            )

    # -----------------------------------------------------
    # FCF SCALE NORMALIZATION
    # -----------------------------------------------------

    if metric_name == "FCF":

        valid = series.dropna()

        if (
            not valid.empty
            and valid.max() != valid.min()
        ):

            minimum = valid.min()
            maximum = valid.max()

            selected_value = (
                (
                    selected_value
                    - minimum
                )
                /
                (
                    maximum
                    - minimum
                )
                * 100
            )

            normalized = (
                (
                    valid
                    - minimum
                )
                /
                (
                    maximum
                    - minimum
                )
                * 100
            )

            average_value = (
                normalized.mean()
            )

    # -----------------------------------------------------
    # REPLACE MISSING VALUES
    # -----------------------------------------------------

    if pd.isna(selected_value):
        selected_value = 0

    if pd.isna(average_value):
        average_value = 0

    selected_values.append(
        float(selected_value)
    )

    average_values.append(
        float(average_value)
    )


# =========================================================
# CLOSE RADAR POLYGON
# =========================================================

radar_labels_closed = (
    radar_labels
    + [radar_labels[0]]
)

selected_values_closed = (
    selected_values
    + [selected_values[0]]
)

average_values_closed = (
    average_values
    + [average_values[0]]
)


# =========================================================
# RADAR CHART
# =========================================================

st.divider()

st.subheader(
    f"📡 {selected_company} vs "
    f"{selected_group} Average"
)


fig = go.Figure()


fig.add_trace(
    go.Scatterpolar(
        r=selected_values_closed,
        theta=radar_labels_closed,
        fill="toself",
        name=selected_company,
    )
)


fig.add_trace(
    go.Scatterpolar(
        r=average_values_closed,
        theta=radar_labels_closed,
        fill=None,
        mode="lines+markers",
        name="Peer Group Average",
    )
)


fig.update_layout(
    polar=dict(
        radialaxis=dict(
            visible=True,
        )
    ),
    height=600,
    showlegend=True,
)


st.plotly_chart(
    fig,
    use_container_width=True,
)


# =========================================================
# KPI COMPARISON TABLE
# =========================================================

st.divider()

st.subheader(
    f"📊 Companies in {selected_group}"
)


comparison_columns = [
    "company_id",
    "company_name",
    "return_on_equity_pct",
    "return_on_capital_employed_pct",
    "net_profit_margin_pct",
    "debt_to_equity",
    "free_cash_flow_cr",
    "pat_cagr_5yr",
    "revenue_cagr_5yr",
    "composite_quality_score",
]


comparison_columns = [
    column
    for column in comparison_columns
    if column in group_df.columns
]


comparison = group_df[
    comparison_columns
].copy()


comparison = comparison.sort_values(
    "composite_quality_score",
    ascending=False,
    na_position="last",
)


# =========================================================
# RENAME TABLE COLUMNS
# =========================================================

comparison = comparison.rename(
    columns={
        "company_id": "Company ID",
        "company_name": "Company",
        "return_on_equity_pct": "ROE (%)",
        "return_on_capital_employed_pct": "ROCE (%)",
        "net_profit_margin_pct": "NPM (%)",
        "debt_to_equity": "D/E",
        "free_cash_flow_cr": "FCF (₹ Cr)",
        "pat_cagr_5yr": "PAT CAGR (%)",
        "revenue_cagr_5yr": "Revenue CAGR (%)",
        "composite_quality_score": "Composite Score",
    }
)


# =========================================================
# ROUND VALUES
# =========================================================

for column in comparison.columns:

    if column not in [
        "Company ID",
        "Company",
    ]:

        comparison[column] = pd.to_numeric(
            comparison[column],
            errors="coerce",
        ).round(2)


# =========================================================
# HIGHLIGHT BENCHMARK COMPANY
# =========================================================

def highlight_benchmark(row):

    company_id = str(
        row["Company ID"]
    )

    if company_id == str(
        selected_company
    ):

        return [
            "font-weight: bold"
            for _ in row
        ]

    return [
        ""
        for _ in row
    ]


styled_table = comparison.style.apply(
    highlight_benchmark,
    axis=1,
)


st.dataframe(
    styled_table,
    use_container_width=True,
    hide_index=True,
)


# =========================================================
# SUMMARY
# =========================================================

st.info(
    f"Peer Group: **{selected_group}**  |  "
    f"Companies: **{len(comparison)}**  |  "
    f"Benchmark: **{selected_company}**"
)