"""
N100 Financial Intelligence Platform
Sprint 5 - Day 34
Batch Report Generation

Outputs:
    reports/tearsheets/<ticker>_tearsheet.pdf
    reports/sector/<sector>_report.pdf
    output/skipped_tearsheets.csv

Day 33 template:
    src/reports/tearsheet.py
    build_tearsheet(company_id, output_path)
"""

from __future__ import annotations

import re
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = PROJECT_ROOT / "nifty100.db"

TEARSHEET_DIR = PROJECT_ROOT / "reports" / "tearsheets"
SECTOR_DIR = PROJECT_ROOT / "reports" / "sector"

OUTPUT_DIR = PROJECT_ROOT / "output"

SKIPPED_FILE = OUTPUT_DIR / "skipped_tearsheets.csv"

FAILURE_FILE = OUTPUT_DIR / "tearsheet_generation_failures.csv"

SECTOR_FAILURE_FILE = OUTPUT_DIR / "sector_generation_failures.csv"


# ============================================================
# COLORS
# ============================================================

NAVY = colors.HexColor("#080f1f")
BLUE = colors.HexColor("#2563eb")
LIGHT_BLUE = colors.HexColor("#eef4ff")
BORDER = colors.HexColor("#dfe6ef")
TEXT = colors.HexColor("#111a2d")
MUTED = colors.HexColor("#64748b")
WHITE = colors.white


# ============================================================
# SECTOR REPORT METRICS
# ============================================================

SECTOR_METRICS = [
    ("Revenue CAGR", "revenue_cagr_5yr"),
    ("PAT CAGR", "pat_cagr_5yr"),
    ("EPS CAGR", "eps_cagr_5yr"),
    ("ROE", "return_on_equity_pct"),
    ("ROCE", "return_on_capital_employed_pct"),
    ("D/E", "debt_to_equity"),
    ("ICR", "interest_coverage"),
    ("FCF", "free_cash_flow_cr"),
]


# ============================================================
# GENERAL HELPERS
# ============================================================


def clean_text(value) -> str:
    """Clean text."""
    if value is None or pd.isna(value):
        return ""

    text = str(value)
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def safe_filename(value: str) -> str:
    """Safe filename."""
    text = clean_text(value)

    text = re.sub(
        r'[<>:"/\\|?*]',
        "_",
        text,
    )

    text = re.sub(
        r"\s+",
        "_",
        text,
    )

    return text.strip("._") or "UNKNOWN"


def normalize_year(value):
    """Normalize year."""
    if value is None or pd.isna(value):
        return np.nan

    match = re.search(
        r"(19|20)\d{2}",
        str(value),
    )

    if match:
        return int(match.group(0))

    return np.nan


