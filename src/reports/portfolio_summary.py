from pathlib import Path
import sqlite3
import math

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "nifty100.db"
OUTPUT_DIR = ROOT / "reports" / "portfolio"
OUTPUT_PDF = OUTPUT_DIR / "portfolio_summary.pdf"

PAGE_W, PAGE_H = A4


# ---------------------------------------------------------
# DATABASE
# ---------------------------------------------------------

def get_connection():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    return sqlite3.connect(DB_PATH)


def load_companies():
    conn = get_connection()

    query = """
        SELECT
            c.id AS ticker,
            c.company_name,
            COALESCE(s.broad_sector, 'Unclassified') AS sector
        FROM companies c
        LEFT JOIN sectors s
            ON c.id = s.company_id
        ORDER BY c.id
    """

    rows = conn.execute(query).fetchall()
    conn.close()

    return rows


def load_ratio_history(ticker):
    conn = get_connection()

    query = """
        SELECT
            year,
            revenue_cagr_5yr,
            pat_cagr_5yr,
            return_on_equity_pct,
            return_on_capital_employed_pct,
            debt_to_equity,
            composite_quality_score
        FROM financial_ratios
        WHERE company_id = ?
        ORDER BY year
    """

    rows = conn.execute(query, (ticker,)).fetchall()
    conn.close()

    return rows


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def clean_company_name(name):
    if name is None:
        return "Unknown Company"

    return " ".join(str(name).replace("\n", " ").split())


def safe_float(value):
    if value is None:
        return None

    try:
        value = float(value)

        if math.isnan(value) or math.isinf(value):
            return None

        return value
    except (TypeError, ValueError):
        return None


def format_number(value, suffix=""):
    value = safe_float(value)

    if value is None:
        return "N/A"

    if abs(value) >= 100:
        text = f"{value:,.1f}"
    else:
        text = f"{value:.2f}"

    return text + suffix


# ---------------------------------------------------------
# TREND ARROWS
# ---------------------------------------------------------

def trend_arrow(previous, current, lower_is_better=False):
    """
    Returns:
        ↑ improved
        ↓ declined
        → flat within 2%
    """

    previous = safe_float(previous)
    current = safe_float(current)

    if previous is None or current is None:
        return "→"

    difference = current - previous

    # Handle previous value near zero
    if abs(previous) < 1e-9:
        if abs(difference) < 0.02:
            return "→"

        if lower_is_better:
            return "↓" if difference > 0 else "↑"

        return "↑" if difference > 0 else "↓"

    percentage_change = abs(difference / previous)

    # Flat within 2%
    if percentage_change <= 0.02:
        return "→"

    if lower_is_better:
        return "↑" if difference < 0 else "↓"

    return "↑" if difference > 0 else "↓"


# ---------------------------------------------------------
# KPI PREPARATION
# ---------------------------------------------------------

def prepare_company(ticker, company_name, sector):
    rows = load_ratio_history(ticker)

    if not rows:
        return {
            "ticker": ticker,
            "company_name": clean_company_name(company_name),
            "sector": sector,
            "latest_year": "N/A",
            "previous_year": "N/A",
            "kpis": []
        }

    latest = rows[-1]
    previous = rows[-2] if len(rows) >= 2 else None

    latest_year = latest[0]
    previous_year = previous[0] if previous else "N/A"

    metrics = [
        (
            "Revenue CAGR (5Y)",
            latest[1],
            previous[1] if previous else None,
            "%",
            False
        ),
        (
            "PAT CAGR (5Y)",
            latest[2],
            previous[2] if previous else None,
            "%",
            False
        ),
        (
            "ROE",
            latest[3],
            previous[3] if previous else None,
            "%",
            False
        ),
        (
            "ROCE",
            latest[4],
            previous[4] if previous else None,
            "%",
            False
        ),
        (
            "Debt / Equity",
            latest[5],
            previous[5] if previous else None,
            "x",
            True
        ),
        (
            "Quality Score",
            latest[6],
            previous[6] if previous else None,
            "",
            False
        ),
    ]

    kpis = []

    for name, current, previous_value, suffix, lower_is_better in metrics:
        kpis.append(
            {
                "name": name,
                "value": current,
                "previous": previous_value,
                "suffix": suffix,
                "arrow": trend_arrow(
                    previous_value,
                    current,
                    lower_is_better=lower_is_better
                )
            }
        )

    return {
        "ticker": ticker,
        "company_name": clean_company_name(company_name),
        "sector": sector,
        "latest_year": latest_year,
        "previous_year": previous_year,
        "kpis": kpis
    }


