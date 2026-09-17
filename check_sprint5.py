from pathlib import Path
import sqlite3
import csv
import re
import sys

ROOT = Path.cwd()
DB = ROOT / "nifty100.db"

print("=" * 90)
print("N100 FINANCIAL INTELLIGENCE PLATFORM")
print("SPRINT 5 — COMPLETE DAY-BY-DAY AUDIT")
print("=" * 90)
print(f"Project root : {ROOT}")
print(f"Database     : {DB}")
print()

PASS = "PASS"
WARN = "WARN"
FAIL = "FAIL"

results = []

def check(name, status, detail=""):
    results.append((name, status, detail))
    symbol = "✅" if status == PASS else ("⚠️" if status == WARN else "❌")
    print(f"{symbol} {name}")
    if detail:
        print(f"   {detail}")

def file_exists(rel):
    return (ROOT / rel).exists()

def csv_info(rel):
    path = ROOT / rel
    if not path.exists():
        return None, None, None
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            cols = reader.fieldnames or []
        return len(rows), cols, path.stat().st_size
    except Exception as e:
        return None, None, None

def pdf_page_count(path):
    try:
        data = path.read_bytes()
        return len(re.findall(rb"/Type\s*/Page\b", data))
    except Exception:
        return None

# ============================================================
# DATABASE
# ============================================================

print("=" * 90)
print("DATABASE CHECK")
print("=" * 90)

if not DB.exists():
    check("ROOT database", FAIL, "nifty100.db not found")
    sys.exit(1)

conn = sqlite3.connect(DB)

tables = [
    "companies",
    "analysis",
    "financial_ratios",
    "profitandloss",
    "balancesheet",
    "cashflow",
    "sectors",
]

existing_tables = {
    row[0]
    for row in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
}

for table in tables:
    if table in existing_tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        check(f"Table: {table}", PASS, f"{count:,} rows")
    else:
        check(f"Table: {table}", FAIL, "table missing")

company_count = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
check(
    "Companies master count",
    PASS if company_count == 92 else WARN,
    f"{company_count} companies"
)

# ============================================================
# DAY 29
# ============================================================

print()
print("=" * 90)
print("DAY 29 — NLP ANALYSIS TEXT PARSER")
print("=" * 90)

parser_file = ROOT / "src" / "nlp" / "parser.py"
analysis_csv = ROOT / "output" / "analysis_parsed.csv"
failure_csv = ROOT / "output" / "parse_failures.csv"

check(
    "Day 29 parser.py",
    PASS if parser_file.exists() else FAIL,
    str(parser_file)
)

rows, cols, size = csv_info("output/analysis_parsed.csv")

required_analysis_cols = [
    "company_id",
    "metric_type",
    "period_years",
    "value_pct",
]

if rows is not None:
    missing = [c for c in required_analysis_cols if c not in cols]
    check(
        "analysis_parsed.csv",
        PASS if not missing else FAIL,
        f"{rows} rows; missing columns: {missing if missing else 'none'}"
    )
else:
    check("analysis_parsed.csv", FAIL, "file missing/unreadable")

rows, cols, size = csv_info("output/parse_failures.csv")
check(
    "parse_failures.csv",
    PASS if rows is not None else FAIL,
    f"{rows if rows is not None else 0} failure records"
)

# Search parser for required target fields / regex
if parser_file.exists():
    text = parser_file.read_text(encoding="utf-8", errors="ignore")

    targets = [
        "compounded_sales_growth",
        "compounded_profit_growth",
        "stock_price_cagr",
        "roe",
    ]

    target_missing = [x for x in targets if x not in text]

    regex_found = (
        "Years" in text
        and "%" in text
        and "period" in text.lower()
    )

    check(
        "Day 29 target metrics",
        PASS if not target_missing else WARN,
        f"missing from source: {target_missing if target_missing else 'none'}"
    )

    check(
        "Day 29 regex parsing logic",
        PASS if regex_found else WARN,
        "parser contains year/percentage extraction logic"
        if regex_found else
        "regex could not be confirmed from source text"
    )

