import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


# ============================================================
# DATABASE
# ============================================================

from dashboard.utils.db import (
    get_companies,
    get_pl,
    get_ratios,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Trend Analysis",
    page_icon="📈",
    layout="wide",
)


# ============================================================
# TITLE
# ============================================================

st.title("📈 Trend Analysis")

st.caption(
    "Analyze 10-year financial trends with year-over-year "
    "growth annotations."
)


# ============================================================
# COMPANY DATA
# ============================================================

companies = get_companies().copy()


# ============================================================
# COMPANY SEARCH
# ============================================================

st.sidebar.markdown(
    "## 🔎 Company Search"
)


search_text = st.sidebar.text_input(
    "Search company or ticker",
    placeholder="Example: INFY or Infosys",
)


company_id_column = (
    "company_id"
    if "company_id" in companies.columns
    else "id"
)


company_name_column = (
    "company_name"
    if "company_name" in companies.columns
    else company_id_column
)


search_df = companies.copy()


if search_text.strip():

    query = (
        search_text
        .strip()
        .lower()
    )

    mask = (
        search_df[company_id_column]
        .astype(str)
        .str.lower()
        .str.contains(
            query,
            na=False,
        )
        |
        search_df[company_name_column]
        .astype(str)
        .str.lower()
        .str.contains(
            query,
            na=False,
        )
    )

    search_df = search_df[mask]


if search_df.empty:

    st.warning(
        "Ticker not found — please try another."
    )

    st.stop()


# ============================================================
# COMPANY SELECTOR
# ============================================================

search_df = search_df.copy()

search_df["display_name"] = (
    search_df[company_name_column]
    .astype(str)
    + " ("
    + search_df[company_id_column]
    .astype(str)
    + ")"
)


selected_company_display = st.sidebar.selectbox(
    "Select Company",
    search_df["display_name"].tolist(),
)


selected_company_row = search_df[
    search_df["display_name"]
    == selected_company_display
].iloc[0]


selected_company_id = (
    selected_company_row[company_id_column]
)


# ============================================================
# LOAD DATA
# ============================================================

pl_df = get_pl(
    selected_company_id
).copy()


ratios_df = get_ratios(
    selected_company_id
).copy()


# ============================================================
# NORMALIZE YEARS
# ============================================================

for dataframe in [
    pl_df,
    ratios_df,
]:

    if not dataframe.empty:

        dataframe["year"] = (
            dataframe["year"]
            .astype(str)
            .str[:4]
        )


# ============================================================
# MERGE
# ============================================================

if not pl_df.empty and not ratios_df.empty:

    trend_df = pl_df.merge(
        ratios_df,
        on=[
            "company_id",
            "year",
        ],
        how="outer",
    )

elif not pl_df.empty:

    trend_df = pl_df.copy()

elif not ratios_df.empty:

    trend_df = ratios_df.copy()

else:

    st.warning(
        "No historical financial data available."
    )

    st.stop()


# ============================================================
# YEAR
# ============================================================

trend_df["year_numeric"] = pd.to_numeric(
    trend_df["year"],
    errors="coerce",
)


trend_df = (
    trend_df
    .dropna(subset=["year_numeric"])
    .sort_values("year_numeric")
)


# ============================================================
# AVAILABLE METRICS
# ============================================================

metric_mapping = {

    "Revenue": "sales",

    "Net Profit": "net_profit",

    "ROE": "return_on_equity_pct",

    "ROCE": "return_on_capital_employed_pct",

    "Net Profit Margin": "net_profit_margin_pct",

    "D/E": "debt_to_equity",

    "FCF": "free_cash_flow_cr",

    "PAT CAGR 5yr": "pat_cagr_5yr",

    "Revenue CAGR 5yr": "revenue_cagr_5yr",

    "Composite Score": "composite_quality_score",
}


available_metrics = {
    label: column
    for label, column in metric_mapping.items()
    if column in trend_df.columns
}


# ============================================================
# METRIC SELECTOR
# ============================================================

st.sidebar.markdown(
    "## 📊 Metrics"
)


selected_metrics = st.sidebar.multiselect(
    "Select up to 3 metrics",
    list(available_metrics.keys()),
    default=[
        metric
        for metric in [
            "Revenue",
            "Net Profit",
        ]
        if metric in available_metrics
    ],
    max_selections=3,
)


if not selected_metrics:

    st.info(
        "Select at least one metric."
    )

    st.stop()


# ============================================================
# HEADER
# ============================================================

company_name = selected_company_row[
    company_name_column
]


st.subheader(
    f"{company_name} ({selected_company_id})"
)


# ============================================================
# DATA AVAILABILITY
# ============================================================

years = (
    trend_df["year_numeric"]
    .astype(int)
    .tolist()
)


if years:

    min_year = min(years)
    max_year = max(years)

    st.caption(
        f"Data available: {min_year}–{max_year}"
    )

    if max_year - min_year < 9:

        st.info(
            "This company has fewer than 10 years "
            "of available data."
        )


# ============================================================
# CHART
# ============================================================

fig = go.Figure()


for metric_index, metric_name in enumerate(
    selected_metrics
):

    column = available_metrics[
        metric_name
    ]


    data = trend_df[
        [
            "year_numeric",
            column,
        ]
    ].copy()


    data[column] = pd.to_numeric(
        data[column],
        errors="coerce",
    )


    data = data.dropna(
        subset=[column]
    )


    if data.empty:
        continue


    data = data.sort_values(
        "year_numeric"
    )


    # --------------------------------------------------------
    # YoY calculation
    # --------------------------------------------------------

    data["yoy"] = (
        data[column]
        .pct_change()
        * 100
    )


    # --------------------------------------------------------
    # Axis assignment
    # --------------------------------------------------------

    if metric_index == 0:

        axis_name = "y"

    elif metric_index == 1:

        axis_name = "y2"

    else:

        axis_name = "y3"


    fig.add_trace(
        go.Scatter(
            x=data["year_numeric"],
            y=data[column],
            mode="lines+markers",
            name=metric_name,
            yaxis=axis_name,
            hovertemplate=(
                "<b>Year:</b> %{x}<br>"
                f"<b>{metric_name}:</b> "
                "%{y:.2f}<br>"
                "<extra></extra>"
            ),
        )
    )


    # --------------------------------------------------------
    # YoY annotations
    # --------------------------------------------------------

    for _, row in data.iterrows():

        if pd.notna(row["yoy"]):

            fig.add_annotation(
                x=row["year_numeric"],
                y=row[column],
                text=(
                    f"YoY {row['yoy']:+.1f}%"
                ),
                showarrow=False,
                yshift=12,
                font=dict(size=8),
                xanchor="center",
            )


# ============================================================
# AXIS TITLES
# ============================================================

axis_titles = [
    available_metrics[m]
    for m in selected_metrics
]


# ============================================================
# LAYOUT
# ============================================================

layout_updates = {

    "height": 650,

    "margin": dict(
        l=60,
        r=80,
        t=90,
        b=60,
    ),

    "hovermode": "x unified",

    "xaxis": dict(
        title="Year",
        tickmode="linear",
        dtick=1,
        tickformat="d",
    ),
}


# ------------------------------------------------------------
# Y axis 1
# ------------------------------------------------------------

if len(selected_metrics) >= 1:

    layout_updates["yaxis"] = {
        "title": selected_metrics[0],
        "side": "left",
    }


# ------------------------------------------------------------
# Y axis 2
# ------------------------------------------------------------

if len(selected_metrics) >= 2:

    layout_updates["yaxis2"] = {
        "title": selected_metrics[1],
        "overlaying": "y",
        "side": "right",
    }


# ------------------------------------------------------------
# Y axis 3
# ------------------------------------------------------------

if len(selected_metrics) >= 3:

    layout_updates["yaxis3"] = {
        "title": selected_metrics[2],
        "overlaying": "y",
        "side": "right",
        "position": 0.94,
    }


fig.update_layout(
    **layout_updates
)


st.plotly_chart(
    fig,
    use_container_width=True,
)


# ============================================================
# HISTORICAL DATA
# ============================================================

with st.expander(
    "📋 View Historical Data"
):

    history_columns = [
        "year_numeric"
    ]


    rename_map = {
        "year_numeric": "Year"
    }


    for metric in selected_metrics:

        column = available_metrics[
            metric
        ]

        if column in trend_df.columns:

            history_columns.append(
                column
            )

            rename_map[column] = metric


    history = trend_df[
        history_columns
    ].copy()


    history = history.rename(
        columns=rename_map
    )


    st.dataframe(
        history,
        use_container_width=True,
        hide_index=True,
    )