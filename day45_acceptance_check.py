from pathlib import Path
import sqlite3
import csv
import json
import time
import subprocess
import sys
import re

ROOT = Path(".")
DB = ROOT / "nifty100.db"

results = {}
details = {}

def gate(num, status, detail=""):
    key = f"AC-{num:02d}"
    results[key] = status
    details[key] = detail
    print(f"{key}: {status}")
    if detail:
        print(f"      {detail}")

print("=" * 80)
print("DAY 45 — FINAL ACCEPTANCE GATES")
print("=" * 80)

# ------------------------------------------------------------------
# Database connection
# ------------------------------------------------------------------

if not DB.exists():
    print("ERROR: nifty100.db not found")
    sys.exit(1)

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

# ------------------------------------------------------------------
# AC-01
# ------------------------------------------------------------------

try:
    count = conn.execute(
        "SELECT COUNT(*) FROM companies"
    ).fetchone()[0]

    gate(
        1,
        "PASS" if count == 92 else "FAIL",
        f"companies count = {count}; expected 92"
    )
except Exception as e:
    gate(1, "FAIL", str(e))

# ------------------------------------------------------------------
# AC-02
# >= 90% companies have >= 10 years P&L, BS and CF
# ------------------------------------------------------------------

try:
    company_count = conn.execute(
        "SELECT COUNT(*) FROM companies"
    ).fetchone()[0]

    tables = set(
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table'"
        )
    )

    candidates = {
        "pnl": [
            "profit_loss",
            "pnl",
            "income_statement",
            "profit_and_loss",
        ],
        "bs": [
            "balance_sheet",
            "balance_sheets",
        ],
        "cf": [
            "cash_flow",
            "cash_flows",
            "cashflow",
        ],
    }

    selected = {}

    for group, names in candidates.items():
        for name in names:
            if name in tables:
                selected[group] = name
                break

    if len(selected) != 3:
        gate(
            2,
            "FAIL",
            f"Could not identify P&L/BS/CF tables. Found: {selected}"
        )
    else:
        qualifying = 0

        company_ids = [
            row[0]
            for row in conn.execute(
                "SELECT company_id FROM companies"
            )
        ]

        for cid in company_ids:
            ok = True

            for table in selected.values():
                columns = [
                    row[1]
                    for row in conn.execute(
                        f"PRAGMA table_info({table})"
                    )
                ]

                company_col = next(
                    (
                        c for c in columns
                        if c.lower() in {
                            "company_id",
                            "companyid",
                            "ticker",
                        }
                    ),
                    None,
                )

                year_col = next(
                    (
                        c for c in columns
                        if c.lower() in {
                            "year",
                            "fy",
                            "financial_year",
                            "fiscal_year",
                        }
                    ),
                    None,
                )

                if not company_col or not year_col:
                    ok = False
                    break

                count_years = conn.execute(
                    f"""
                    SELECT COUNT(DISTINCT "{year_col}")
                    FROM "{table}"
                    WHERE "{company_col}" = ?
                    """,
                    (cid,),
                ).fetchone()[0]

                if count_years < 10:
                    ok = False
                    break

            if ok:
                qualifying += 1

        percentage = (
            qualifying / company_count * 100
            if company_count else 0
        )

        gate(
            2,
            "PASS" if percentage >= 90 else "FAIL",
            f"{qualifying}/{company_count} companies = {percentage:.2f}%"
        )

except Exception as e:
    gate(2, "FAIL", str(e))

# ------------------------------------------------------------------
# AC-03
# ------------------------------------------------------------------

try:
    rows = conn.execute(
        "PRAGMA foreign_key_check"
    ).fetchall()

    gate(
        3,
        "PASS" if len(rows) == 0 else "FAIL",
        f"foreign_key_check returned {len(rows)} rows"
    )
except Exception as e:
    gate(3, "FAIL", str(e))

