from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "analyst_guide.pdf"


styles = getSampleStyleSheet()

TITLE = ParagraphStyle(
    "TitleCustom",
    parent=styles["Title"],
    alignment=TA_CENTER,
    fontSize=24,
    leading=30,
    spaceAfter=20,
)

SUBTITLE = ParagraphStyle(
    "SubtitleCustom",
    parent=styles["Normal"],
    alignment=TA_CENTER,
    fontSize=12,
    leading=18,
    spaceAfter=30,
)

H1 = ParagraphStyle(
    "H1Custom",
    parent=styles["Heading1"],
    fontSize=18,
    leading=22,
    spaceAfter=12,
)

H2 = ParagraphStyle(
    "H2Custom",
    parent=styles["Heading2"],
    fontSize=13,
    leading=17,
    spaceBefore=8,
    spaceAfter=8,
)

BODY = ParagraphStyle(
    "BodyCustom",
    parent=styles["BodyText"],
    fontSize=10,
    leading=15,
    spaceAfter=8,
)

CODE = ParagraphStyle(
    "CodeCustom",
    parent=styles["Code"],
    fontName="Courier",
    fontSize=8.5,
    leading=12,
    leftIndent=10,
    spaceAfter=10,
)

CENTER = ParagraphStyle(
    "CenterCustom",
    parent=BODY,
    alignment=TA_CENTER,
)


def p(text, style=BODY):
    return Paragraph(text, style)


def code(text):
    return Paragraph(text.replace("\n", "<br/>"), CODE)


def table(data, widths=None):
    converted = []

    for row in data:
        converted.append(
            [
                Paragraph(str(cell), BODY)
                for cell in row
            ]
        )

    t = Table(converted, colWidths=widths, repeatRows=1)

    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )

    return t


def footer(canvas, doc):
    canvas.saveState()

    canvas.setFont("Helvetica", 8)
    canvas.drawString(
        0.6 * inch,
        0.4 * inch,
        "N100 Financial Intelligence Platform — Analyst Guide",
    )

    canvas.drawRightString(
        7.9 * inch,
        0.4 * inch,
        f"Page {doc.page}",
    )

    canvas.restoreState()


story = []


# ============================================================
# PAGE 1 — COVER
# ============================================================

story.append(Spacer(1, 1.5 * inch))
story.append(p("N100 Financial Intelligence Platform", TITLE))
story.append(p("Analyst Guide", TITLE))
story.append(
    p(
        "User documentation for the Streamlit dashboard, "
        "financial analysis workflow, PDF reports, and REST API.",
        SUBTITLE,
    )
)

story.append(Spacer(1, 0.5 * inch))

story.append(
    p(
        "<b>Project:</b> N100 Financial Intelligence Platform<br/>"
        "<b>Database:</b> nifty100.db<br/>"
        "<b>Dashboard:</b> Streamlit<br/>"
        "<b>API:</b> FastAPI<br/>"
        "<b>Report generation:</b> ReportLab",
        CENTER,
    )
)

story.append(Spacer(1, 1.0 * inch))

story.append(
    p(
        "This guide explains how an analyst can start the platform, "
        "navigate the dashboard, screen companies, inspect company "
        "information, generate reports, use the API, and troubleshoot "
        "common runtime issues.",
        CENTER,
    )
)

story.append(PageBreak())


# ============================================================
# PAGE 2 — PLATFORM OVERVIEW
# ============================================================

story.append(p("1. Platform Overview", H1))

story.append(
    p(
        "The N100 Financial Intelligence Platform is a financial "
        "analytics application built around a SQLite database containing "
        "structured information for the project's Nifty 100 company universe."
    )
)

story.append(p("Core Components", H2))

story.append(
    table(
        [
            ["Component", "Purpose"],
            ["SQLite database", "Stores structured company and financial data."],
            ["ETL layer", "Loads, normalizes, validates, and prepares data."],
            ["Analytics layer", "Calculates financial metrics and analytical outputs."],
            ["Streamlit dashboard", "Provides the interactive analyst interface."],
            ["FastAPI service", "Exposes financial information through REST endpoints."],
            ["Reports module", "Generates PDF financial reports and tearsheets."],
        ],
        [1.5 * inch, 5.5 * inch],
    )
)

