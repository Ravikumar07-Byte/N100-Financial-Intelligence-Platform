"""
N100 Financial Intelligence Platform
Day 26 - Valuation Module

Responsibilities
----------------
1. Load market valuation data.
2. Calculate FCF Yield for all 92 companies.
3. Calculate 5-year median P/E for each company.
4. Calculate latest sector median P/E.
5. Calculate P/E versus sector median.
6. Assign valuation flags:
      Caution  -> P/E > sector median * 1.5
      Discount -> P/E < sector median * 0.7
      Fair     -> otherwise
7. Generate:
      output/valuation_summary.xlsx
      output/valuation_flags.csv
"""

from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = PROJECT_ROOT / "nifty100.db"

MARKET_CAP_FILE = (
    PROJECT_ROOT
    / "data"
    / "supporting"
    / "market_cap.xlsx"
)

OUTPUT_DIR = PROJECT_ROOT / "output"

VALUATION_SUMMARY_FILE = (
    OUTPUT_DIR / "valuation_summary.xlsx"
)

VALUATION_FLAGS_FILE = (
    OUTPUT_DIR / "valuation_flags.csv"
)


# ============================================================
# REQUIRED OUTPUT COLUMNS
# ============================================================

OUTPUT_COLUMNS = [
    "company_id",
    "company_name",
    "sector",
    "P/E",
    "P/B",
    "EV/EBITDA",
    "FCF_yield_pct",
    "5yr_median_PE",
    "PE_vs_sector_median_pct",
    "flag",
]


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    """Return a connection to the project SQLite database."""

    return sqlite3.connect(DB_PATH)


# ============================================================
# LOAD COMPANY DATA
# ============================================================

def load_companies():

    connection = get_connection()

    query = """
        SELECT
            id AS company_id,
            company_name
        FROM companies
    """

    df = pd.read_sql_query(
        query,
        connection,
    )

    connection.close()

    return df


# ============================================================
# LOAD SECTOR DATA
# ============================================================

def load_sectors():

    connection = get_connection()

    query = """
        SELECT
            company_id,
            broad_sector AS sector,
            sub_sector
        FROM sectors
    """

    df = pd.read_sql_query(
        query,
        connection,
    )

    connection.close()

    return df


# ============================================================
# LOAD FINANCIAL RATIOS
# ============================================================

def load_financial_ratios():

    connection = get_connection()

    query = """
        SELECT
            company_id,
            year,
            free_cash_flow_cr
        FROM financial_ratios
    """

    df = pd.read_sql_query(
        query,
        connection,
    )

    connection.close()

    return df


# ============================================================
# LOAD MARKET CAP EXCEL
# ============================================================

def load_market_cap_excel():

    if not MARKET_CAP_FILE.exists():

        raise FileNotFoundError(
            f"Market cap file not found: "
            f"{MARKET_CAP_FILE}"
        )

    df = pd.read_excel(
        MARKET_CAP_FILE
    )

    return df


# ============================================================
# NORMALIZE MARKET CAP COLUMNS
# ============================================================