# ------------------------------------------------------------------
# AC-04
# ------------------------------------------------------------------

try:
    count = conn.execute(
        "SELECT COUNT(*) FROM financial_ratios"
    ).fetchone()[0]

    gate(
        4,
        "PASS" if count >= 1100 else "FAIL",
        f"financial_ratios count = {count}"
    )
except Exception as e:
    gate(4, "FAIL", str(e))

# ------------------------------------------------------------------
# AC-05
# Revenue CAGR spot check
# ------------------------------------------------------------------

try:
    cols = [
        row[1]
        for row in conn.execute(
            "PRAGMA table_info(financial_ratios)"
        )
    ]

    cagr_col = next(
        (
            c for c in cols
            if "revenue" in c.lower()
            and "cagr" in c.lower()
        ),
        None,
    )

    if cagr_col:
        row = conn.execute(
            f"""
            SELECT company_id, "{cagr_col}"
            FROM financial_ratios
            WHERE "{cagr_col}" IS NOT NULL
            LIMIT 1
            """
        ).fetchone()

        if row:
            gate(
                5,
                "PASS",
                f"Revenue CAGR spot-check available: "
                f"{row[0]} = {row[1]}"
            )
        else:
            gate(5, "FAIL", "No Revenue CAGR records found")
    else:
        gate(
            5,
            "FAIL",
            "Revenue CAGR column not found in financial_ratios"
        )

except Exception as e:
    gate(5, "FAIL", str(e))

# ------------------------------------------------------------------
# AC-06
# ROE matches companies.roe_percentage for 5 companies
# ------------------------------------------------------------------

try:
    ratio_cols = [
        row[1]
        for row in conn.execute(
            "PRAGMA table_info(financial_ratios)"
        )
    ]

    roe_col = next(
        (
            c for c in ratio_cols
            if "roe" in c.lower()
        ),
        None,
    )

    company_cols = [
        row[1]
        for row in conn.execute(
            "PRAGMA table_info(companies)"
        )
    ]

    company_roe = next(
        (
            c for c in company_cols
            if "roe" in c.lower()
        ),
        None,
    )

    if not roe_col or not company_roe:
        gate(
            6,
            "FAIL",
            f"ROE columns not found: ratio={roe_col}, "
            f"company={company_roe}"
        )
    else:
        rows = conn.execute(
            f"""
            SELECT r.company_id,
                   r."{roe_col}" AS ratio_roe,
                   c."{company_roe}" AS company_roe
            FROM financial_ratios r
            JOIN companies c
              ON c.company_id = r.company_id
            WHERE r."{roe_col}" IS NOT NULL
              AND c."{company_roe}" IS NOT NULL
            LIMIT 5
            """
        ).fetchall()

        passed = 0

        for row in rows:
            a = float(row["ratio_roe"])
            b = float(row["company_roe"])

            tolerance = max(abs(b) * 0.05, 0.000001)

            if abs(a - b) <= tolerance:
                passed += 1

        gate(
            6,
            "PASS" if len(rows) == 5 and passed == 5 else "FAIL",
            f"{passed}/{len(rows)} sampled companies within 5%"
        )

except Exception as e:
    gate(6, "FAIL", str(e))

# ------------------------------------------------------------------
# AC-07
# Quality screener preset
# ------------------------------------------------------------------

try:
    config = ROOT / "config" / "screener_config.yaml"

    if not config.exists():
        gate(7, "FAIL", "screener_config.yaml not found")
    else:
        text = config.read_text(
            encoding="utf-8"
        ).lower()

        # Verify configuration exists and contains quality-related
        # configuration rather than claiming a runtime result.
        quality = "quality" in text

        output = ROOT / "output" / "screener_output.xlsx"

        if output.exists():
            import pandas as pd

            df = pd.read_excel(output)

            n = len(df)

            gate(
                7,
                "PASS" if quality and 10 <= n <= 50 else "FAIL",
                f"Quality config present={quality}; "
                f"screener rows={n}"
            )
        else:
            gate(
                7,
                "FAIL",
                "screener_output.xlsx not found"
            )

