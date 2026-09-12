"""
N100 Financial Intelligence Platform
Sprint 4 - Day 24
Screener Dashboard

Features:
- 10 financial metric filters
- 6 predefined screening presets
- Live filtering
- Composite quality score sorting
- Result count
- CSV export
"""

import sys
from pathlib import Path

import pandas as pd
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
    get_market_valuations,
)


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Stock Screener",
    page_icon="🔎",
    layout="wide",
)


# =========================================================
# PAGE HEADER
# =========================================================

st.title("🔎 Stock Screener")

st.caption(
    "Screen Nifty 100 companies using profitability, "
    "growth, cash flow, valuation and leverage metrics."
)


# =========================================================
# LOAD DATABASE DATA
# =========================================================

companies = get_companies()

ratios = get_all_ratios(2024)

valuations = get_market_valuations(2024)


if companies.empty:
    st.error("Company master data is unavailable.")
    st.stop()


if ratios.empty:
    st.error("Financial ratio data is unavailable.")
    st.stop()


# =========================================================
# PREPARE COMPANY DATA
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


df = ratios.merge(
    company_info,
    on="company_id",
    how="left",
)


# =========================================================
# ADD SECTOR INFORMATION
# =========================================================

try:

    sector_data = pd.read_sql_query(
        """
        SELECT
            company_id,
            broad_sector AS sector,
            sub_sector
        FROM sectors
        """,
        __import__("sqlite3").connect(
            str(PROJECT_ROOT / "nifty100.db")
        ),
    )

    sector_data["company_id"] = (
        sector_data["company_id"]
        .astype(str)
    )

    sector_data = sector_data.drop_duplicates(
        subset=["company_id"]
    )

    df = df.merge(
        sector_data,
        on="company_id",
        how="left",
    )

except Exception:

    df["sector"] = "N/A"
    df["sub_sector"] = "N/A"


# =========================================================
# MERGE MARKET VALUATION
# =========================================================

if not valuations.empty:

    valuation_columns = [
        "company_id",
        "pe_ratio",
        "pb_ratio",
        "ev_ebitda",
        "dividend_yield_pct",
    ]

    valuation_columns = [
        column
        for column in valuation_columns
        if column in valuations.columns
    ]

    valuation_df = valuations[
        valuation_columns
    ].copy()

    valuation_df["company_id"] = (
        valuation_df["company_id"]
        .astype(str)
    )

    valuation_df = valuation_df.drop_duplicates(
        subset=["company_id"]
    )

    df = df.merge(
        valuation_df,
        on="company_id",
        how="left",
    )


# =========================================================
# STANDARDIZE METRICS
# =========================================================

df["ROE"] = pd.to_numeric(
    df["return_on_equity_pct"],
    errors="coerce",
)

df["D/E"] = pd.to_numeric(
    df["debt_to_equity"],
    errors="coerce",
)

df["FCF"] = pd.to_numeric(
    df["free_cash_flow_cr"],
    errors="coerce",
)

df["Revenue CAGR"] = pd.to_numeric(
    df["revenue_cagr_5yr"],
    errors="coerce",
)

df["PAT CAGR"] = pd.to_numeric(
    df["pat_cagr_5yr"],
    errors="coerce",
)

df["OPM"] = pd.to_numeric(
    df["operating_profit_margin_pct"],
    errors="coerce",
)

df["ICR"] = pd.to_numeric(
    df["interest_coverage"],
    errors="coerce",
)

df["P/E"] = pd.to_numeric(
    df.get(
        "pe_ratio",
        pd.Series(index=df.index, dtype=float),
    ),
    errors="coerce",
)

df["P/B"] = pd.to_numeric(
    df.get(
        "pb_ratio",
        pd.Series(index=df.index, dtype=float),
    ),
    errors="coerce",
)

df["Dividend Yield"] = pd.to_numeric(
    df.get(
        "dividend_yield_pct",
        pd.Series(index=df.index, dtype=float),
    ),
    errors="coerce",
)

df["Composite Score"] = pd.to_numeric(
    df["composite_quality_score"],
    errors="coerce",
)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.header("🎛️ Screening Filters")

st.sidebar.caption(
    "Adjust the filters to screen companies."
)


# =========================================================
# PRESET DEFINITIONS
# =========================================================

