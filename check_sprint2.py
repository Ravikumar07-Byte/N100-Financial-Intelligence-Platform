import sqlite3
from pathlib import Path
import subprocess
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "nifty100.db"

OUTPUT_DIR = ROOT / "output"
LOG_FILE = OUTPUT_DIR / "ratio_edge_cases.log"
CAPITAL_FILE = OUTPUT_DIR / "capital_allocation.csv"


print("=" * 80)
print("SPRINT 2 — FINANCIAL RATIO ENGINE VERIFICATION")
print("=" * 80)

passed = 0
failed = 0
warnings = 0


def check(name, condition, details=""):
    global passed, failed

    if condition:
        print(f"[PASS] {name}")
        if details:
            print(f"       {details}")
        passed += 1
    else:
        print(f"[FAIL] {name}")
        if details:
            print(f"       {details}")
        failed += 1


def warn(name, details=""):
    global warnings

    print(f"[WARN] {name}")
    if details:
        print(f"       {details}")

    warnings += 1


# ---------------------------------------------------------------------
# 1. DATABASE EXISTS
# ---------------------------------------------------------------------

print("\n1. DATABASE")
print("-" * 80)

check(
    "nifty100.db exists",
    DB_PATH.exists(),
    str(DB_PATH)
)


if not DB_PATH.exists():
    print("\nDatabase not found. Verification stopped.")
    sys.exit(1)


# ---------------------------------------------------------------------
# CONNECT DATABASE
# ---------------------------------------------------------------------

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()


# ---------------------------------------------------------------------
# 2. FINANCIAL_RATIOS TABLE
# ---------------------------------------------------------------------

print("\n2. FINANCIAL_RATIOS TABLE")
print("-" * 80)

cursor.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type='table'
      AND name='financial_ratios'