# ============================================================
# DAY 30
# ============================================================

print()
print("=" * 90)
print("DAY 30 — NLP AUTO PROS/CONS GENERATOR")
print("=" * 90)

pros_file = ROOT / "src" / "nlp" / "pros_cons_generator.py"

check(
    "Day 30 pros_cons_generator.py",
    PASS if pros_file.exists() else FAIL,
    str(pros_file)
)

rows, cols, size = csv_info("output/pros_cons_generated.csv")

required_pros_cols = [
    "company_id",
    "type",
    "rule_id",
    "text",
    "confidence_pct",
]

if rows is not None:
    missing = [c for c in required_pros_cols if c not in cols]
    check(
        "pros_cons_generated.csv columns",
        PASS if not missing else FAIL,
        f"{rows} records; missing: {missing if missing else 'none'}"
    )

    try:
        with (ROOT / "output" / "pros_cons_generated.csv").open(
            "r", encoding="utf-8-sig", newline=""
        ) as f:
            data = list(csv.DictReader(f))

        company_ids = {r["company_id"] for r in data}
        pros = {
            r["company_id"]
            for r in data
            if r.get("type", "").lower() == "pro"
        }
        cons = {
            r["company_id"]
            for r in data
            if r.get("type", "").lower() == "con"
        }

        confidence_values = []
        for r in data:
            try:
                confidence_values.append(float(r["confidence_pct"]))
            except:
                pass

        check(
            "Every company has a Pro",
            PASS if len(pros) == company_count else FAIL,
            f"{len(pros)}/{company_count}"
        )

        check(
            "Every company has a Con",
            PASS if len(cons) == company_count else FAIL,
            f"{len(cons)}/{company_count}"
        )

        if confidence_values:
            min_conf = min(confidence_values)
            max_conf = max(confidence_values)
            check(
                "Confidence filtering",
                PASS if min_conf > 60 else WARN,
                f"min={min_conf:.2f}, max={max_conf:.2f}"
            )

    except Exception as e:
        check("Pros/Cons content validation", FAIL, str(e))

# Count rule IDs in source
if pros_file.exists():
    text = pros_file.read_text(encoding="utf-8", errors="ignore")

    pro_rules = len(re.findall(r"PRO[_ ]?0?[1-9]|PRO[_ ]?1[0-2]", text))
    con_rules = len(re.findall(r"CON[_ ]?0?[1-9]|CON[_ ]?1[0-2]", text))

    # More reliable: check explicit rule identifiers
    explicit_pro = len(set(re.findall(r"PRO[_-]?(?:0?[1-9]|1[0-2])", text.upper())))
    explicit_con = len(set(re.findall(r"CON[_-]?(?:0?[1-9]|1[0-2])", text.upper())))

    check(
        "12 Pro rules implemented",
        PASS if explicit_pro >= 12 else WARN,
        f"detected {explicit_pro} explicit Pro rule IDs"
    )

    check(
        "12 Con rules implemented",
        PASS if explicit_con >= 12 else WARN,
        f"detected {explicit_con} explicit Con rule IDs"
    )

# ============================================================
# DAY 31
# ============================================================

print()
print("=" * 90)
print("DAY 31 — CASH FLOW INTELLIGENCE")
print("=" * 90)

cashflow_intelligence_files = [
    ROOT / "src" / "analytics" / "cashflow_intelligence.py",
    ROOT / "src" / "analytics" / "cashflow_kpis.py",
]

found_cashflow_source = None
for f in cashflow_intelligence_files:
    if f.exists():
        found_cashflow_source = f
        break

check(
    "Day 31 cash flow source",
    PASS if found_cashflow_source else FAIL,
    str(found_cashflow_source.relative_to(ROOT))
    if found_cashflow_source else "not found"
)