except Exception as e:
    gate(7, "FAIL", str(e))

# ------------------------------------------------------------------
# AC-08
# Company Profile < 3 seconds
# ------------------------------------------------------------------

try:
    app = ROOT / "src" / "dashboard" / "app.py"

    if not app.exists():
        gate(8, "FAIL", "Streamlit app.py not found")
    else:
        gate(
            8,
            "REQUIRES_RUNTIME",
            "Company Profile timing must be measured through the running Streamlit app"
        )

except Exception as e:
    gate(8, "FAIL", str(e))

# ------------------------------------------------------------------
# AC-09
# CSV download valid and well-formed
# ------------------------------------------------------------------

try:
    candidates = [
        ROOT / "output" / "screener_output.csv",
        ROOT / "output" / "screener.csv",
    ]

    csv_file = next(
        (p for p in candidates if p.exists()),
        None,
    )

    if csv_file:
        with csv_file.open(
            newline="",
            encoding="utf-8-sig"
        ) as f:
            rows = list(csv.reader(f))

        valid = len(rows) >= 2 and len(rows[0]) > 0

        gate(
            9,
            "PASS" if valid else "FAIL",
            f"{csv_file} rows={len(rows)}"
        )
    else:
        gate(
            9,
            "REQUIRES_RUNTIME",
            "No saved screener CSV found; verify Streamlit CSV download directly"
        )

except Exception as e:
    gate(9, "FAIL", str(e))

# ------------------------------------------------------------------
# AC-10
# 5 sampled tearsheets
# ------------------------------------------------------------------

try:
    tearsheets = sorted(
        (ROOT / "reports" / "tearsheets").glob("*.pdf")
    )

    if len(tearsheets) < 5:
        gate(
            10,
            "FAIL",
            f"Only {len(tearsheets)} tearsheet PDFs found"
        )
    else:
        from pypdf import PdfReader

        sampled = tearsheets[:5]
        failed = []

        for pdf in sampled:
            reader = PdfReader(str(pdf))

            for page_number, page in enumerate(reader.pages, 1):
                text = page.extract_text() or ""

                if not text.strip():
                    failed.append(
                        f"{pdf.name}:page {page_number}: no text"
                    )

        gate(
            10,
            "PASS" if not failed else "FAIL",
            (
                f"Checked {len(sampled)} PDFs"
                if not failed
                else "; ".join(failed)
            )
        )

except Exception as e:
    gate(10, "FAIL", str(e))

# ------------------------------------------------------------------
# AC-11
# API health
# ------------------------------------------------------------------

try:
    import requests

    openapi = ROOT / "docs" / "openapi.json"

    if not openapi.exists():
        gate(11, "FAIL", "docs/openapi.json not found")
    else:
        spec = json.loads(
            openapi.read_text(encoding="utf-8")
        )

        paths = spec.get("paths", {})

        health_paths = [
            p for p in paths
            if "health" in p.lower()
        ]

        if health_paths:
            gate(
                11,
                "REQUIRES_RUNTIME",
                f"Health endpoint documented: {health_paths}"
            )
        else:
            gate(
                11,
                "FAIL",
                "No health endpoint found in OpenAPI"
            )

except Exception as e:
    gate(11, "FAIL", str(e))

# ------------------------------------------------------------------
# AC-12
# TCS ratios endpoint 10+ years
# ------------------------------------------------------------------

try:
    openapi = ROOT / "docs" / "openapi.json"

    if openapi.exists():
        spec = json.loads(
            openapi.read_text(encoding="utf-8")
        )

        ratio_paths = [
            p for p in spec.get("paths", {})
            if "ratio" in p.lower()
        ]

        gate(
            12,
            "REQUIRES_RUNTIME" if ratio_paths else "FAIL",
            f"Ratio endpoints documented: {ratio_paths}"
        )
    else:
        gate(12, "FAIL", "OpenAPI specification missing")