def normalize_market_cap_columns(df):

    df = df.copy()

    # --------------------------------------------------------
    # Normalize column names
    # --------------------------------------------------------

    df.columns = [
        str(column).strip()
        for column in df.columns
    ]

    # --------------------------------------------------------
    # Find company ID column
    # --------------------------------------------------------

    company_candidates = [
        "company_id",
        "Company ID",
        "company",
        "ticker",
        "symbol",
        "id",
    ]

    company_column = None

    for column in company_candidates:

        if column in df.columns:
            company_column = column
            break

    if company_column is None:

        raise ValueError(
            "Could not identify company_id column "
            f"in market_cap.xlsx. "
            f"Available columns: {list(df.columns)}"
        )

    if company_column != "company_id":

        df = df.rename(
            columns={
                company_column: "company_id"
            }
        )

    # --------------------------------------------------------
    # Required valuation columns
    # --------------------------------------------------------

    rename_map = {}

    column_lower = {
        str(column).lower().strip(): column
        for column in df.columns
    }

    # Year
    for candidate in [
        "year",
        "financial_year",
        "fy",
    ]:

        if candidate in column_lower:

            original = column_lower[candidate]

            rename_map[original] = "year"

            break

    # Market cap
    for candidate in [
        "market_cap_crore",
        "market cap crore",
        "market_cap",
        "market cap",
    ]:

        if candidate in column_lower:

            original = column_lower[candidate]

            rename_map[original] = (
                "market_cap_crore"
            )

            break

    # P/E
    for candidate in [
        "pe_ratio",
        "p/e",
        "pe",
        "p_e",
    ]:

        if candidate in column_lower:

            original = column_lower[candidate]

            rename_map[original] = "pe_ratio"

            break

    # P/B
    for candidate in [
        "pb_ratio",
        "p/b",
        "pb",
        "p_b",
    ]:

        if candidate in column_lower:

            original = column_lower[candidate]

            rename_map[original] = "pb_ratio"

            break

    # EV/EBITDA
    for candidate in [
        "ev_ebitda",
        "ev/ebitda",
        "ev ebitda",
    ]:

        if candidate in column_lower:

            original = column_lower[candidate]

            rename_map[original] = "ev_ebitda"

            break

    df = df.rename(
        columns=rename_map
    )

    # --------------------------------------------------------
    # Validate required columns
    # --------------------------------------------------------

    required = [
        "company_id",
        "year",
        "market_cap_crore",
        "pe_ratio",
        "pb_ratio",
        "ev_ebitda",
    ]

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:

        raise ValueError(
            "market_cap.xlsx is missing required "
            f"columns: {missing}\n"
            f"Available columns: {list(df.columns)}"
        )

    # --------------------------------------------------------
    # Normalize company IDs
    # --------------------------------------------------------

    df["company_id"] = (
        df["company_id"]
        .astype(str)
        .str.strip()
    )

    # --------------------------------------------------------
    # Normalize year
    # --------------------------------------------------------

    df["year"] = (
        df["year"]
        .astype(str)
        .str[:4]
    )

    # --------------------------------------------------------
    # Numeric columns
    # --------------------------------------------------------

    numeric_columns = [
        "market_cap_crore",
        "pe_ratio",
        "pb_ratio",
        "ev_ebitda",
    ]

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    return df


# ============================================================
# NORMALIZE FINANCIAL RATIO DATA
# ============================================================

def normalize_ratio_data(df):

    df = df.copy()

    df["company_id"] = (
        df["company_id"]
        .astype(str)
        .str.strip()
    )

    df["year"] = (
        df["year"]
        .astype(str)
        .str[:4]
    )

    df["free_cash_flow_cr"] = pd.to_numeric(
        df["free_cash_flow_cr"],
        errors="coerce",
    )

    return df


# ============================================================
# GET LATEST MARKET VALUATION
# ============================================================

def get_latest_market_data(market_df):

    df = market_df.copy()

    year_numeric = pd.to_numeric(
        df["year"],
        errors="coerce",
    )

    df["_year_numeric"] = year_numeric

    df = df.dropna(
        subset=["_year_numeric"]
    )

    if df.empty:

        raise ValueError(
            "No valid market valuation years found."
        )

    latest_year = int(
        df["_year_numeric"].max()
    )

    latest = df[
        df["_year_numeric"]
        == latest_year
    ].copy()

    # One record per company
    latest = (
        latest
        .sort_values("_year_numeric")
        .drop_duplicates(
            subset=["company_id"],
            keep="last",
        )
    )

    latest = latest.drop(
        columns=["_year_numeric"]
    )

    return latest, latest_year


# ============================================================
# GET LATEST FCF
# ============================================================

def get_latest_fcf(ratio_df):

    df = ratio_df.copy()

    year_numeric = pd.to_numeric(
        df["year"],
        errors="coerce",
    )

    df["_year_numeric"] = year_numeric

    df = df.dropna(
        subset=["_year_numeric"]
    )

    if df.empty:

        return pd.DataFrame(
            columns=[
                "company_id",
                "free_cash_flow_cr",
                "fcf_year",
            ]
        )

    # Latest FCF year for each company
    df = (
        df
        .sort_values(
            [
                "company_id",
                "_year_numeric",
            ]
        )
        .drop_duplicates(
            subset=["company_id"],
            keep="last",
        )
    )

    result = df[
        [
            "company_id",
            "free_cash_flow_cr",
            "_year_numeric",
        ]
    ].copy()

    result = result.rename(
        columns={
            "_year_numeric": "fcf_year"
        }
    )

    return result


# ============================================================
# CALCULATE 5-YEAR MEDIAN P/E
# ============================================================