xlsx_path = ROOT / "output" / "cashflow_intelligence.xlsx"

if xlsx_path.exists():
    try:
        import pandas as pd

        df_cf = pd.read_excel(xlsx_path)

        required_cf_cols = [
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
            "capital_allocation_label",
        ]

        missing = [c for c in required_cf_cols if c not in df_cf.columns]

        check(
            "cashflow_intelligence.xlsx exists",
            PASS,
            f"{len(df_cf)} rows"
        )

        check(
            "Cash Flow required columns",
            PASS if not missing else FAIL,
            f"missing: {missing if missing else 'none'}"
        )

        check(
            "Cash Flow company coverage",
            PASS if len(df_cf) == company_count else FAIL,
            f"{len(df_cf)}/{company_count} companies"
        )

        if "distress_flag" in df_cf.columns:
            distress = int(df_cf["distress_flag"].fillna(False).astype(bool).sum())
            print(f"   Distress flagged : {distress}")

        if "deleveraging_flag" in df_cf.columns:
            deleveraging = int(
                df_cf["deleveraging_flag"].fillna(False).astype(bool).sum()
            )
            print(f"   Deleveraging     : {deleveraging}")

    except Exception as e:
        check("cashflow_intelligence.xlsx", FAIL, str(e))
else:
    check("cashflow_intelligence.xlsx", FAIL, "file missing")

distress_rows, distress_cols, distress_size = csv_info(
    "output/distress_alerts.csv"
)

check(
    "distress_alerts.csv",
    PASS if distress_rows is not None else FAIL,
    f"{distress_rows if distress_rows is not None else 0} alert records"
)

# ============================================================
# DAY 32
# ============================================================

print()
print("=" * 90)
print("DAY 32 — CAPITAL ALLOCATION REPORT")
print("=" * 90)

capital_report = ROOT / "src" / "analytics" / "capital_allocation_report.py"

check(
    "capital_allocation_report.py",
    PASS if capital_report.exists() else FAIL,
    str(capital_report)
)

pattern_csv = ROOT / "output" / "pattern_changes.csv"
distribution_csv = ROOT / "output" / "capital_allocation_distribution.csv"

rows, cols, size = csv_info("output/pattern_changes.csv")
check(
    "pattern_changes.csv",
    PASS if rows is not None else FAIL,
    f"{rows if rows is not None else 0} pattern-change records"
)

rows, cols, size = csv_info("output/capital_allocation_distribution.csv")
check(
    "capital_allocation_distribution.csv",
    PASS if rows is not None else FAIL,
    f"{rows if rows is not None else 0} distribution records"
)

# Check latest capital allocation distribution
if "capital_allocation" in existing_tables:
    pass

# ============================================================
# DAY 33
# ============================================================

print()
print("=" * 90)
print("DAY 33 — PDF TEARSHEET TEMPLATE")
print("=" * 90)

tearsheet_file = ROOT / "src" / "reports" / "tearsheet.py"

check(
    "tearsheet.py",
    PASS if tearsheet_file.exists() else FAIL,
    str(tearsheet_file)
)

if tearsheet_file.exists():
    text = tearsheet_file.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    required_terms = [
        "ReportLab",
        "build_tearsheet",
        "create_header",
        "create_kpi_tiles",
        "save_revenue_profit_chart",
        "save_roe_roce_chart",
        "save_balance_sheet_chart",
        "save_cashflow_chart",
        "create_bullet_list",
        "create_capital_badge",
    ]

    missing = [x for x in required_terms if x.lower() not in text.lower()]

    check(
        "Tearsheet required components",
        PASS if not missing else WARN,
        f"missing source markers: {missing if missing else 'none'}"
    )

# Five official spot-checks
spot_tickers = [
    "TCS",
    "HDFCBANK",
    "RELIANCE",
    "SUNPHARMA",
    "TATASTEEL",
]

