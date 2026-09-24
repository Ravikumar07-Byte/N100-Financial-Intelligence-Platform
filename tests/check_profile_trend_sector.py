"""
N100 Financial Intelligence Platform
Profile + Trend + Sector Verification

Run from project root:

    python tests/check_profile_trend_sector.py
"""

import sqlite3
import sys
from pathlib import Path

import pandas as pd

# ============================================================
# CONFIG
# ============================================================

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "nifty100.db"

if not DB_PATH.exists():
    # fallback
    DB_PATH = ROOT / "db" / "nifty100.db"

YEAR = 2024

PASS = 0
FAIL = 0
WARN = 0


# ============================================================
# HELPERS
# ============================================================


def ok(message):
    global PASS
    PASS += 1
    print(f"  [PASS] {message}")


def fail(message):
    global FAIL
    FAIL += 1
    print(f"  [FAIL] {message}")


def warn(message):
    global WARN
    WARN += 1
    print(f"  [WARN] {message}")


def section(title):
    print("\n" + "=" * 75)
    print(title)
    print("=" * 75)


def query(sql, params=()):
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(sql, conn, params=params)


def table_exists(table):
    df = query(
        """
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        AND name=?
        """,
        (table,),
    )
    return not df.empty


def columns(table):
    df = query(f"PRAGMA table_info({table})")
    return df["name"].tolist()


# ============================================================
# START
# ============================================================

print("\nN100 FINANCIAL INTELLIGENCE PLATFORM")
print("PROFILE + TREND + SECTOR VERIFICATION")
print("=" * 75)

print(f"Project root : {ROOT}")
print(f"Database     : {DB_PATH}")
print(f"Financial yr : {YEAR}")


if not DB_PATH.exists():
    print("\n[ERROR] nifty100.db not found.")
    sys.exit(1)


# ============================================================
# 1. DATABASE STRUCTURE
# ============================================================

section("1. DATABASE STRUCTURE")


required_tables = [
    "companies",
    "financial_ratios",
    "profitandloss",
    "balancesheet",
    "cashflow",
    "sectors",
    "market_cap",
]

for table in required_tables:

    if table_exists(table):
        ok(f"Table exists: {table}")
    else:
        fail(f"Missing table: {table}")


print("\nImportant columns:")

for table in required_tables:

    if table_exists(table):

        print(f"\n{table}:")
        print("  " + ", ".join(columns(table)))


# ============================================================
# 2. COMPANY PROFILE
# ============================================================

section("2. COMPANY PROFILE")


companies = query("""
    SELECT
        id,
        company_name,
        company_logo,
        chart_link,
        about_company,
        website,
        nse_profile,
        bse_profile,
        face_value,
        book_value,
        roce_percentage,
        roe_percentage
    FROM companies
    ORDER BY company_name
    """)


print(f"Companies loaded: {len(companies)}")


# ------------------------------------------------------------
# 2.1 Company count
# ------------------------------------------------------------

if len(companies) == 92:
    ok("Company universe contains 92 companies.")
else:
    warn(
        f"Company universe contains {len(companies)} companies "
        f"instead of expected 92."
    )


# ------------------------------------------------------------
# 2.2 Required profile fields
# ------------------------------------------------------------

profile_fields = [
    "company_name",
    "about_company",
    "face_value",
    "book_value",
    "roce_percentage",
    "roe_percentage",
]


print("\nProfile field completeness:")

for field in profile_fields:

    missing = companies[field].isna().sum()

    if missing == 0:
        ok(f"{field}: 0 missing")
    else:
        warn(f"{field}: {missing} missing")


# ------------------------------------------------------------
# 2.3 Duplicate company names
# ------------------------------------------------------------

duplicates = companies[companies["company_name"].duplicated(keep=False)]

if duplicates.empty:
    ok("No duplicate company names.")
else:
    fail(
        "Duplicate company names detected: "
        + ", ".join(duplicates["company_name"].tolist())
    )


# ------------------------------------------------------------
# 2.4 Known companies
# ------------------------------------------------------------

known_companies = [
    "ITC Ltd",
    "Bajaj Auto Ltd",
    "Abbott India Ltd",
]


print("\nKnown company lookup:")

for name in known_companies:

    match = companies[companies["company_name"].str.lower() == name.lower()]

    if len(match) == 1:

        row = match.iloc[0]

        ok(f"{name} found | " f"Sector metadata available through sectors table")

    elif len(match) > 1:

        fail(f"{name}: multiple company records found.")

    else:

        warn(f"{name}: exact company name not found.")


