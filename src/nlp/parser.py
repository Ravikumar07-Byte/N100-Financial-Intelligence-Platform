r"""
Day 29 - NLP Analysis Text Parser
N100 Financial Intelligence Platform

Purpose:
    Parse semi-structured financial text from analysis.xlsx using regex.

Input:
    data/raw/analysis.xlsx

Outputs:
    output/analysis_parsed.csv
    output/parse_failures.csv
    output/analysis_cagr_validation.csv

Required regex:
    (\d+)\s*Years?:?\s*([\d.]+)%

Validation:
    Compare 5-year CAGR values extracted from analysis.xlsx
    against the existing Ratio Engine values.

    Divergence greater than 5 percentage points is flagged
    for manual review.

    Missing companies or missing Ratio Engine values are
    also flagged for manual review, but are NOT classified
    as CAGR divergence.
"""

from pathlib import Path
import re
import sqlite3

import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = PROJECT_ROOT / "data" / "raw" / "analysis.xlsx"
DB_FILE = PROJECT_ROOT / "nifty100.db"
OUTPUT_DIR = PROJECT_ROOT / "output"

PARSED_FILE = OUTPUT_DIR / "analysis_parsed.csv"
FAILURE_FILE = OUTPUT_DIR / "parse_failures.csv"
VALIDATION_FILE = OUTPUT_DIR / "analysis_cagr_validation.csv"


# ============================================================
# REGEX
# ============================================================

# Project specification:
# (\d+)\s*Years?:?\s*([\d.]+)%

PATTERN = re.compile(
    r"(\d+)\s*Years?:?\s*([\d.]+)%"
)


# ============================================================
# TARGET FIELDS
# ============================================================

TARGET_FIELDS = [
    "compounded_sales_growth",
    "compounded_profit_growth",
    "stock_price_cagr",
    "roe",
]


# ============================================================
# LOAD ANALYSIS FILE
# ============================================================

def load_analysis():
    """
    Load the Analysis sheet.

    The first Excel row is the title.
    The second Excel row contains the actual headers.
    Therefore header=1 is required.
    """

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    df = pd.read_excel(
        INPUT_FILE,
        sheet_name="Analysis",
        header=1
    )

    # Remove completely empty rows/columns.
    df = df.dropna(axis=0, how="all")
    df = df.dropna(axis=1, how="all")

    # Clean column names.
    df.columns = [
        str(column).strip()
        for column in df.columns
    ]

    return df


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text(value):
    """
    Convert an Excel cell to clean text.
    """

    if pd.isna(value):
        return ""

    return str(value).strip()


# ============================================================
# REGEX PARSER
# ============================================================

def parse_metric_text(text):
    """
    Extract period and percentage from text.

    Example:

        10 Years: 21%

    Returns:

        period_years = 10
        value_pct = 21.0

    If the required regex does not match:

        (None, None)
    """

    text = clean_text(text)

    if not text:
        return None, None

    match = PATTERN.search(text)

    if not match:
        return None, None

    period_years = int(match.group(1))
    value_pct = float(match.group(2))

    return period_years, value_pct


# ============================================================
# PARSE ALL TARGET FIELDS
# ============================================================

def parse_analysis(df):
    """
    Parse all four required financial text fields.

    Returns:
        parsed_df
        failures_df
    """

    required_columns = [
        "company_id",
        *TARGET_FIELDS
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing required columns: "
            + ", ".join(missing_columns)
        )

    parsed_rows = []
    failure_rows = []

    for excel_index, row in df.iterrows():

        company_id = clean_text(
            row["company_id"]
        )

        # Ignore rows without company ID.
        if not company_id:
            continue

        for metric_type in TARGET_FIELDS:

            source_text = clean_text(
                row[metric_type]
            )

            period_years, value_pct = (
                parse_metric_text(source_text)
            )

            if period_years is not None:

                parsed_rows.append(
                    {
                        "company_id": company_id,
                        "metric_type": metric_type,
                        "period_years": period_years,
                        "value_pct": value_pct,
                    }
                )

            else:

                failure_rows.append(
                    {
                        "company_id": company_id,
                        "metric_type": metric_type,
                        "source_text": source_text,
                        "reason": "Regex pattern did not match",
                        "excel_row": excel_index + 2,
                    }
                )

    parsed_df = pd.DataFrame(
        parsed_rows,
        columns=[
            "company_id",
            "metric_type",
            "period_years",
            "value_pct",
        ],
    )

    failures_df = pd.DataFrame(
        failure_rows,
        columns=[
            "company_id",
            "metric_type",
            "source_text",
            "reason",
            "excel_row",
        ],
    )

    return parsed_df, failures_df