def calculate_five_year_median_pe(
    market_df,
    latest_year,
):

    df = market_df.copy()

    df["_year_numeric"] = pd.to_numeric(
        df["year"],
        errors="coerce",
    )

    # Five-year window including latest year
    first_year = latest_year - 4

    df = df[
        (
            df["_year_numeric"]
            >= first_year
        )
        &
        (
            df["_year_numeric"]
            <= latest_year
        )
    ].copy()

    # Ignore invalid/non-positive P/E
    # because P/E is not meaningful for loss-making companies.
    df.loc[
        df["pe_ratio"] <= 0,
        "pe_ratio",
    ] = np.nan

    median_df = (
        df
        .groupby("company_id")[
            "pe_ratio"
        ]
        .median()
        .reset_index()
    )

    median_df = median_df.rename(
        columns={
            "pe_ratio": "5yr_median_PE"
        }
    )

    return median_df


# ============================================================
# CALCULATE SECTOR MEDIAN P/E
# ============================================================

def calculate_sector_median_pe(
    latest_market,
    sectors,
):

    df = latest_market.merge(
        sectors[
            [
                "company_id",
                "sector",
            ]
        ],
        on="company_id",
        how="left",
    )

    # Ignore invalid/non-positive P/E
    valid_pe = df[
        df["pe_ratio"].notna()
        &
        (df["pe_ratio"] > 0)
        &
        df["sector"].notna()
    ].copy()

    sector_medians = (
        valid_pe
        .groupby("sector")[
            "pe_ratio"
        ]
        .median()
        .reset_index()
    )

    sector_medians = sector_medians.rename(
        columns={
            "pe_ratio": "sector_median_pe"
        }
    )

    return sector_medians


# ============================================================
# APPLY VALUATION FLAG
# ============================================================

def valuation_flag(
    pe,
    sector_median,
):

    if pd.isna(pe):

        return "Fair"

    if pd.isna(sector_median):

        return "Fair"

    if pe > (
        sector_median * 1.5
    ):

        return "Caution"

    if pe < (
        sector_median * 0.7
    ):

        return "Discount"

    return "Fair"


# ============================================================
# BUILD VALUATION SUMMARY
# ============================================================

def build_valuation_summary():

    print("=" * 70)
    print("N100 FINANCIAL INTELLIGENCE PLATFORM")
    print("DAY 26 - VALUATION MODULE")
    print("=" * 70)

    # --------------------------------------------------------
    # Load data
    # --------------------------------------------------------

    print("\n[1/8] Loading companies...")

    companies = load_companies()

    print(
        f"      Companies loaded: "
        f"{len(companies)}"
    )

    print(
        "\n[2/8] Loading sectors..."
    )

    sectors = load_sectors()

    print(
        f"      Sector assignments: "
        f"{len(sectors)}"
    )

    print(
        "\n[3/8] Loading financial ratios..."
    )

    ratios = load_financial_ratios()

    ratios = normalize_ratio_data(
        ratios
    )

    print(
        f"      Ratio rows: "
        f"{len(ratios)}"
    )

    print(
        "\n[4/8] Loading market_cap.xlsx..."
    )

    market_df = load_market_cap_excel()

    market_df = normalize_market_cap_columns(
        market_df
    )

    print(
        f"      Market valuation rows: "
        f"{len(market_df)}"
    )

    # --------------------------------------------------------
    # Latest market data
    # --------------------------------------------------------

    print(
        "\n[5/8] Determining latest market year..."
    )

    latest_market, latest_year = (
        get_latest_market_data(
            market_df
        )
    )

    print(
        f"      Latest market year: "
        f"{latest_year}"
    )

    # --------------------------------------------------------
    # Latest FCF
    # --------------------------------------------------------

    latest_fcf = get_latest_fcf(
        ratios
    )

    # --------------------------------------------------------
    # Five-year median PE
    # --------------------------------------------------------

    five_year_median = (
        calculate_five_year_median_pe(
            market_df,
            latest_year,
        )
    )

    # --------------------------------------------------------
    # Sector median PE
    # --------------------------------------------------------

    sector_medians = (
        calculate_sector_median_pe(
            latest_market,
            sectors,
        )
    )

    # --------------------------------------------------------
    # Merge company + sector
    # --------------------------------------------------------

    summary = companies.merge(
        sectors[
            [
                "company_id",
                "sector",
            ]
        ],
        on="company_id",
        how="left",
    )

    # --------------------------------------------------------
    # Merge latest market valuation
    # --------------------------------------------------------

    market_columns = [
        "company_id",
        "market_cap_crore",
        "pe_ratio",
        "pb_ratio",
        "ev_ebitda",
    ]

    summary = summary.merge(
        latest_market[
            market_columns
        ],
        on="company_id",
        how="left",
    )

    # --------------------------------------------------------
    # Merge latest FCF
    # --------------------------------------------------------

    summary = summary.merge(
        latest_fcf[
            [
                "company_id",
                "free_cash_flow_cr",
            ]
        ],
        on="company_id",
        how="left",
    )

    # --------------------------------------------------------
    # Calculate FCF yield
    # --------------------------------------------------------

    summary["FCF_yield_pct"] = np.where(
        (
            summary["market_cap_crore"]
            .notna()
        )
        &
        (
            summary["market_cap_crore"]
            > 0
        )
        &
        (
            summary["free_cash_flow_cr"]
            .notna()
        ),
        (
            summary["free_cash_flow_cr"]
            /
            summary["market_cap_crore"]
            *
            100
        ),
        np.nan,
    )

    # --------------------------------------------------------
    # Merge 5-year median PE
    # --------------------------------------------------------

    summary = summary.merge(
        five_year_median,
        on="company_id",
        how="left",
    )

    # --------------------------------------------------------
    # Merge sector median PE
    # --------------------------------------------------------

    summary = summary.merge(
        sector_medians,
        on="sector",
        how="left",
    )

    # --------------------------------------------------------
    # P/E vs sector median
    # --------------------------------------------------------

    summary["PE_vs_sector_median_pct"] = np.where(
        (
            summary["pe_ratio"].notna()
        )
        &
        (
            summary["sector_median_pe"].notna()
        )
        &
        (
            summary["sector_median_pe"] != 0
        ),
        (
            (
                summary["pe_ratio"]
                /
                summary["sector_median_pe"]
            )
            - 1
        )
        * 100,
        np.nan,
    )

    # --------------------------------------------------------
    # Valuation flags
    # --------------------------------------------------------

    summary["flag"] = summary.apply(
        lambda row: valuation_flag(
            row["pe_ratio"],
            row["sector_median_pe"],
        ),
        axis=1,
    )

    # --------------------------------------------------------
    # Rename final valuation columns
    # --------------------------------------------------------

    summary = summary.rename(
        columns={
            "pe_ratio": "P/E",
            "pb_ratio": "P/B",
            "ev_ebitda": "EV/EBITDA",
        }
    )

    # --------------------------------------------------------
    # Keep exactly required output columns
    # --------------------------------------------------------

    summary = summary[
        OUTPUT_COLUMNS
    ].copy()

    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    summary = summary.sort_values(
        [
            "flag",
            "company_id",
        ],
        ascending=[
            True,
            True,
        ],
    ).reset_index(
        drop=True
    )

    return (
        summary,
        latest_year,
        sector_medians,
    )