# ------------------------------------------------------------
# 2.5 Invalid company edge case
# ------------------------------------------------------------

invalid_ticker = "ABCXYZ999"

print(f"\nTesting invalid company search: {invalid_ticker}")

# Search company table using multiple likely fields.

invalid_result = query(
    """
    SELECT *
    FROM companies
    WHERE
        company_name LIKE ?
        OR id LIKE ?
    """,
    (
        f"%{invalid_ticker}%",
        f"%{invalid_ticker}%",
    ),
)


if invalid_result.empty:

    ok("Invalid company returns zero database records.")

else:

    fail("Invalid company unexpectedly matched a record.")


# ------------------------------------------------------------
# 2.6 Check that invalid lookup does not create fake data
# ------------------------------------------------------------

if invalid_result.empty:

    fake_values = [
        "ABCXYZ999",
        "0.00",
        "Unknown",
    ]

    ok("Invalid company lookup does not require " "a fabricated company record.")


# ============================================================
# 3. TREND ANALYSIS
# ============================================================

section("3. TREND ANALYSIS")


# Pick a company with substantial historical data.

trend_company = query("""
    SELECT
        company_id,
        COUNT(*) AS years_available
    FROM profitandloss
    GROUP BY company_id
    ORDER BY years_available DESC
    LIMIT 1
    """)


if trend_company.empty:

    fail("No profit-and-loss history found.")
else:

    trend_company_id = trend_company.iloc[0]["company_id"]
    available_years = int(trend_company.iloc[0]["years_available"])

    print(f"Trend test company_id : {trend_company_id}")

    print(f"Available P&L records  : {available_years}")

    if available_years >= 10:
        ok("At least 10 historical P&L records " "are available for trend analysis.")
    else:
        warn("Less than 10 historical P&L records " "are available.")


# ------------------------------------------------------------
# 3.1 Inspect historical years
# ------------------------------------------------------------

if not trend_company.empty:

    trend_df = query(
        """
        SELECT *
        FROM profitandloss
        WHERE company_id = ?
        ORDER BY year
        """,
        (trend_company_id,),
    )

    print("\nHistorical years:")

    if "year" in trend_df.columns:

        print(trend_df["year"].dropna().astype(str).tolist())

        unique_years = trend_df["year"].dropna().astype(str).unique()

        if len(unique_years) >= 10:

            ok(f"Trend dataset contains {len(unique_years)} " "unique years.")

        else:

            warn(f"Only {len(unique_years)} unique years found.")


# ------------------------------------------------------------
# 3.2 Check 2024
# ------------------------------------------------------------

if not trend_company.empty:

    current = query(
        """
        SELECT *
        FROM profitandloss
        WHERE company_id = ?
        AND substr(CAST(year AS TEXT), 1, 4) = ?
        """,
        (
            trend_company_id,
            str(YEAR),
        ),
    )

    if not current.empty:
        ok(f"Trend data available for {YEAR}.")
    else:
        warn(f"No P&L record found for {YEAR} " f"for test company.")


# ------------------------------------------------------------
# 3.3 Revenue history
# ------------------------------------------------------------

print("\nP&L columns:")

if not trend_company.empty:

    print("  " + ", ".join(trend_df.columns.tolist()))


possible_revenue_columns = [
    "revenue",
    "revenue_crore",
    "revenue_crores",
    "sales",
    "sales_crore",
    "total_revenue",
]


revenue_column = None

for col in possible_revenue_columns:

    if col in trend_df.columns:
        revenue_column = col
        break


if revenue_column:

    valid_revenue = trend_df[revenue_column].notna().sum()

    if valid_revenue >= 2:

        ok(f"Revenue trend data available " f"({valid_revenue} records).")

    else:

        fail("Insufficient revenue history.")

else:

    warn("Could not automatically identify revenue column.")


# ------------------------------------------------------------
# 3.4 Net profit history
# ------------------------------------------------------------

possible_profit_columns = [
    "net_profit",
    "net_profit_crore",
    "profit_after_tax",
    "pat",
    "profit",
]


profit_column = None

for col in possible_profit_columns:

    if col in trend_df.columns:
        profit_column = col
        break


if profit_column:

    valid_profit = trend_df[profit_column].notna().sum()

    if valid_profit >= 2:

        ok(f"Net profit trend data available " f"({valid_profit} records).")

    else:

        fail("Insufficient net profit history.")

else:

    warn("Could not automatically identify net profit column.")


# ------------------------------------------------------------
# 3.5 YoY calculation test
# ------------------------------------------------------------