except Exception as e:
    gate(12, "FAIL", str(e))

# ------------------------------------------------------------------
# AC-13
# API screener vs Excel
# ------------------------------------------------------------------

try:
    openapi = ROOT / "docs" / "openapi.json"
    excel = ROOT / "output" / "screener_output.xlsx"

    if not openapi.exists() or not excel.exists():
        gate(
            13,
            "FAIL",
            "OpenAPI or screener_output.xlsx missing"
        )
    else:
        spec = json.loads(
            openapi.read_text(encoding="utf-8")
        )

        screener_paths = [
            p for p in spec.get("paths", {})
            if "screen" in p.lower()
        ]

        gate(
            13,
            "REQUIRES_RUNTIME",
            f"Screener API endpoints documented: {screener_paths}; "
            "runtime result comparison required"
        )

except Exception as e:
    gate(13, "FAIL", str(e))

# ------------------------------------------------------------------
# AC-14
# 11 peer groups
# ------------------------------------------------------------------

try:
    tables = [
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    ]

    if "peer_percentiles" not in tables:
        gate(
            14,
            "FAIL",
            "peer_percentiles table not found"
        )
    else:
        columns = [
            row[1]
            for row in conn.execute(
                "PRAGMA table_info(peer_percentiles)"
            )
        ]

        group_col = next(
            (
                c for c in columns
                if "peer" in c.lower()
                or "group" in c.lower()
                or "sector" in c.lower()
            ),
            None,
        )

        if group_col:
            count = conn.execute(
                f'''
                SELECT COUNT(DISTINCT "{group_col}")
                FROM peer_percentiles
                '''
            ).fetchone()[0]

            gate(
                14,
                "PASS" if count >= 11 else "FAIL",
                f"Distinct peer groups = {count}"
            )
        else:
            gate(
                14,
                "FAIL",
                "Could not identify peer group column"
            )

except Exception as e:
    gate(14, "FAIL", str(e))

# ------------------------------------------------------------------
# AC-15
# 92 companies have cluster_id
# ------------------------------------------------------------------

try:
    import pandas as pd

    path = ROOT / "output" / "cluster_labels.csv"

    if not path.exists():
        gate(15, "FAIL", "cluster_labels.csv missing")
    else:
        df = pd.read_csv(path)

        cluster_cols = [
            c for c in df.columns
            if "cluster_id" in c.lower()
        ]

        if not cluster_cols:
            gate(15, "FAIL", "cluster_id column missing")
        else:
            c = cluster_cols[0]
            valid = (
                len(df) == 92
                and df[c].notna().all()
            )

            gate(
                15,
                "PASS" if valid else "FAIL",
                f"rows={len(df)}, non-null cluster IDs={df[c].notna().sum()}"
            )

except Exception as e:
    gate(15, "FAIL", str(e))

# ------------------------------------------------------------------
# AC-16
# 92 companies with pro + con
# ------------------------------------------------------------------

try:
    import pandas as pd

    path = ROOT / "output" / "pros_cons_generated.csv"

    if not path.exists():
        gate(16, "FAIL", "pros_cons_generated.csv missing")
    else:
        df = pd.read_csv(path)

        company_col = next(
            (
                c for c in df.columns
                if c.lower() in {
                    "company_id",
                    "ticker",
                    "symbol",
                    "company",
                }
            ),
            None,
        )

        pro_col = next(
            (
                c for c in df.columns
                if "pro" in c.lower()
            ),
            None,
        )

        con_col = next(
            (
                c for c in df.columns
                if "con" in c.lower()
            ),
            None,
        )

        if not all([company_col, pro_col, con_col]):
            gate(
                16,
                "FAIL",
                f"columns={list(df.columns)}"
            )
        else:
            grouped = df.groupby(company_col).agg(
                pro_count=(pro_col, lambda x: x.astype(str).str.strip().ne("").sum()),
                con_count=(con_col, lambda x: x.astype(str).str.strip().ne("").sum()),
            )

            valid = (
                len(grouped) == 92
                and (grouped["pro_count"] >= 1).all()
                and (grouped["con_count"] >= 1).all()
            )

            gate(
                16,
                "PASS" if valid else "FAIL",
                f"companies={len(grouped)}"
            )

