# N100 Financial Intelligence Platform

A financial analytics platform for analyzing financial and qualitative information from **92 companies** in the Nifty 100 dataset.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Technology Stack](#technology-stack)
3. [Project Structure](#project-structure)
4. [Running the Project](#running-the-project)
5. [Database](#database)
6. [ETL Pipeline](#etl-pipeline)
7. [Data Quality](#data-quality)
8. [Automated Testing](#automated-testing)
9. [Streamlit Dashboard](#streamlit-dashboard)
10. [Dashboard Screens](#dashboard-screens)
11. [Valuation Module](#valuation-module)
12. [Sprint 4: Dashboard & Valuation Module](#sprint-4--dashboard--valuation-module)
13. [Integration QA](#integration-qa)
14. [Sprint 4 Retrospective](#sprint-4-retrospective)
15. [Sprint Status](#sprint-status)
16. [Overall Project Deliverables](#overall-project-deliverables)
17. [Data Disclaimer](#data-disclaimer)
18. [Author](#author)

---

## Project Overview

The **N100 Financial Intelligence Platform** is an end-to-end financial analytics system covering:

- Data ingestion and ETL
- Data normalization and validation
- SQLite database management
- Financial ratio analytics
- Company screening
- Peer comparison
- Trend analysis
- Sector analysis
- Capital allocation analysis
- Valuation analytics
- NLP and qualitative intelligence
- PDF financial reports
- Interactive Streamlit dashboard
- FastAPI REST API
- Automated testing and QA

### Dataset

| Item | Detail |
|---|---|
| Companies | 92 |
| Database | SQLite (`nifty100.db`) |
| Dashboard screens | 8 |
| Financial analysis | Multi-year company-level data |
| Technology | Python-based analytics platform |

---

## Technology Stack

| Category | Technologies |
|---|---|
| Programming | Python |
| Data Processing | Pandas, NumPy |
| Excel Processing | OpenPyXL |
| Database | SQLite |
| Analytics | Pandas, NumPy, SciPy |
| Machine Learning | Scikit-learn |
| Visualization | Plotly |
| Dashboard | Streamlit |
| API | FastAPI, Uvicorn |
| Reports | ReportLab |
| Testing | Pytest |
| Development | Git, VS Code |
| Environment | Python Virtual Environment |

---

## Project Structure

```text
N100-Financial-Intelligence-Platform/
│
├── data/
│   ├── raw/                          # Source Excel files
│   └── supporting/                   # Supplementary datasets
│
├── db/
│   └── schema.sql                    # SQLite schema
│
├── src/
│   ├── etl/
│   │   ├── loader.py
│   │   ├── normaliser.py
│   │   ├── validator.py
│   │   └── db_loader.py
│   │
│   ├── analytics/
│   │   ├── ratios.py
│   │   ├── cagr.py
│   │   ├── peer.py
│   │   ├── valuation.py
│   │   ├── clustering.py
│   │   └── cashflow_intelligence.py
│   │
│   ├── screener/
│   │   └── engine.py
│   │
│   ├── nlp/
│   │   ├── parser.py
│   │   └── pros_cons_generator.py
│   │
│   ├── dashboard/
│   │   ├── app.py
│   │   ├── sidebar.py
│   │   ├── pages/
│   │   │   ├── 01_home.py
│   │   │   ├── 02_profile.py
│   │   │   ├── 03_screener.py
│   │   │   ├── 04_peers.py
│   │   │   ├── 05_trends.py
│   │   │   ├── 06_sectors.py
│   │   │   ├── 07_capital.py
│   │   │   └── 08_reports.py
│   │   └── utils/
│   │       ├── db.py
│   │       └── api_client.py
│   │
│   ├── api/
│   │   ├── main.py
│   │   └── routers/
│   │
│   └── reports/                      # PDF report generation
│
├── tests/
│   ├── api/
│   ├── dq/
│   ├── etl/
│   ├── integration/
│   ├── kpi/
│   └── screener/
│
├── notebooks/
│   └── exploratory_queries.sql
├── screenshots/                      # Dashboard screenshots
├── output/
├── reports/
├── scripts/
├── nifty100.db
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## Running the Project

### Activate Virtual Environment (Windows PowerShell)

```powershell
.venv\Scripts\Activate.ps1
```

### Run Dashboard

```powershell
streamlit run src/dashboard/app.py
```

The dashboard opens in the browser at `http://localhost:8501` (Streamlit picks another port if this one is busy).

### Run All Tests

```powershell
python -m pytest -v
```

### Run ETL Tests

```powershell
python -m pytest tests/etl -v
```

### Compile Python Source

```powershell
python -m compileall -q src
```

### Run Valuation Module

```powershell
python src/analytics/valuation.py
```

### Verify Valuation Output

```powershell
python -c "import pandas as pd; df=pd.read_excel('output/valuation_summary.xlsx'); print('Rows:',len(df)); print('Unique companies:',df['company_id'].nunique()); print(df['flag'].value_counts().to_dict())"
```

---

## Database

The platform uses SQLite as its primary database: **`nifty100.db`**.

It contains:

- 92 companies
- Company profile information
- Financial ratios
- Profit & Loss information
- Balance Sheet information
- Cash Flow information
- Sector information
- Supporting financial datasets (stock prices: 5,520 records)

### Database Verification

```text
Companies:               92
Unique Company IDs:      92
Missing Company IDs:     0
Missing Company Names:   0
Foreign-Key Violations:  0
Duplicate Business Keys: 0
```

### Companies Table

```text
id
company_logo
company_name
chart_link
about_company
website
nse_profile
bse_profile
face_value
book_value
roce_percentage
roe_percentage
```

> The `companies` table uses **`id`** as the company identifier (not `company_id`). Verify with `PRAGMA table_info(companies);`.

Exploratory SQL queries are available in `notebooks/exploratory_queries.sql`.

---

## ETL Pipeline

The ETL pipeline loads, normalizes, validates, and stores financial data.

```text
Source Excel Files
        │
        ▼
Data Loading            (loader.py)
        │
        ▼
Normalization           (normaliser.py)
        │
        ▼
Data Validation         (validator.py)
        │
        ▼
Business-Key Validation
        │
        ▼
SQLite Database         (db_loader.py)
        │
        ▼
Audit & Quality Reports (output/)
```

### Audit Outputs

```text
output/load_audit.csv
output/load_audit_day05_reconciled.csv
output/validation_failures.csv
```

---

## Data Quality

Validation checks cover:

- Primary-key uniqueness
- Company/year business-key uniqueness
- Foreign-key integrity
- Financial consistency (balance sheet)
- Sales validation
- Operating margin validation
- Net-cash validation
- Tax-rate validation
- Dividend validation
- EPS validation
- URL validation
- Dataset coverage

### Sprint 1 Validation

| Check | Result |
|---|---:|
| Companies | 92 |
| Unique Company IDs | 92 |
| Missing Company IDs | 0 |
| Missing Company Names | 0 |
| Foreign-Key Violations | 0 |
| Duplicate Business Keys | 0 |
| ETL Tests | 38 passed |

**Known exception:** `JIOFIN` has P&L coverage from 2023-03 to TTM (3 available years). This is retained as a source-data limitation rather than artificially modifying the original data.

---

## Automated Testing

```powershell
python -m pytest tests/etl -v
```

Sprint 1 result: **38 passed** (covers `normalize_year()`, `normalize_ticker()` and related functions).

The project also contains tests for:

- API endpoints
- Data quality rules
- ETL
- CAGR calculations
- Cash-flow KPIs
- Profitability ratios
- Leverage metrics
- Screener engine
- Dashboard/API integration

---

## Streamlit Dashboard

The platform contains an **8-screen Streamlit dashboard**.

```powershell
streamlit run src/dashboard/app.py
```

The application was successfully started and verified during Sprint 4 integration QA.

---

## Dashboard Screens

### 1. Home Dashboard: `01_home.py`

Overview of the Nifty 100 universe with key financial KPIs, sector distribution, company rankings, and year-based analysis.

- Summary KPI cards (average ROE, median P/E, median Debt/Equity, median Revenue CAGR)
- Company statistics and debt-free company count
- Sector distribution
- Quality/company analysis
- Year-based analysis and filtering

![Home Dashboard](screenshots/01_home.png)

### 2. Company Profile: `02_profile.py`

Detailed company-level information, financial performance, and insights.

- Company search
- Company information, sector and company details
- ROE, ROCE, Net Profit Margin, Debt/Equity, Revenue CAGR, Free Cash Flow
- Revenue and Net Profit trends
- ROE/ROCE trend analysis
- Pros and cons
- Missing data handled with safe fallbacks such as `N/A`

![Company Profile](screenshots/02_profile.png)

### 3. Company Screener: `03_screener.py`

Filters companies using financial metrics and predefined presets.

- Filters: ROE, Debt/Equity, FCF, Revenue CAGR, PAT CAGR, OPM, P/E, P/B, Dividend Yield, Interest Coverage Ratio
- Presets: Quality, Value, Growth, Dividend, Debt-Free, Turnaround
- Dynamic result table and result count
- CSV export

![Company Screener](screenshots/03_screener.png)

### 4. Peer Comparison: `04_peers.py`

Compares companies within their peer groups.

- Peer group selection
- Company comparison and KPI comparison
- Radar chart (Plotly `Scatterpolar`)
- Peer-group average comparison
- Benchmark company highlighting

![Peer Comparison](screenshots/04_peers.png)

### 5. Trend Analysis: `05_trends.py`

Historical financial trend visualization.

- Company search
- Multi-metric selection (up to three metrics simultaneously)
- Multi-year (10-year) trend charts
- Year-over-year analysis

![Trend Analysis](screenshots/05_trends.png)

### 6. Sector Analysis: `06_sectors.py`

Sector-level analysis of financial performance.

- Sector selection
- Revenue vs ROE bubble chart
- Market-cap based bubble sizing
- Sub-sector visualization
- Sector median KPI comparison

![Sector Analysis](screenshots/06_sectors.png)

### 7. Capital Allocation Map: `07_capital.py`

Visualizes companies by capital allocation pattern.

- Capital allocation classification
- Interactive Plotly treemap
- Company grouping and pattern-based analysis

![Capital Allocation](screenshots/07_capital.png)

### 8. Annual Reports: `08_reports.py`

Access to available company annual reports.

- Company search
- Annual report year selection
- BSE report links
- Report availability status
- Missing/404 report handling

![Annual Reports](screenshots/08_reports.png)

---

## Valuation Module

Implemented in `src/analytics/valuation.py`.

### Metrics Calculated

- P/E
- P/B
- EV/EBITDA
- Free Cash Flow Yield
- 5-year median P/E
- P/E vs sector median
- Valuation classification

### Valuation Rules

```text
P/E > Sector Median × 1.5   →  Caution
P/E < Sector Median × 0.7   →  Discount
Otherwise                   →  Fair
```

### `output/valuation_summary.xlsx`

```text
Rows: 92
Unique companies: 92
```

Columns:

```text
company_id, company_name, sector, P/E, P/B, EV/EBITDA,
FCF_yield_pct, 5yr_median_PE, PE_vs_sector_median_pct, flag
```

| Flag | Count |
|---|---:|
| Fair | 48 |
| Discount | 30 |
| Caution | 14 |

FCF Yield coverage: **91 available, 1 missing**.

### `output/valuation_flags.csv`

Contains only `Caution` and `Discount` companies.

```text
Rows: 44   (Discount: 30, Caution: 14)
```

---

## Sprint 4 — Dashboard & Valuation Module

**Days:** 22–28
**Sprint Goal:** Build and verify a fully working 8-screen Streamlit dashboard and valuation module for the 92-company dataset.
**Status:** Technical work complete. Demo and team-lead sign-off pending.

| Day | Task | Completed Work |
|---|---|---|
| 22 | Streamlit App Scaffold | `app.py`, 8 pages, shared DB loader, Streamlit config, sidebar navigation, startup verification |
| 23 | Home & Company Profile | KPI tiles, sector visualization, quality analysis, year selector, company search, profile card, ROE/ROCE, trends, pros/cons, missing-ticker handling |
| 24 | Screener & Peer Comparison | 10 screening metrics, presets, dynamic results, CSV export, result count, peer group selection, radar comparison, KPI comparison |
| 25 | Remaining Screens | Trend Analysis, Sector Analysis, Capital Allocation Map, Annual Reports |
| 26 | Valuation Module | FCF yield, sector median P/E, valuation classification, `valuation_summary.xlsx`, `valuation_flags.csv` |
| 27 | Integration QA & Bug Fixes | Compilation, page/core/database/valuation verification, Streamlit launch, missing-data handling |
| 28 | Retrospective & Documentation | README, run instructions, 8-screen descriptions, retrospective, edge cases, QA findings |

### Sprint 4 Deliverables

| Deliverable | Status |
|---|---|
| `src/dashboard/app.py` | ✅ Complete |
| `pages/01_home.py` to `pages/08_reports.py` (8 screens) | ✅ Complete |
| `src/dashboard/utils/db.py` | ✅ Complete |
| `src/analytics/valuation.py` | ✅ Complete |
| `output/valuation_summary.xlsx` | ✅ Complete |
| `output/valuation_flags.csv` | ✅ Complete |
| `README.md` | ✅ Updated |
| Dashboard screenshots | 🔄 Add to `screenshots/` |
| Task board update | ⏳ Pending |

### Sprint 4 Definition of Done

| Exit Criterion | Status |
|---|---|
| All 8 dashboard screens created | ✅ |
| Dashboard starts successfully | ✅ |
| Python source compilation passes | ✅ |
| 92 companies available in database | ✅ |
| Valuation summary contains 92 rows and required columns | ✅ |
| Valuation flags verified | ✅ |
| Screener CSV export implemented | ✅ |
| Missing-data handling implemented | ✅ |
| Integration QA performed | ✅ |
| README documentation updated | ✅ |
| Manual check of all 8 screens with multiple tickers | ⏳ |
| Partial-data ticker behavior confirmed | ⏳ |
| Extreme screener slider behavior confirmed | ⏳ |
| Chart sizing confirmed across screens | ⏳ |
| Company Profile load time measured for 5 tickers | ⏳ |
| Live 8-screen demo with team lead | ⏳ |
| Team-lead sign-off | ⏳ |

---

## Integration QA

Day 27 focused on integration testing and bug fixing.

| Check | Result |
|---|---|
| `python -m compileall -q src` | ✅ Pass |
| All 8 dashboard pages (`01_home.py` to `08_reports.py`) | ✅ Pass |
| Core files (`app.py`, `utils/db.py`, `valuation.py`) | ✅ Pass |
| Project files (`nifty100.db`, valuation outputs) | ✅ Pass |
| Database: 92 companies, 92 unique IDs, 0 missing IDs/names | ✅ Pass |
| Valuation: 92 rows, required columns, valid flags | ✅ Pass |
| Streamlit launch and browser load | ✅ Pass |

Valid flags: `Fair`, `Discount`, `Caution`.

---

## Sprint 4 Retrospective

### UX Decisions

- 8-screen Streamlit structure, one screen per analytical task:

```text
Market Overview → Company Profile → Screening → Peer Comparison
→ Trend Analysis → Sector Analysis → Capital Allocation → Annual Reports
```

- Sidebar navigation for accessing dashboard modules
- Company search/ticker selection for company-specific analysis
- Plotly charts for interactive financial visualization
- KPI cards for quick interpretation
- CSV export on the screener
- Missing values shown as `N/A` or fallback values
- Layout adjusted during Day 27 QA to avoid chart overflow

### Data Edge Cases

- Missing financial metrics and NaN values
- Partial historical data (companies with fewer than 10 years)
- Missing valuation data
- FCF yield missing for 1 of 92 companies
- Missing report URLs and report URLs returning 404/unavailable
- Empty screener results
- Database schema differences between modules
- Partial data must never crash the dashboard

### Database Schema Finding

A QA query attempted to access `company_id` in the `companies` table. The actual identifier column is `id`, confirmed via `PRAGMA table_info(companies);`. This was a query/schema naming mismatch, not database corruption.

### Performance / QA Findings

- Python source compilation passed for the whole `src` directory.
- All 8 dashboard page files and core files exist and compile.
- Streamlit started successfully and opened in the browser, with no startup or import failure.
- A pandas `FutureWarning` about DataFrame concatenation was observed in `01_home.py`. It did not block startup and should be cleaned up.
- Company Profile load time across 5 tickers still needs to be measured.

---

## Sprint Status

| Sprint | Name | Status |
|---|---|---|
| Sprint 1 | Data Foundation | ✅ DONE |
| Sprint 2 | Financial Ratio Engine | ✅ DONE |
| Sprint 3 | Screener & Peer Comparison Engine | ✅ DONE |
| Sprint 4 | Dashboard & Valuation Module | ✅ DONE (demo/sign-off pending) |
| Sprint 5 | Intelligence, NLP & PDF Reports | 🔄 IN PROGRESS |
| Sprint 6 | API Server, Clustering & Final QA | ⏳ TODO |

**Sprint 1 completed:** environment setup, Excel ingestion, normalization, validation, SQLite database, data quality checks, audit outputs, manual review, testing.
**Sprint 2 completed:** financial analytics and ratio-engine development.
**Sprint 3 completed:** screener engine, screening metrics, composite scoring, peer comparison, peer analytics.
**Sprint 5 work:** NLP, qualitative intelligence, cash-flow intelligence, pros/cons generation, PDF reports.
**Sprint 6 planned:** FastAPI integration, API testing, company clustering, productionization, final QA, documentation, deployment.

---

## Overall Project Deliverables

| Area | Status |
|---|---|
| Data Foundation | ✅ DONE |
| ETL Pipeline | ✅ DONE |
| Data Validation | ✅ DONE |
| SQLite Database | ✅ DONE |
| Financial Ratio Engine | ✅ DONE |
| Screener Engine | ✅ DONE |
| Peer Comparison | ✅ DONE |
| Streamlit Dashboard (8 screens) | ✅ DONE |
| Valuation Module and Excel/CSV Outputs | ✅ DONE |
| NLP / Intelligence | 🔄 IN PROGRESS |
| PDF Reports | 🔄 IN PROGRESS |
| FastAPI | 🔄 IN PROGRESS |
| Clustering | 🔄 IN PROGRESS |
| Final QA | ⏳ TODO |

### Current Project Status

```text
N100 FINANCIAL INTELLIGENCE PLATFORM

Sprint 1  — DONE
Sprint 2  — DONE
Sprint 3  — DONE
Sprint 4  — DONE
Sprint 5  — IN PROGRESS
Sprint 6  — TODO
```

The platform currently has a validated financial-data foundation, financial analytics, screening and peer-analysis capabilities, an 8-screen Streamlit dashboard, valuation outputs, and NLP/intelligence, PDF reporting and API layers under continued development.

---

## Data Disclaimer

Some supporting datasets, including stock-price and market-cap data, are simulated or project-provided as specified in the project execution plan. They must not be represented as live or real-time market data.

This platform is intended for educational, analytical, internship, and software-development purposes. Its analytics and valuation outputs should not be interpreted as investment advice or a recommendation to buy or sell securities.

---

## Author

**Ravikumar S**
BE — Computer Science and Engineering

**N100 Financial Intelligence Platform**