""")

table_exists = cursor.fetchone() is not None

check(
    "financial_ratios table exists",
    table_exists
)


if not table_exists:
    conn.close()
    print("\nfinancial_ratios table does not exist.")
    sys.exit(1)


cursor.execute("SELECT COUNT(*) FROM financial_ratios")
row_count = cursor.fetchone()[0]

check(
    "financial_ratios row count >= 1,100",
    row_count >= 1100,
    f"Actual rows: {row_count}"
)


# ---------------------------------------------------------------------
# 3. REQUIRED KPI COLUMNS
# ---------------------------------------------------------------------

print("\n3. REQUIRED KPI COLUMNS")
print("-" * 80)

required_columns = [
    "net_profit_margin_pct",
    "operating_profit_margin_pct",
    "return_on_equity_pct",
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
]

cursor.execute("PRAGMA table_info(financial_ratios)")
db_columns = {row[1] for row in cursor.fetchall()}

missing_columns = [
    col for col in required_columns
    if col not in db_columns
]

check(
    "All required KPI columns exist",
    len(missing_columns) == 0,
    f"Missing: {missing_columns}" if missing_columns else "All required columns found"
)


# ---------------------------------------------------------------------
# 4. KPI NULL CHECK
# ---------------------------------------------------------------------

print("\n4. KPI POPULATION CHECK")
print("-" * 80)

for column in required_columns:

    if column not in db_columns:
        continue

    cursor.execute(f"""
        SELECT
            COUNT(*) AS total_rows,
            COUNT("{column}") AS non_null_rows
        FROM financial_ratios
    """)

    total, non_null = cursor.fetchone()

    check(
        f"{column} is not null-only",
        non_null > 0,
        f"{non_null}/{total} rows populated"
    )


# ---------------------------------------------------------------------
# 5. CAPITAL ALLOCATION FILE
# ---------------------------------------------------------------------

print("\n5. CAPITAL ALLOCATION")
print("-" * 80)

check(
    "capital_allocation.csv exists",
    CAPITAL_FILE.exists(),
    str(CAPITAL_FILE)
)

if CAPITAL_FILE.exists():

    try:
        cap_df = pd.read_csv(CAPITAL_FILE)

        required_cap_columns = [
            "company_id",
            "year",
            "cfo_sign",
            "cfi_sign",
            "cff_sign",
            "pattern_label",
        ]

        missing = [
            c for c in required_cap_columns
            if c not in cap_df.columns
        ]

        check(
            "Capital allocation columns exist",
            len(missing) == 0,
            f"Missing: {missing}" if missing else "All columns found"
        )

        check(
            "Capital allocation file contains rows",
            len(cap_df) > 0,
            f"Rows: {len(cap_df)}"
        )

        expected_patterns = {
            "Reinvestor",
            "Shareholder Returns",
            "Liquidating Assets",
            "Distress Signal",
            "Growth Funded by Debt",
            "Cash Accumulator",
            "Pre-Revenue",
            "Mixed",
        }

        if "pattern_label" in cap_df.columns:

            actual_patterns = set(
                cap_df["pattern_label"]
                .dropna()
                .astype(str)
                .unique()
            )

            unexpected = actual_patterns - expected_patterns

            check(
                "Capital allocation uses expected pattern labels",
                len(unexpected) == 0,
                f"Unexpected labels: {unexpected}"
            )

            print("\n       Pattern distribution:")

            print(
                cap_df["pattern_label"]
                .value_counts()
                .to_string()
            )

    except Exception as e:
        check(
            "capital_allocation.csv readable",
            False,
            str(e)
        )


# ---------------------------------------------------------------------
# 6. RATIO EDGE CASE LOG
# ---------------------------------------------------------------------

print("\n6. RATIO EDGE CASE LOG")
print("-" * 80)

check(
    "ratio_edge_cases.log exists",
    LOG_FILE.exists(),
    str(LOG_FILE)
)

if LOG_FILE.exists():

    try:
        text = LOG_FILE.read_text(
            encoding="utf-8",
            errors="ignore"
        )

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        check(
            "ratio_edge_cases.log is not empty",
            len(lines) > 0,
            f"Non-empty lines: {len(lines)}"
        )

        categories = [
            "data source issue",
            "version difference",
            "formula discrepancy",
        ]

        found_categories = [
            category
            for category in categories
            if category.lower() in text.lower()
        ]

        check(
            "Edge-case categories documented",
            len(found_categories) > 0,
            f"Found categories: {found_categories}"
        )

    except Exception as e:
        check(
            "ratio_edge_cases.log readable",
            False,
            str(e)
        )


# ---------------------------------------------------------------------
# 7. KPI UNIT TESTS
# ---------------------------------------------------------------------

print("\n7. KPI UNIT TESTS")
print("-" * 80)

tests_dir = ROOT / "tests" / "kpi"

check(
    "tests/kpi directory exists",
    tests_dir.exists(),
    str(tests_dir)
)

if tests_dir.exists():

    test_files = list(tests_dir.glob("test_*.py"))

    print(f"       KPI test files: {len(test_files)}")

    for f in test_files:
        print(f"       - {f.name}")

    try:

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/kpi",
                "-v",
                "--tb=short",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )

        print("\n--- PYTEST OUTPUT ---")
        print(result.stdout)

        if result.stderr:
            print("--- STDERR ---")
            print(result.stderr)

        check(
            "KPI unit tests pass",
            result.returncode == 0,
            f"pytest exit code: {result.returncode}"
        )

    except Exception as e:

        check(
            "KPI tests executable",
            False,
            str(e)
        )


# ---------------------------------------------------------------------
# 8. RATIO ENGINE FILES
# ---------------------------------------------------------------------

print("\n8. SPRINT 2 SOURCE FILES")
print("-" * 80)

required_files = [
    ROOT / "src" / "analytics" / "ratios.py",
    ROOT / "src" / "analytics" / "cagr.py",
    ROOT / "src" / "analytics" / "cashflow_kpis.py",
]

for file_path in required_files:

    check(
        file_path.relative_to(ROOT).as_posix(),
        file_path.exists()
    )


# ---------------------------------------------------------------------
# 9. SCREENER PREVIEW
# ---------------------------------------------------------------------

print("\n9. SCREENER PREVIEW")
print("-" * 80)

try:

    query = """
        SELECT COUNT(*)
        FROM financial_ratios
        WHERE return_on_equity_pct > 15
          AND debt_to_equity < 1
    """

    cursor.execute(query)

    screener_count = cursor.fetchone()[0]

    check(
        "ROE > 15% and D/E < 1 result count between 15 and 50",
        15 <= screener_count <= 50,
        f"Result count: {screener_count}"
    )

except Exception as e:

    check(
        "Screener preview query works",
        False,
        str(e)
    )


# ---------------------------------------------------------------------
# 10. DEBT-FREE D/E CHECK
# ---------------------------------------------------------------------

print("\n10. EDGE CASE — DEBT FREE")
print("-" * 80)

if "debt_to_equity" in db_columns:

    cursor.execute("""
        SELECT COUNT(*)
        FROM financial_ratios
        WHERE debt_to_equity = 0
    """)

    debt_free_count = cursor.fetchone()[0]

    check(
        "Debt-free companies can have D/E = 0",
        debt_free_count > 0,
        f"Rows with D/E = 0: {debt_free_count}"
    )


# ---------------------------------------------------------------------
# 11. ICR LABEL CHECK
# ---------------------------------------------------------------------

print("\n11. ICR LABEL")
print("-" * 80)

if "icr_label" in db_columns:

    cursor.execute("""
        SELECT COUNT(*)
        FROM financial_ratios
        WHERE LOWER(icr_label) = 'debt free'
    """)

    debt_free_icr = cursor.fetchone()[0]

    check(
        "Debt Free ICR label exists",
        debt_free_icr > 0,
        f"Debt Free labels: {debt_free_icr}"
    )

else:

    warn(
        "icr_label column not present",
        "Sprint 2 specification requires a separate icr_label column."
    )


# ---------------------------------------------------------------------
# 12. HIGH LEVERAGE FLAG
# ---------------------------------------------------------------------

print("\n12. HIGH LEVERAGE FLAG")
print("-" * 80)

if "high_leverage_flag" in db_columns:

    cursor.execute("""
        SELECT COUNT(*)
        FROM financial_ratios
        WHERE high_leverage_flag = 1
    """)

    high_leverage = cursor.fetchone()[0]

    print(
        f"[INFO] High leverage rows: {high_leverage}"
    )

else:

    warn(
        "high_leverage_flag column not present",
        "Sprint 2 specifies this flag."
    )


# ---------------------------------------------------------------------
# 13. ICR WARNING FLAG
# ---------------------------------------------------------------------

print("\n13. ICR WARNING FLAG")
print("-" * 80)

if "icr_warning_flag" in db_columns:

    cursor.execute("""
        SELECT COUNT(*)
        FROM financial_ratios
        WHERE icr_warning_flag = 1
    """)

    icr_warning = cursor.fetchone()[0]

    print(
        f"[INFO] ICR warning rows: {icr_warning}"
    )

else:

    warn(
        "icr_warning_flag column not present",
        "Sprint 2 specifies ICR < 1.5 warning flag."
    )


# ---------------------------------------------------------------------
# 14. FINANCIALS SECTOR CHECK
# ---------------------------------------------------------------------

print("\n14. FINANCIALS SECTOR CHECK")
print("-" * 80)

try:

    cursor.execute("""
        SELECT COUNT(*)
        FROM companies
        WHERE LOWER(broad_sector) = 'financials'
    """)

    financial_companies = cursor.fetchone()[0]

    print(
        f"[INFO] Financials broad_sector companies: {financial_companies}"
    )

    check(
        "Financials sector has approximately 19 companies",
        financial_companies == 19,
        f"Actual: {financial_companies}"
    )

except Exception as e:

    warn(
        "Could not verify Financials sector",
        str(e)
    )


# ---------------------------------------------------------------------
# 15. DATABASE INTEGRITY
# ---------------------------------------------------------------------

print("\n15. DATABASE INTEGRITY")
print("-" * 80)

cursor.execute("PRAGMA foreign_key_check")
fk_errors = cursor.fetchall()

check(
    "Foreign key check has zero violations",
    len(fk_errors) == 0,
    f"Violations: {len(fk_errors)}"
)


# ---------------------------------------------------------------------
# 16. SAMPLE DATA
# ---------------------------------------------------------------------

print("\n16. SAMPLE FINANCIAL RATIOS")
print("-" * 80)

select_columns = [
    "company_id",
    "year",
]

for col in required_columns[:8]:

    if col in db_columns:
        select_columns.append(col)

query = f"""
    SELECT {", ".join(select_columns)}
    FROM financial_ratios
    LIMIT 5
"""

sample_df = pd.read_sql_query(query, conn)

print(sample_df.to_string(index=False))


# ---------------------------------------------------------------------
# FINAL SUMMARY
# ---------------------------------------------------------------------

conn.close()

print("\n" + "=" * 80)
print("SPRINT 2 VERIFICATION SUMMARY")
print("=" * 80)

print(f"PASS    : {passed}")
print(f"FAIL    : {failed}")
print(f"WARNING : {warnings}")

print()

if failed == 0:
    print("RESULT: SPRINT 2 EXIT CRITERIA PASSED")
else:
    print("RESULT: SPRINT 2 HAS ITEMS REQUIRING REVIEW")

print("=" * 80)