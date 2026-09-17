"""
N100 Financial Intelligence Platform
Sprint 4 - Day 23
Company Profile Screen
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from dashboard.utils.db import (
    get_companies,
    get_ratios,
    get_pl,
    get_sectors,
)


st.set_page_config(
    page_title="Company Profile",
    layout="wide",
)


# ---------------------------------------------------------
# LOAD COMPANY MASTER
# ---------------------------------------------------------

companies = get_companies()
sectors = get_sectors()


# ---------------------------------------------------------
# HELPER
# ---------------------------------------------------------

def find_column(df, possible_names):
    lookup = {str(col).lower(): col for col in df.columns}

    for name in possible_names:
        if name.lower() in lookup:
            return lookup[name.lower()]

    return None


def safe_value(df, possible_names, default=0):
    col = find_column(df, possible_names)

    if col and not df.empty:
        values = pd.to_numeric(
            df[col],
            errors="coerce",
        ).dropna()

        if not values.empty:
            return values.iloc[0]

    return default


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

st.title("Company Profile")
st.caption(
    "Search and analyse individual Nifty 100 companies."
)


# ---------------------------------------------------------
# COMPANY SEARCH / AUTOCOMPLETE
# ---------------------------------------------------------

company_options = []

for _, row in companies.iterrows():

    ticker = str(row["id"])

    company_name = str(
        row.get("company_name", "")
    )

    company_options.append(
        f"{company_name} ({ticker})"
    )


search = st.selectbox(
    "Search Company or NSE Ticker",
    company_options,
    index=0 if company_options else None,
    placeholder="Type company name or ticker...",
)


if not search:
    st.info("Please select a company.")
    st.stop()


# Extract ticker
ticker = search.split("(")[-1].replace(")", "").strip()


# ---------------------------------------------------------
# COMPANY MASTER RECORD
# ---------------------------------------------------------

company_match = companies[
    companies["id"].astype(str) == ticker
]


if company_match.empty:

    st.error(
        "Ticker not found — please try another"
    )

    st.stop()


company = company_match.iloc[0]


# ---------------------------------------------------------
# COMPANY INFORMATION
# ---------------------------------------------------------

sector_match = sectors[
    sectors["company_id"].astype(str) == ticker
]


sector = ""
sub_sector = ""

if not sector_match.empty:

    sector_col = find_column(
        sector_match,
        ["broad_sector", "sector"],
    )

    sub_sector_col = find_column(
        sector_match,
        ["sub_sector", "subsector"],
    )

    if sector_col:
        sector = sector_match.iloc[0][sector_col]

    if sub_sector_col:
        sub_sector = sector_match.iloc[0][
            sub_sector_col
        ]


st.subheader(
    company.get(
        "company_name",
        ticker,
    )
)

info1, info2, info3, info4 = st.columns(4)

info1.metric(
    "NSE Ticker",
    ticker,
)

info2.write("**Sector**")
info2.write(str(sector))

info3.write("**Sub-sector**")
info3.write(str(sub_sector))

info4.write("**Face Value**")
info4.write(
    str(company.get("face_value", "N/A"))
)


about = company.get(
    "about_company",
    "",
)

if pd.notna(about) and str(about).strip():

    st.markdown("### About the Company")

    st.write(str(about))


st.divider()


# ---------------------------------------------------------
# LOAD FINANCIAL DATA
# ---------------------------------------------------------

ratios = get_ratios(ticker)
pl = get_pl(ticker)


if ratios.empty:

    st.warning(
        "Financial ratio data is not available for this company."
    )

    st.stop()


# Latest ratio record
ratios = ratios.sort_values(
    "year",
    ascending=False,
)

latest_ratio = ratios.iloc[0]


# ---------------------------------------------------------
# KPI VALUES
# ---------------------------------------------------------

roe = safe_value(
    pd.DataFrame([latest_ratio]),
    ["roe", "roe_percentage", "return_on_equity"],
)

roce = safe_value(
    pd.DataFrame([latest_ratio]),
    ["roce", "roce_percentage", "return_on_capital_employed"],
)

npm = safe_value(
    pd.DataFrame([latest_ratio]),
    [
        "npm",
        "net_profit_margin",
        "net_profit_margin_percentage",
    ],
)

de = safe_value(
    pd.DataFrame([latest_ratio]),
    [
        "de",
        "d_e",
        "debt_equity",
        "debt_to_equity",
    ],
)

revenue_cagr = safe_value(
    pd.DataFrame([latest_ratio]),
    [
        "revenue_cagr_5yr",
        "revenue_cagr_5y",
        "revenue_cagr_5",
        "revenue_cagr",
    ],
)

fcf = safe_value(
    pd.DataFrame([latest_ratio]),
    [
        "fcf",
        "free_cash_flow",
        "free_cash_flow_crore",
    ],
)


# ---------------------------------------------------------
# SIX KPI TILES
# ---------------------------------------------------------

st.subheader("Key Financial Indicators")

k1, k2, k3 = st.columns(3)
k4, k5, k6 = st.columns(3)

k1.metric("ROE", f"{roe:.2f}%")
k2.metric("ROCE", f"{roce:.2f}%")
k3.metric("Net Profit Margin", f"{npm:.2f}%")

k4.metric("D/E", f"{de:.2f}")
k5.metric(
    "Revenue CAGR 5yr",
    f"{revenue_cagr:.2f}%",
)
k6.metric(
    "FCF (Latest Year)",
    f"{fcf:,.2f}",
)


st.divider()


# ---------------------------------------------------------
# 10-YEAR REVENUE & NET PROFIT
# ---------------------------------------------------------

st.subheader(
    "10-Year Revenue & Net Profit"
)


if not pl.empty:

    year_col = find_column(
        pl,
        ["year"],
    )

    revenue_col = find_column(
        pl,
        [
            "revenue",
            "sales",
            "total_revenue",
        ],
    )

    profit_col = find_column(
        pl,
        [
            "net_profit",
            "profit_after_tax",
            "pat",
            "net_profit_crore",
        ],
    )

    if (
        year_col
        and revenue_col
        and profit_col
    ):

        chart_df = pl.copy()

        chart_df[year_col] = pd.to_numeric(
            chart_df[year_col],
            errors="coerce",
        )

        chart_df[revenue_col] = pd.to_numeric(
            chart_df[revenue_col],
            errors="coerce",
        )

        chart_df[profit_col] = pd.to_numeric(
            chart_df[profit_col],
            errors="coerce",
        )

        chart_df = (
            chart_df
            .dropna(
                subset=[
                    year_col,
                    revenue_col,
                    profit_col,
                ]
            )
            .sort_values(year_col)
            .tail(10)
        )

        fig = go.Figure()

        fig.add_bar(
            x=chart_df[year_col],
            y=chart_df[revenue_col],
            name="Revenue",
        )

        fig.add_bar(
            x=chart_df[year_col],
            y=chart_df[profit_col],
            name="Net Profit",
        )

        fig.update_layout(
            barmode="group",
            xaxis_title="Year",
            yaxis_title="Amount",
            hovermode="x unified",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    else:

        st.info(
            "Revenue or Net Profit columns were not found."
        )

else:

    st.info(
        "No Profit & Loss history available."
    )


# ---------------------------------------------------------
# ROE / ROCE DUAL AXIS
# ---------------------------------------------------------

st.subheader(
    "ROE & ROCE — 10 Year Trend"
)

trend = ratios.copy()

year_col = find_column(
    trend,
    ["year"],
)

roe_col = find_column(
    trend,
    ["roe", "roe_percentage", "return_on_equity"],
)

roce_col = find_column(
    trend,
    ["roce", "roce_percentage", "return_on_capital_employed"],
)


if year_col and roe_col and roce_col:

    trend[year_col] = pd.to_numeric(
        trend[year_col],
        errors="coerce",
    )

    trend[roe_col] = pd.to_numeric(
        trend[roe_col],
        errors="coerce",
    )

    trend[roce_col] = pd.to_numeric(
        trend[roce_col],
        errors="coerce",
    )

    trend = (
        trend
        .dropna(
            subset=[
                year_col,
                roe_col,
                roce_col,
            ]
        )
        .sort_values(year_col)
        .tail(10)
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=trend[year_col],
            y=trend[roe_col],
            mode="lines+markers",
            name="ROE",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=trend[year_col],
            y=trend[roce_col],
            mode="lines+markers",
            name="ROCE",
            yaxis="y2",
        )
    )

    fig.update_layout(
        xaxis=dict(
            title="Year",
        ),
        yaxis=dict(
            title="ROE (%)",
        ),
        yaxis2=dict(
            title="ROCE (%)",
            overlaying="y",
            side="right",
        ),
        hovermode="x unified",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

else:

    st.info(
        "ROE/ROCE trend data is not available."
    )


# ---------------------------------------------------------
# PROS & CONS
# ---------------------------------------------------------

st.divider()

st.subheader("Pros & Cons")

st.info(
    "Pros and cons will be displayed here when the "
    "prosandcons dataset is connected to the dashboard."
)