# ============================================================
# SAVE OUTPUTS
# ============================================================

def save_outputs(
    summary,
    latest_year,
    sector_medians,
):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Excel summary
    # --------------------------------------------------------

    summary.to_excel(
        VALUATION_SUMMARY_FILE,
        index=False,
        sheet_name="Valuation Summary",
    )

    # --------------------------------------------------------
    # Caution / Discount only
    # --------------------------------------------------------

    flags = summary[
        summary["flag"].isin(
            [
                "Caution",
                "Discount",
            ]
        )
    ].copy()

    flags.to_csv(
        VALUATION_FLAGS_FILE,
        index=False,
    )

    # --------------------------------------------------------
    # Verification output
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("VALUATION OUTPUT")
    print("=" * 70)

    print(
        f"\nLatest market year: {latest_year}"
    )

    print(
        f"Companies in summary: "
        f"{len(summary)}"
    )

    print(
        f"Unique companies: "
        f"{summary['company_id'].nunique()}"
    )

    print(
        "\nFlag distribution:"
    )

    print(
        summary["flag"]
        .value_counts()
        .to_string()
    )

    print(
        "\nFCF Yield available:"
    )

    print(
        summary["FCF_yield_pct"]
        .notna()
        .sum()
    )

    print(
        "\nSector medians:"
    )

    print(
        sector_medians.to_string(
            index=False
        )
    )

    print(
        "\nFiles generated:"
    )

    print(
        f"  {VALUATION_SUMMARY_FILE}"
    )

    print(
        f"  {VALUATION_FLAGS_FILE}"
    )

    print(
        "\nRequired columns:"
    )

    for column in summary.columns:

        print(
            f"  ✓ {column}"
        )

    print(
        "\n" + "=" * 70
    )
    print(
        "DAY 26 VALUATION MODULE COMPLETE"
    )
    print(
        "=" * 70
    )


# ============================================================
# MAIN
# ============================================================

def main():

    summary, latest_year, sector_medians = (
        build_valuation_summary()
    )

    save_outputs(
        summary,
        latest_year,
        sector_medians,
    )


if __name__ == "__main__":

    main()