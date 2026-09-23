"""
N100 Financial Intelligence Platform
Sprint 4 - Day 23
Home Screen

Sprint 4 requirements:
- 6 summary KPI tiles
- Financial year selector 2019-2024
- 11-sector donut chart
- Top 5 companies by composite quality score
- Real database-backed data
- Missing-data-safe calculations
- Plotly charts
"""

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = PROJECT_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


# ============================================================
# DATABASE
# ============================================================

from dashboard.utils.db import (
    get_companies,
    get_latest_market_valuations,
    get_ratios,
    get_sectors,
)


# ============================================================
# CONSTANTS
# ============================================================

AVAILABLE_YEARS = list(range(2019, 2025))
DEFAULT_YEAR = 2024


# ============================================================
# SAFE HELPERS
# ============================================================

def safe_numeric(series):
    return pd.to_numeric(series, errors="coerce")


def safe_mean(df, column):
    if df is None or df.empty or column not in df.columns:
        return None

    values = safe_numeric(df[column]).dropna()

    if values.empty:
        return None

    return float(values.mean())


def safe_median(df, column):
    if df is None or df.empty or column not in df.columns:
        return None

    values = safe_numeric(df[column]).dropna()

    if values.empty:
        return None

    return float(values.median())


def format_percent(value):
    if value is None or pd.isna(value):
        return "N/A"

    return f"{float(value):.2f}%"


def format_number(value):
    if value is None or pd.isna(value):
        return "N/A"

    return f"{float(value):.2f}"


def safe_get_ratios(ticker, year=None):
    """
    Safely retrieve ratio data for one company.
    Missing/invalid data must never crash the dashboard.
    """

    try:
        result = get_ratios(str(ticker), year)

        if result is None:
            return pd.DataFrame()

        if not isinstance(result, pd.DataFrame):
            return pd.DataFrame()

        return result.copy()

    except Exception:
        return pd.DataFrame()


def get_tickers(companies):
    """
    Extract unique company IDs/tickers from company master data.
    """

    if companies is None or companies.empty:
        return []

    if "id" not in companies.columns:
        return []

    return (
        companies["id"]
        .dropna()
        .astype(str)
        .str.strip()
        .replace("", pd.NA)
        .dropna()
        .unique()
        .tolist()
    )


def find_sector_column(df):
    """
    Detect the sector column used by the current database.
    """

    if df is None or df.empty:
        return None

    candidates = [
        "sector",
        "sector_name",
        "broad_sector",
        "industry",
    ]

    for column in candidates:
        if column in df.columns:
            return column

    return None


# ============================================================
# LOAD COMPANY MASTER
# ============================================================

try:
    companies = get_companies()

    if companies is None:
        companies = pd.DataFrame()

except Exception:
    companies = pd.DataFrame()


total_companies = len(companies)


# ============================================================
# SELECTED FINANCIAL YEAR
# ============================================================

selected_year = st.session_state.get(
    "dashboard_year",
    DEFAULT_YEAR,
)

try:
    selected_year = int(selected_year)
except Exception:
    selected_year = DEFAULT_YEAR

if selected_year not in AVAILABLE_YEARS:
    selected_year = DEFAULT_YEAR


# ============================================================
# PAGE HEADER
# ============================================================

header_left, header_right = st.columns(
    [5, 1],
    vertical_alignment="bottom",
)

with header_left:

    st.caption("N100 MARKET INTELLIGENCE")
    st.title("Home")
    st.write(
        "Financial performance, valuation and sector intelligence"
    )

with header_right:

    st.html(
    f"""
    <div style="
        text-align: right;
        padding-top: 18px;
    ">
        <div style="
            color: #68778e;
            font-size: 9px;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        ">
            FINANCIAL YEAR
        </div>

        <div style="
            color: #111a2d;
            font-size: 20px;
            font-weight: 800;
            margin-top: 4px;
        ">
            {selected_year}
        </div>
    </div>
    """
)


st.divider()


# ============================================================
# LOAD SELECTED-YEAR RATIOS
# ============================================================

ratio_frames = []

tickers = get_tickers(companies)