except Exception as e:
    gate(16, "FAIL", str(e))

# ------------------------------------------------------------------
# AC-17
# 92 tearsheets, >= 30 KB
# ------------------------------------------------------------------

try:
    path = ROOT / "reports" / "tearsheets"

    pdfs = list(path.glob("*.pdf"))

    too_small = [
        p.name
        for p in pdfs
        if p.stat().st_size < 30 * 1024
    ]

    valid = len(pdfs) == 92 and not too_small

    gate(
        17,
        "PASS" if valid else "FAIL",
        f"PDFs={len(pdfs)}, below_30KB={len(too_small)}"
    )

except Exception as e:
    gate(17, "FAIL", str(e))

# ------------------------------------------------------------------
# AC-18
# pytest >= 60 and 0 failures
# ------------------------------------------------------------------

try:
    test = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests",
            "-q",
        ],
        capture_output=True,
        text=True,
    )

    output = test.stdout + test.stderr

    match = re.search(
        r"(\d+)\s+passed",
        output,
    )

    passed_tests = (
        int(match.group(1))
        if match
        else 0
    )

    gate(
        18,
        "PASS"
        if test.returncode == 0 and passed_tests >= 60
        else "FAIL",
        f"pytest passed={passed_tests}"
    )

except Exception as e:
    gate(18, "FAIL", str(e))

# ------------------------------------------------------------------
# AC-19
# validation_failures columns
# ------------------------------------------------------------------

try:
    path = ROOT / "output" / "validation_failures.csv"

    if not path.exists():
        gate(19, "FAIL", "validation_failures.csv missing")
    else:
        with path.open(
            encoding="utf-8-sig",
            newline=""
        ) as f:
            reader = csv.reader(f)
            header = next(reader)

        required = {
            "company_id",
            "field",
            "issue",
            "severity",
        }

        actual = {x.strip().lower() for x in header}
        missing = required - actual

        gate(
            19,
            "PASS" if not missing else "FAIL",
            f"columns={header}"
        )

except Exception as e:
    gate(19, "FAIL", str(e))

# ------------------------------------------------------------------
# AC-20
# analyst guide >= 10 pages
# ------------------------------------------------------------------

try:
    from pypdf import PdfReader

    path = ROOT / "docs" / "analyst_guide.pdf"

    pages = len(
        PdfReader(str(path)).pages
    )

    gate(
        20,
        "PASS" if pages >= 10 else "FAIL",
        f"pages={pages}"
    )

except Exception as e:
    gate(20, "FAIL", str(e))

# ------------------------------------------------------------------
# FINAL SUMMARY
# ------------------------------------------------------------------

print("\n" + "=" * 80)
print("DAY 45 — ACCEPTANCE GATE SUMMARY")
print("=" * 80)

for i in range(1, 21):
    key = f"AC-{i:02d}"
    print(f"{key}: {results.get(key, 'NOT RUN')}")

passed = sum(
    1 for value in results.values()
    if value == "PASS"
)

failed = sum(
    1 for value in results.values()
    if value == "FAIL"
)

runtime = sum(
    1 for value in results.values()
    if value == "REQUIRES_RUNTIME"
)

print("-" * 80)
print(f"PASS: {passed}")
print(f"FAIL: {failed}")
print(f"REQUIRES RUNTIME/MANUAL VERIFICATION: {runtime}")
print("=" * 80)

conn.close()