PRESETS = {

    "Quality": {
        "roe": 15.0,
        "de": 1.0,
        "fcf": 0.0,
        "revenue": 10.0,
        "pat": 0.0,
        "opm": 0.0,
        "pe": 200.0,
        "pb": 100.0,
        "dividend": 0.0,
        "icr": 0.0,
    },

    "Value": {
        "roe": 0.0,
        "de": 2.0,
        "fcf": 0.0,
        "revenue": -50.0,
        "pat": -100.0,
        "opm": -50.0,
        "pe": 20.0,
        "pb": 3.0,
        "dividend": 1.0,
        "icr": 0.0,
    },

    "Growth": {
        "roe": 0.0,
        "de": 2.0,
        "fcf": 0.0,
        "revenue": 15.0,
        "pat": 20.0,
        "opm": -50.0,
        "pe": 200.0,
        "pb": 100.0,
        "dividend": 0.0,
        "icr": 0.0,
    },

    "Dividend": {
        "roe": 0.0,
        "de": 100.0,
        "fcf": 0.0,
        "revenue": -50.0,
        "pat": -100.0,
        "opm": -50.0,
        "pe": 200.0,
        "pb": 100.0,
        "dividend": 2.0,
        "icr": 0.0,
    },

    "Debt-Free": {
        "roe": 12.0,
        "de": 0.0,
        "fcf": 0.0,
        "revenue": -50.0,
        "pat": -100.0,
        "opm": -50.0,
        "pe": 200.0,
        "pb": 100.0,
        "dividend": 0.0,
        "icr": 0.0,
    },

    "Turnaround": {
        "roe": 0.0,
        "de": 100.0,
        "fcf": 0.0,
        "revenue": 10.0,
        "pat": -100.0,
        "opm": -50.0,
        "pe": 200.0,
        "pb": 100.0,
        "dividend": 0.0,
        "icr": 0.0,
    },
}


# =========================================================
# PRESET STATE
# =========================================================

if "preset_selected" not in st.session_state:
    st.session_state.preset_selected = "Custom"


def apply_preset(name):
    """
    Apply predefined screening values.
    """

    values = PRESETS[name]

    for key, value in values.items():

        st.session_state[
            f"filter_{key}"
        ] = value

    st.session_state.preset_selected = name


# =========================================================
# PRESET BUTTONS
# =========================================================

st.sidebar.subheader("⚡ Presets")

preset_col1, preset_col2 = st.sidebar.columns(2)


with preset_col1:

    if st.button(
        "Quality",
        use_container_width=True,
    ):
        apply_preset("Quality")
        st.rerun()

    if st.button(
        "Growth",
        use_container_width=True,
    ):
        apply_preset("Growth")
        st.rerun()

    if st.button(
        "Dividend",
        use_container_width=True,
    ):
        apply_preset("Dividend")
        st.rerun()


with preset_col2:

    if st.button(
        "Value",
        use_container_width=True,
    ):
        apply_preset("Value")
        st.rerun()

    if st.button(
        "Debt-Free",
        use_container_width=True,
    ):
        apply_preset("Debt-Free")
        st.rerun()

    if st.button(
        "Turnaround",
        use_container_width=True,
    ):
        apply_preset("Turnaround")
        st.rerun()


# =========================================================
# FILTER SLIDERS
# =========================================================

roe_min = st.sidebar.slider(
    "ROE minimum (%)",
    min_value=0.0,
    max_value=100.0,
    value=float(
        st.session_state.get(
            "filter_roe",
            0.0,
        )
    ),
    step=1.0,
    key="filter_roe",
)


de_max = st.sidebar.slider(
    "D/E maximum",
    min_value=0.0,
    max_value=20.0,
    value=float(
        st.session_state.get(
            "filter_de",
            20.0,
        )
    ),
    step=0.1,
    key="filter_de",
)


fcf_min = st.sidebar.slider(
    "FCF minimum (₹ Cr)",
    min_value=-5000.0,
    max_value=10000.0,
    value=float(
        st.session_state.get(
            "filter_fcf",
            -5000.0,
        )
    ),
    step=100.0,
    key="filter_fcf",
)


revenue_min = st.sidebar.slider(
    "Revenue CAGR minimum (%)",
    min_value=-50.0,
    max_value=100.0,
    value=float(
        st.session_state.get(
            "filter_revenue",
            -50.0,
        )
    ),
    step=1.0,
    key="filter_revenue",
)


pat_min = st.sidebar.slider(
    "PAT CAGR minimum (%)",
    min_value=-100.0,
    max_value=150.0,
    value=float(
        st.session_state.get(
            "filter_pat",
            -100.0,
        )
    ),
    step=1.0,
    key="filter_pat",
)


opm_min = st.sidebar.slider(
    "OPM minimum (%)",
    min_value=-50.0,
    max_value=100.0,
    value=float(
        st.session_state.get(
            "filter_opm",
            -50.0,
        )
    ),
    step=1.0,
    key="filter_opm",
)


pe_max = st.sidebar.slider(
    "P/E maximum",
    min_value=0.0,
    max_value=200.0,
    value=float(
        st.session_state.get(
            "filter_pe",
            200.0,
        )
    ),
    step=1.0,
    key="filter_pe",
)