for ticker in tickers:

    df = safe_get_ratios(
        ticker,
        selected_year,
    )

    if df.empty:
        continue

    ratio_frames.append(df)


if ratio_frames:

    ratios = pd.concat(
        ratio_frames,
        ignore_index=True,
    )

else:

    ratios = pd.DataFrame()


# ============================================================
# NORMALIZE RATIO NUMBERS
# ============================================================

ratio_numeric_columns = [
    "net_profit_margin_pct",
    "operating_profit_margin_pct",
    "return_on_equity_pct",
    "return_on_capital_employed_pct",
    "return_on_assets_pct",
    "debt_to_equity",
    "interest_coverage",
    "free_cash_flow_cr",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
    "composite_quality_score",
]

for column in ratio_numeric_columns:

    if column in ratios.columns:

        ratios[column] = pd.to_numeric(
            ratios[column],
            errors="coerce",
        )


# ============================================================
# LOAD MARKET VALUATION DATA
# ============================================================

try:

    valuations = get_latest_market_valuations(
        selected_year
    )

    if valuations is None:
        valuations = pd.DataFrame()

except Exception:

    valuations = pd.DataFrame()


valuation_numeric_columns = [
    "market_cap_crore",
    "enterprise_value_crore",
    "pe_ratio",
    "pb_ratio",
    "ev_ebitda",
    "dividend_yield_pct",
]

for column in valuation_numeric_columns:

    if column in valuations.columns:

        valuations[column] = pd.to_numeric(
            valuations[column],
            errors="coerce",
        )


# ============================================================
# REQUIRED SIX KPIs
# ============================================================

average_roe = safe_mean(
    ratios,
    "return_on_equity_pct",
)

median_pe = safe_median(
    valuations,
    "pe_ratio",
)

median_de = safe_median(
    ratios,
    "debt_to_equity",
)

median_revenue_cagr = safe_median(
    ratios,
    "revenue_cagr_5yr",
)


# ============================================================
# DEBT-FREE COMPANIES
# ============================================================

debt_free_count = 0

if not ratios.empty and "debt_to_equity" in ratios.columns:

    debt_values = pd.to_numeric(
        ratios["debt_to_equity"],
        errors="coerce",
    )

    debt_free_count = int(
        (debt_values == 0).sum()
    )


# ============================================================
# DATA COVERAGE
# ============================================================

available_ratio_tickers = 0

if not ratios.empty:

    if "company_id" in ratios.columns:

        available_ratio_tickers = (
            ratios["company_id"]
            .dropna()
            .astype(str)
            .nunique()
        )

    elif "id" in ratios.columns:

        available_ratio_tickers = (
            ratios["id"]
            .dropna()
            .astype(str)
            .nunique()
        )


if (
    total_companies > 0
    and available_ratio_tickers < total_companies
):

    st.info(
        f"Ratio data is available for "
        f"{available_ratio_tickers} of "
        f"{total_companies} companies for "
        f"{selected_year}. "
        f"Unavailable values are shown as N/A."
    )


# ============================================================
# SIX REQUIRED KPI TILES
# ============================================================

kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(
    6,
    gap="small",
)

with kpi1:

    st.metric(
        "AVERAGE ROE",
        format_percent(average_roe),
        help=f"Average ROE for {selected_year}.",
    )


with kpi2:

    st.metric(
        "MEDIAN P/E",
        format_number(median_pe),
        help=f"Median P/E for {selected_year}.",
    )


with kpi3:

    st.metric(
        "MEDIAN D/E",
        format_number(median_de),
        help=f"Median debt-to-equity for {selected_year}.",
    )


with kpi4:

    st.metric(
        "TOTAL COMPANIES",
        str(total_companies),
        help="Companies in the N100 analytics universe.",
    )


with kpi5:

    st.metric(
        "MEDIAN REVENUE CAGR 5YR",
        format_percent(median_revenue_cagr),
        help="Median five-year revenue CAGR.",
    )


with kpi6:

    st.metric(
        "DEBT-FREE COMPANIES",
        str(debt_free_count),
        help=f"Companies with D/E = 0 in {selected_year}.",
    )


# ============================================================
# FINANCIAL QUALITY TREND
# ============================================================