spot_ok = 0

for ticker in spot_tickers:
    p = ROOT / "reports" / "tearsheets" / f"{ticker}_tearsheet.pdf"

    if p.exists():
        pages = pdf_page_count(p)
        size_kb = p.stat().st_size / 1024

        good = pages == 2 and size_kb >= 30

        if good:
            spot_ok += 1

        print(
            f"   {ticker:<12} "
            f"{'PASS' if good else 'WARN':<5} "
            f"pages={pages}, size={size_kb:.1f} KB"
        )
    else:
        print(f"   {ticker:<12} FAIL  file missing")

check(
    "Day 33 five-company PDF validation",
    PASS if spot_ok == 5 else FAIL,
    f"{spot_ok}/5 passed 2-page + 30KB structural check"
)

# ============================================================
# DAY 34
# ============================================================

print()
print("=" * 90)
print("DAY 34 — BATCH REPORT GENERATION")
print("=" * 90)

tearsheet_dir = ROOT / "reports" / "tearsheets"
sector_dir = ROOT / "reports" / "sector"

tearsheets = sorted(tearsheet_dir.glob("*_tearsheet.pdf")) if tearsheet_dir.exists() else []

check(
    "Company tearsheet directory",
    PASS if tearsheet_dir.exists() else FAIL,
    f"{len(tearsheets)} PDFs found"
)

# Skipped log
skipped_rows, skipped_cols, skipped_size = csv_info(
    "output/skipped_tearsheets.csv"
)

skipped_count = skipped_rows if skipped_rows is not None else 0

check(
    "Skipped tearsheet log",
    PASS if skipped_rows is not None else FAIL,
    f"{skipped_count} skipped company record(s)"
)

expected_eligible = company_count - skipped_count

check(
    "Tearsheet count",
    PASS if len(tearsheets) == expected_eligible else FAIL,
    f"{len(tearsheets)} generated / {expected_eligible} expected"
)

# Validate every tearsheet
bad_size = []
bad_pages = []

for p in tearsheets:
    size_kb = p.stat().st_size / 1024
    pages = pdf_page_count(p)

    if size_kb < 30:
        bad_size.append((p.name, size_kb))

    if pages != 2:
        bad_pages.append((p.name, pages))

check(
    "All tearsheets >= 30 KB",
    PASS if not bad_size else WARN,
    f"{len(bad_size)} below 30 KB"
)

check(
    "All tearsheets are 2 pages",
    PASS if not bad_pages else FAIL,
    f"{len(bad_pages)} incorrect page-count PDFs"
)

# Sector reports
sector_reports = sorted(sector_dir.glob("*_report.pdf")) if sector_dir.exists() else []

check(
    "Sector report directory",
    PASS if sector_dir.exists() else FAIL,
    f"{len(sector_reports)} sector PDFs found"
)

# Actual sectors from DB
if "sectors" in existing_tables:
    sector_rows = conn.execute(
        "SELECT DISTINCT broad_sector FROM sectors "
        "WHERE broad_sector IS NOT NULL "
        "ORDER BY broad_sector"
    ).fetchall()

    actual_sectors = [r[0] for r in sector_rows]

    print()
    print("Actual sectors in database:")
    for s in actual_sectors:
        print(f"   - {s}")

    check(
        "Sector report coverage",
        PASS if len(sector_reports) == len(actual_sectors) else WARN,
        f"{len(sector_reports)} reports for {len(actual_sectors)} actual database sectors"
    )

    if len(actual_sectors) != 11:
        print(
            "   NOTE: Official specification says 11 sectors, "
            f"but database contains {len(actual_sectors)} distinct broad sectors."
        )

# ============================================================
# DAY 35
# ============================================================

print()
print("=" * 90)
print("DAY 35 — PORTFOLIO SUMMARY PDF")
print("=" * 90)

