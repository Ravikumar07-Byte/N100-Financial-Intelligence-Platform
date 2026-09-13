"""
N100 Financial Intelligence Platform
Sprint 5 - Day 31

Cash Flow Intelligence Module

Purpose:
    Analyze cash-flow quality and capital allocation
    for all companies in the N100 database.

Database:
    nifty100.db

Actual schema:

companies:
    id
    company_name

cashflow:
    company_id
    year
    operating_activity
    investing_activity
    financing_activity
    net_cash_flow

profitandloss:
    company_id
    year
    sales
    net_profit

financial_ratios:
    company_id
    year
    free_cash_flow_cr
    total_debt_cr
    cash_from_operations_cr

sectors:
    company_id
    broad_sector

Outputs:
    output/cashflow_intelligence.xlsx
    output/distress_alerts.csv
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import math
import re
import sqlite3

import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

DB_PATH = ROOT / "nifty100.db"
OUTPUT_DIR = ROOT / "output"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

INTELLIGENCE_OUTPUT = (
    OUTPUT_DIR / "cashflow_intelligence.xlsx"
)

DISTRESS_OUTPUT = (
    OUTPUT_DIR / "distress_alerts.csv"
)


# ============================================================
# ACTUAL DATABASE COLUMN NAMES
# ============================================================

COMPANY_ID_COLUMN = "id"

CASHFLOW_CFO_COLUMN = "operating_activity"
CASHFLOW_CFI_COLUMN = "investing_activity"
CASHFLOW_CFF_COLUMN = "financing_activity"

PNL_SALES_COLUMN = "sales"
PNL_PAT_COLUMN = "net_profit"

RATIO_FCF_COLUMN = "free_cash_flow_cr"
RATIO_DEBT_COLUMN = "total_debt_cr"

SECTOR_COLUMN = "broad_sector"


# ============================================================
# DATABASE HELPERS
# ============================================================

def load_table(
    conn: sqlite3.Connection,
    table_name: str
) -> pd.DataFrame:
    """
    Load a complete SQLite table into pandas.
    """

    return pd.read_sql_query(
        f'SELECT * FROM "{table_name}"',
        conn
    )


def check_required_tables(
    conn: sqlite3.Connection
) -> None:
    """
    Verify that all Day 31 source tables exist.
    """

    required_tables = {
        "companies",
        "cashflow",
        "profitandloss",
        "financial_ratios",
        "sectors"
    }

    rows = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        """
    ).fetchall()

    available_tables = {
        row[0]
        for row in rows
    }

    missing = (
        required_tables
        - available_tables
    )

    if missing:

        raise ValueError(
            "Missing required database tables: "
            f"{sorted(missing)}"
        )


# ============================================================
# DATA CLEANING
# ============================================================

def clean_company_id(
    value
) -> Optional[str]:
    """
    Convert company identifier to a clean string.
    """

    if pd.isna(value):
        return None

    return str(value).strip()


def safe_float(
    value
) -> Optional[float]:
    """
    Safely convert value to finite float.
    """

    try:

        if pd.isna(value):
            return None

        value = float(value)

        if not math.isfinite(value):
            return None

        return value

    except (
        TypeError,
        ValueError
    ):

        return None


def year_number(
    value
) -> Optional[int]:
    """
    Extract a four-digit year.

    Supports:
        2024
        FY2024
        2024-25
    """

    if pd.isna(value):
        return None

    text = str(value).strip()

    match = re.search(
        r"(19|20)\d{2}",
        text
    )

    if match:

        return int(
            match.group(0)
        )

    try:

        return int(
            float(text)
        )

    except (
        TypeError,
        ValueError
    ):

        return None