# ---------------------------------------------------------
# PDF DRAWING
# ---------------------------------------------------------

def draw_header(pdf, company):
    # Header
    pdf.setFillColor(colors.HexColor("#080f1f"))
    pdf.rect(0, PAGE_H - 105, PAGE_W, 105, fill=1, stroke=0)

    pdf.setFillColor(colors.white)

    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawString(
        40,
        PAGE_H - 48,
        company["ticker"]
    )

    pdf.setFont("Helvetica", 11)
    pdf.drawString(
        40,
        PAGE_H - 68,
        company["company_name"][:75]
    )

    pdf.setFont("Helvetica", 9)
    pdf.setFillColor(colors.HexColor("#cbd5e1"))
    pdf.drawString(
        40,
        PAGE_H - 87,
        f"Sector: {company['sector']}"
    )

    pdf.setFillColor(colors.HexColor("#2563eb"))
    pdf.rect(0, PAGE_H - 108, PAGE_W, 3, fill=1, stroke=0)


def draw_section_title(pdf, title, y):
    pdf.setFillColor(colors.HexColor("#111a2d"))
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(40, y, title)

    pdf.setStrokeColor(colors.HexColor("#dfe6ef"))
    pdf.line(40, y - 6, PAGE_W - 40, y - 6)

    return y - 25


def draw_kpi_card(pdf, x, y, width, height, kpi):
    pdf.setFillColor(colors.white)
    pdf.setStrokeColor(colors.HexColor("#dfe6ef"))

    pdf.roundRect(
        x,
        y,
        width,
        height,
        7,
        fill=1,
        stroke=1
    )

    # KPI name
    pdf.setFillColor(colors.HexColor("#64748b"))
    pdf.setFont("Helvetica-Bold", 8.5)
    pdf.drawString(
        x + 12,
        y + height - 20,
        kpi["name"]
    )

    # Value
    pdf.setFillColor(colors.HexColor("#111a2d"))
    pdf.setFont("Helvetica-Bold", 17)

    value_text = format_number(
        kpi["value"],
        kpi["suffix"]
    )

    pdf.drawString(
        x + 12,
        y + 22,
        value_text
    )

    # Arrow
    arrow = kpi["arrow"]

    if arrow == "↑":
        arrow_color = colors.HexColor("#00a67d")
    elif arrow == "↓":
        arrow_color = colors.HexColor("#ef5350")
    else:
        arrow_color = colors.HexColor("#64748b")

    pdf.setFillColor(arrow_color)
    pdf.setFont("Helvetica-Bold", 16)

    pdf.drawRightString(
        x + width - 12,
        y + 21,
        arrow
    )


def draw_kpis(pdf, company):
    y = PAGE_H - 145

    pdf.setFillColor(colors.HexColor("#64748b"))
    pdf.setFont("Helvetica", 8.5)

    if company["previous_year"] != "N/A":
        period_text = (
            f"Latest year: {company['latest_year']}   |   "
            f"Compared with: {company['previous_year']}"
        )
    else:
        period_text = f"Latest year: {company['latest_year']}"

    pdf.drawString(40, y, period_text)

    y -= 22

    card_width = 160
    card_height = 78
    gap_x = 17
    gap_y = 16

    start_x = 40

    for index, kpi in enumerate(company["kpis"]):
        row = index // 3
        col = index % 3

        x = start_x + col * (card_width + gap_x)
        card_y = y - row * (card_height + gap_y)

        draw_kpi_card(
            pdf,
            x,
            card_y,
            card_width,
            card_height,
            kpi
        )

    return y - 2 * (card_height + gap_y) - 15


def draw_trend_legend(pdf, y):
    pdf.setFont("Helvetica", 8.5)
    pdf.setFillColor(colors.HexColor("#64748b"))

    pdf.drawString(
        40,
        y,
        "Trend direction: "
    )

    pdf.setFillColor(colors.HexColor("#00a67d"))
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(103, y - 1, "↑")

    pdf.setFillColor(colors.HexColor("#64748b"))
    pdf.setFont("Helvetica", 8.5)
    pdf.drawString(113, y, "Improved")

    pdf.setFillColor(colors.HexColor("#ef5350"))
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(164, y - 1, "↓")

    pdf.setFillColor(colors.HexColor("#64748b"))
    pdf.setFont("Helvetica", 8.5)
    pdf.drawString(174, y, "Declined")

    pdf.setFillColor(colors.HexColor("#64748b"))
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(224, y - 1, "→")

    pdf.setFont("Helvetica", 8.5)
    pdf.drawString(234, y, "Flat within 2%")


