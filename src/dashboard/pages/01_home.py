"""
N100 Financial Intelligence Platform
Sprint 4 - Home Screen

Home screen for the N100 Financial Intelligence Platform.

Sprint 4 requirements implemented:
- 6 summary KPI tiles
- Financial year 2019-2024 controlled from sidebar
- 11-sector company distribution
- Top 5 companies by composite quality score
- Valuation insights
- Real database-backed N100 data
- Missing-data-safe calculations
- Plotly charts
"""

from pathlib import Path
import sys

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
    get_ratios,
    get_sectors,
    get_latest_market_valuations,
)


# ============================================================
# PAGE CONSTANTS
# ============================================================

DEFAULT_YEAR = 2024

AVAILABLE_YEARS = list(
    range(2019, 2025)
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clean_numeric(df, column):
    """
    Return a numeric Series with invalid values removed.
    """

    if df is None or df.empty:
        return pd.Series(dtype="float64")

    if column not in df.columns:
        return pd.Series(dtype="float64")

    return pd.to_numeric(
        df[column],
        errors="coerce",
    ).dropna()


def safe_mean(df, column):
    """
    Safely calculate mean.
    """

    values = clean_numeric(
        df,
        column,
    )

    if values.empty:
        return None

    return float(
        values.mean()
    )


def safe_median(df, column):
    """
    Safely calculate median.
    """

    values = clean_numeric(
        df,
        column,
    )

    if values.empty:
        return None

    return float(
        values.median()
    )


def format_percent(value):
    """
    Format percentage values.
    """

    if value is None:
        return "N/A"

    try:

        if pd.isna(value):
            return "N/A"

    except Exception:
        return "N/A"

    return f"{float(value):.2f}%"


def format_number(value):
    """
    Format normal numeric values.
    """

    if value is None:
        return "N/A"

    try:

        if pd.isna(value):
            return "N/A"

    except Exception:
        return "N/A"

    return f"{float(value):.2f}"


def safe_get_ratios(
    ticker,
    year=None,
):
    """
    Safely retrieve ratio data.

    Some companies may have incomplete data for a particular
    year. An empty DataFrame is returned instead of allowing
    the Home screen to crash.
    """

    try:

        result = get_ratios(
            str(ticker),
            year,
        )

        if result is None:
            return pd.DataFrame()

        if not isinstance(
            result,
            pd.DataFrame,
        ):
            return pd.DataFrame()

        return result.copy()

    except Exception:

        return pd.DataFrame()


def get_company_tickers(companies):
    """
    Return unique company tickers.
    """

    if (
        companies is None
        or companies.empty
        or "id" not in companies.columns
    ):
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


# ============================================================
# LOAD COMPANY MASTER DATA
# ============================================================

try:

    companies = get_companies()

    if companies is None:
        companies = pd.DataFrame()

except Exception:

    companies = pd.DataFrame()


# ============================================================
# FINANCIAL YEAR
# ============================================================

selected_year = st.session_state.get(
    "dashboard_year",
    DEFAULT_YEAR,
)

try:

    selected_year = int(
        selected_year
    )

except Exception:

    selected_year = DEFAULT_YEAR


if selected_year not in AVAILABLE_YEARS:

    selected_year = DEFAULT_YEAR


# ============================================================
# LOAD SELECTED-YEAR RATIOS
# ============================================================

ratio_frames = []

tickers = get_company_tickers(
    companies
)


for ticker in tickers:

    ratio_df = safe_get_ratios(
        ticker,
        selected_year,
    )

    if ratio_df.empty:
        continue

    ratio_frames.append(
        ratio_df
    )


if ratio_frames:

    ratios = pd.concat(
        ratio_frames,
        ignore_index=True,
    )

else:

    ratios = pd.DataFrame()


# ============================================================
# NORMALIZE NUMERIC RATIO COLUMNS
# ============================================================

RATIO_NUMERIC_COLUMNS = [
    "net_profit_margin_pct",
    "operating_profit_margin_pct",
    "return_on_equity_pct",
    "return_on_capital_employed_pct",
    "return_on_assets_pct",
    "debt_to_equity",
    "interest_coverage",
    "asset_turnover",
    "free_cash_flow_cr",
    "capex_cr",
    "earnings_per_share",
    "book_value_per_share",
    "dividend_payout_ratio_pct",
    "total_debt_cr",
    "cash_from_operations_cr",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
    "eps_cagr_5yr",
    "composite_quality_score",
    "net_debt",
]


for column in RATIO_NUMERIC_COLUMNS:

    if column in ratios.columns:

        ratios[column] = pd.to_numeric(
            ratios[column],
            errors="coerce",
        )


# ============================================================
# MARKET VALUATION DATA
# ============================================================

try:

    valuations = get_latest_market_valuations(
        selected_year
    )

    if valuations is None:
        valuations = pd.DataFrame()

except Exception:

    valuations = pd.DataFrame()


VALUATION_NUMERIC_COLUMNS = [
    "market_cap_crore",
    "enterprise_value_crore",
    "pe_ratio",
    "pb_ratio",
    "ev_ebitda",
    "dividend_yield_pct",
]


for column in VALUATION_NUMERIC_COLUMNS:

    if column in valuations.columns:

        valuations[column] = pd.to_numeric(
            valuations[column],
            errors="coerce",
        )


# ============================================================
# KPI CALCULATIONS
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
# TOTAL COMPANIES
# ============================================================

if companies.empty:

    total_companies = 0

else:

    total_companies = len(
        companies
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


# ============================================================
# DEBT-FREE COUNT
# ============================================================

debt_free_count = 0

if (
    not ratios.empty
    and "debt_to_equity" in ratios.columns
):

    debt_values = pd.to_numeric(
        ratios["debt_to_equity"],
        errors="coerce",
    )

    debt_free_count = int(
        (debt_values == 0).sum()
    )


# ============================================================
# PAGE HEADER
# ============================================================

header_left, header_right = st.columns(
    [5, 1],
    vertical_alignment="bottom",
)


with header_left:

    st.caption(
        "N100 MARKET INTELLIGENCE"
    )

    st.title(
        "Home"
    )

    st.write(
        "Financial performance, valuation and sector intelligence"
    )


with header_right:

    st.markdown(
        f"""
        <div style="
            text-align:right;
            padding-top:18px;
        ">

            <div style="
                color:#68778e;
                font-size:9px;
                font-weight:800;
                letter-spacing:.08em;
                text-transform:uppercase;
            ">
                FINANCIAL YEAR
            </div>

            <div style="
                color:#111a2d;
                font-size:20px;
                font-weight:800;
                margin-top:4px;
            ">
                {selected_year}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


st.divider()


# ============================================================
# DATA COVERAGE NOTE
# ============================================================

if (
    total_companies > 0
    and available_ratio_tickers < total_companies
):

    st.info(
        f"Ratio data is available for "
        f"{available_ratio_tickers} of "
        f"{total_companies} companies for "
        f"{selected_year}. "
        f"Unavailable values are excluded from "
        f"summary calculations."
    )


# ============================================================
# SIX REQUIRED KPI CARDS
# ============================================================

kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(
    6,
    gap="small",
)


with kpi1:

    st.metric(
        label="AVERAGE ROE",
        value=format_percent(
            average_roe
        ),
        help=(
            "Average return on equity "
            f"for {selected_year}."
        ),
    )


with kpi2:

    st.metric(
        label="MEDIAN P/E RATIO",
        value=format_number(
            median_pe
        ),
        help="Median price-to-earnings ratio.",
    )


with kpi3:

    st.metric(
        label="MEDIAN DEBT / EQUITY",
        value=format_number(
            median_de
        ),
        help="Median debt-to-equity ratio.",
    )


with kpi4:

    st.metric(
        label="COMPANIES TRACKED",
        value=str(
            total_companies
        ),
        help=(
            "Companies in the Nifty 100 "
            "analytics universe."
        ),
    )


with kpi5:

    st.metric(
        label="MEDIAN REVENUE CAGR · 5YR",
        value=format_percent(
            median_revenue_cagr
        ),
        help=(
            "Median five-year revenue CAGR."
        ),
    )


with kpi6:

    st.metric(
        label="DEBT-FREE COMPANIES",
        value=str(
            debt_free_count
        ),
        help=(
            "Companies with D/E = 0 "
            f"in {selected_year}."
        ),
    )


# ============================================================
# SECTION SPACING
# ============================================================

st.write("")


# ============================================================
# QUALITY TREND + SECTOR ALLOCATION
# ============================================================

trend_col, sector_col = st.columns(
    [1.65, 1],
    gap="medium",
)


# ============================================================
# FINANCIAL QUALITY TREND
# ============================================================

with trend_col:

    st.markdown(
        "### N100 Financial Quality Trend"
    )

    st.caption(
        "Median composite quality score across available years"
    )


    trend_rows = []


    # --------------------------------------------------------
    # Use all companies
    # --------------------------------------------------------

    for year in AVAILABLE_YEARS:

        year_scores = []


        for ticker in tickers:

            df = safe_get_ratios(
                ticker,
                year,
            )

            if df.empty:
                continue


            values = clean_numeric(
                df,
                "composite_quality_score",
            )


            if values.empty:
                continue


            year_scores.append(
                float(
                    values.iloc[-1]
                )
            )


        if year_scores:

            trend_rows.append(
                {
                    "Year": year,
                    "Composite Score": float(
                        pd.Series(
                            year_scores
                        ).median()
                    ),
                }
            )


    trend_df = pd.DataFrame(
        trend_rows
    )


    if not trend_df.empty:

        fig = px.line(
            trend_df,
            x="Year",
            y="Composite Score",
            markers=True,
        )


        fig.update_traces(
            line=dict(
                color="#2d6df3",
                width=2.5,
            ),
            marker=dict(
                color="#2d6df3",
                size=7,
            ),
        )


        fig.update_layout(
            height=310,

            margin=dict(
                l=10,
                r=10,
                t=10,
                b=10,
            ),

            paper_bgcolor="#ffffff",
            plot_bgcolor="#ffffff",

            font=dict(
                family="Inter, Arial, sans-serif",
                size=10,
                color="#111a2d",
            ),

            xaxis=dict(
                title=None,
                showgrid=False,
                zeroline=False,
                dtick=1,
            ),

            yaxis=dict(
                title=None,
                showgrid=True,
                gridcolor="#edf1f5",
                zeroline=False,
            ),

            showlegend=False,

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
            "Quality trend data is not available."
        )


# ============================================================
# SECTOR ALLOCATION
# ============================================================

with sector_col:

    st.markdown(
        "### Sector Allocation"
    )

    st.caption(
        "N100 company distribution by sector"
    )


    # --------------------------------------------------------
    # Load sector data
    # --------------------------------------------------------

    try:

        sectors = get_sectors()

        if sectors is None:
            sectors = pd.DataFrame()

    except Exception:

        sectors = pd.DataFrame()


    sector_df = pd.DataFrame()


    if not sectors.empty:

        sector_df = sectors.copy()


    # --------------------------------------------------------
    # Detect sector column
    # --------------------------------------------------------

    sector_column = None


    for candidate in [
        "sector",
        "sector_name",
        "broad_sector",
        "industry",
    ]:

        if candidate in sector_df.columns:

            sector_column = candidate

            break


    # --------------------------------------------------------
    # Fall back to company master data
    # --------------------------------------------------------

    if (
        sector_column is None
        and not companies.empty
    ):

        for candidate in [
            "sector",
            "sector_name",
            "broad_sector",
        ]:

            if candidate in companies.columns:

                sector_df = companies.copy()

                sector_column = candidate

                break


    # --------------------------------------------------------
    # Build allocation
    # --------------------------------------------------------

    if (
        sector_column is not None
        and not sector_df.empty
    ):

        allocation = (
            sector_df[
                sector_column
            ]
            .astype(str)
            .str.strip()
            .replace("", "Unknown")
            .value_counts()
            .reset_index()
        )


        allocation.columns = [
            "Sector",
            "Companies",
        ]


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

                paper_bgcolor="#ffffff",

                font=dict(
                    family="Inter, Arial, sans-serif",
                    size=9,
                    color="#111a2d",
                ),

                legend=dict(
                    font=dict(
                        size=8,
                    ),
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


        else:

            st.info(
                "Sector allocation data is not available."
            )


    else:

        st.info(
            "Sector classification data is not available."
        )


# ============================================================
# SECOND CONTENT ROW
# ============================================================

st.write("")


top_col, valuation_col = st.columns(
    [1.65, 1],
    gap="medium",
)


# ============================================================
# TOP 5 COMPANIES
# ============================================================

with top_col:

    st.markdown(
        "### Top Companies by Composite Quality"
    )

    st.caption(
        f"Highest available quality scores for {selected_year}"
    )


    if (
        not ratios.empty
        and "composite_quality_score" in ratios.columns
    ):

        top5 = ratios.copy()


        top5[
            "composite_quality_score"
        ] = pd.to_numeric(
            top5[
                "composite_quality_score"
            ],
            errors="coerce",
        )


        top5 = (
            top5
            .dropna(
                subset=[
                    "composite_quality_score"
                ]
            )
            .sort_values(
                "composite_quality_score",
                ascending=False,
            )
            .drop_duplicates(
                subset=[
                    "company_id"
                ]
                if "company_id" in top5.columns
                else None
            )
            .head(5)
        )


        if not top5.empty:

            # ------------------------------------------------
            # Build company-name lookup
            # ------------------------------------------------

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


            # ------------------------------------------------
            # Resolve ticker
            # ------------------------------------------------

            if "company_id" in top5.columns:

                top5["Ticker"] = (
                    top5["company_id"]
                    .astype(str)
                    .str.strip()
                )

            elif "id" in top5.columns:

                top5["Ticker"] = (
                    top5["id"]
                    .astype(str)
                    .str.strip()
                )

            else:

                top5["Ticker"] = "N/A"


            # ------------------------------------------------
            # Company names
            # ------------------------------------------------

            top5["Company"] = (
                top5["Ticker"]
                .map(company_map)
                .fillna(
                    top5["Ticker"]
                )
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


            display_df[
                "Quality Score"
            ] = pd.to_numeric(
                display_df[
                    "Quality Score"
                ],
                errors="coerce",
            ).round(2)


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


    else:

        st.info(
            "Composite quality data is not available."
        )


# ============================================================
# VALUATION INSIGHTS
# ============================================================

with valuation_col:

    st.markdown(
        "### Valuation Insights"
    )

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
                and "flag" in valuation_summary.columns
            ):

                flags = (
                    valuation_summary[
                        "flag"
                    ]
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
        "Caution: P/E > 1.5× sector median. "
        "Discount: P/E < 0.7× sector median. "
        "Otherwise Fair."
    )


# ============================================================
# FINAL DATA STATUS
# ============================================================

st.write("")


status_left, status_right = st.columns(
    [2, 1]
)


with status_left:

    st.caption(
        f"Data coverage · "
        f"{available_ratio_tickers} / "
        f"{total_companies} companies"
    )


with status_right:

    st.caption(
        f"Selected financial year · {selected_year}"
    )


# ============================================================
# HOME FOOTER
# ============================================================

st.divider()


footer1, footer2, footer3 = st.columns(
    3
)


with footer1:

    st.caption(
        f"N100 UNIVERSE · "
        f"{total_companies} COMPANIES TRACKED"
    )


with footer2:

    st.caption(
        f"FINANCIAL YEAR · "
        f"{selected_year}"
    )


with footer3:

    st.caption(
        "DATA REFRESH · 10 MINUTES"
    )