story.append(Spacer(1, 12))

story.append(p("Project Structure", H2))

story.append(
    code(
        """src/
  analytics/
  api/
  dashboard/
  etl/
  nlp/
  reports/
  screener/

tests/
  api/
  db/
  dq/
  etl/
  integration/
  kpi/
  performance/
  screener/

docs/
output/
reports/
nifty100.db"""
    )
)

story.append(p("Primary Services", H2))

story.append(
    p(
        "The dashboard runs on port 8501 and the FastAPI application "
        "runs on port 8000 during normal local development."
    )
)

story.append(PageBreak())


# ============================================================
# PAGE 3 — SETUP AND STARTUP
# ============================================================

story.append(p("2. Environment and Startup", H1))

story.append(p("Activate the Virtual Environment", H2))

story.append(
    code(
        r""".venv\Scripts\Activate.ps1"""
    )
)

story.append(p("Start FastAPI", H2))

story.append(
    code(
        "uvicorn src.api.main:app --host 127.0.0.1 --port 8000"
    )
)

story.append(
    p(
        "After startup, the API is available locally at "
        "<b>http://127.0.0.1:8000</b>. "
        "FastAPI documentation is available through the application's "
        "documentation endpoint."
    )
)

story.append(p("Start Streamlit", H2))

story.append(
    code(
        "streamlit run src\\dashboard\\app.py --server.port 8501"
    )
)

story.append(
    p(
        "The Streamlit dashboard is available at "
        "<b>http://localhost:8501</b>."
    )
)

story.append(p("Normal Two-Service Setup", H2))

story.append(
    code(
        """Terminal 1
uvicorn src.api.main:app --host 127.0.0.1 --port 8000

Terminal 2
streamlit run src\\dashboard\\app.py --server.port 8501"""
    )
)

story.append(p("Expected Ports", H2))

story.append(
    table(
        [
            ["Service", "Port", "Purpose"],
            ["FastAPI", "8000", "REST API"],
            ["Streamlit", "8501", "Interactive dashboard"],
        ],
        [2.0 * inch, 1.2 * inch, 3.8 * inch],
    )
)

story.append(PageBreak())


# ============================================================
# PAGE 4 — DASHBOARD NAVIGATION
# ============================================================

story.append(p("3. Dashboard Navigation", H1))

story.append(
    p(
        "The Streamlit application is organized into multiple dashboard "
        "pages. The analyst can use the navigation controls to move "
        "between company analysis, screening, peer analysis, trends, "
        "sector analysis, capital allocation, and reporting."
    )
)

story.append(
    table(
        [
            ["Page", "Primary purpose"],
            ["Home", "Platform overview and key market/company information."],
            ["Profile", "Detailed analysis of an individual company."],
            ["Screener", "Filter companies using financial criteria."],
            ["Peers", "Compare companies within peer groups."],
            ["Trends", "Analyze financial trends across periods."],
            ["Sectors", "Review sector-level information."],
            ["Capital", "Analyze capital allocation information."],
            ["Reports", "Generate and access financial reports."],
        ],
        [1.5 * inch, 5.5 * inch],
    )
)

story.append(p("Navigation Workflow", H2))

story.append(
    code(
        """Home
  |
  +-- Profile
  |
  +-- Screener
  |
  +-- Peers
  |
  +-- Trends
  |
  +-- Sectors
  |
  +-- Capital
  |
  +-- Reports"""
    )
)

story.append(
    p(
        "For company-level analysis, an analyst will typically begin "
        "with the Screener or Profile page. Screening can identify "
        "companies matching selected criteria, after which the Profile "
        "page can be used for detailed inspection."
    )
)

story.append(PageBreak())


# ============================================================
# PAGE 5 — HOME AND PROFILE
# ============================================================

story.append(p("4. Home and Company Profile", H1))

story.append(p("Home Screen", H2))

