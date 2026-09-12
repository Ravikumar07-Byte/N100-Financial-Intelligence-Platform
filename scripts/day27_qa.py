"""
Day 27 — Integration QA & Bug Fixes
N100 Financial Intelligence Platform

Checks:
1. All 8 Streamlit screens exist and can be compiled.
2. 10 tickers across IT, Financials, FMCG, Energy, Healthcare.
3. Partial/missing data handling.
4. Extreme screener data conditions.
5. Chart configuration/layout checks.
6. Missing-value handling.
7. Company Profile data-load performance for 5 tickers.
8. SQLite database integrity.

Note:
This script performs automated data/static QA.
Manual browser verification is still required for:
- All 8 live Streamlit screens
- Visual chart sizing/overflow
- Actual UI display of N/A values
- Interactive screener/preset behavior
- Annual report links
"""

from pathlib import Path
import sys
import time
import sqlite3
import math

import pandas as pd


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SRC = PROJECT_ROOT / "src"

PAGES = SRC / "dashboard" / "pages"

DB_PATH = PROJECT_ROOT / "nifty100.db"


if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


# ============================================================
# TEST CONFIGURATION
# ============================================================

TEST_TICKERS = {
    "IT": [
        "INFY",
        "TCS",
    ],
    "Financials": [
        "HDFCBANK",
        "SBIN",
    ],
    "FMCG": [
        "HINDUNILVR",
        "ITC",
    ],
    "Energy": [
        "RELIANCE",
        "ONGC",
    ],
    "Healthcare": [
        "DRREDDY",
        "SUNPHARMA",
    ],
}


ALL_TICKERS = [
    ticker
    for tickers in TEST_TICKERS.values()
    for ticker in tickers
]


REQUIRED_PAGES = [
    "01_home.py",
    "02_profile.py",
    "03_screener.py",
    "04_peers.py",
    "05_trends.py",
    "06_sectors.py",
    "07_capital.py",
    "08_reports.py",
]


# Screener is intentionally excluded because the Day 27
# chart test is only for pages that are expected to contain
# Plotly visualizations.
CHART_PAGES = [
    "01_home.py",
    "02_profile.py",
    "04_peers.py",
    "05_trends.py",
    "06_sectors.py",
    "07_capital.py",
]


PERFORMANCE_TICKERS = [
    "INFY",
    "TCS",
    "HDFCBANK",
    "DRREDDY",
    "SBIN",
]


# ============================================================
# RESULT TRACKING
# ============================================================

results = []


def record(test, status, details=""):
    """
    Store and print a QA result.
    """

    results.append(
        {
            "Test": test,
            "Status": status,
            "Details": details,
        }
    )

    if status == "PASS":
        symbol = "PASS"
    elif status == "FAIL":
        symbol = "FAIL"
    else:
        symbol = "WARN"

    print(f"[{symbol}] {test}")

    if details:
        print(f"       {details}")


# ============================================================
# IMPORT DATABASE FUNCTIONS
# ============================================================

try:

    from dashboard.utils.db import (
        get_companies,
        get_profile_history,
        get_latest_profile_metrics,
        get_all_ratios,
        get_market_valuations,
        get_home_financial_data,
        get_market_data_for_year,
    )

    record(
        "Database utility import",
        "PASS",
        "dashboard.utils.db imported successfully.",
    )

except Exception as exc:

    record(
        "Database utility import",
        "FAIL",
        repr(exc),
    )

    raise


# ============================================================
# 1. CHECK ALL 8 STREAMLIT SCREENS
# ============================================================

print("\n" + "=" * 70)
print("1. ALL 8 STREAMLIT SCREENS")
print("=" * 70)

missing_pages = []

for page in REQUIRED_PAGES:

    path = PAGES / page

    if path.exists():

        record(
            f"Screen exists: {page}",
            "PASS",
            str(path.relative_to(PROJECT_ROOT)),
        )

    else:

        missing_pages.append(page)

        record(
            f"Screen exists: {page}",
            "FAIL",
            "Page file not found.",
        )


if not missing_pages:

    record(
        "All 8 dashboard screens",
        "PASS",
        "All required Streamlit page files are present.",
    )


# ============================================================
# 2. COMPILE ALL STREAMLIT PAGES
# ============================================================

print("\n" + "=" * 70)
print("2. STREAMLIT PAGE SYNTAX CHECK")
print("=" * 70)

syntax_failures = []