st.write("")

trend_col, sector_col = st.columns(
    [1.65, 1],
    gap="medium",
)


with trend_col:

    st.markdown("### N100 Financial Quality Trend")

    st.caption(
        "Median composite quality score across available years"
    )

    trend_rows = []

    for year in AVAILABLE_YEARS:

        year_scores = []

        for ticker in tickers:

            df = safe_get_ratios(
                ticker,
                year,
            )

            if df.empty:
                continue

            if "composite_quality_score" not in df.columns:
                continue

            values = pd.to_numeric(
                df["composite_quality_score"],
                errors="coerce",
            ).dropna()

            if values.empty:
                continue

            year_scores.append(
                float(values.iloc[-1])
            )

        if year_scores:

            trend_rows.append(
                {
                    "Year": year,
                    "Composite Score": float(
                        pd.Series(year_scores).median()
                    ),
                }
            )

    trend_df = pd.DataFrame(trend_rows)

    if not trend_df.empty:

        fig = px.line(
            trend_df,
            x="Year",
            y="Composite Score",
            markers=True,
        )

        fig.update_layout(
            height=310,
            margin=dict(
                l=10,
                r=10,
                t=10,
                b=10,
            ),
            showlegend=False,
            xaxis_title=None,
            yaxis_title=None,
            hovermode="x unified",
        )

        st.plotly_chart(
            fig,
            width="stretch",
            config={
                "displayModeBar": False,
                "responsive": True,
            },
        )

    else:

        st.info(
            "Composite quality trend data is not available."
        )


# ============================================================
# SECTOR ALLOCATION
# ============================================================

with sector_col:

    st.markdown("### Sector Allocation")

    st.caption(
        "N100 company distribution by sector"
    )

    try:

        sectors = get_sectors()

        if sectors is None:
            sectors = pd.DataFrame()

    except Exception:

        sectors = pd.DataFrame()


    sector_column = find_sector_column(
        sectors
    )


    # Fall back to company master
    if sector_column is None:

        sector_source = companies.copy()

        sector_column = find_sector_column(
            sector_source
        )

    else:

        sector_source = sectors.copy()


    if (
        sector_column is not None
        and not sector_source.empty
    ):

        allocation = (
            sector_source[
                sector_column
            ]
            .astype(str)
            .str.strip()
            .replace(
                "",
                "Unknown",
            )
            .value_counts()
            .reset_index()
        )

        allocation.columns = [
            "Sector",
            "Companies",
        ]

        allocation = allocation.sort_values(
            "Companies",
            ascending=False,
        )


        if not allocation.empty:

            fig = px.pie(
                allocation,
                names="Sector",
                values="Companies",
                hole=0.58,
            )

            fig.update_layout(
                height=310,
                margin=dict(
                    l=5,
                    r=5,
                    t=5,
                    b=5,
                ),
                legend=dict(
                    font=dict(size=8)
                ),
            )

            fig.update_traces(
                textinfo="percent",
                textposition="inside",
                hovertemplate=(
                    "%{label}<br>"
                    "%{value} companies<br>"
                    "%{percent}"
                    "<extra></extra>"
                ),
            )

            st.plotly_chart(
                fig,
                width="stretch",
                config={
                    "displayModeBar": False,
                    "responsive": True,
                },
            )

            # Sprint 4 requires 11 sectors.
            if len(allocation) != 11:

                st.warning(
                    f"Sector data currently contains "
                    f"{len(allocation)} sectors; "
                    f"Sprint 4 requires 11."
                )

        else:

            st.info(
                "Sector allocation data is not available."
            )

    else:

        st.info(
            "Sector classification data is not available."
        )


# ============================================================
# TOP 5 COMPANIES
# ============================================================

st.write("")

top_col, valuation_col = st.columns(
    [1.65, 1],
    gap="medium",
)