story.append(
    p(
        "The Home screen provides the main entry point to the dashboard. "
        "It presents the platform's high-level financial information and "
        "serves as the starting point for navigating to detailed analysis."
    )
)

story.append(p("Company Profile", H2))

story.append(
    p(
        "The Company Profile page is designed for detailed analysis of "
        "an individual company. Select a company/ticker through the "
        "available dashboard controls to inspect its stored information."
    )
)

story.append(p("Typical Profile Information", H2))

story.append(
    table(
        [
            ["Information", "Description"],
            ["Company identity", "Company name and ticker-related information."],
            ["Sector", "Broad and sub-sector classification."],
            ["Financial ratios", "Stored profitability, leverage and efficiency metrics."],
            ["Profit & loss", "Historical income statement information."],
            ["Balance sheet", "Historical balance-sheet information."],
            ["Cash flow", "Operating, investing and financing cash-flow information."],
            ["Market information", "Stored market-cap and valuation information."],
        ],
        [2.0 * inch, 5.0 * inch],
    )
)

story.append(p("Profile Usage Workflow", H2))

story.append(
    code(
        """1. Open Company Profile.
2. Select the required company.
3. Review company and sector information.
4. Inspect financial ratios.
5. Review historical financial statements.
6. Compare relevant metrics across periods.
7. Use Reports when a PDF output is required."""
    )
)

story.append(PageBreak())


# ============================================================
# PAGE 6 — SCREENER
# ============================================================

story.append(p("5. Screener", H1))

story.append(
    p(
        "The Screener page is used to filter the company universe according "
        "to financial conditions. It allows an analyst to narrow the dataset "
        "before performing detailed company-level analysis."
    )
)

story.append(p("Example Screening Criterion", H2))

story.append(
    code(
        "min_roe = 15"
    )
)

story.append(
    p(
        "The corresponding API request used during Day 43 testing was:"
    )
)

story.append(
    code(
        "GET /api/v1/screener?min_roe=15"
    )
)

story.append(
    p(
        "The tested request returned HTTP 200 and produced a response "
        "containing 54 companies in the tested project database."
    )
)

story.append(p("Recommended Screening Workflow", H2))

story.append(
    code(
        """1. Open Screener.
2. Set the required financial filters.
3. Run the screening operation.
4. Review the returned companies.
5. Select companies for deeper Profile analysis.
6. Generate reports where required."""
    )
)

story.append(p("Interpretation", H2))

story.append(
    p(
        "Screening results represent the output of the selected filters. "
        "They should be interpreted together with the underlying financial "
        "data and the other available dashboard analysis rather than as a "
        "standalone conclusion."
    )
)

story.append(PageBreak())


# ============================================================
# PAGE 7 — PEERS / TRENDS / SECTORS
# ============================================================

story.append(p("6. Peers, Trends and Sectors", H1))

story.append(p("Peer Analysis", H2))

story.append(
    p(
        "The Peers page supports comparison between companies that belong "
        "to relevant peer groups. Analysts can use peer information to "
        "understand relative financial characteristics."
    )
)

story.append(p("Trends", H2))

story.append(
    p(
        "The Trends page is intended for examining changes in financial "
        "metrics across available periods. Historical values should be "
        "read with attention to the years actually present in the database."
    )
)

story.append(p("Sector Analysis", H2))

story.append(
    p(
        "The Sectors page organizes companies using the sector information "
        "stored in the database. It can be used to inspect broad-sector "
        "and sub-sector classifications and related financial information."
    )
)

story.append(
    table(
        [
            ["Screen", "Analyst question"],
            ["Peers", "How do selected companies compare with their peers?"],
            ["Trends", "How have selected metrics changed over time?"],
            ["Sectors", "How are companies distributed across sectors?"],
        ],
        [1.5 * inch, 5.5 * inch],
    )
)

story.append(p("Important Data Consideration", H2))

story.append(
    p(
        "The platform's project documentation identifies certain supporting "
        "datasets as simulated according to the project plan. Such data "
        "should not be represented as live market data."
    )
)