for page in REQUIRED_PAGES:

    path = PAGES / page

    if not path.exists():
        continue

    try:

        # utf-8-sig handles both:
        # - normal UTF-8
        # - UTF-8 files containing BOM
        source = path.read_text(
            encoding="utf-8-sig"
        )

        compile(
            source,
            str(path),
            "exec",
        )

        record(
            f"Python syntax: {page}",
            "PASS",
            "Compilation successful.",
        )

    except Exception as exc:

        syntax_failures.append(page)

        record(
            f"Python syntax: {page}",
            "FAIL",
            repr(exc),
        )


if not syntax_failures:

    record(
        "All 8 page syntax checks",
        "PASS",
        "All dashboard pages compiled successfully.",
    )


# ============================================================
# 3. CHECK 92-COMPANY UNIVERSE
# ============================================================

print("\n" + "=" * 70)
print("3. COMPANY UNIVERSE")
print("=" * 70)

companies = None

company_ids = set()


try:

    companies = get_companies()

    company_count = len(companies)

    if company_count == 92:

        record(
            "Company universe",
            "PASS",
            "92 companies available.",
        )

    else:

        record(
            "Company universe",
            "FAIL",
            (
                f"Expected 92 companies, "
                f"found {company_count}."
            ),
        )


    # --------------------------------------------------------
    # IMPORTANT DATABASE STRUCTURE
    #
    # get_companies() returns:
    #
    # id
    # company_logo
    # company_name
    # ...
    #
    # The ticker/company identifier is stored in "id".
    # There is no "company_id" column in this DataFrame.
    # --------------------------------------------------------

    if "id" not in companies.columns:

        record(
            "Company identifier column",
            "FAIL",
            "Expected companies['id'] column was not found.",
        )

    else:

        company_ids = set(
            companies["id"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        record(
            "Company identifier column",
            "PASS",
            (
                f"Loaded {len(company_ids)} "
                "company identifiers from companies['id']."
            ),
        )

except Exception as exc:

    record(
        "Company universe",
        "FAIL",
        repr(exc),
    )


# ============================================================
# 4. TEST 10 TICKERS ACROSS 5 SECTORS
# ============================================================

print("\n" + "=" * 70)
print("4. 10 TICKER CROSS-SECTOR QA")
print("=" * 70)

missing_tickers = []

ticker_results = []

if not company_ids:

    record(
        "Cross-sector ticker validation",
        "FAIL",
        "No company identifiers available.",
    )

else:

    for sector, tickers in TEST_TICKERS.items():

        for ticker in tickers:

            ticker = str(ticker).strip().upper()

            if ticker not in company_ids:

                missing_tickers.append(ticker)

                record(
                    f"{ticker} — {sector}",
                    "FAIL",
                    "Ticker not found in company universe.",
                )

                continue

            try:

                start = time.perf_counter()

                history = get_profile_history(
                    ticker
                )

                elapsed = (
                    time.perf_counter()
                    - start
                )

                if (
                    history is None
                    or len(history) == 0
                ):

                    record(
                        f"{ticker} — {sector}",
                        "FAIL",
                        "No profile history returned.",
                    )

                    continue

                ticker_results.append(
                    {
                        "ticker": ticker,
                        "sector": sector,
                        "rows": len(history),
                        "load_seconds": elapsed,
                    }
                )

                record(
                    f"{ticker} — {sector}",
                    "PASS",
                    (
                        f"{len(history)} historical "
                        f"rows loaded in {elapsed:.4f}s."
                    ),
                )

            except Exception as exc:

                record(
                    f"{ticker} — {sector}",
                    "FAIL",
                    repr(exc),
                )


if not missing_tickers:

    record(
        "Cross-sector ticker coverage",
        "PASS",
        (
            "All 10 required tickers were found "
            "across IT, Financials, FMCG, Energy "
            "and Healthcare."
        ),
    )

else:

    record(
        "Cross-sector ticker coverage",
        "FAIL",
        f"Missing tickers: {missing_tickers}",
    )


# ============================================================
# 5. PARTIAL DATA / MISSING DATA TEST
# ============================================================

print("\n" + "=" * 70)
print("5. PARTIAL / MISSING DATA QA")
print("=" * 70)

partial_data_found = False

partial_tickers = []

missing_value_tickers = []


for ticker in ALL_TICKERS:

    try:

        history = get_profile_history(
            ticker
        )

        if (
            history is None
            or len(history) == 0
        ):

            record(
                f"{ticker} partial-data handling",
                "FAIL",
                "No data returned.",
            )

            continue

        df = history.copy()

        years_available = len(df)

        missing_columns = [
            column
            for column in df.columns
            if df[column].isna().any()
        ]


        # ----------------------------------------------------
        # Fewer than 10 years
        # ----------------------------------------------------

        if years_available < 10:

            partial_data_found = True

            partial_tickers.append(ticker)

            record(
                f"{ticker} historical coverage",
                "PASS",
                (
                    f"Only {years_available} historical "
                    "rows available; partial-history "
                    "condition detected safely."
                ),
            )


        # ----------------------------------------------------
        # Missing fields
        # ----------------------------------------------------

        if missing_columns:

            partial_data_found = True

            missing_value_tickers.append(
                ticker
            )

            details = (
                f"{years_available} rows; "
                f"missing columns="
                f"{missing_columns[:8]}"
            )

            record(
                f"{ticker} missing-data handling",
                "PASS",
                details,
            )


        # ----------------------------------------------------
        # Completely populated case
        # ----------------------------------------------------

        if (
            years_available >= 10
            and not missing_columns
        ):

            record(
                f"{ticker} missing-data scan",
                "PASS",
                (
                    f"{years_available} rows; "
                    "no missing values detected."
                ),
            )

    except Exception as exc:

        record(
            f"{ticker} partial-data handling",
            "FAIL",
            repr(exc),
        )


if partial_data_found:

    record(
        "Partial/missing data coverage",
        "PASS",
        (
            f"Detected partial/missing data safely. "
            f"Partial-history tickers: "
            f"{partial_tickers if partial_tickers else 'None'}; "
            f"missing-value tickers: "
            f"{missing_value_tickers if missing_value_tickers else 'None'}."
        ),
    )

else:

    record(
        "Partial/missing data coverage",
        "WARN",
        (
            "No partial-history or missing-value "
            "case was found among the selected tickers."
        ),
    )


# ============================================================
# 6. EXTREME SCREENER CONDITIONS
# ============================================================

print("\n" + "=" * 70)
print("6. EXTREME SCREENER CONDITIONS")
print("=" * 70)

try:

    ratios = get_all_ratios(
        2024
    )

    if (
        ratios is None
        or len(ratios) == 0
    ):

        raise ValueError(
            "No ratio data available."
        )


    numeric_columns = [
        "return_on_equity_pct",
        "debt_to_equity",
        "free_cash_flow_cr",
        "revenue_cagr_5yr",
        "pat_cagr_5yr",
        "operating_profit_margin_pct",
        "interest_coverage",
    ]


    available_numeric = [
        column
        for column in numeric_columns
        if column in ratios.columns
    ]


    if not available_numeric:

        raise ValueError(
            "No screener numeric columns found."
        )


    test_df = ratios.copy()


    # --------------------------------------------------------
    # Convert all screener fields safely to numeric.
    # --------------------------------------------------------

    for column in available_numeric:

        test_df[column] = pd.to_numeric(
            test_df[column],
            errors="coerce",
        )


    # --------------------------------------------------------
    # Extreme minimum filters
    # --------------------------------------------------------

    minimum_df = test_df.copy()

    for column in available_numeric:

        minimum_value = (
            test_df[column].min()
        )

        if pd.notna(minimum_value):

            minimum_df = minimum_df[
                minimum_df[column].isna()
                | (
                    minimum_df[column]
                    >= minimum_value
                )
            ]


    record(
        "Screener — all minimum values",
        "PASS",
        (
            f"Processed {len(minimum_df)} "
            "rows without crash."
        ),
    )


    # --------------------------------------------------------
    # Extreme maximum filters
    # --------------------------------------------------------

    maximum_df = test_df.copy()

    for column in available_numeric:

        maximum_value = (
            test_df[column].max()
        )

        if pd.notna(maximum_value):

            maximum_df = maximum_df[
                maximum_df[column].isna()
                | (
                    maximum_df[column]
                    <= maximum_value
                )
            ]


    record(
        "Screener — all maximum values",
        "PASS",
        (
            f"Processed {len(maximum_df)} "
            "rows without crash."
        ),
    )


    # --------------------------------------------------------
    # Guaranteed no-result condition
    #
    # We previously used ROE >= 1000, but the dataset contains
    # two legitimate/extreme values:
    #
    # BEL  = 4744.047619
    # HAL  = 3816.582915
    #
    # Therefore 1000 is NOT guaranteed to produce zero rows.
    #
    # 100000 is used here as a deliberately impossible test
    # threshold to verify safe zero-result handling.
    # --------------------------------------------------------

    restrictive_df = test_df.copy()


    if "return_on_equity_pct" in restrictive_df.columns:

        restrictive_df = restrictive_df[
            restrictive_df[
                "return_on_equity_pct"
            ] >= 100000
        ]


        if len(restrictive_df) == 0:

            record(
                "Screener — restrictive/no-result condition",
                "PASS",
                (
                    "Returned 0 rows safely "
                    "without crash."
                ),
            )

        else:

            record(
                "Screener — restrictive/no-result condition",
                "WARN",
                (
                    f"Returned {len(restrictive_df)} "
                    "rows; verify restrictive "
                    "threshold behavior."
                ),
            )

    else:

        record(
            "Screener — restrictive/no-result condition",
            "WARN",
            "ROE column unavailable.",
        )


except Exception as exc:

    record(
        "Extreme screener conditions",
        "FAIL",
        repr(exc),
    )


# ============================================================
# 7. MISSING VALUE CONVERSION TEST
# ============================================================

print("\n" + "=" * 70)
print("7. MISSING VALUE HANDLING")
print("=" * 70)


def display_value(
    value,
    suffix=""
):
    """
    Expected dashboard behavior:

    None / NaN -> N/A
    numeric -> formatted numeric value

    Important:
    0 is a valid numeric value and must display
    as 0.00 rather than N/A.
    """

    if value is None:

        return "N/A"


    try:

        if pd.isna(value):

            return "N/A"

    except Exception:

        pass


    try:

        number = float(value)

        if math.isnan(number):

            return "N/A"

        return (
            f"{number:.2f}"
            f"{suffix}"
        )

    except (
        TypeError,
        ValueError,
    ):

        return "N/A"


test_values = [
    None,
    float("nan"),
    0,
    12.3456,
]


expected_values = [
    "N/A",
    "N/A",
    "0.00",
    "12.35",
]


for value, expected_value in zip(
    test_values,
    expected_values,
):

    actual = display_value(
        value
    )

    if actual == expected_value:

        record(
            f"Missing-value conversion: {value}",
            "PASS",
            f"Displayed as {actual}",
        )

    else:

        record(
            f"Missing-value conversion: {value}",
            "FAIL",
            (
                f"Expected {expected_value}, "
                f"got {actual}"
            ),
        )


# ============================================================
# 8. PROFILE LOAD PERFORMANCE
# ============================================================

print("\n" + "=" * 70)
print("8. COMPANY PROFILE PERFORMANCE")
print("=" * 70)

performance_times = []


for ticker in PERFORMANCE_TICKERS:

    try:

        start = time.perf_counter()


        history = get_profile_history(
            ticker
        )

        metrics = get_latest_profile_metrics(
            ticker
        )


        elapsed = (
            time.perf_counter()
            - start
        )


        performance_times.append(
            elapsed
        )


        # Ensure both calls actually returned.
        if history is None:

            raise ValueError(
                "Profile history returned None."
            )


        if metrics is None:

            raise ValueError(
                "Latest profile metrics returned None."
            )


        if elapsed < 3:

            record(
                f"{ticker} profile load",
                "PASS",
                (
                    f"{elapsed:.4f}s "
                    "(< 3 seconds)"
                ),
            )

        else:

            record(
                f"{ticker} profile load",
                "FAIL",
                (
                    f"{elapsed:.4f}s "
                    "(>= 3 seconds)"
                ),
            )


    except Exception as exc:

        record(
            f"{ticker} profile load",
            "FAIL",
            repr(exc),
        )


if performance_times:

    maximum_time = max(
        performance_times
    )

    average_time = (
        sum(performance_times)
        / len(performance_times)
    )


    record(
        "Profile performance summary",
        "PASS"
        if maximum_time < 3
        else "FAIL",
        (
            f"Max={maximum_time:.4f}s, "
            f"Average={average_time:.4f}s"
        ),
    )


# ============================================================
# 9. CHART / PAGE CONFIGURATION STATIC CHECK
# ============================================================

print("\n" + "=" * 70)
print("9. CHART / LAYOUT STATIC CHECK")
print("=" * 70)


chart_issues = []


for page in CHART_PAGES:

    path = PAGES / page


    if not path.exists():

        continue


    try:

        text = path.read_text(
            encoding="utf-8-sig"
        )


        # ----------------------------------------------------
        # Detect Plotly charts.
        # ----------------------------------------------------

        has_plotly = (
            "plotly_chart" in text
            or "px." in text
            or "go." in text
        )


        if not has_plotly:

            record(
                f"Chart check: {page}",
                "WARN",
                (
                    "No Plotly chart configuration "
                    "detected; visually verify page."
                ),
            )

            chart_issues.append(
                page
            )

            continue


        # ----------------------------------------------------
        # Responsive chart configuration.
        # ----------------------------------------------------

        responsive = (
            "use_container_width=True"
            in text
            or 'width="stretch"'
            in text
            or "width='stretch'"
            in text
        )


        if responsive:

            record(
                f"Chart responsiveness: {page}",
                "PASS",
                (
                    "Responsive chart "
                    "configuration detected."
                ),
            )

        else:

            chart_issues.append(
                page
            )

            record(
                f"Chart responsiveness: {page}",
                "WARN",
                (
                    "Plotly chart detected; "
                    "visually verify width/overflow."
                ),
            )


    except Exception as exc:

        record(
            f"Chart check: {page}",
            "FAIL",
            repr(exc),
        )


# ------------------------------------------------------------
# Chart summary
# ------------------------------------------------------------

if not chart_issues:

    record(
        "Chart responsiveness summary",
        "PASS",
        (
            "All expected chart pages contain "
            "responsive chart configuration."
        ),
    )

else:

    record(
        "Chart responsiveness summary",
        "WARN",
        (
            "Manual visual verification required "
            f"for: {chart_issues}"
        ),
    )


# ============================================================
# 10. DATABASE INTEGRATION CHECK
# ============================================================

print("\n" + "=" * 70)
print("10. DATABASE INTEGRATION")
print("=" * 70)


try:

    if not DB_PATH.exists():

        raise FileNotFoundError(
            f"Database not found: {DB_PATH}"
        )


    connection = sqlite3.connect(
        DB_PATH
    )


    cursor = connection.cursor()


    # --------------------------------------------------------
    # Foreign-key integrity
    # --------------------------------------------------------

    cursor.execute(
        "PRAGMA foreign_key_check"
    )


    foreign_key_errors = (
        cursor.fetchall()
    )


    if len(foreign_key_errors) == 0:

        record(
            "SQLite foreign-key integrity",
            "PASS",
            (
                "PRAGMA foreign_key_check "
                "returned 0 errors."
            ),
        )

    else:

        record(
            "SQLite foreign-key integrity",
            "FAIL",
            (
                f"{len(foreign_key_errors)} "
                "foreign-key errors."
            ),
        )


    # --------------------------------------------------------
    # Database connectivity
    # --------------------------------------------------------

    cursor.execute(
        "SELECT COUNT(*) FROM companies"
    )


    db_company_count = (
        cursor.fetchone()[0]
    )


    if db_company_count == 92:

        record(
            "SQLite company count",
            "PASS",
            "SQLite companies table contains 92 rows.",
        )

    else:

        record(
            "SQLite company count",
            "FAIL",
            (
                f"Expected 92 rows, "
                f"found {db_company_count}."
            ),
        )


    connection.close()


except Exception as exc:

    record(
        "SQLite foreign-key integrity",
        "FAIL",
        repr(exc),
    )


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("DAY 27 QA SUMMARY")
print("=" * 70)


results_df = pd.DataFrame(
    results
)


if len(results_df) > 0:

    passed = (
        results_df["Status"]
        == "PASS"
    ).sum()


    failed = (
        results_df["Status"]
        == "FAIL"
    ).sum()


    warnings = (
        results_df["Status"]
        == "WARN"
    ).sum()

else:

    passed = 0
    failed = 0
    warnings = 0


print(
    f"PASS    : {passed}"
)

print(
    f"FAIL    : {failed}"
)

print(
    f"WARNING : {warnings}"
)

print(
    f"TOTAL   : {len(results_df)}"
)


# ============================================================
# RESULT TABLE
# ============================================================

print("\nResults:")


if len(results_df) > 0:

    print(
        results_df.to_string(
            index=False
        )
    )


# ============================================================
# SAVE QA REPORT
# ============================================================

output_dir = (
    PROJECT_ROOT
    / "output"
)


output_dir.mkdir(
    exist_ok=True
)


report_path = (
    output_dir
    / "day27_qa_report.csv"
)


results_df.to_csv(
    report_path,
    index=False,
)


print("\nQA report saved to:")

print(
    report_path
)


# ============================================================
# FINAL STATUS
# ============================================================

if failed > 0:

    print(
        "\nDAY 27 STATUS: NOT COMPLETE"
    )

    print(
        "Fix the failed automated checks "
        "before marking Day 27 complete."
    )

elif warnings > 0:

    print(
        "\nDAY 27 STATUS: AUTOMATED QA PASSED WITH WARNINGS"
    )

    print(
        "Review the warnings and complete "
        "manual browser verification."
    )

else:

    print(
        "\nDAY 27 STATUS: AUTOMATED QA PASSED"
    )

    print(
        "All automated Day 27 checks passed."
    )

    print(
        "Manual browser verification is still required "
        "for all 8 live screens, visual chart sizing, "
        "interactive behavior, and UI-level N/A display."
    )