with top_col:

    st.markdown(
        "### Top 5 Companies by Composite Quality"
    )

    st.caption(
        f"Highest composite quality scores for "
        f"{selected_year}"
    )


    if (
        not ratios.empty
        and "composite_quality_score" in ratios.columns
    ):

        top5 = ratios.copy()

        top5[
            "composite_quality_score"
        ] = pd.to_numeric(
            top5["composite_quality_score"],
            errors="coerce",
        )

        top5 = top5.dropna(
            subset=[
                "composite_quality_score"
            ]
        )


        if "company_id" in top5.columns:

            top5 = top5.drop_duplicates(
                subset=["company_id"]
            )

            top5["Ticker"] = (
                top5["company_id"]
                .astype(str)
                .str.strip()
            )

        elif "id" in top5.columns:

            top5 = top5.drop_duplicates(
                subset=["id"]
            )

            top5["Ticker"] = (
                top5["id"]
                .astype(str)
                .str.strip()
            )

        else:

            top5["Ticker"] = "N/A"


        top5 = (
            top5
            .sort_values(
                "composite_quality_score",
                ascending=False,
            )
            .head(5)
        )


        # Company-name lookup
        company_map = {}

        if (
            not companies.empty
            and "id" in companies.columns
            and "company_name" in companies.columns
        ):

            company_map = (
                companies
                .drop_duplicates(
                    subset=["id"]
                )
                .set_index("id")[
                    "company_name"
                ]
                .to_dict()
            )


        top5["Company"] = (
            top5["Ticker"]
            .map(company_map)
            .fillna(top5["Ticker"])
        )


        display_df = top5[
            [
                "Company",
                "Ticker",
                "composite_quality_score",
            ]
        ].copy()


        display_df.columns = [
            "Company",
            "Ticker",
            "Quality Score",
        ]


        display_df["Quality Score"] = (
            pd.to_numeric(
                display_df["Quality Score"],
                errors="coerce",
            )
            .round(2)
        )


        st.dataframe(
            display_df,
            hide_index=True,
            width="stretch",
            height=245,
        )

    else:

        st.info(
            "Composite quality data is not available."
        )


# ============================================================
# VALUATION INSIGHTS
# ============================================================

with valuation_col:

    st.markdown("### Valuation Insights")

    st.caption(
        "P/E positioning from the valuation module"
    )


    valuation_path = (
        PROJECT_ROOT
        / "output"
        / "valuation_summary.xlsx"
    )


    caution = 0
    discount = 0
    fair = 0


    if valuation_path.exists():

        try:

            valuation_summary = pd.read_excel(
                valuation_path
            )

            if (
                not valuation_summary.empty
                and "flag"
                in valuation_summary.columns
            ):

                flags = (
                    valuation_summary["flag"]
                    .astype(str)
                    .str.strip()
                    .str.title()
                )

                counts = flags.value_counts()

                caution = int(
                    counts.get(
                        "Caution",
                        0,
                    )
                )

                discount = int(
                    counts.get(
                        "Discount",
                        0,
                    )
                )

                fair = int(
                    counts.get(
                        "Fair",
                        0,
                    )
                )

        except Exception:

            caution = 0
            discount = 0
            fair = 0


    val1, val2, val3 = st.columns(
        3,
        gap="small",
    )


    with val1:

        st.metric(
            "CAUTION",
            str(caution),
        )


    with val2:

        st.metric(
            "DISCOUNT",
            str(discount),
        )


    with val3:

        st.metric(
            "FAIR",
            str(fair),
        )


    st.write("")

    st.caption(
        "Caution: P/E > 1.5x sector median. "
        "Discount: P/E < 0.7x sector median. "
        "Otherwise Fair."
    )


# ============================================================
# DATA STATUS
# ============================================================

st.write("")

status_left, status_right = st.columns(
    [2, 1]
)

with status_left:

    st.caption(
        f"Data coverage: "
        f"{available_ratio_tickers} / "
        f"{total_companies} companies"
    )


with status_right:

    st.caption(
        f"Selected financial year: "
        f"{selected_year}"
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

footer1, footer2, footer3 = st.columns(3)

with footer1:

    st.caption(
        f"N100 UNIVERSE: "
        f"{total_companies} COMPANIES TRACKED"
    )

with footer2:

    st.caption(
        f"FINANCIAL YEAR: {selected_year}"
    )

with footer3:

    st.caption(
        "DATA REFRESH: 10 MINUTES"
    )