pb_max = st.sidebar.slider(
    "P/B maximum",
    min_value=0.0,
    max_value=100.0,
    value=float(
        st.session_state.get(
            "filter_pb",
            100.0,
        )
    ),
    step=1.0,
    key="filter_pb",
)


dividend_min = st.sidebar.slider(
    "Dividend Yield minimum (%)",
    min_value=0.0,
    max_value=20.0,
    value=float(
        st.session_state.get(
            "filter_dividend",
            0.0,
        )
    ),
    step=0.5,
    key="filter_dividend",
)


icr_min = st.sidebar.slider(
    "ICR minimum",
    min_value=0.0,
    max_value=200.0,
    value=float(
        st.session_state.get(
            "filter_icr",
            0.0,
        )
    ),
    step=1.0,
    key="filter_icr",
)


# =========================================================
# APPLY FILTERS
# =========================================================

result = df.copy()


result = result[
    result["ROE"].isna()
    | (result["ROE"] >= roe_min)
]


result = result[
    result["D/E"].isna()
    | (result["D/E"] <= de_max)
]


result = result[
    result["FCF"].isna()
    | (result["FCF"] >= fcf_min)
]


result = result[
    result["Revenue CAGR"].isna()
    | (result["Revenue CAGR"] >= revenue_min)
]


result = result[
    result["PAT CAGR"].isna()
    | (result["PAT CAGR"] >= pat_min)
]


result = result[
    result["OPM"].isna()
    | (result["OPM"] >= opm_min)
]


result = result[
    result["P/E"].isna()
    | (result["P/E"] <= pe_max)
]


result = result[
    result["P/B"].isna()
    | (result["P/B"] <= pb_max)
]


result = result[
    result["Dividend Yield"].isna()
    | (
        result["Dividend Yield"]
        >= dividend_min
    )
]


result = result[
    result["ICR"].isna()
    | (result["ICR"] >= icr_min)
]


# =========================================================
# SORT BY COMPOSITE QUALITY SCORE
# =========================================================

result = result.sort_values(
    "Composite Score",
    ascending=False,
    na_position="last",
)


# =========================================================
# RESULT COUNT
# =========================================================

st.subheader(
    f"📊 {len(result)} companies match your filters"
)


# =========================================================
# DISPLAY TABLE
# =========================================================

display_columns = [
    "company_id",
    "company_name",
    "sector",
    "Composite Score",
    "ROE",
    "D/E",
    "FCF",
    "Revenue CAGR",
    "PAT CAGR",
    "OPM",
    "P/E",
    "P/B",
    "Dividend Yield",
    "ICR",
]


display_columns = [
    column
    for column in display_columns
    if column in result.columns
]


display_df = result[
    display_columns
].copy()


# =========================================================
# ROUND NUMERIC VALUES FOR DISPLAY
# =========================================================

numeric_columns = [
    "Composite Score",
    "ROE",
    "D/E",
    "FCF",
    "Revenue CAGR",
    "PAT CAGR",
    "OPM",
    "P/E",
    "P/B",
    "Dividend Yield",
    "ICR",
]


for column in numeric_columns:

    if column in display_df.columns:

        display_df[column] = pd.to_numeric(
            display_df[column],
            errors="coerce",
        ).round(2)


# =========================================================
# TABLE
# =========================================================

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
)


# =========================================================
# CSV DOWNLOAD
# =========================================================

csv_data = display_df.to_csv(
    index=False
).encode("utf-8")


st.download_button(
    label="⬇️ Download Screener Results CSV",
    data=csv_data,
    file_name="screener_results.csv",
    mime="text/csv",
)


# =========================================================
# CURRENT PRESET
# =========================================================

st.caption(
    f"Current preset: "
    f"**{st.session_state.preset_selected}**"
)


# =========================================================
# FILTER SUMMARY
# =========================================================

with st.expander("ℹ️ Current Filter Values"):

    filter_summary = pd.DataFrame(
        {
            "Metric": [
                "ROE minimum",
                "D/E maximum",
                "FCF minimum",
                "Revenue CAGR minimum",
                "PAT CAGR minimum",
                "OPM minimum",
                "P/E maximum",
                "P/B maximum",
                "Dividend Yield minimum",
                "ICR minimum",
            ],
            "Value": [
                roe_min,
                de_max,
                fcf_min,
                revenue_min,
                pat_min,
                opm_min,
                pe_max,
                pb_max,
                dividend_min,
                icr_min,
            ],
        }
    )

    st.dataframe(
        filter_summary,
        use_container_width=True,
        hide_index=True,
    )