story.append(PageBreak())


# ============================================================
# PAGE 8 — CAPITAL AND REPORTS
# ============================================================

story.append(p("7. Capital Allocation and Reports", H1))

story.append(p("Capital Allocation", H2))

story.append(
    p(
        "The Capital page provides access to capital-allocation-related "
        "analysis available in the platform. Analysts can use the page "
        "alongside company financial statements and ratios for context."
    )
)

story.append(p("Reports", H2))

story.append(
    p(
        "The Reports page provides the interface for generating financial "
        "report outputs. The platform includes a report/tearsheet module "
        "under <b>src/reports/</b>."
    )
)

story.append(p("PDF Tearsheets", H2))

story.append(
    p(
        "A tearsheet is a compact PDF representation of relevant company "
        "information. The exact available fields depend on the current "
        "report implementation."
    )
)

story.append(p("Typical Workflow", H2))

story.append(
    code(
        """1. Open Reports.
2. Select the required company or report option.
3. Generate the report.
4. Wait for PDF generation to complete.
5. Open/save the generated PDF.
6. Verify the company and reporting information before use."""
    )
)

story.append(p("Report Code", H2))

story.append(
    code(
        """src/reports/
  batch_reports.py
  portfolio_summary.py
  tearsheet.py"""
    )
)

story.append(PageBreak())


# ============================================================
# PAGE 9 — API
# ============================================================

story.append(p("8. REST API Usage", H1))

story.append(
    p(
        "The platform provides a FastAPI REST service. The API uses the "
        "prefix <b>/api/v1</b> for versioned endpoints."
    )
)

story.append(p("API Base URL", H2))

story.append(
    code(
        "http://127.0.0.1:8000/api/v1"
    )
)

story.append(p("Screener Example", H2))

story.append(
    code(
        'curl "http://127.0.0.1:8000/api/v1/screener?min_roe=15"'
    )
)

story.append(p("Health Check", H2))

story.append(
    code(
        'curl "http://127.0.0.1:8000/"'
    )
)

story.append(p("PowerShell Alternative", H2))

story.append(
    code(
        'Invoke-RestMethod "http://127.0.0.1:8000/api/v1/screener?min_roe=15"'
    )
)

story.append(p("Python Requests Example", H2))

story.append(
    code(
        """import requests

response = requests.get(
    "http://127.0.0.1:8000/api/v1/screener",
    params={"min_roe": 15},
    timeout=5,
)

print(response.status_code)
print(response.json())"""
    )
)

story.append(p("API Documentation", H2))

story.append(
    p(
        "When FastAPI is running, use the application's documentation "
        "endpoint to inspect available routes, parameters, and schemas."
    )
)

story.append(PageBreak())


# ============================================================
# PAGE 10 — TESTING AND PERFORMANCE
# ============================================================

story.append(p("9. Testing and Performance", H1))

story.append(p("Test Suite", H2))

story.append(
    code(
        "pytest tests -v"
    )
)

story.append(p("Performance Tests", H2))

story.append(
    code(
        """pytest tests\\performance\\test_screener_load.py -v -s

pytest tests\\performance\\test_profile_performance.py -v -s"""
    )
)

story.append(p("Day 43 Screener Result", H2))

story.append(
    table(
        [
            ["Metric", "Measured"],
            ["Concurrent requests", "10"],
            ["Successful requests", "10/10"],
            ["Total time", "0.0769 sec"],
            ["Maximum request", "0.0753 sec"],
            ["Average request", "0.0583 sec"],
        ],
        [3.0 * inch, 4.0 * inch],
    )
)

story.append(p("Company Profile Results", H2))

story.append(
    table(
        [
            ["Ticker", "Load time"],
            ["TCS", "0.0119 sec"],
            ["HDFCBANK", "0.0062 sec"],
            ["HINDUNILVR", "0.0061 sec"],
            ["RELIANCE", "0.0059 sec"],
            ["SUNPHARMA", "0.0054 sec"],
        ],
        [3.0 * inch, 4.0 * inch],
    )
)