def draw_summary(pdf, company, y):
    y = draw_section_title(
        pdf,
        "Portfolio Snapshot",
        y
    )

    pdf.setFillColor(colors.HexColor("#f5f7fa"))
    pdf.setStrokeColor(colors.HexColor("#dfe6ef"))

    pdf.roundRect(
        40,
        y - 82,
        PAGE_W - 80,
        75,
        8,
        fill=1,
        stroke=1
    )

    pdf.setFillColor(colors.HexColor("#111a2d"))
    pdf.setFont("Helvetica-Bold", 10)

    pdf.drawString(
        55,
        y - 28,
        "Company"
    )

    pdf.setFont("Helvetica", 10)
    pdf.drawString(
        135,
        y - 28,
        company["company_name"][:65]
    )

    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(
        55,
        y - 51,
        "Sector"
    )

    pdf.setFont("Helvetica", 10)
    pdf.drawString(
        135,
        y - 51,
        company["sector"][:55]
    )

    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(
        55,
        y - 70,
        "Coverage"
    )

    pdf.setFont("Helvetica", 10)
    pdf.drawString(
        135,
        y - 70,
        "Latest available financial year"
    )


def draw_footer(pdf, company_index, total):
    pdf.setFillColor(colors.HexColor("#64748b"))
    pdf.setFont("Helvetica", 7.5)

    pdf.drawString(
        40,
        24,
        "N100 Financial Intelligence Platform"
    )

    pdf.drawRightString(
        PAGE_W - 40,
        24,
        f"{company_index} / {total}"
    )


def build_pdf():
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    companies = load_companies()

    if len(companies) != 92:
        raise ValueError(
            f"Expected 92 companies, found {len(companies)}"
        )

    pdf = canvas.Canvas(
        str(OUTPUT_PDF),
        pagesize=A4
    )

    pdf.setTitle(
        "N100 Financial Intelligence Platform - Portfolio Summary"
    )

    total = len(companies)

    for index, (ticker, company_name, sector) in enumerate(
        companies,
        start=1
    ):
        company = prepare_company(
            ticker,
            company_name,
            sector
        )

        draw_header(
            pdf,
            company
        )

        y = draw_kpis(
            pdf,
            company
        )

        draw_trend_legend(
            pdf,
            y
        )

        draw_summary(
            pdf,
            company,
            y - 28
        )

        draw_footer(
            pdf,
            index,
            total
        )

        pdf.showPage()

    pdf.save()

    return {
        "companies": total,
        "output": OUTPUT_PDF,
        "size_kb": OUTPUT_PDF.stat().st_size / 1024
    }


def validate_pdf():
    try:
        from pypdf import PdfReader
    except ImportError:
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            return {
                "status": "SKIP",
                "message": "pypdf/PyPDF2 not installed"
            }

    reader = PdfReader(str(OUTPUT_PDF))

    pages = len(reader.pages)

    if pages != 92:
        raise AssertionError(
            f"Expected 92 pages, found {pages}"
        )

    text_pages = 0

    for page in reader.pages:
        text = page.extract_text() or ""

        if text.strip():
            text_pages += 1

    if text_pages != 92:
        raise AssertionError(
            f"Expected text on 92 pages, found {text_pages}"
        )

    return {
        "status": "PASS",
        "pages": pages,
        "text_pages": text_pages,
        "size_kb": OUTPUT_PDF.stat().st_size / 1024
    }


def main():
    print("=" * 70)
    print("DAY 35 — PORTFOLIO SUMMARY PDF")
    print("=" * 70)

    result = build_pdf()

    print()
    print(f"Companies processed : {result['companies']}")
    print(f"PDF generated       : {result['output']}")
    print(f"PDF size            : {result['size_kb']:.1f} KB")

    print()
    print("Validation:")
    validation = validate_pdf()

    for key, value in validation.items():
        print(f"{key:20}: {value}")

    print()
    print("DAY 35 PORTFOLIO PDF STATUS: COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()
