from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

CAPITAL_FILE = (
    PROJECT_ROOT
    / "output"
    / "capital_allocation.csv"
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Capital Allocation",
    page_icon="💰",
    layout="wide",
)


# ============================================================
# TITLE
# ============================================================

st.title("💰 Capital Allocation Map")

st.caption(
    "Explore all Nifty 100 companies grouped by "
    "capital allocation patterns."
)


# ============================================================
# LOAD CAPITAL DATA
# ============================================================

@st.cache_data(ttl=600)
def load_capital_data():

    if not CAPITAL_FILE.exists():

        return pd.DataFrame()

    return pd.read_csv(
        CAPITAL_FILE
    )


capital_df = load_capital_data()


# ============================================================
# VALIDATION
# ============================================================

if capital_df.empty:

    st.error(
        "Capital allocation data could not be loaded."
    )

    st.info(
        "Expected file: output/capital_allocation.csv"
    )

    st.stop()


required_columns = [
    "company_id",
    "year",
    "cfo_sign",
    "cfi_sign",
    "cff_sign",
    "pattern_label",
]


missing_columns = [
    column
    for column in required_columns
    if column not in capital_df.columns
]


if missing_columns:

    st.error(
        f"Missing columns: {missing_columns}"
    )

    st.write(
        "Available columns:",
        list(capital_df.columns),
    )

    st.stop()


# ============================================================
# NORMALIZE YEAR
# ============================================================

capital_df["year_numeric"] = pd.to_numeric(
    capital_df["year"],
    errors="coerce",
)


# ============================================================
# KEEP LATEST YEAR FOR EACH COMPANY
# ============================================================

latest_company_year = (
    capital_df
    .sort_values("year_numeric")
    .drop_duplicates(
        subset=["company_id"],
        keep="last",
    )
    .copy()
)


# ============================================================
# CLEAN PATTERN
# ============================================================

latest_company_year["pattern_label"] = (
    latest_company_year["pattern_label"]
    .fillna("Unclassified")
    .astype(str)
)


# ============================================================
# SUMMARY
# ============================================================

pattern_counts = (
    latest_company_year
    .groupby("pattern_label")
    .size()
    .reset_index(name="company_count")
    .sort_values(
        "company_count",
        ascending=False,
    )
)


# ============================================================
# TOP METRICS
# ============================================================

col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        "Companies",
        latest_company_year["company_id"].nunique(),
    )


with col2:

    st.metric(
        "Patterns",
        pattern_counts["pattern_label"].nunique(),
    )


with col3:

    st.metric(
        "Largest Pattern",
        int(pattern_counts["company_count"].max()),
    )


# ============================================================
# TREEMAP
# ============================================================

st.subheader(
    "🗺️ Capital Allocation Patterns"
)


treemap_df = pattern_counts.copy()

treemap_df["All Companies"] = "Nifty 100"


fig = px.treemap(
    treemap_df,
    path=[
        "All Companies",
        "pattern_label",
    ],
    values="company_count",
    hover_data={
        "company_count": True,
    },
)


fig.update_layout(
    height=620,
    margin=dict(
        l=10,
        r=10,
        t=40,
        b=10,
    ),
)


st.plotly_chart(
    fig,
    use_container_width=True,
)


# ============================================================
# PATTERN SELECTION
# ============================================================

st.subheader(
    "🔍 Explore Pattern"
)


selected_pattern = st.selectbox(
    "Select a capital allocation pattern",
    pattern_counts["pattern_label"].tolist(),
)


selected_companies = latest_company_year[
    latest_company_year["pattern_label"]
    == selected_pattern
].copy()


# ============================================================
# COMPANY COUNT
# ============================================================

st.write(
    f"### {selected_pattern}"
)

st.caption(
    f"{len(selected_companies)} companies"
)


# ============================================================
# COMPANY TABLE
# ============================================================

display_columns = [
    "company_id",
    "year",
    "cfo_sign",
    "cfi_sign",
    "cff_sign",
    "pattern_label",
]


display_df = selected_companies[
    display_columns
].copy()


display_df = display_df.rename(
    columns={
        "company_id": "Company ID",
        "year": "Year",
        "cfo_sign": "CFO Sign",
        "cfi_sign": "CFI Sign",
        "cff_sign": "CFF Sign",
        "pattern_label": "Pattern",
    }
)


st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
)


# ============================================================
# DOWNLOAD
# ============================================================

csv_data = display_df.to_csv(
    index=False
).encode("utf-8")


st.download_button(
    "⬇️ Download Selected Pattern CSV",
    data=csv_data,
    file_name=(
        "capital_allocation_"
        + selected_pattern.replace(" ", "_")
        + ".csv"
    ),
    mime="text/csv",
)