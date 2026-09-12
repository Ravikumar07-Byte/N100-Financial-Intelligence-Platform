import sys
import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


DB_PATH = PROJECT_ROOT / "nifty100.db"


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Sector Analysis",
    page_icon="🏭",
    layout="wide",
)


# ============================================================
# TITLE
# ============================================================

st.title("🏭 Sector Analysis")

st.caption(
    "Compare Nifty 100 companies using revenue, ROE, "
    "market capitalization and sub-sector."
)


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data(ttl=600)
def load_sector_data():

    connection = sqlite3.connect(DB_PATH)

    companies = pd.read_sql_query(
        """
        SELECT
            id AS company_id,
            company_name,
            about_company
        FROM companies
        """,
        connection,
    )

    sectors = pd.read_sql_query(
        """
        SELECT
            company_id,
            broad_sector,
            sub_sector,
            index_weight_pct,
            market_cap_category
        FROM sectors
        """,
        connection,
    )

    profit_loss = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            sales,
            net_profit
        FROM profitandloss
        """,
        connection,
    )

    ratios = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            return_on_equity_pct,
            net_profit_margin_pct,
            debt_to_equity
        FROM financial_ratios
        """,
        connection,
    )

    market = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            market_cap_crore
        FROM market_cap
        """,
        connection,
    )

    connection.close()

    return (
        companies,
        sectors,
        profit_loss,
        ratios,
        market,
    )


(
    companies,
    sectors,
    profit_loss,
    ratios,
    market,
) = load_sector_data()


# ============================================================
# NORMALIZE YEAR
# ============================================================

for dataframe in [
    profit_loss,
    ratios,
    market,
]:

    if not dataframe.empty:

        dataframe["year"] = (
            dataframe["year"]
            .astype(str)
            .str[:4]
        )


# ============================================================
# LATEST YEAR FOR EACH DATASET
# ============================================================

def latest_year(dataframe):

    if dataframe.empty:
        return None

    years = pd.to_numeric(
        dataframe["year"],
        errors="coerce",
    ).dropna()

    if years.empty:
        return None

    return int(years.max())


pl_year = latest_year(profit_loss)
ratio_year = latest_year(ratios)
market_year = latest_year(market)


# ============================================================
# LATEST RECORDS
# ============================================================

latest_pl = profit_loss[
    profit_loss["year"] == str(pl_year)
].copy() if pl_year else pd.DataFrame()


latest_ratios = ratios[
    ratios["year"] == str(ratio_year)
].copy() if ratio_year else pd.DataFrame()


latest_market = market[
    market["year"] == str(market_year)
].copy() if market_year else pd.DataFrame()


# ============================================================
# MERGE COMPANY + SECTOR
# ============================================================

sector_df = companies.merge(
    sectors,
    on="company_id",
    how="left",
)


# ============================================================
# MERGE P&L
# ============================================================

if not latest_pl.empty:

    sector_df = sector_df.merge(
        latest_pl[
            [
                "company_id",
                "sales",
                "net_profit",
            ]
        ],
        on="company_id",
        how="left",
    )


# ============================================================
# MERGE RATIOS
# ============================================================

if not latest_ratios.empty:

    sector_df = sector_df.merge(
        latest_ratios[
            [
                "company_id",
                "return_on_equity_pct",
                "net_profit_margin_pct",
                "debt_to_equity",
            ]
        ],
        on="company_id",
        how="left",
    )


# ============================================================
# MERGE MARKET CAP
# ============================================================

if not latest_market.empty:

    sector_df = sector_df.merge(
        latest_market[
            [
                "company_id",
                "market_cap_crore",
            ]
        ],
        on="company_id",
        how="left",
    )


# ============================================================
# CLEAN SECTOR FIELDS
# ============================================================

sector_df["broad_sector"] = (
    sector_df["broad_sector"]
    .fillna("Unknown")
    .astype(str)
)

sector_df["sub_sector"] = (
    sector_df["sub_sector"]
    .fillna("Other")
    .astype(str)
)


# ============================================================
# NUMERIC COLUMNS
# ============================================================

numeric_columns = [
    "sales",
    "net_profit",
    "return_on_equity_pct",
    "net_profit_margin_pct",
    "debt_to_equity",
    "market_cap_crore",
]


for column in numeric_columns:

    if column in sector_df.columns:

        sector_df[column] = pd.to_numeric(
            sector_df[column],
            errors="coerce",
        )


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.markdown("## 🏭 Sector")

sector_list = sorted(
    sector_df["broad_sector"]
    .dropna()
    .unique()
    .tolist()
)


if not sector_list:

    st.error("No sector data available.")

    st.stop()


selected_sector = st.sidebar.selectbox(
    "Select Sector",
    sector_list,
)


# ============================================================
# FILTER SELECTED SECTOR
# ============================================================

selected_df = sector_df[
    sector_df["broad_sector"]
    == selected_sector
].copy()


# ============================================================
# HEADER KPIs
# ============================================================

st.subheader(
    f"{selected_sector} — Sector Analysis"
)

col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "Companies",
        len(selected_df),
    )


with col2:

    median_roe = selected_df[
        "return_on_equity_pct"
    ].median()

    st.metric(
        "Median ROE",
        "N/A"
        if pd.isna(median_roe)
        else f"{median_roe:.2f}%",
    )


with col3:

    median_revenue = selected_df[
        "sales"
    ].median()

    st.metric(
        "Median Revenue",
        "N/A"
        if pd.isna(median_revenue)
        else f"₹{median_revenue:,.0f} Cr",
    )


with col4:

    median_market_cap = selected_df[
        "market_cap_crore"
    ].median()

    st.metric(
        "Median Market Cap",
        "N/A"
        if pd.isna(median_market_cap)
        else f"₹{median_market_cap:,.0f} Cr",
    )


# ============================================================
# BUBBLE CHART
# ============================================================

st.subheader("📊 Revenue vs ROE")

bubble_df = selected_df.dropna(
    subset=[
        "sales",
        "return_on_equity_pct",
        "market_cap_crore",
    ]
).copy()


if bubble_df.empty:

    st.warning(
        "Insufficient data for the sector bubble chart."
    )

else:

    fig = px.scatter(
        bubble_df,
        x="sales",
        y="return_on_equity_pct",
        size="market_cap_crore",
        color="sub_sector",
        hover_name="company_name",
        hover_data={
            "company_id": True,
            "sales": ":,.0f",
            "return_on_equity_pct": ":.2f",
            "market_cap_crore": ":,.0f",
            "sub_sector": True,
        },
        labels={
            "sales": "Revenue (₹ Cr)",
            "return_on_equity_pct": "ROE (%)",
            "market_cap_crore": "Market Cap (₹ Cr)",
            "sub_sector": "Sub-Sector",
        },
        title=(
            f"{selected_sector}: Revenue vs ROE"
        ),
        size_max=55,
    )

    fig.update_layout(
        height=620,
        margin=dict(
            l=40,
            r=40,
            t=80,
            b=40,
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


# ============================================================
# SECTOR MEDIAN KPI BAR CHART
# ============================================================

st.subheader("📈 Sector Median KPIs")


median_data = {
    "Revenue (₹ Cr)": selected_df["sales"].median(),
    "ROE (%)": selected_df["return_on_equity_pct"].median(),
    "Net Profit Margin (%)": selected_df[
        "net_profit_margin_pct"
    ].median(),
    "D/E": selected_df["debt_to_equity"].median(),
}


median_df = pd.DataFrame(
    {
        "Metric": list(median_data.keys()),
        "Median": list(median_data.values()),
    }
).dropna()


if median_df.empty:

    st.warning(
        "No median KPI data available."
    )

else:

    median_fig = px.bar(
        median_df,
        x="Metric",
        y="Median",
        text="Median",
        title=(
            f"{selected_sector} Median KPIs"
        ),
    )

    median_fig.update_traces(
        texttemplate="%{text:.2f}",
        textposition="outside",
    )

    median_fig.update_layout(
        height=450,
        margin=dict(
            l=40,
            r=40,
            t=80,
            b=40,
        ),
    )

    st.plotly_chart(
        median_fig,
        use_container_width=True,
    )


# ============================================================
# COMPANY TABLE
# ============================================================

with st.expander(
    "📋 Companies in Selected Sector"
):

    table_columns = [
        "company_id",
        "company_name",
        "sub_sector",
        "sales",
        "return_on_equity_pct",
        "market_cap_crore",
    ]

    table_columns = [
        column
        for column in table_columns
        if column in selected_df.columns
    ]

    display_df = selected_df[
        table_columns
    ].copy()

    display_df = display_df.rename(
        columns={
            "company_id": "Company ID",
            "company_name": "Company",
            "sub_sector": "Sub-Sector",
            "sales": "Revenue (₹ Cr)",
            "return_on_equity_pct": "ROE (%)",
            "market_cap_crore": "Market Cap (₹ Cr)",
        }
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )