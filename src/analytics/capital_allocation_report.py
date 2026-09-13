"""
N100 Financial Intelligence Platform
Sprint 5 - Day 32
Capital Allocation Report

Tasks:
1. Verify Sprint 2 capital_allocation.csv for all 92 companies.
2. Generate latest-year distribution for all 8 patterns.
3. Add latest capital allocation pattern to cashflow_intelligence.xlsx.
4. Detect year-over-year pattern changes.
5. Save pattern_changes.csv.
"""

from __future__ import annotations

from pathlib import Path
import re
import sqlite3

import pandas as pd


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_PATH = PROJECT_ROOT / "nifty100.db"

OUTPUT_DIR = PROJECT_ROOT / "output"

CAPITAL_ALLOCATION_FILE = (
    OUTPUT_DIR / "capital_allocation.csv"
)

CASHFLOW_INTELLIGENCE_FILE = (
    OUTPUT_DIR / "cashflow_intelligence.xlsx"
)

DISTRIBUTION_FILE = (
    OUTPUT_DIR / "capital_allocation_distribution.csv"
)

PATTERN_CHANGES_FILE = (
    OUTPUT_DIR / "pattern_changes.csv"
)


# ============================================================
# EXPECTED COMPANY COUNT
# ============================================================

EXPECTED_COMPANIES = 92


# ============================================================
# EXPECTED 8 CAPITAL ALLOCATION PATTERNS
# ============================================================

EXPECTED_PATTERNS = [
    "Shareholder Returns",
    "Reinvestor",
    "Liquidating Assets",
    "Distress Signal",
    "Growth Funded by Debt",
    "Cash Accumulator",
    "Pre-Revenue",
    "Mixed",
]


# ============================================================
# YEAR NORMALIZATION
# ============================================================

def normalize_year(value):
    """
    Convert different year formats into a four-digit year.

    Supported examples:

        2025
        2025.0
        "2025"
        "FY2025"
        "FY 2025"
        "Mar 2025"
        "2025-03-31"
        "2025-03"
        "2025A"

    Returns:
        "2025"

    or None if no valid four-digit year is found.
    """

    if pd.isna(value):
        return None

    text = str(value).strip()

    if not text:
        return None

    # --------------------------------------------------------
    # First try normal numeric conversion
    # --------------------------------------------------------

    try:

        number = float(text)

        if number.is_integer():

            year = int(number)

            if 1900 <= year <= 2100:
                return str(year)

    except (ValueError, TypeError):
        pass

    # --------------------------------------------------------
    # Extract four-digit year from text
    # --------------------------------------------------------

    matches = re.findall(
        r"(19\d{2}|20\d{2}|21\d{2})",
        text,
    )

    if matches:

        # Use the first valid four-digit year
        return matches[0]

    return None


# ============================================================
# COMPANY ID NORMALIZATION
# ============================================================

def normalize_company_id(value):

    if pd.isna(value):
        return None

    value = str(value).strip().upper()

    if not value:
        return None

    return value


# ============================================================
# COLUMN FINDER
# ============================================================

def find_column(df, candidates):

    normalized_columns = {
        str(column).strip().lower(): column
        for column in df.columns
    }

    for candidate in candidates:

        key = candidate.strip().lower()

        if key in normalized_columns:

            return normalized_columns[key]

    return None


# ============================================================
# LOAD COMPANIES
# ============================================================

def load_companies():

    if not DATABASE_PATH.exists():

        raise FileNotFoundError(
            f"Database not found:\n{DATABASE_PATH}"
        )

    with sqlite3.connect(DATABASE_PATH) as connection:

        companies = pd.read_sql_query(
            """
            SELECT
                id AS company_id,
                company_name
            FROM companies
            """,
            connection,
        )

    companies["company_id"] = (
        companies["company_id"]
        .map(normalize_company_id)
    )

    return companies


# ============================================================
# LOAD CAPITAL ALLOCATION
# ============================================================

def load_capital_allocation():

    if not CAPITAL_ALLOCATION_FILE.exists():

        raise FileNotFoundError(
            "Capital allocation file not found:\n"
            f"{CAPITAL_ALLOCATION_FILE}"
        )

    df = pd.read_csv(
        CAPITAL_ALLOCATION_FILE
    )

    print("\nCapital allocation columns:")
    print(list(df.columns))

    # --------------------------------------------------------
    # Find columns
    # --------------------------------------------------------

    company_column = find_column(
        df,
        [
            "company_id",
            "company",
            "id",
        ],
    )

    year_column = find_column(
        df,
        [
            "year",
        ],
    )

    pattern_column = find_column(
        df,
        [
            "pattern_label",
            "capital_allocation",
            "capital_allocation_label",
            "pattern",
        ],
    )

    if company_column is None:

        raise ValueError(
            "Could not find company_id column."
        )

    if year_column is None:

        raise ValueError(
            "Could not find year column."
        )

    if pattern_column is None:

        raise ValueError(
            "Could not find pattern column."
        )

    # --------------------------------------------------------
    # Rename columns
    # --------------------------------------------------------

    df = df.rename(
        columns={
            company_column: "company_id",
            year_column: "year",
            pattern_column: "pattern_label",
        }
    )

    # --------------------------------------------------------
    # Normalize values
    # --------------------------------------------------------

    df["company_id"] = (
        df["company_id"]
        .map(normalize_company_id)
    )

    df["year_original"] = df["year"]

    df["year"] = (
        df["year"]
        .map(normalize_year)
    )

    df["pattern_label"] = (
        df["pattern_label"]
        .astype(str)
        .str.strip()
    )

    # --------------------------------------------------------
    # Show year diagnostics
    # --------------------------------------------------------

    print("\nYear normalization:")

    print(
        f"Original year values : "
        f"{df['year_original'].nunique()}"
    )

    print(
        f"Valid normalized years : "
        f"{df['year'].notna().sum()}"
    )

    print(
        f"Invalid year values : "
        f"{df['year'].isna().sum()}"
    )

    print("\nSample normalized years:")

    print(
        df[
            [
                "year_original",
                "year",
            ]
        ]
        .drop_duplicates()
        .head(15)
        .to_string(index=False)
    )

    # --------------------------------------------------------
    # Remove rows without company ID
    # --------------------------------------------------------

    df = df[
        df["company_id"].notna()
        & (df["company_id"] != "")
    ].copy()

    return df


# ============================================================
# GET LATEST YEAR
# ============================================================

def get_latest_year(df):

    valid_years = pd.to_numeric(
        df["year"],
        errors="coerce",
    ).dropna()

    if valid_years.empty:

        raise ValueError(
            "Could not determine latest year after "
            "year normalization."
        )

    return int(valid_years.max())


# ============================================================
# TASK 1
# COVERAGE VALIDATION
# ============================================================

def verify_coverage(
    df,
    companies,
):

    print("\n" + "=" * 70)
    print("COVERAGE VALIDATION")
    print("=" * 70)

    # --------------------------------------------------------
    # Company sets
    # --------------------------------------------------------

    db_companies = set(
        companies["company_id"]
        .dropna()
    )

    csv_companies = set(
        df["company_id"]
        .dropna()
    )

    print(
        f"Companies in database : "
        f"{len(db_companies)}"
    )

    print(
        f"Companies in CSV      : "
        f"{len(csv_companies)}"
    )

    # --------------------------------------------------------
    # Missing companies
    # --------------------------------------------------------

    missing_companies = sorted(
        db_companies - csv_companies
    )

    extra_companies = sorted(
        csv_companies - db_companies
    )

    print(
        f"Missing companies     : "
        f"{len(missing_companies)}"
    )

    print(
        f"Extra companies       : "
        f"{len(extra_companies)}"
    )

    if missing_companies:

        print("\nMissing company IDs:")

        for company_id in missing_companies:

            print(
                f"  - {company_id}"
            )

    if extra_companies:

        print("\nExtra company IDs:")

        for company_id in extra_companies:

            print(
                f"  - {company_id}"
            )

    # --------------------------------------------------------
    # Invalid years
    # --------------------------------------------------------

    invalid_years = df[
        df["year"].isna()
    ]

    print(
        f"\nInvalid year rows     : "
        f"{len(invalid_years)}"
    )

    if not invalid_years.empty:

        print(
            "\nRows with invalid years:"
        )

        print(
            invalid_years[
                [
                    "company_id",
                    "year_original",
                ]
            ]
            .head(20)
            .to_string(index=False)
        )

    # --------------------------------------------------------
    # Duplicate company-year
    # --------------------------------------------------------

    duplicates = df[
        df.duplicated(
            subset=[
                "company_id",
                "year",
            ],
            keep=False,
        )
    ].copy()

    print(
        f"\nDuplicate company-year rows : "
        f"{len(duplicates)}"
    )

    if not duplicates.empty:

        print(
            "\nDuplicate records:"
        )

        print(
            duplicates[
                [
                    "company_id",
                    "year",
                    "pattern_label",
                ]
            ]
            .to_string(index=False)
        )

    # --------------------------------------------------------
    # Records per company
    # --------------------------------------------------------

    records_per_company = (
        df.groupby("company_id")
        .size()
    )

    print(
        "\nRecords per company:"
    )

    print(
        f"  Minimum : "
        f"{records_per_company.min()}"
    )

    print(
        f"  Maximum : "
        f"{records_per_company.max()}"
    )

    print(
        f"  Average : "
        f"{records_per_company.mean():.2f}"
    )

    companies_without_records = (
        db_companies
        - set(records_per_company.index)
    )

    print(
        f"\nCompanies with no records : "
        f"{len(companies_without_records)}"
    )

    # --------------------------------------------------------
    # Pattern validation
    # --------------------------------------------------------

    actual_patterns = set(
        df["pattern_label"]
        .dropna()
    )

    unexpected_patterns = sorted(
        actual_patterns
        - set(EXPECTED_PATTERNS)
    )

    print(
        f"\nUnique patterns found : "
        f"{len(actual_patterns)}"
    )

    print("\nPattern counts:")

    pattern_counts = (
        df["pattern_label"]
        .value_counts()
    )

    for pattern in EXPECTED_PATTERNS:

        print(
            f"  {pattern:<30} "
            f"{pattern_counts.get(pattern, 0)}"
        )

    if unexpected_patterns:

        print(
            "\nUnexpected patterns:"
        )

        for pattern in unexpected_patterns:

            print(
                f"  - {pattern}"
            )

    else:

        print(
            "\nPattern validation : PASS"
        )

    # --------------------------------------------------------
    # Status
    # --------------------------------------------------------

    coverage_pass = (
        len(db_companies) == EXPECTED_COMPANIES
        and len(csv_companies) == EXPECTED_COMPANIES
        and len(missing_companies) == 0
        and len(duplicates) == 0
        and len(companies_without_records) == 0
        and len(invalid_years) == 0
        and len(unexpected_patterns) == 0
    )

    if coverage_pass:

        print(
            "\n[PASS] Capital allocation coverage "
            "validated for all 92 companies."
        )

    else:

        print(
            "\n[REVIEW] Coverage validation found issues."
        )

    return coverage_pass


# ============================================================
# TASK 2
# LATEST YEAR DISTRIBUTION
# ============================================================

def generate_distribution(df):

    latest_year = get_latest_year(df)

    latest_df = df[
        pd.to_numeric(
            df["year"],
            errors="coerce",
        ) == latest_year
    ].copy()

    print("\n" + "=" * 70)
    print("LATEST-YEAR CAPITAL ALLOCATION DISTRIBUTION")
    print("=" * 70)

    print(
        f"\nLatest year : {latest_year}"
    )

    # --------------------------------------------------------
    # Count all 8 patterns
    # --------------------------------------------------------

    counts = (
        latest_df["pattern_label"]
        .value_counts()
    )

    distribution = pd.DataFrame(
        {
            "year": latest_year,
            "capital_allocation_pattern":
                EXPECTED_PATTERNS,
            "company_count": [
                int(counts.get(pattern, 0))
                for pattern in EXPECTED_PATTERNS
            ],
        }
    )

    # --------------------------------------------------------
    # Display
    # --------------------------------------------------------

    print()

    for _, row in distribution.iterrows():

        print(
            f"{row['capital_allocation_pattern']:<30}"
            f"{int(row['company_count'])}"
        )

    total = int(
        distribution["company_count"].sum()
    )

    print(
        f"\nDistribution total : "
        f"{total}"
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    distribution.to_csv(
        DISTRIBUTION_FILE,
        index=False,
    )

    print(
        f"\nDistribution output:"
        f"\n{DISTRIBUTION_FILE}"
    )

    if total == EXPECTED_COMPANIES:

        print(
            "\n[PASS] Latest-year distribution "
            "covers all 92 companies."
        )

    else:

        print(
            "\n[REVIEW] Latest-year distribution "
            f"contains {total} companies."
        )

    return distribution, latest_year


# ============================================================
# TASK 3
# UPDATE CASHFLOW INTELLIGENCE EXCEL
# ============================================================

def update_cashflow_intelligence(
    capital_df,
    latest_year,
):

    if not CASHFLOW_INTELLIGENCE_FILE.exists():

        raise FileNotFoundError(
            "Cash flow intelligence file not found:\n"
            f"{CASHFLOW_INTELLIGENCE_FILE}"
        )

    intelligence = pd.read_excel(
        CASHFLOW_INTELLIGENCE_FILE
    )

    print("\n" + "=" * 70)
    print("UPDATING CASH FLOW INTELLIGENCE")
    print("=" * 70)

    # --------------------------------------------------------
    # Find company ID
    # --------------------------------------------------------

    company_column = find_column(
        intelligence,
        [
            "company_id",
            "company",
            "id",
        ],
    )

    if company_column is None:

        raise ValueError(
            "Could not find company_id in "
            "cashflow_intelligence.xlsx"
        )

    if company_column != "company_id":

        intelligence = intelligence.rename(
            columns={
                company_column:
                    "company_id"
            }
        )

    intelligence["company_id"] = (
        intelligence["company_id"]
        .map(normalize_company_id)
    )

    # --------------------------------------------------------
    # Select latest year
    # --------------------------------------------------------

    latest_capital = capital_df[
        pd.to_numeric(
            capital_df["year"],
            errors="coerce",
        ) == latest_year
    ].copy()

    latest_capital = latest_capital[
        [
            "company_id",
            "pattern_label",
        ]
    ].drop_duplicates(
        subset=["company_id"]
    )

    latest_capital = latest_capital.rename(
        columns={
            "pattern_label":
                "capital_allocation"
        }
    )

    # --------------------------------------------------------
    # Remove existing column if present
    # --------------------------------------------------------

    if "capital_allocation" in intelligence.columns:

        intelligence = intelligence.drop(
            columns=[
                "capital_allocation"
            ]
        )

    # --------------------------------------------------------
    # Merge
    # --------------------------------------------------------

    intelligence = intelligence.merge(
        latest_capital,
        on="company_id",
        how="left",
    )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    total_companies = len(
        intelligence
    )

    matched = int(
        intelligence[
            "capital_allocation"
        ].notna().sum()
    )

    missing = (
        total_companies - matched
    )

    print(
        f"Companies in Excel       : "
        f"{total_companies}"
    )

    print(
        f"Capital allocation matched: "
        f"{matched}"
    )

    print(
        f"Missing capital allocation: "
        f"{missing}"
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    with pd.ExcelWriter(
        CASHFLOW_INTELLIGENCE_FILE,
        engine="openpyxl",
    ) as writer:

        intelligence.to_excel(
            writer,
            index=False,
            sheet_name="cashflow_intelligence",
        )

    if (
        total_companies == EXPECTED_COMPANIES
        and matched == EXPECTED_COMPANIES
    ):

        print(
            "\n[PASS] Capital allocation added "
            "for all 92 companies."
        )

    else:

        print(
            "\n[REVIEW] Capital allocation "
            "matching is incomplete."
        )

    print(
        f"\nUpdated Excel:"
        f"\n{CASHFLOW_INTELLIGENCE_FILE}"
    )

    return intelligence


# ============================================================
# TASK 4
# YEAR-OVER-YEAR PATTERN CHANGES
# ============================================================

def generate_pattern_changes(
    df,
    companies,
):

    print("\n" + "=" * 70)
    print("YEAR-OVER-YEAR PATTERN CHANGES")
    print("=" * 70)

    working = df[
        [
            "company_id",
            "year",
            "pattern_label",
        ]
    ].copy()

    # --------------------------------------------------------
    # Numeric year for sorting
    # --------------------------------------------------------

    working["year_numeric"] = pd.to_numeric(
        working["year"],
        errors="coerce",
    )

    working = working[
        working["year_numeric"].notna()
    ].copy()

    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    working = working.sort_values(
        [
            "company_id",
            "year_numeric",
        ]
    )

    # --------------------------------------------------------
    # Previous pattern
    # --------------------------------------------------------

    working["previous_year"] = (
        working
        .groupby("company_id")["year_numeric"]
        .shift(1)
    )

    working["previous_pattern"] = (
        working
        .groupby("company_id")["pattern_label"]
        .shift(1)
    )

    # --------------------------------------------------------
    # Detect changes
    # --------------------------------------------------------

    changes = working[
        working["previous_pattern"].notna()
        & (
            working["previous_pattern"]
            != working["pattern_label"]
        )
    ].copy()

    # --------------------------------------------------------
    # Add company name
    # --------------------------------------------------------

    company_names = companies[
        [
            "company_id",
            "company_name",
        ]
    ].drop_duplicates(
        subset=["company_id"]
    )

    changes = changes.merge(
        company_names,
        on="company_id",
        how="left",
    )

    # --------------------------------------------------------
    # Rename columns
    # --------------------------------------------------------

    changes = changes.rename(
        columns={
            "year_numeric":
                "current_year",
            "pattern_label":
                "current_pattern",
        }
    )

    changes["previous_year"] = (
        changes["previous_year"]
        .astype(int)
    )

    changes["current_year"] = (
        changes["current_year"]
        .astype(int)
    )

    # --------------------------------------------------------
    # Final columns
    # --------------------------------------------------------

    changes = changes[
        [
            "company_id",
            "company_name",
            "previous_year",
            "previous_pattern",
            "current_year",
            "current_pattern",
        ]
    ]

    changes = changes.sort_values(
        [
            "company_id",
            "current_year",
        ]
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    changes.to_csv(
        PATTERN_CHANGES_FILE,
        index=False,
    )

    print(
        f"\nPattern changes detected : "
        f"{len(changes)}"
    )

    if not changes.empty:

        print(
            "\nFirst 20 pattern changes:"
        )

        print(
            changes
            .head(20)
            .to_string(index=False)
        )

    else:

        print(
            "\nNo year-over-year pattern "
            "changes detected."
        )

    print(
        f"\nPattern changes output:"
        f"\n{PATTERN_CHANGES_FILE}"
    )

    return changes


# ============================================================
# FINAL VALIDATION
# ============================================================

def final_validation(
    capital_df,
    intelligence_df,
    distribution_df,
    changes_df,
):

    print("\n" + "=" * 70)
    print("FINAL DAY 32 VALIDATION")
    print("=" * 70)

    # --------------------------------------------------------
    # Capital allocation rows
    # --------------------------------------------------------

    print(
        f"Capital allocation rows : "
        f"{len(capital_df)}"
    )

    # --------------------------------------------------------
    # Unique companies
    # --------------------------------------------------------

    unique_companies = (
        capital_df["company_id"]
        .nunique()
    )

    print(
        f"Unique companies        : "
        f"{unique_companies}"
    )

    # --------------------------------------------------------
    # Year coverage
    # --------------------------------------------------------

    valid_years = (
        capital_df["year"]
        .dropna()
        .nunique()
    )

    print(
        f"Unique years            : "
        f"{valid_years}"
    )

    # --------------------------------------------------------
    # Excel
    # --------------------------------------------------------

    print(
        f"Intelligence rows       : "
        f"{len(intelligence_df)}"
    )

    has_column = (
        "capital_allocation"
        in intelligence_df.columns
    )

    print(
        f"capital_allocation column : "
        f"{'YES' if has_column else 'NO'}"
    )

    # --------------------------------------------------------
    # Distribution
    # --------------------------------------------------------

    distribution_total = int(
        distribution_df[
            "company_count"
        ].sum()
    )

    print(
        f"Latest-year distribution : "
        f"{distribution_total} companies"
    )

    # --------------------------------------------------------
    # Pattern changes
    # --------------------------------------------------------

    print(
        f"Pattern changes         : "
        f"{len(changes_df)}"
    )

    # --------------------------------------------------------
    # Final status
    # --------------------------------------------------------

    if (
        unique_companies == EXPECTED_COMPANIES
        and len(intelligence_df)
            == EXPECTED_COMPANIES
        and has_column
        and distribution_total
            == EXPECTED_COMPANIES
    ):

        print(
            "\nDAY 32 STATUS: COMPLETED"
        )

    else:

        print(
            "\nDAY 32 STATUS: REVIEW REQUIRED"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("N100 CAPITAL ALLOCATION REPORT")
    print("SPRINT 5 - DAY 32")
    print("=" * 70)

    print(
        f"\nProject root:"
        f"\n{PROJECT_ROOT}"
    )

    print(
        f"\nDatabase:"
        f"\n{DATABASE_PATH}"
    )

    print(
        f"\nCapital allocation CSV:"
        f"\n{CAPITAL_ALLOCATION_FILE}"
    )

    # --------------------------------------------------------
    # Output directory
    # --------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Load companies
    # --------------------------------------------------------

    print(
        "\nLoading company database..."
    )

    companies = load_companies()

    print(
        f"Companies loaded : "
        f"{len(companies)}"
    )

    # --------------------------------------------------------
    # Load capital allocation
    # --------------------------------------------------------

    print(
        "\nLoading Sprint 2 capital allocation..."
    )

    capital_df = load_capital_allocation()

    print(
        f"\nCapital allocation rows : "
        f"{len(capital_df)}"
    )

    # --------------------------------------------------------
    # Task 1
    # --------------------------------------------------------

    verify_coverage(
        capital_df,
        companies,
    )

    # --------------------------------------------------------
    # Task 2
    # --------------------------------------------------------

    distribution_df, latest_year = (
        generate_distribution(
            capital_df
        )
    )

    # --------------------------------------------------------
    # Task 3
    # --------------------------------------------------------

    intelligence_df = (
        update_cashflow_intelligence(
            capital_df,
            latest_year,
        )
    )

    # --------------------------------------------------------
    # Task 4
    # --------------------------------------------------------

    changes_df = (
        generate_pattern_changes(
            capital_df,
            companies,
        )
    )

    # --------------------------------------------------------
    # Final validation
    # --------------------------------------------------------

    final_validation(
        capital_df,
        intelligence_df,
        distribution_df,
        changes_df,
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()