# ============================================================
# LOAD RATIO ENGINE DATA
# ============================================================

def load_ratio_engine():
    """
    Load CAGR values calculated by the existing Ratio Engine.

    Existing financial_ratios columns include:

        revenue_cagr_5yr
        pat_cagr_5yr
    """

    if not DB_FILE.exists():
        print(
            "[WARNING] nifty100.db does not exist."
        )

        return pd.DataFrame()

    connection = sqlite3.connect(DB_FILE)

    try:

        query = """
            SELECT
                company_id,
                year,
                revenue_cagr_5yr,
                pat_cagr_5yr
            FROM financial_ratios
        """

        ratio_df = pd.read_sql_query(
            query,
            connection
        )

    finally:

        connection.close()

    return ratio_df


# ============================================================
# CAGR CROSS VALIDATION
# ============================================================

def cross_validate_cagr(parsed_df):
    """
    Compare 5-year CAGR values from analysis.xlsx
    with CAGR values from the Ratio Engine.

    Mapping:

        compounded_sales_growth
            -> revenue_cagr_5yr

        compounded_profit_growth
            -> pat_cagr_5yr

    Validation rules:

        1. Divergence > 5 percentage points
           -> Manual review

        2. Company missing from Ratio Engine
           -> Manual review

        3. Ratio Engine value missing
           -> Manual review

        4. Otherwise
           -> Within tolerance

    Important:
        Missing company/data is NOT classified as
        CAGR divergence.
    """

    validation_columns = [
        "company_id",
        "metric_type",
        "period_years",
        "parsed_value_pct",
        "ratio_engine_value_pct",
        "divergence_pct_points",
        "manual_review",
        "reason",
    ]

    ratio_df = load_ratio_engine()

    if ratio_df.empty:
        return pd.DataFrame(
            columns=validation_columns
        )

    # --------------------------------------------------------
    # Normalize Ratio Engine company IDs
    # --------------------------------------------------------

    ratio_df["company_id"] = (
        ratio_df["company_id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # --------------------------------------------------------
    # Normalize parsed company IDs
    # --------------------------------------------------------

    parsed_work = parsed_df.copy()

    parsed_work["company_id"] = (
        parsed_work["company_id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # --------------------------------------------------------
    # Keep latest Ratio Engine year for each company
    # --------------------------------------------------------

    ratio_latest = (
        ratio_df
        .sort_values("year")
        .groupby("company_id", as_index=False)
        .tail(1)
    )

    # --------------------------------------------------------
    # Only 5-year CAGR values are comparable
    # --------------------------------------------------------

    cagr_df = parsed_work[
        parsed_work["period_years"] == 5
    ].copy()

    cagr_df = cagr_df[
        cagr_df["metric_type"].isin(
            [
                "compounded_sales_growth",
                "compounded_profit_growth",
            ]
        )
    ]

    # --------------------------------------------------------
    # Mapping between NLP fields and Ratio Engine fields
    # --------------------------------------------------------

    metric_mapping = {
        "compounded_sales_growth":
            "revenue_cagr_5yr",

        "compounded_profit_growth":
            "pat_cagr_5yr",
    }

    validation_rows = []

    # --------------------------------------------------------
    # Validate each parsed CAGR
    # --------------------------------------------------------

    for _, parsed_row in cagr_df.iterrows():

        company_id = str(
            parsed_row["company_id"]
        ).strip().upper()

        metric_type = parsed_row[
            "metric_type"
        ]

        ratio_column = metric_mapping[
            metric_type
        ]

        parsed_value = float(
            parsed_row["value_pct"]
        )

        # ----------------------------------------------------
        # Find company in Ratio Engine
        # ----------------------------------------------------

        matches = ratio_latest[
            ratio_latest["company_id"]
            == company_id
        ]

        # ----------------------------------------------------
        # Company not found
        # ----------------------------------------------------

        if matches.empty:

            validation_rows.append(
                {
                    "company_id": company_id,
                    "metric_type": metric_type,
                    "period_years": 5,
                    "parsed_value_pct":
                        parsed_value,
                    "ratio_engine_value_pct":
                        None,
                    "divergence_pct_points":
                        None,
                    "manual_review": True,
                    "reason":
                        "Company not found in Ratio Engine",
                }
            )

            continue

        # ----------------------------------------------------
        # Ratio Engine value
        # ----------------------------------------------------

        ratio_value = matches.iloc[0][
            ratio_column
        ]

        # ----------------------------------------------------
        # Ratio Engine value missing
        # ----------------------------------------------------

        if pd.isna(ratio_value):

            validation_rows.append(
                {
                    "company_id": company_id,
                    "metric_type": metric_type,
                    "period_years": 5,
                    "parsed_value_pct":
                        parsed_value,
                    "ratio_engine_value_pct":
                        None,
                    "divergence_pct_points":
                        None,
                    "manual_review": True,
                    "reason":
                        "Ratio Engine value is missing",
                }
            )

            continue

        ratio_value = float(
            ratio_value
        )

        # ----------------------------------------------------
        # Calculate divergence
        # ----------------------------------------------------

        divergence = abs(
            parsed_value - ratio_value
        )

        divergence = round(
            divergence,
            4
        )

        # ----------------------------------------------------
        # Manual review threshold
        # ----------------------------------------------------

        manual_review = (
            divergence > 5.0
        )

        if manual_review:

            reason = (
                "Divergence > 5 percentage points"
            )

        else:

            reason = (
                "Within 5 percentage-point tolerance"
            )

        validation_rows.append(
            {
                "company_id": company_id,
                "metric_type": metric_type,
                "period_years": 5,
                "parsed_value_pct":
                    parsed_value,
                "ratio_engine_value_pct":
                    ratio_value,
                "divergence_pct_points":
                    divergence,
                "manual_review":
                    manual_review,
                "reason":
                    reason,
            }
        )

    return pd.DataFrame(
        validation_rows,
        columns=validation_columns
    )


# ============================================================
# VALIDATION SUMMARY
# ============================================================

def print_validation_summary(validation_df):
    """
    Print a clear Day 29 validation summary.

    Distinguishes:
        - Actual CAGR divergences
        - Missing Ratio Engine companies
        - Missing Ratio Engine values
    """

    if validation_df.empty:

        print(
            "    No CAGR comparisons available."
        )

        return

    total = len(validation_df)

    manual_review_count = int(
        validation_df[
            "manual_review"
        ].sum()
    )

    divergence_count = int(
        (
            validation_df["reason"]
            == "Divergence > 5 percentage points"
        ).sum()
    )

    missing_company_count = int(
        (
            validation_df["reason"]
            == "Company not found in Ratio Engine"
        ).sum()
    )

    missing_value_count = int(
        (
            validation_df["reason"]
            == "Ratio Engine value is missing"
        ).sum()
    )

    within_tolerance_count = int(
        (
            validation_df["reason"]
            == "Within 5 percentage-point tolerance"
        ).sum()
    )

    print(
        f"    CAGR comparisons: {total}"
    )

    print(
        f"    Within tolerance: "
        f"{within_tolerance_count}"
    )

    print(
        f"    Actual divergences >5 points: "
        f"{divergence_count}"
    )

    print(
        f"    Missing companies: "
        f"{missing_company_count}"
    )

    print(
        f"    Missing Ratio Engine values: "
        f"{missing_value_count}"
    )

    print(
        f"    Manual review flags: "
        f"{manual_review_count}"
    )

    # --------------------------------------------------------
    # Show actual divergence records
    # --------------------------------------------------------

    if divergence_count > 0:

        print(
            "\n    [WARNING] Actual CAGR divergences:"
        )

        divergence_df = validation_df[
            validation_df["reason"]
            == "Divergence > 5 percentage points"
        ]

        print(
            divergence_df[
                [
                    "company_id",
                    "metric_type",
                    "parsed_value_pct",
                    "ratio_engine_value_pct",
                    "divergence_pct_points",
                ]
            ].to_string(index=False)
        )

    else:

        print(
            "\n    [PASS] No actual CAGR divergence >5 percentage points."
        )

    # --------------------------------------------------------
    # Show missing company records
    # --------------------------------------------------------

    if missing_company_count > 0:

        print(
            "\n    [INFO] Companies missing from Ratio Engine:"
        )

        missing_company_df = validation_df[
            validation_df["reason"]
            == "Company not found in Ratio Engine"
        ]

        print(
            missing_company_df[
                [
                    "company_id",
                    "metric_type",
                    "parsed_value_pct",
                ]
            ].to_string(index=False)
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("DAY 29 — NLP ANALYSIS TEXT PARSER")
    print("=" * 70)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # 1. Load source
    # --------------------------------------------------------

    print("\n[1] Loading analysis.xlsx...")

    df = load_analysis()

    print(
        f"    Rows loaded: {len(df)}"
    )

    print(
        f"    Columns: {list(df.columns)}"
    )

    # --------------------------------------------------------
    # 2. Parse text
    # --------------------------------------------------------

    print("\n[2] Parsing financial text...")

    parsed_df, failures_df = (
        parse_analysis(df)
    )

    # --------------------------------------------------------
    # 3. Save parsed output
    # --------------------------------------------------------

    parsed_df.to_csv(
        PARSED_FILE,
        index=False
    )

    failures_df.to_csv(
        FAILURE_FILE,
        index=False
    )

    print(
        f"    Parsed records: {len(parsed_df)}"
    )

    print(
        f"    Failed records: {len(failures_df)}"
    )

    print(
        f"    Created: {PARSED_FILE}"
    )

    print(
        f"    Created: {FAILURE_FILE}"
    )

    # --------------------------------------------------------
    # 4. Cross validation
    # --------------------------------------------------------

    print(
        "\n[3] Cross-validating 5-year CAGR "
        "against Ratio Engine..."
    )

    validation_df = cross_validate_cagr(
        parsed_df
    )

    validation_df.to_csv(
        VALIDATION_FILE,
        index=False
    )

    print(
        f"    Created: {VALIDATION_FILE}"
    )

    # --------------------------------------------------------
    # 5. Validation summary
    # --------------------------------------------------------

    print(
        "\n[4] CAGR validation summary"
    )

    print_validation_summary(
        validation_df
    )

    # --------------------------------------------------------
    # 6. Parsing summary
    # --------------------------------------------------------

    print(
        "\n[5] Parsing summary"
    )

    if not parsed_df.empty:

        print("\nMetric counts:")

        print(
            parsed_df[
                "metric_type"
            ]
            .value_counts()
            .to_string()
        )

        print("\nPeriod counts:")

        print(
            parsed_df[
                "period_years"
            ]
            .value_counts()
            .sort_index()
            .to_string()
        )

    else:

        print(
            "    No records were parsed."
        )

    # --------------------------------------------------------
    # 7. Failure summary
    # --------------------------------------------------------

    print(
        "\n[6] Regex failure summary"
    )

    if not failures_df.empty:

        print(
            f"    Total regex failures: "
            f"{len(failures_df)}"
        )

        print(
            "\n    Failure counts by metric:"
        )

        print(
            failures_df[
                "metric_type"
            ]
            .value_counts()
            .to_string()
        )

    else:

        print(
            "    No regex failures."
        )

    # --------------------------------------------------------
    # 8. Final status
    # --------------------------------------------------------

    print("\n" + "=" * 70)

    if not validation_df.empty:

        actual_divergences = int(
            (
                validation_df["reason"]
                == "Divergence > 5 percentage points"
            ).sum()
        )

        if actual_divergences == 0:

            print(
                "DAY 29 STATUS: COMPLETED"
            )

            print(
                "No actual CAGR divergence >5 percentage points."
            )

        else:

            print(
                "DAY 29 STATUS: COMPLETED WITH REVIEW FLAGS"
            )

            print(
                f"Actual CAGR divergences: "
                f"{actual_divergences}"
            )

    else:

        print(
            "DAY 29 STATUS: COMPLETED"
        )

    print("=" * 70)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()