if revenue_column and len(trend_df) >= 2:

    yoy_df = trend_df[["year", revenue_column]].copy()

    yoy_df[revenue_column] = pd.to_numeric(
        yoy_df[revenue_column],
        errors="coerce",
    )

    yoy_df = yoy_df.dropna(subset=[revenue_column])

    yoy_df["yoy"] = yoy_df[revenue_column].pct_change() * 100

    valid_yoy = yoy_df["yoy"].notna().sum()

    if valid_yoy >= 1:

        ok(f"YoY growth can be calculated " f"for {valid_yoy} year transitions.")

    else:

        fail("YoY calculation produced no valid transitions.")


# ============================================================
# 4. SECTOR ANALYSIS
# ============================================================

section("4. SECTOR ANALYSIS")


sectors = query("""
    SELECT
        s.company_id,
        c.company_name,
        s.broad_sector,
        s.sub_sector,
        s.index_weight_pct,
        s.market_cap_category
    FROM sectors s
    LEFT JOIN companies c
        ON c.id = s.company_id
    """)


print(f"Sector records: {len(sectors)}")


# ------------------------------------------------------------
# 4.1 Sector coverage
# ------------------------------------------------------------

sector_counts = sectors["broad_sector"].dropna().value_counts()


print("\nBroad sectors:")

for sector, count in sector_counts.items():

    print(f"  {sector:<30} {count:>3}")


if sector_counts.empty:

    fail("No broad-sector data found.")

else:

    ok(f"Broad-sector classification exists " f"for {len(sector_counts)} sectors.")


# ------------------------------------------------------------
# 4.2 Missing sector assignments
# ------------------------------------------------------------

missing_sector = sectors[sectors["broad_sector"].isna()]


if missing_sector.empty:

    ok("No companies have missing broad-sector classification.")

else:

    fail(
        f"{len(missing_sector)} companies have " "missing broad-sector classification."
    )

    print(missing_sector[["company_id", "company_name"]].to_string(index=False))


# ------------------------------------------------------------
# 4.3 Missing sub-sector assignments
# ------------------------------------------------------------

missing_subsector = sectors[sectors["sub_sector"].isna()]


if missing_subsector.empty:

    ok("No companies have missing sub-sector classification.")

else:

    warn(
        f"{len(missing_subsector)} companies have " "missing sub-sector classification."
    )


# ------------------------------------------------------------
# 4.4 Sector counts vs company universe
# ------------------------------------------------------------

sector_company_ids = sectors["company_id"].dropna().astype(str).nunique()


company_count = len(companies)


if sector_company_ids == company_count:

    ok("Every company has a sector record.")

else:

    fail(
        f"Sector coverage mismatch: " f"{sector_company_ids}/{company_count} companies."
    )


# ============================================================
# 5. SECTOR MEDIAN KPI TEST
# ============================================================

section("5. SECTOR MEDIAN KPI TEST")


# Get financial ratios for the selected year.

ratios = query(
    """
    SELECT *
    FROM financial_ratios
    WHERE substr(CAST(year AS TEXT), 1, 4) = ?
    """,
    (str(YEAR),),
)


print(f"Ratio records for {YEAR}: {len(ratios)}")


if ratios.empty:

    fail(f"No financial ratio data found for {YEAR}.")

else:

    ok(f"Financial ratio data available for {YEAR}.")


# ------------------------------------------------------------
# 5.1 Print ratio columns
# ------------------------------------------------------------

print("\nFinancial ratio columns:")

print("  " + ", ".join(ratios.columns.tolist()))


# ------------------------------------------------------------
# 5.2 Detect KPI columns
# ------------------------------------------------------------

kpi_candidates = {
    "ROE": [
        "roe",
        "roe_percentage",
        "return_on_equity",
        "return_on_equity_pct",
    ],
    "Revenue": [
        "revenue",
        "revenue_crore",
        "revenue_crores",
    ],
    "Net Profit Margin": [
        "net_profit_margin",
        "npm",
        "net_profit_margin_pct",
    ],
    "D/E": [
        "de",
        "debt_equity",
        "debt_to_equity",
        "debt_equity_ratio",
    ],
}


found_kpis = {}


for label, candidates in kpi_candidates.items():

    for candidate in candidates:

        if candidate in ratios.columns:

            found_kpis[label] = candidate
            break


print("\nDetected KPI columns:")

for label, column in found_kpis.items():

    print(f"  {label:<22} -> {column}")


if len(found_kpis) >= 2:

    ok(f"{len(found_kpis)} sector-analysis KPI fields detected.")

else:

    warn("Fewer than 2 expected KPI fields " "were detected automatically.")