def numeric(value):
    """Numeric."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return np.nan


def fmt_pct(value):
    """Fmt pct."""
    value = numeric(value)

    if pd.isna(value):
        return "N/A"

    return f"{value:.2f}%"


def fmt_number(value):
    """Fmt number."""
    value = numeric(value)

    if pd.isna(value):
        return "N/A"

    return f"{value:.2f}"


def fmt_cr(value):
    """Fmt cr."""
    value = numeric(value)

    if pd.isna(value):
        return "N/A"

    return f"{value:,.2f}"


# ============================================================
# DATABASE
# ============================================================


def load_database():
    """Load database."""

    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found:\n{DB_PATH}")

    conn = sqlite3.connect(DB_PATH)

    try:

        companies = pd.read_sql_query(
            """
            SELECT
                id,
                company_name
            FROM companies
            """,
            conn,
        )

        pnl = pd.read_sql_query(
            """
            SELECT
                company_id,
                year,
                sales,
                net_profit
            FROM profitandloss
            """,
            conn,
        )

        ratios = pd.read_sql_query(
            """
            SELECT
                company_id,
                year,
                revenue_cagr_5yr,
                pat_cagr_5yr,
                eps_cagr_5yr,
                return_on_equity_pct,
                return_on_capital_employed_pct,
                debt_to_equity,
                interest_coverage,
                free_cash_flow_cr
            FROM financial_ratios
            """,
            conn,
        )

        sectors = pd.read_sql_query(
            """
            SELECT
                company_id,
                broad_sector,
                sub_sector
            FROM sectors
            """,
            conn,
        )

    finally:
        conn.close()

    companies["id"] = companies["id"].astype(str).str.strip()

    pnl["company_id"] = pnl["company_id"].astype(str).str.strip()

    ratios["company_id"] = ratios["company_id"].astype(str).str.strip()

    sectors["company_id"] = sectors["company_id"].astype(str).str.strip()

    pnl["year"] = pnl["year"].apply(normalize_year)

    ratios["year"] = ratios["year"].apply(normalize_year)

    return (
        companies,
        pnl,
        ratios,
        sectors,
    )


# ============================================================
# DAY 33 INTEGRATION
# ============================================================


def load_day33_template():
    """Load day33 template."""

    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(
            0,
            str(PROJECT_ROOT),
        )

    from src.reports import tearsheet

    if not hasattr(
        tearsheet,
        "build_tearsheet",
    ):
        raise AttributeError(
            "Day 33 tearsheet.py does not contain " "'build_tearsheet'."
        )

    return tearsheet.build_tearsheet


# ============================================================
# ELIGIBILITY
# ============================================================


def determine_eligibility(
    companies,
    pnl,
):
    """Determine eligibility."""

    valid_pnl = pnl.dropna(subset=["year"]).copy()

    year_counts = valid_pnl.groupby("company_id")["year"].nunique().to_dict()

    eligible = []
    skipped = []

    for _, row in companies.iterrows():

        company_id = clean_text(row["id"])

        company_name = clean_text(row["company_name"])

        years = int(
            year_counts.get(
                company_id,
                0,
            )
        )

        if years >= 3:

            eligible.append(
                {
                    "company_id": company_id,
                    "company_name": company_name,
                    "years": years,
                }
            )

        else:

            skipped.append(
                {
                    "company_id": company_id,
                    "company_name": company_name,
                    "years_available": years,
                    "reason": ("Fewer than 3 years " "of financial data"),
                }
            )

    return (
        eligible,
        skipped,
    )


# ============================================================
# CLEAN OLD OUTPUTS
# ============================================================


def clean_previous_outputs():
    """Clean previous outputs."""

    TEARSHEET_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    SECTOR_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    for pdf in TEARSHEET_DIR.glob("*_tearsheet.pdf"):
        pdf.unlink()

    for pdf in SECTOR_DIR.glob("*_report.pdf"):
        pdf.unlink()

    if FAILURE_FILE.exists():
        FAILURE_FILE.unlink()

    if SECTOR_FAILURE_FILE.exists():
        SECTOR_FAILURE_FILE.unlink()


# ============================================================
# SECTOR DATA
# ============================================================


def build_sector_dataframe(
    companies,
    ratios,
    sectors,
):
    """Build sector dataframe."""

    latest_ratios = (
        ratios.dropna(subset=["year"])
        .sort_values(["company_id", "year"])
        .groupby(
            "company_id",
            as_index=False,
        )
        .tail(1)
    )

    merged = companies.merge(
        sectors[
            [
                "company_id",
                "broad_sector",
                "sub_sector",
            ]
        ],
        left_on="id",
        right_on="company_id",
        how="left",
    )

    merged = merged.merge(
        latest_ratios,
        on="company_id",
        how="left",
    )

    merged["broad_sector"] = merged["broad_sector"].fillna("Unknown").apply(clean_text)

    merged["company_name"] = merged["company_name"].apply(clean_text)

    return merged


# ============================================================
# REPORT STYLES
# ============================================================


def create_styles():
    """Create styles."""

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="SectorSection",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=TEXT,
            spaceAfter=6,
        )
    )

    styles.add(
        ParagraphStyle(
            name="Cell",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=7,
            leading=9,
            textColor=TEXT,
            wordWrap="CJK",
        )
    )

    styles.add(
        ParagraphStyle(
            name="CellBold",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=7,
            leading=9,
            textColor=TEXT,
            wordWrap="CJK",
        )
    )

    styles.add(
        ParagraphStyle(
            name="HeaderCell",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=7,
            leading=9,
            textColor=WHITE,
            alignment=TA_CENTER,
            wordWrap="CJK",
        )
    )

    styles.add(
        ParagraphStyle(
            name="SummaryLabel",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=7,
            leading=9,
            textColor=MUTED,
            alignment=TA_CENTER,
            wordWrap="CJK",
        )
    )

    styles.add(
        ParagraphStyle(
            name="SummaryValue",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=13,
            textColor=TEXT,
            alignment=TA_CENTER,
            wordWrap="CJK",
        )
    )

    return styles


# ============================================================
# SECTOR HEADER / FOOTER
# ============================================================


def draw_sector_header_footer(
    canvas,
    doc,
    sector_name,
):
    """Draw sector header footer."""

    canvas.saveState()

    width, height = landscape(A4)

    canvas.setFillColor(NAVY)

    canvas.rect(
        0,
        height - 23 * mm,
        width,
        23 * mm,
        fill=1,
        stroke=0,
    )

    canvas.setFillColor(WHITE)

    canvas.setFont(
        "Helvetica-Bold",
        15,
    )

    canvas.drawString(
        15 * mm,
        height - 14 * mm,
        f"{sector_name} — Sector Intelligence Report",
    )

    canvas.setFont(
        "Helvetica",
        8,
    )

    canvas.drawString(
        15 * mm,
        height - 19 * mm,
        "N100 Financial Intelligence Platform | Sprint 5",
    )

    canvas.setStrokeColor(BORDER)

    canvas.line(
        15 * mm,
        10 * mm,
        width - 15 * mm,
        10 * mm,
    )

    canvas.setFillColor(MUTED)

    canvas.setFont(
        "Helvetica",
        7,
    )

    canvas.drawString(
        15 * mm,
        6 * mm,
        "N100 Financial Intelligence Platform",
    )

    canvas.drawRightString(
        width - 15 * mm,
        6 * mm,
        f"Page {doc.page}",
    )

    canvas.restoreState()


# ============================================================
# SECTOR REPORT
# ============================================================


def generate_sector_report(
    sector_name,
    sector_df,
    output_path,
):
    """Generate sector report."""

    styles = create_styles()

    document = BaseDocTemplate(
        str(output_path),
        pagesize=landscape(A4),
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=30 * mm,
        bottomMargin=15 * mm,
        title=f"{sector_name} Sector Report",
        author="N100 Financial Intelligence Platform",
    )

    frame = Frame(
        document.leftMargin,
        document.bottomMargin,
        document.width,
        document.height,
        id="sector_frame",
    )

    document.addPageTemplates(
        [
            PageTemplate(
                id="sector_template",
                frames=frame,
                onPage=lambda canvas, doc: draw_sector_header_footer(
                    canvas,
                    doc,
                    sector_name,
                ),
            )
        ]
    )

    story = []

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "Sector Summary",
            styles["SectorSection"],
        )
    )

    summary_headers = [
        "Companies",
        "Median Revenue CAGR",
        "Median PAT CAGR",
        "Median ROE",
        "Median ROCE",
        "Median D/E",
        "Median ICR",
        "Median FCF",
    ]

    summary_values = [
        str(len(sector_df)),
        fmt_pct(sector_df["revenue_cagr_5yr"].median()),
        fmt_pct(sector_df["pat_cagr_5yr"].median()),
        fmt_pct(sector_df["return_on_equity_pct"].median()),
        fmt_pct(sector_df["return_on_capital_employed_pct"].median()),
        fmt_number(sector_df["debt_to_equity"].median()),
        fmt_number(sector_df["interest_coverage"].median()),
        fmt_cr(sector_df["free_cash_flow_cr"].median()),
    ]

    summary_data = [
        [
            Paragraph(
                value,
                styles["SummaryLabel"],
            )
            for value in summary_headers
        ],
        [
            Paragraph(
                value,
                styles["SummaryValue"],
            )
            for value in summary_values
        ],
    ]

    summary_table = Table(
        summary_data,
        colWidths=[
            28 * mm,
            32 * mm,
            32 * mm,
            27 * mm,
            27 * mm,
            25 * mm,
            27 * mm,
            32 * mm,
        ],
        repeatRows=1,
    )

    summary_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    LIGHT_BLUE,
                ),
                (
                    "BACKGROUND",
                    (0, 1),
                    (-1, 1),
                    WHITE,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.6,
                    BORDER,
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    BORDER,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),
            ]
        )
    )

    story.append(summary_table)

    story.append(
        Spacer(
            1,
            7 * mm,
        )
    )

    # --------------------------------------------------------
    # COMPANY LIST
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "Companies in Sector",
            styles["SectorSection"],
        )
    )

    headers = [
        "Ticker",
        "Company",
        "Revenue CAGR",
        "PAT CAGR",
        "EPS CAGR",
        "ROE",
        "ROCE",
        "D/E",
        "ICR",
        "FCF",
    ]

    table_data = [
        [
            Paragraph(
                value,
                styles["HeaderCell"],
            )
            for value in headers
        ]
    ]

    sector_df = sector_df.sort_values("id")

    for _, row in sector_df.iterrows():

        table_data.append(
            [
                Paragraph(
                    clean_text(row["id"]),
                    styles["CellBold"],
                ),
                Paragraph(
                    clean_text(row["company_name"]),
                    styles["Cell"],
                ),
                Paragraph(
                    fmt_pct(row["revenue_cagr_5yr"]),
                    styles["Cell"],
                ),
                Paragraph(
                    fmt_pct(row["pat_cagr_5yr"]),
                    styles["Cell"],
                ),
                Paragraph(
                    fmt_pct(row["eps_cagr_5yr"]),
                    styles["Cell"],
                ),
                Paragraph(
                    fmt_pct(row["return_on_equity_pct"]),
                    styles["Cell"],
                ),
                Paragraph(
                    fmt_pct(row["return_on_capital_employed_pct"]),
                    styles["Cell"],
                ),
                Paragraph(
                    fmt_number(row["debt_to_equity"]),
                    styles["Cell"],
                ),
                Paragraph(
                    fmt_number(row["interest_coverage"]),
                    styles["Cell"],
                ),
                Paragraph(
                    fmt_cr(row["free_cash_flow_cr"]),
                    styles["Cell"],
                ),
            ]
        )

    company_table = Table(
        table_data,
        colWidths=[
            21 * mm,
            61 * mm,
            25 * mm,
            25 * mm,
            25 * mm,
            22 * mm,
            22 * mm,
            18 * mm,
            22 * mm,
            27 * mm,
        ],
        repeatRows=1,
        splitByRow=1,
    )

    company_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    NAVY,
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    WHITE,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.6,
                    BORDER,
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.35,
                    BORDER,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [
                        WHITE,
                        colors.HexColor("#f8fafc"),
                    ],
                ),
            ]
        )
    )

    story.append(company_table)

    document.build(story)


# ============================================================
# MAIN
# ============================================================


def main():
    """Main."""

    print("=" * 70)
    print("N100 BATCH REPORT GENERATION")
    print("SPRINT 5 - DAY 34")
    print("=" * 70)

    print()
    print("Project root:")
    print(PROJECT_ROOT)

    print()
    print("Database:")
    print(DB_PATH)

    # --------------------------------------------------------
    # DATABASE
    # --------------------------------------------------------

    print()
    print("Loading database...")

    (
        companies,
        pnl,
        ratios,
        sectors,
    ) = load_database()

    print(f"Companies : {len(companies)}")

    print(f"P&L       : {len(pnl)}")

    print(f"Ratios    : {len(ratios)}")

    print(f"Sectors   : {len(sectors)}")

    # --------------------------------------------------------
    # CLEAN OUTPUTS
    # --------------------------------------------------------

    print()
    print("Cleaning previous batch PDFs...")

    clean_previous_outputs()

    # --------------------------------------------------------
    # ELIGIBILITY
    # --------------------------------------------------------

    print()
    print("Checking company eligibility...")

    (
        eligible,
        skipped,
    ) = determine_eligibility(
        companies,
        pnl,
    )

    print(f"Eligible companies : {len(eligible)}")

    print(f"Skipped companies  : {len(skipped)}")

    skipped_df = pd.DataFrame(
        skipped,
        columns=[
            "company_id",
            "company_name",
            "years_available",
            "reason",
        ],
    )

    skipped_df.to_csv(
        SKIPPED_FILE,
        index=False,
    )

    print(f"Skipped log        : {SKIPPED_FILE}")

    if skipped:
        print()
        print("Skipped companies:")

        for item in skipped:
            print(
                f"  {item['company_id']} "
                f"— {item['company_name']} "
                f"({item['years_available']} years)"
            )

    # --------------------------------------------------------
    # DAY 33 TEMPLATE
    # --------------------------------------------------------

    print()
    print("Loading Day 33 tearsheet template...")

    build_tearsheet = load_day33_template()

    print("[PASS] Day 33 build_tearsheet() loaded.")

    # --------------------------------------------------------
    # BATCH TEARSHEETS
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("BATCH TEARSHEET GENERATION")
    print("=" * 70)

    success_count = 0
    failure_records = []

    total = len(eligible)

    for index, item in enumerate(
        eligible,
        start=1,
    ):

        ticker = clean_text(item["company_id"])

        company_name = clean_text(item["company_name"])

        output_path = TEARSHEET_DIR / f"{safe_filename(ticker)}_tearsheet.pdf"

        try:

            result = build_tearsheet(
                ticker,
                str(output_path),
            )

            if output_path.exists():

                success_count += 1

                print(f"[{index:02d}/{total}] " f"[PASS] {ticker} — " f"{company_name}")

            else:

                failure_records.append(
                    {
                        "company_id": ticker,
                        "company_name": company_name,
                        "reason": (
                            f"build_tearsheet returned "
                            f"{result!r} but output PDF "
                            f"was not found"
                        ),
                    }
                )

                print(
                    f"[{index:02d}/{total}] " f"[FAIL] {ticker} — " f"PDF not created"
                )

        except Exception as exc:

            failure_records.append(
                {
                    "company_id": ticker,
                    "company_name": company_name,
                    "reason": str(exc),
                }
            )

            print(f"[{index:02d}/{total}] " f"[FAIL] {ticker} — {exc}")

    if failure_records:

        pd.DataFrame(failure_records).to_csv(
            FAILURE_FILE,
            index=False,
        )

        print()
        print(f"Failure log: {FAILURE_FILE}")

    print()
    print(f"Tearsheet success : {success_count}")

    print(f"Tearsheet failed  : {len(failure_records)}")

    # --------------------------------------------------------
    # SECTOR REPORTS
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("BATCH SECTOR REPORT GENERATION")
    print("=" * 70)

    sector_df = build_sector_dataframe(
        companies,
        ratios,
        sectors,
    )

    sector_names = sorted(
        [
            clean_text(value)
            for value in sector_df["broad_sector"].dropna().unique()
            if clean_text(value)
        ]
    )

    print(f"Sectors identified : " f"{len(sector_names)}")

    sector_success = 0
    sector_failures = []

    for index, sector_name in enumerate(
        sector_names,
        start=1,
    ):

        current_df = sector_df[sector_df["broad_sector"] == sector_name].copy()

        output_path = SECTOR_DIR / f"{safe_filename(sector_name)}_report.pdf"

        try:

            generate_sector_report(
                sector_name,
                current_df,
                output_path,
            )

            if output_path.exists():

                sector_success += 1

                print(
                    f"[{index:02d}/"
                    f"{len(sector_names)}] "
                    f"[PASS] {sector_name} "
                    f"({len(current_df)} companies)"
                )

            else:

                sector_failures.append(
                    {
                        "sector": sector_name,
                        "reason": ("PDF was not created"),
                    }
                )

                print(f"[{index:02d}/" f"{len(sector_names)}] " f"[FAIL] {sector_name}")

        except Exception as exc:

            sector_failures.append(
                {
                    "sector": sector_name,
                    "reason": str(exc),
                }
            )

            print(
                f"[{index:02d}/"
                f"{len(sector_names)}] "
                f"[FAIL] {sector_name} — {exc}"
            )

    if sector_failures:

        pd.DataFrame(sector_failures).to_csv(
            SECTOR_FAILURE_FILE,
            index=False,
        )

    # --------------------------------------------------------
    # TEARSHEET VALIDATION
    # --------------------------------------------------------

    generated_tearsheets = sorted(TEARSHEET_DIR.glob("*_tearsheet.pdf"))

    generated_tickers = {
        p.stem.replace(
            "_tearsheet",
            "",
        )
        for p in generated_tearsheets
    }

    expected_tickers = {item["company_id"] for item in eligible}

    missing_tickers = sorted(expected_tickers - generated_tickers)

    extra_tickers = sorted(generated_tickers - expected_tickers)

    tearsheet_pass = (
        len(generated_tearsheets) == len(eligible)
        and not missing_tickers
        and not extra_tickers
        and not failure_records
    )

    # --------------------------------------------------------
    # SECTOR VALIDATION
    # --------------------------------------------------------

    generated_sector_reports = sorted(SECTOR_DIR.glob("*_report.pdf"))

    sector_pass = (
        len(generated_sector_reports) == len(sector_names) and not sector_failures
    )

    # --------------------------------------------------------
    # FINAL VALIDATION
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("DAY 34 FINAL VALIDATION")
    print("=" * 70)

    print(f"Companies in database : " f"{len(companies)}")

    print(f"Eligible companies    : " f"{len(eligible)}")

    print(f"Skipped companies     : " f"{len(skipped)}")

    print(f"Tearsheet PDFs        : " f"{len(generated_tearsheets)}")

    print(f"Expected tearsheets   : " f"{len(eligible)}")

    print(f"Sector reports        : " f"{len(generated_sector_reports)}")

    print(f"Expected sectors      : " f"{len(sector_names)}")

    print(f"Skipped log           : " f"{'YES' if SKIPPED_FILE.exists() else 'NO'}")

    print(f"Tearsheet validation  : " f"{'PASS' if tearsheet_pass else 'FAIL'}")

    print(f"Sector validation     : " f"{'PASS' if sector_pass else 'FAIL'}")

    if missing_tickers:

        print()
        print("Missing tearsheets:")

        for ticker in missing_tickers:
            print(f"  - {ticker}")

    if extra_tickers:

        print()
        print("Unexpected tearsheets:")

        for ticker in extra_tickers:
            print(f"  - {ticker}")

    if failure_records:

        print()
        print("Tearsheet failures:")

        for item in failure_records:
            print(f"  - {item['company_id']}: " f"{item['reason']}")

    if sector_failures:

        print()
        print("Sector failures:")

        for item in sector_failures:
            print(f"  - {item['sector']}: " f"{item['reason']}")

    if tearsheet_pass and sector_pass:

        print()
        print("DAY 34 STATUS: COMPLETED")

    else:

        print()
        print("DAY 34 STATUS: REVIEW REQUIRED")


if __name__ == "__main__":
    main()