story.append(
    p(
        "All five tested Company Profile data-loading measurements were "
        "below the Day 43 target of 3 seconds."
    )
)

story.append(PageBreak())


# ============================================================
# PAGE 11 — TROUBLESHOOTING
# ============================================================

story.append(p("10. Troubleshooting", H1))

story.append(p("FastAPI Will Not Start", H2))

story.append(
    p(
        "Check whether another process is already using port 8000. "
        "Stop the conflicting process or start FastAPI on an available "
        "port and update the client configuration accordingly."
    )
)

story.append(
    code(
        "netstat -ano | findstr :8000"
    )
)

story.append(p("Streamlit Will Not Start", H2))

story.append(
    p(
        "Check port 8501:"
    )
)

story.append(
    code(
        "netstat -ano | findstr :8501"
    )
)

story.append(p("Database Not Found", H2))

story.append(
    p(
        "Ensure that <b>nifty100.db</b> exists in the expected project "
        "location and that the application is being started from the "
        "project root."
    )
)

story.append(p("API Returns an Error", H2))

story.append(
    code(
        """1. Confirm FastAPI is running.
2. Check the API URL.
3. Check the endpoint path.
4. Inspect the FastAPI terminal output.
5. Test the endpoint through the API documentation."""
    )
)

story.append(p("Streamlit Warnings During Pytest", H2))

story.append(
    p(
        "The Day 43 Company Profile performance tests produced Streamlit "
        "warnings such as 'No runtime found, using MemoryCacheStorageManager' "
        "and 'missing ScriptRunContext'. These occurred because Streamlit "
        "functions were exercised from pytest/bare mode. They did not cause "
        "the performance tests to fail."
    )
)

story.append(PageBreak())


# ============================================================
# PAGE 12 — FINAL CHECKLIST
# ============================================================

story.append(p("11. Analyst Quick Reference", H1))

story.append(p("Startup Checklist", H2))

story.append(
    code(
        """1. Activate .venv.
2. Confirm nifty100.db exists.
3. Start FastAPI on port 8000.
4. Start Streamlit on port 8501.
5. Open the Streamlit dashboard.
6. Verify the required dashboard page loads."""
    )
)

story.append(p("Analysis Checklist", H2))

story.append(
    code(
        """1. Use Screener to identify companies matching criteria.
2. Open Company Profile for detailed information.
3. Review ratios and historical statements.
4. Use Peers for comparative analysis.
5. Use Trends for historical changes.
6. Use Sectors for sector-level context.
7. Use Capital for capital-allocation analysis.
8. Generate a PDF tearsheet/report when required."""
    )
)

story.append(p("API Checklist", H2))

story.append(
    code(
        """1. Confirm FastAPI is running.
2. Use /api/v1 endpoints.
3. Check HTTP status codes.
4. Validate returned JSON.
5. Use the API documentation when exploring endpoints."""
    )
)

story.append(p("Documentation and Quality Checklist", H2))

story.append(
    table(
        [
            ["Item", "Location"],
            ["Analyst guide", "docs/analyst_guide.pdf"],
            ["API collection", "docs/N100_API.postman_collection.json"],
            ["OpenAPI specification", "docs/openapi.json"],
            ["Performance notes", "output/perf_notes.md"],
            ["Test suite", "tests/"],
            ["Source code", "src/"],
        ],
        [2.5 * inch, 4.5 * inch],
    )
)

story.append(Spacer(1, 20))

story.append(
    p(
        "<b>End of Analyst Guide</b>",
        CENTER,
    )
)


doc = SimpleDocTemplate(
    str(OUTPUT),
    pagesize=A4,
    rightMargin=0.6 * inch,
    leftMargin=0.6 * inch,
    topMargin=0.65 * inch,
    bottomMargin=0.65 * inch,
    title="N100 Financial Intelligence Platform — Analyst Guide",
    author="N100 Financial Intelligence Platform",
)

doc.build(
    story,
    onFirstPage=footer,
    onLaterPages=footer,
)

print(f"Created: {OUTPUT}")