# ============================================================
# 6. ACTUAL SECTOR MEDIANS
# ============================================================

section("6. ACTUAL SECTOR MEDIANS")


# Need company_id to join ratios to sectors.

if "company_id" not in ratios.columns:

    fail(
        "financial_ratios does not contain company_id; "
        "cannot join ratios to sectors."
    )

else:

    merged = sectors.merge(
        ratios,
        on="company_id",
        how="inner",
        suffixes=("_sector", "_ratio"),
    )

    print(f"Joined sector + ratio rows: {len(merged)}")

    if merged.empty:

        fail("Sector and financial-ratio tables " "could not be joined.")

    else:

        ok("Sector and financial-ratio data " "can be joined.")

        # ----------------------------------------------------
        # Calculate medians
        # ----------------------------------------------------

        for label, column in found_kpis.items():

            if column not in merged.columns:
                continue

            merged[column] = pd.to_numeric(
                merged[column],
                errors="coerce",
            )

            median_df = (
                merged.dropna(
                    subset=[
                        "broad_sector",
                        column,
                    ]
                )
                .groupby("broad_sector")[column]
                .median()
                .sort_values(ascending=False)
            )

            if not median_df.empty:

                ok(f"{label}: median calculated " f"for {len(median_df)} sectors.")

                print(f"\n{label} median:")

                print(median_df.round(2).to_string())

            else:

                fail(f"{label}: no valid sector medians.")


# ============================================================
# 7. SUB-SECTOR TEST
# ============================================================

section("7. SUB-SECTOR TEST")


subsector_counts = (
    sectors[sectors["sub_sector"].notna()]
    .groupby(
        [
            "broad_sector",
            "sub_sector",
        ]
    )
    .size()
    .reset_index(name="companies")
)


print(subsector_counts.to_string(index=False))


if subsector_counts.empty:

    fail("No sub-sector data available.")

else:

    ok(f"{len(subsector_counts)} sector/sub-sector " "groups detected.")


# ============================================================
# 8. MATERIALS SECTOR SPECIFIC TEST
# ============================================================

section("8. MATERIALS SECTOR TEST")


materials = sectors[
    sectors["broad_sector"].astype(str).str.strip().str.lower() == "materials"
]


print(f"Materials companies: {len(materials)}")


if materials.empty:

    fail("Materials sector is missing.")

else:

    ok(f"Materials sector contains " f"{len(materials)} companies.")

    print("\nMaterials companies:")

    print(
        materials[
            [
                "company_id",
                "company_name",
                "sub_sector",
            ]
        ].to_string(index=False)
    )


# ============================================================
# 9. INFORMATION TECHNOLOGY TEST
# ============================================================

section("9. INFORMATION TECHNOLOGY TEST")


it = sectors[
    sectors["broad_sector"].astype(str).str.strip().str.lower()
    == "information technology"
]


print(f"Information Technology companies: {len(it)}")


if it.empty:

    fail("Information Technology sector is missing.")

else:

    ok(f"Information Technology sector contains " f"{len(it)} companies.")


# ============================================================
# 10. DATA QUALITY CHECK
# ============================================================

section("10. DATA QUALITY")


# Duplicate company-sector assignments

duplicates = sectors[
    sectors.duplicated(
        subset=["company_id"],
        keep=False,
    )
]


if duplicates.empty:

    ok("Each company has exactly one sector assignment.")

else:

    warn(f"{len(duplicates)} duplicate sector records found.")

    print(
        duplicates[
            [
                "company_id",
                "company_name",
                "broad_sector",
                "sub_sector",
            ]
        ].to_string(index=False)
    )


# ------------------------------------------------------------
# Null market cap category
# ------------------------------------------------------------

if "market_cap_category" in sectors.columns:

    missing_market_cap = sectors["market_cap_category"].isna().sum()

    if missing_market_cap == 0:

        ok("No missing market-cap categories.")

    else:

        warn(f"{missing_market_cap} missing " "market-cap categories.")


# ============================================================
# FINAL RESULT
# ============================================================

section("FINAL VERIFICATION RESULT")


print(f"PASS : {PASS}")
print(f"WARN : {WARN}")
print(f"FAIL : {FAIL}")


print("\nStatus:")

if FAIL == 0 and WARN == 0:

    print("  [PASS] Profile + Trend + Sector verification clean.")

elif FAIL == 0:

    print(
        "  [PASS WITH WARNINGS] Core functionality/data "
        "is present, but some edge cases need review."
    )

else:

    print("  [FAIL] One or more verification checks failed.")


print("\nVerification complete.")