portfolio_script = ROOT / "src" / "reports" / "portfolio_summary.py"
portfolio_pdf = ROOT / "reports" / "portfolio" / "portfolio_summary.pdf"

check(
    "portfolio_summary.py",
    PASS if portfolio_script.exists() else FAIL,
    str(portfolio_script)
)

if portfolio_pdf.exists():
    portfolio_size = portfolio_pdf.stat().st_size / 1024
    portfolio_pages = pdf_page_count(portfolio_pdf)

    check(
        "Portfolio PDF exists",
        PASS,
        f"{portfolio_size:.1f} KB"
    )

    check(
        "Portfolio PDF page count",
        PASS if portfolio_pages == company_count else FAIL,
        f"{portfolio_pages} pages / {company_count} expected"
    )

    if portfolio_script.exists():
        text = portfolio_script.read_text(
            encoding="utf-8",
            errors="ignore"
        )

        kpis = [
            "Revenue CAGR",
            "PAT CAGR",
            "ROE",
            "ROCE",
            "Debt / Equity",
            "Quality Score",
        ]

        missing_kpis = [
            k for k in kpis
            if k.lower() not in text.lower()
        ]

        arrow_terms = ["↑", "↓", "→", "improved", "declined", "flat"]

        arrow_found = any(x.lower() in text.lower() for x in arrow_terms)

        check(
            "Portfolio six KPI implementation",
            PASS if not missing_kpis else WARN,
            f"missing source labels: {missing_kpis if missing_kpis else 'none'}"
        )

        check(
            "Portfolio trend-arrow logic",
            PASS if arrow_found else WARN,
            "trend logic found" if arrow_found else "could not confirm"
        )

else:
    check(
        "Portfolio PDF exists",
        FAIL,
        "reports/portfolio/portfolio_summary.pdf missing"
    )

# ============================================================
# OFFICIAL DELIVERABLES
# ============================================================

print()
print("=" * 90)
print("OFFICIAL SPRINT 5 DELIVERABLES")
print("=" * 90)

deliverables = [
    "output/pros_cons_generated.csv",
    "output/analysis_parsed.csv",
    "output/cashflow_intelligence.xlsx",
    "output/distress_alerts.csv",
    "reports/tearsheets",
    "reports/sector",
    "reports/portfolio",
    "src/nlp/parser.py",
    "src/nlp/pros_cons_generator.py",
    "src/reports/tearsheet.py",
    "src/reports/sector_report.py",
]

for rel in deliverables:
    p = ROOT / rel
    check(
        rel,
        PASS if p.exists() else WARN,
        "exists" if p.exists() else "MISSING"
    )

# ============================================================
# FINAL SCORE
# ============================================================

print()
print("=" * 90)
print("FINAL SPRINT 5 AUDIT")
print("=" * 90)

pass_count = sum(1 for _, s, _ in results if s == PASS)
warn_count = sum(1 for _, s, _ in results if s == WARN)
fail_count = sum(1 for _, s, _ in results if s == FAIL)

total = len(results)

score = (pass_count / total * 100) if total else 0

print(f"Checks passed : {pass_count}")
print(f"Warnings      : {warn_count}")
print(f"Failures      : {fail_count}")
print(f"Audit score   : {score:.1f}%")
print()

if fail_count == 0 and warn_count == 0:
    print("🎉 SPRINT 5 AUDIT STATUS: FULLY VERIFIED")
elif fail_count == 0:
    print("🟡 SPRINT 5 AUDIT STATUS: FUNCTIONALLY COMPLETE")
    print("   Minor specification/documentation items remain.")
else:
    print("🔴 SPRINT 5 AUDIT STATUS: ACTION REQUIRED")

print()
print("IMPORTANT:")
print("- Do not create a fake 11th sector if the database has only 10.")
print("- One skipped tearsheet is valid when the company has <3 years of data.")
print("- Team-lead review/sign-off is an administrative completion item.")
print("=" * 90)

conn.close()