def prepare_dataframe(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Prepare company IDs and year values.
    """

    df = df.copy()

    if "company_id" in df.columns:

        df["company_id"] = (
            df["company_id"]
            .apply(clean_company_id)
        )

    if "year" in df.columns:

        df["_year_num"] = (
            df["year"]
            .apply(year_number)
        )

    return df


# ============================================================
# COMPANY HISTORY
# ============================================================

def get_company_history(
    df: pd.DataFrame,
    company_id: str
) -> pd.DataFrame:
    """
    Return chronological records for one company.
    """

    if df.empty:

        return pd.DataFrame()

    if "company_id" not in df.columns:

        return pd.DataFrame()

    result = df[
        df["company_id"] == company_id
    ].copy()

    if result.empty:

        return result

    if "_year_num" in result.columns:

        result = result.sort_values(
            "_year_num"
        )

    return result


def get_latest_row(
    df: pd.DataFrame,
    company_id: str
):
    """
    Return latest financial record.
    """

    history = get_company_history(
        df,
        company_id
    )

    if history.empty:

        return None

    return history.iloc[-1]


# ============================================================
# SECTOR LOOKUP
# ============================================================

def build_sector_lookup(
    sectors_df: pd.DataFrame
) -> dict:
    """
    Build:

        company_id -> broad_sector
    """

    lookup = {}

    for _, row in sectors_df.iterrows():

        company_id = clean_company_id(
            row.get("company_id")
        )

        sector = row.get(
            SECTOR_COLUMN
        )

        if company_id is None:

            continue

        if pd.isna(sector):

            sector = "Unknown"

        lookup[
            company_id
        ] = str(sector).strip()

    return lookup


# ============================================================
# CFO QUALITY
# ============================================================

def calculate_cfo_quality(
    company_id: str,
    cashflow_df: pd.DataFrame,
    pnl_df: pd.DataFrame
):
    """
    CFO Quality Score:

        CFO / PAT

    Average over the latest five valid years.

    Labels:

        > 1.0       High Quality
        0.5 - 1.0   Moderate
        < 0.5       Accrual Risk
    """

    cf_history = get_company_history(
        cashflow_df,
        company_id
    )

    pnl_history = get_company_history(
        pnl_df,
        company_id
    )

    if (
        cf_history.empty
        or pnl_history.empty
    ):

        return None, None

    ratios = []

    for _, cf_row in cf_history.iterrows():

        year = cf_row.get(
            "_year_num"
        )

        cfo = safe_float(
            cf_row.get(
                CASHFLOW_CFO_COLUMN
            )
        )

        if cfo is None:

            continue

        matching_pnl = pnl_history[
            pnl_history["_year_num"]
            == year
        ]

        if matching_pnl.empty:

            continue

        pat = safe_float(
            matching_pnl.iloc[-1].get(
                PNL_PAT_COLUMN
            )
        )

        if pat is None or pat == 0:

            continue

        ratio = cfo / pat

        if math.isfinite(ratio):

            ratios.append(
                ratio
            )

    ratios = ratios[-5:]

    if not ratios:

        return None, None

    average_ratio = float(
        np.mean(ratios)
    )

    if average_ratio > 1.0:

        label = "High Quality"

    elif average_ratio >= 0.5:

        label = "Moderate"

    else:

        label = "Accrual Risk"

    return (
        average_ratio,
        label
    )


# ============================================================
# CAPEX INTENSITY
# ============================================================

def calculate_capex_intensity(
    company_id: str,
    cashflow_df: pd.DataFrame,
    pnl_df: pd.DataFrame
):
    """
    CapEx Intensity:

        ABS(Investing Activity)
        ----------------------- × 100
              Sales

    Labels:

        < 3%       Asset Light
        3 - 8%     Moderate
        > 8%       Capital Intensive
    """

    cf_latest = get_latest_row(
        cashflow_df,
        company_id
    )

    pnl_latest = get_latest_row(
        pnl_df,
        company_id
    )

    if (
        cf_latest is None
        or pnl_latest is None
    ):

        return None, None

    investing = safe_float(
        cf_latest.get(
            CASHFLOW_CFI_COLUMN
        )
    )

    sales = safe_float(
        pnl_latest.get(
            PNL_SALES_COLUMN
        )
    )

    if (
        investing is None
        or sales is None
        or sales <= 0
    ):

        return None, None

    intensity = (
        abs(investing)
        / sales
        * 100
    )

    if intensity < 3:

        label = "Asset Light"

    elif intensity <= 8:

        label = "Moderate"

    else:

        label = "Capital Intensive"

    return (
        intensity,
        label
    )


# ============================================================
# FCF HISTORY
# ============================================================

def get_fcf_history(
    company_id: str,
    ratios_df: pd.DataFrame,
    cashflow_df: pd.DataFrame
):
    """
    Primary source:

        financial_ratios.free_cash_flow_cr

    Fallback:

        CFO + CFI
    """

    ratio_history = get_company_history(
        ratios_df,
        company_id
    )

    values = []

    if not ratio_history.empty:

        for _, row in ratio_history.iterrows():

            fcf = safe_float(
                row.get(
                    RATIO_FCF_COLUMN
                )
            )

            year = row.get(
                "_year_num"
            )

            if fcf is not None:

                values.append(
                    (
                        year,
                        fcf
                    )
                )

    if values:

        return values

    # --------------------------------------------------------
    # Fallback
    # --------------------------------------------------------

    cf_history = get_company_history(
        cashflow_df,
        company_id
    )

    if cf_history.empty:

        return []

    for _, row in cf_history.iterrows():

        cfo = safe_float(
            row.get(
                CASHFLOW_CFO_COLUMN
            )
        )

        cfi = safe_float(
            row.get(
                CASHFLOW_CFI_COLUMN
            )
        )

        year = row.get(
            "_year_num"
        )

        if (
            cfo is not None
            and cfi is not None
        ):

            values.append(
                (
                    year,
                    cfo + cfi
                )
            )

    return values


# ============================================================
# FCF CAGR
# ============================================================

def calculate_fcf_cagr_5yr(
    company_id: str,
    ratios_df: pd.DataFrame,
    cashflow_df: pd.DataFrame
):
    """
    Calculate five-year FCF CAGR.

    Requires six annual observations:

        Year 0 → Year 5
    """

    history = get_fcf_history(
        company_id,
        ratios_df,
        cashflow_df
    )

    if len(history) < 6:

        return None

    history = history[-6:]

    beginning = safe_float(
        history[0][1]
    )

    ending = safe_float(
        history[-1][1]
    )

    if (
        beginning is None
        or ending is None
        or beginning <= 0
        or ending <= 0
    ):

        return None

    try:

        cagr = (
            (
                ending / beginning
            )
            ** (1 / 5)
            - 1
        ) * 100

    except (
        ArithmeticError,
        ValueError
    ):

        return None

    if math.isfinite(cagr):

        return cagr

    return None


# ============================================================
# FCF CONVERSION
# ============================================================

def calculate_fcf_conversion(
    company_id: str,
    ratios_df: pd.DataFrame,
    pnl_df: pd.DataFrame,
    cashflow_df: pd.DataFrame
):
    """
    Day 31 FCF Conversion:

        FCF / PAT × 100
    """

    fcf_history = get_fcf_history(
        company_id,
        ratios_df,
        cashflow_df
    )

    if not fcf_history:

        return None

    latest_fcf = safe_float(
        fcf_history[-1][1]
    )

    pnl_latest = get_latest_row(
        pnl_df,
        company_id
    )

    if pnl_latest is None:

        return None

    pat = safe_float(
        pnl_latest.get(
            PNL_PAT_COLUMN
        )
    )

    if (
        latest_fcf is None
        or pat is None
        or pat == 0
    ):

        return None

    conversion = (
        latest_fcf
        / pat
        * 100
    )

    if math.isfinite(conversion):

        return conversion

    return None


# ============================================================
# DISTRESS SIGNAL
# ============================================================

def calculate_distress(
    company_id: str,
    cashflow_df: pd.DataFrame,
    pnl_df: pd.DataFrame
):
    """
    Distress condition:

        Latest CFO < 0
        AND
        Latest CFF > 0
    """

    latest_cf = get_latest_row(
        cashflow_df,
        company_id
    )

    latest_pnl = get_latest_row(
        pnl_df,
        company_id
    )

    if latest_cf is None:

        return (
            False,
            None,
            None,
            None
        )

    cfo = safe_float(
        latest_cf.get(
            CASHFLOW_CFO_COLUMN
        )
    )

    cff = safe_float(
        latest_cf.get(
            CASHFLOW_CFF_COLUMN
        )
    )

    latest_profit = None

    if latest_pnl is not None:

        latest_profit = safe_float(
            latest_pnl.get(
                PNL_PAT_COLUMN
            )
        )

    distress = (
        cfo is not None
        and cff is not None
        and cfo < 0
        and cff > 0
    )

    return (
        distress,
        cfo,
        cff,
        latest_profit
    )


# ============================================================
# DEBT HISTORY
# ============================================================

def get_debt_history(
    company_id: str,
    ratios_df: pd.DataFrame
):
    """
    Get total debt history from financial ratios.
    """

    history = get_company_history(
        ratios_df,
        company_id
    )

    if history.empty:

        return []

    values = []

    for _, row in history.iterrows():

        debt = safe_float(
            row.get(
                RATIO_DEBT_COLUMN
            )
        )

        year = row.get(
            "_year_num"
        )

        if debt is not None:

            values.append(
                (
                    year,
                    debt
                )
            )

    return values


# ============================================================
# DELEVERAGING
# ============================================================

def calculate_deleveraging(
    company_id: str,
    cashflow_df: pd.DataFrame,
    ratios_df: pd.DataFrame
):
    """
    Deleveraging condition:

        Latest CFF < 0
        AND
        Latest Debt < Previous Debt
    """

    latest_cf = get_latest_row(
        cashflow_df,
        company_id
    )

    if latest_cf is None:

        return False

    cff = safe_float(
        latest_cf.get(
            CASHFLOW_CFF_COLUMN
        )
    )

    if cff is None or cff >= 0:

        return False

    debt_history = get_debt_history(
        company_id,
        ratios_df
    )

    if len(debt_history) < 2:

        return False

    previous_debt = debt_history[-2][1]
    latest_debt = debt_history[-1][1]

    return (
        latest_debt
        < previous_debt
    )


# ============================================================
# CAPITAL ALLOCATION LABEL
# ============================================================

def capital_allocation_label(
    distress_flag: bool,
    deleveraging_flag: bool,
    cfo_quality_label: Optional[str],
    capex_label: Optional[str],
    fcf_conversion_pct: Optional[float]
):
    """
    Overall capital allocation classification.
    """

    if distress_flag:

        return "Financing Dependent"

    if deleveraging_flag:

        return "Deleveraging"

    if (
        cfo_quality_label
        == "High Quality"
        and capex_label
        == "Asset Light"
        and fcf_conversion_pct is not None
        and fcf_conversion_pct >= 80
    ):

        return "Efficient Capital Allocation"

    if capex_label == "Capital Intensive":

        return "Growth Investment"

    if cfo_quality_label == "Accrual Risk":

        return "Cash Flow Risk"

    if (
        cfo_quality_label
        == "High Quality"
        and capex_label
        == "Moderate"
    ):

        return "Balanced"

    return "Neutral"


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("N100 CASH FLOW INTELLIGENCE")
    print("SPRINT 5 - DAY 31")
    print("=" * 70)

    # --------------------------------------------------------
    # Database
    # --------------------------------------------------------

    print("\nDatabase:")
    print(DB_PATH)

    if not DB_PATH.exists():

        raise FileNotFoundError(
            f"Database not found: {DB_PATH}"
        )

    conn = sqlite3.connect(
        DB_PATH
    )

    # --------------------------------------------------------
    # Check tables
    # --------------------------------------------------------

    check_required_tables(
        conn
    )

    # --------------------------------------------------------
    # Load data
    # --------------------------------------------------------

    companies_df = load_table(
        conn,
        "companies"
    )

    cashflow_df = load_table(
        conn,
        "cashflow"
    )

    pnl_df = load_table(
        conn,
        "profitandloss"
    )

    ratios_df = load_table(
        conn,
        "financial_ratios"
    )

    sectors_df = load_table(
        conn,
        "sectors"
    )

    conn.close()

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # companies.id is the company identifier.
    # Other tables use company_id.
    #
    # Therefore:
    #
    # companies.id -> company_id
    # --------------------------------------------------------

    companies_df = companies_df.rename(
        columns={
            "id": "company_id"
        }
    )

    # --------------------------------------------------------
    # Prepare
    # --------------------------------------------------------

    companies_df = prepare_dataframe(
        companies_df
    )

    cashflow_df = prepare_dataframe(
        cashflow_df
    )

    pnl_df = prepare_dataframe(
        pnl_df
    )

    ratios_df = prepare_dataframe(
        ratios_df
    )

    sectors_df = prepare_dataframe(
        sectors_df
    )

    # --------------------------------------------------------
    # Schema validation
    # --------------------------------------------------------

    required_columns = {

        "companies": [
            "company_id",
            "company_name"
        ],

        "cashflow": [
            "company_id",
            "year",
            "operating_activity",
            "investing_activity",
            "financing_activity"
        ],

        "profitandloss": [
            "company_id",
            "year",
            "sales",
            "net_profit"
        ],

        "financial_ratios": [
            "company_id",
            "year",
            "free_cash_flow_cr",
            "total_debt_cr"
        ],

        "sectors": [
            "company_id",
            "broad_sector"
        ]
    }

    datasets = {

        "companies":
            companies_df,

        "cashflow":
            cashflow_df,

        "profitandloss":
            pnl_df,

        "financial_ratios":
            ratios_df,

        "sectors":
            sectors_df
    }

    for table_name, columns in (
        required_columns.items()
    ):

        df = datasets[
            table_name
        ]

        missing = [
            column
            for column in columns
            if column not in df.columns
        ]

        if missing:

            raise ValueError(
                f"{table_name} missing "
                f"columns: {missing}"
            )

    # --------------------------------------------------------
    # Company IDs
    # --------------------------------------------------------

    company_ids = (
        companies_df["company_id"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )

    # --------------------------------------------------------
    # Dataset counts
    # --------------------------------------------------------

    print("\nDataset counts:")

    print(
        f"  Companies        : "
        f"{len(companies_df)}"
    )

    print(
        f"  Cash Flow        : "
        f"{len(cashflow_df)}"
    )

    print(
        f"  Profit & Loss    : "
        f"{len(pnl_df)}"
    )

    print(
        f"  Financial Ratios : "
        f"{len(ratios_df)}"
    )

    print(
        f"  Sectors          : "
        f"{len(sectors_df)}"
    )

    # --------------------------------------------------------
    # Sector lookup
    # --------------------------------------------------------

    sector_lookup = build_sector_lookup(
        sectors_df
    )

    # --------------------------------------------------------
    # Process companies
    # --------------------------------------------------------

    print("\nProcessing companies...")

    results = []

    distress_alerts = []

    for index, company_id in enumerate(
        company_ids,
        start=1
    ):

        # ----------------------------------------------------
        # Sector
        # ----------------------------------------------------

        sector = sector_lookup.get(
            company_id,
            "Unknown"
        )

        # ----------------------------------------------------
        # CFO Quality
        # ----------------------------------------------------

        (
            cfo_score,
            cfo_label
        ) = calculate_cfo_quality(
            company_id,
            cashflow_df,
            pnl_df
        )

        # ----------------------------------------------------
        # CapEx
        # ----------------------------------------------------

        (
            capex_pct,
            capex_label
        ) = calculate_capex_intensity(
            company_id,
            cashflow_df,
            pnl_df
        )

        # ----------------------------------------------------
        # FCF CAGR
        # ----------------------------------------------------

        fcf_cagr = (
            calculate_fcf_cagr_5yr(
                company_id,
                ratios_df,
                cashflow_df
            )
        )

        # ----------------------------------------------------
        # FCF Conversion
        # ----------------------------------------------------

        fcf_conversion = (
            calculate_fcf_conversion(
                company_id,
                ratios_df,
                pnl_df,
                cashflow_df
            )
        )

        # ----------------------------------------------------
        # Distress
        # ----------------------------------------------------

        (
            distress,
            cfo,
            cff,
            latest_profit
        ) = calculate_distress(
            company_id,
            cashflow_df,
            pnl_df
        )

        # ----------------------------------------------------
        # Deleveraging
        # ----------------------------------------------------

        deleveraging = (
            calculate_deleveraging(
                company_id,
                cashflow_df,
                ratios_df
            )
        )

        # ----------------------------------------------------
        # Capital Allocation
        # ----------------------------------------------------

        allocation = (
            capital_allocation_label(
                distress,
                deleveraging,
                cfo_label,
                capex_label,
                fcf_conversion
            )
        )

        # ----------------------------------------------------
        # Result
        # ----------------------------------------------------

        results.append(
            {
                "company_id":
                    company_id,

                "sector":
                    sector,

                "cfo_quality_score":
                    (
                        round(
                            cfo_score,
                            4
                        )
                        if cfo_score is not None
                        else None
                    ),

                "cfo_quality_label":
                    cfo_label,

                "capex_intensity_pct":
                    (
                        round(
                            capex_pct,
                            4
                        )
                        if capex_pct is not None
                        else None
                    ),

                "capex_label":
                    capex_label,

                "fcf_cagr_5yr":
                    (
                        round(
                            fcf_cagr,
                            4
                        )
                        if fcf_cagr is not None
                        else None
                    ),

                "fcf_conversion_pct":
                    (
                        round(
                            fcf_conversion,
                            4
                        )
                        if fcf_conversion is not None
                        else None
                    ),

                "distress_flag":
                    bool(distress),

                "deleveraging_flag":
                    bool(deleveraging),

                "capital_allocation_label":
                    allocation
            }
        )

        # ----------------------------------------------------
        # Distress Alert
        # ----------------------------------------------------

        if distress:

            distress_alerts.append(
                {
                    "company_id":
                        company_id,

                    "cfo":
                        cfo,

                    "cff":
                        cff,

                    "latest_net_profit":
                        latest_profit
                }
            )

        if index % 20 == 0:

            print(
                f"  Processed "
                f"{index}/{len(company_ids)}"
            )

    # ========================================================
    # DATAFRAMES
    # ========================================================

    output_columns = [

        "company_id",
        "sector",
        "cfo_quality_score",
        "cfo_quality_label",
        "capex_intensity_pct",
        "capex_label",
        "fcf_cagr_5yr",
        "fcf_conversion_pct",
        "distress_flag",
        "deleveraging_flag",
        "capital_allocation_label"
    ]

    intelligence_df = pd.DataFrame(
        results,
        columns=output_columns
    )

    distress_df = pd.DataFrame(
        distress_alerts,
        columns=[
            "company_id",
            "cfo",
            "cff",
            "latest_net_profit"
        ]
    )

    # ========================================================
    # VALIDATION
    # ========================================================

    print("\n" + "=" * 70)
    print("VALIDATION")
    print("=" * 70)

    print(
        f"Companies processed : "
        f"{len(intelligence_df)}"
    )

    print(
        f"Distress companies  : "
        f"{len(distress_df)}"
    )

    # --------------------------------------------------------
    # CFO Quality
    # --------------------------------------------------------

    print(
        "\nCFO Quality distribution:"
    )

    print(
        intelligence_df[
            "cfo_quality_label"
        ]
        .value_counts(
            dropna=False
        )
        .to_string()
    )

    # --------------------------------------------------------
    # CapEx
    # --------------------------------------------------------

    print(
        "\nCapEx distribution:"
    )

    print(
        intelligence_df[
            "capex_label"
        ]
        .value_counts(
            dropna=False
        )
        .to_string()
    )

    # --------------------------------------------------------
    # Distress
    # --------------------------------------------------------

    print(
        "\nDistress flag distribution:"
    )

    print(
        intelligence_df[
            "distress_flag"
        ]
        .value_counts(
            dropna=False
        )
        .to_string()
    )

    # --------------------------------------------------------
    # Deleveraging
    # --------------------------------------------------------

    print(
        "\nDeleveraging distribution:"
    )

    print(
        intelligence_df[
            "deleveraging_flag"
        ]
        .value_counts(
            dropna=False
        )
        .to_string()
    )

    # --------------------------------------------------------
    # Capital allocation
    # --------------------------------------------------------

    print(
        "\nCapital allocation distribution:"
    )

    print(
        intelligence_df[
            "capital_allocation_label"
        ]
        .value_counts(
            dropna=False
        )
        .to_string()
    )

    # --------------------------------------------------------
    # Numeric coverage
    # --------------------------------------------------------

    print(
        "\nNumeric coverage:"
    )

    numeric_columns = [

        "cfo_quality_score",
        "capex_intensity_pct",
        "fcf_cagr_5yr",
        "fcf_conversion_pct"
    ]

    for column in numeric_columns:

        valid = (
            intelligence_df[column]
            .notna()
            .sum()
        )

        print(
            f"  {column:<25}"
            f"{valid}/{len(intelligence_df)}"
        )

    # --------------------------------------------------------
    # Sector coverage
    # --------------------------------------------------------

    known_sector_count = (
        intelligence_df[
            "sector"
        ]
        .ne("Unknown")
        .sum()
    )

    print(
        "\nSector coverage:"
    )

    print(
        f"  Known sectors : "
        f"{known_sector_count}/"
        f"{len(intelligence_df)}"
    )

    # ========================================================
    # REQUIRED COLUMN CHECK
    # ========================================================

    missing_columns = [
        column
        for column in output_columns
        if column not in intelligence_df.columns
    ]

    if missing_columns:

        raise ValueError(
            "Missing required output columns: "
            f"{missing_columns}"
        )

    if len(intelligence_df) != len(
        company_ids
    ):

        raise ValueError(
            "Not all companies were processed."
        )

    # ========================================================
    # SAVE EXCEL
    # ========================================================

    with pd.ExcelWriter(
        INTELLIGENCE_OUTPUT,
        engine="openpyxl"
    ) as writer:

        intelligence_df.to_excel(
            writer,
            sheet_name="Cash Flow Intelligence",
            index=False
        )

        # ----------------------------------------------------
        # Summary
        # ----------------------------------------------------

        summary_rows = []

        for label, count in (
            intelligence_df[
                "cfo_quality_label"
            ]
            .value_counts(
                dropna=False
            )
            .items()
        ):

            summary_rows.append(
                {
                    "metric":
                        "CFO Quality",

                    "category":
                        label,

                    "count":
                        count
                }
            )

        for label, count in (
            intelligence_df[
                "capex_label"
            ]
            .value_counts(
                dropna=False
            )
            .items()
        ):

            summary_rows.append(
                {
                    "metric":
                        "CapEx",

                    "category":
                        label,

                    "count":
                        count
                }
            )

        summary_df = pd.DataFrame(
            summary_rows
        )

        summary_df.to_excel(
            writer,
            sheet_name="Summary",
            index=False
        )

    # ========================================================
    # SAVE DISTRESS CSV
    # ========================================================

    distress_df.to_csv(
        DISTRESS_OUTPUT,
        index=False
    )

    # ========================================================
    # OUTPUT
    # ========================================================

    print("\n" + "=" * 70)
    print("OUTPUT")
    print("=" * 70)

    print(
        f"Excel : "
        f"{INTELLIGENCE_OUTPUT}"
    )

    print(
        f"CSV   : "
        f"{DISTRESS_OUTPUT}"
    )

    print(
        f"\nExcel rows: "
        f"{len(intelligence_df)}"
    )

    print(
        f"Distress alerts: "
        f"{len(distress_df)}"
    )

    print(
        "\nFirst 10 records:"
    )

    print(
        intelligence_df.head(10).to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # Distress details
    # --------------------------------------------------------

    if not distress_df.empty:

        print(
            "\nDistress alerts:"
        )

        print(
            distress_df.to_string(
                index=False
            )
        )

    else:

        print(
            "\nNo companies currently meet "
            "the distress condition."
        )

    print("\n" + "=" * 70)
    print("DAY 31 STATUS: COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()