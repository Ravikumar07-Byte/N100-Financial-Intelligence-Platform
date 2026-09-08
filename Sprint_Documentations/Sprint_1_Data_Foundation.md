# SPRINT 1 — DATA FOUNDATION

**Project:** N100 Financial Intelligence Platform  
**Sprint:** Sprint 1 — Data Foundation  
**Duration:** Day 01–07  
**Story Points:** 34 SP  
**Due Date:** 22 Aug 2026  
**Status:** COMPLETED  

---

# 1. SPRINT GOAL

By the end of Sprint 1, the team established the complete data foundation for the N100 Financial Intelligence Platform.

The sprint focused on:

- Setting up the development environment
- Loading the 12 source Excel datasets
- Building the ETL pipeline
- Normalising company and year data
- Implementing data-quality validation
- Creating the SQLite database
- Loading and reconciling financial data
- Performing manual data-quality review
- Establishing the foundation for Sprint 2 and Sprint 3

The primary database created during this sprint was:

`nifty100.db`

---

# 2. SOURCE DATA

The project uses **12 source Excel files**.

## Core Data

1. `analysis.xlsx`
2. `balancesheet.xlsx`
3. `cashflow.xlsx`
4. `companies.xlsx`
5. `documents.xlsx`
6. `profitandloss.xlsx`
7. `prosandcons.xlsx`

## Supporting Data

8. `financial_ratios.xlsx`
9. `market_cap.xlsx`
10. `peer_groups.xlsx`
11. `sectors.xlsx`
12. `stock_prices.xlsx`

> Note: The original Sprint 1 specification referred to a 10-table target, while the project data foundation subsequently includes the `peer_groups` table used by Sprint 3 peer analytics.

---

# 3. DAY 01 — ENVIRONMENT SETUP

## Topic

**Development Environment and Project Structure**

## Objective

Set up the complete development environment required for ETL, database processing, testing, and reporting.

## Work Completed

- Created project repository structure
- Created Python virtual environment
- Installed required Python libraries
- Configured environment variables
- Created initial project configuration
- Prepared Makefile targets
- Initialised Git repository and project workflow

## Key Areas

- Python virtual environment
- Dependency management
- Project directories
- Configuration
- Git version control
- ETL foundation

## Deliverables

- Project directory structure
- Python virtual environment
- Dependency configuration
- Initial configuration files
- Git repository

## Git

Sprint 1 project initialization was committed to Git.

---

# 4. DAY 02 — EXCEL LOADER & DATA NORMALISATION

## Topic

**Excel Loader and Normalisation**

## Objective

Develop a reusable ETL loader capable of reading the source Excel files and normalising inconsistent company identifiers and year formats.

## Work Completed

- Implemented Excel loading logic
- Implemented year normalisation
- Implemented ticker/company identifier normalisation
- Added handling for source-data variations
- Connected source files with database-loading workflow
- Added unit-test coverage

## Key Functions

### `normalize_year()`

Standardises year values into a consistent representation for database processing.

### `normalize_ticker()`

Normalises company/ticker identifiers so that records can be matched consistently across source files.

## Testing

The Sprint 1 target included:

- 35+ ETL unit tests
- 20 tests for `normalize_year`
- 15 tests for `normalize_ticker`

## Deliverables

- `src/etl/loader.py`
- Normalisation functionality
- ETL unit tests
- Excel ingestion workflow

## Git Commit

`[S1][Day02] feat: implement Excel loader and data normalisation`

---

# 5. DAY 03 — SCHEMA VALIDATOR & DATA QUALITY RULES

## Topic

**Data Quality Validation — DQ-01 to DQ-16**

## Objective

Create a validation framework capable of identifying critical and warning-level data-quality problems before and during database loading.

## Work Completed

Implemented the Sprint 1 data-quality validation framework covering:

- Primary-key uniqueness
- Company/year uniqueness
- Foreign-key integrity
- Balance-sheet validation
- Operating-profit-margin cross-check
- Sales validation
- Cash-flow validation
- Tax-rate validation
- Dividend validation
- URL validation
- EPS sign validation
- Year coverage
- Exact duplicate detection
- Required-field validation
- Numeric validity

## DQ Rules

### DQ-01

Primary-key uniqueness.

### DQ-02

`(company_id, year)` uniqueness.

### DQ-03

Foreign-key integrity.

### DQ-04

Balance-sheet balance validation.

### DQ-05

Operating-profit-margin cross-check.

### DQ-06

Positive-sales validation.

### DQ-07

Cash-flow consistency.

### DQ-08

Tax-rate validation.

### DQ-09

Dividend-cap validation.

### DQ-10

URL validation.

### DQ-11

EPS-sign validation.

### DQ-12

Net-cash / related financial validation.

### DQ-13

Year-coverage validation.

### DQ-14

Exact-duplicate validation.

### DQ-15

Required-field validation.

### DQ-16

Numeric-validity validation.

## Severity

The validation framework distinguishes between:

- **CRITICAL**
- **WARNING**

Critical failures were required to be resolved before completion of the data foundation.

## Deliverables

- `src/etl/validator.py`
- DQ validation framework
- Validation failure reporting
- DQ test coverage

## Git Commit

`[S1][Day03] feat: implement data quality validation rules`

---

# 6. DAY 04 — SQLITE DATABASE SCHEMA

## Topic

**SQLite Database Design**

## Objective

Create the relational SQLite database structure required to store the N100 financial datasets.

## Work Completed

- Created SQLite database schema
- Defined primary keys
- Defined foreign keys
- Added relational constraints
- Configured SQLite foreign-key enforcement
- Connected database schema with ETL loader

## Database

`nifty100.db`

## Main Tables

- `companies`
- `profitandloss`
- `balancesheet`
- `cashflow`
- `analysis`
- `documents`
- `prosandcons`
- `sectors`
- `stock_prices`
- `financial_ratios`
- `peer_groups`

## Foreign-Key Enforcement

The database uses:

`PRAGMA foreign_keys = ON`

This ensures that relationships between company master data and dependent financial records are validated by SQLite.

## Deliverables

- `db/schema.sql`
- SQLite database structure
- Primary-key definitions
- Foreign-key definitions
- Database-loading integration

## Git Commit

`[S1][Day04] feat: implement SQLite database schema`

---

# 7. DAY 05 — FULL DATA LOAD & RECONCILIATION

## Topic

**Full ETL Data Load**

## Objective

Load the source Excel datasets into SQLite and reconcile the resulting database records.

## Work Completed

- Loaded core datasets
- Loaded supporting datasets
- Applied normalisation
- Applied database constraints
- Generated loading audit information
- Checked table row counts
- Performed foreign-key validation
- Reconciled loaded data against source data

## Source Categories

### Core

- Companies
- Profit & Loss
- Balance Sheet
- Cash Flow
- Analysis
- Documents
- Pros & Cons

### Supporting

- Financial Ratios
- Market Cap
- Peer Groups
- Sectors
- Stock Prices

## Important Validation

### Companies

Expected master-company count:

`92`

### Foreign Keys

Expected result:

`PRAGMA foreign_key_check` → **0 rows**

## Approximate Source/Data Counts

The Sprint 1 specification recorded approximately:

- Companies = 92
- Profit & Loss ≈ 1276
- Balance Sheet ≈ 1312
- Cash Flow ≈ 1187
- Stock Prices = 5520

These figures represent the Sprint 1 loading/reconciliation targets.

## Deliverables

- `nifty100.db`
- `output/load_audit.csv`
- Full ETL loading workflow
- Data reconciliation results

## Git Commit

`feat: complete Day 05 full data load and reconciliation`

---

# 8. DAY 06 — DATA QUALITY MANUAL REVIEW

## Topic

**Manual Data Quality Review**

## Objective

Perform manual verification of loaded financial data in addition to automated validation.

## Work Completed

- Selected companies for manual review
- Checked company records
- Checked financial-year coverage
- Reviewed companies with limited historical records
- Investigated loader/data issues
- Corrected loader-related issues where required
- Re-ran validation after corrections

## Manual Review

The Sprint 1 exit criteria required:

**5 companies manually reviewed**

The review focused on:

- Company identity
- Financial-year coverage
- Financial values
- Data consistency
- Database records

## Deliverables

- Manual review results
- Corrected ETL behaviour where required
- Revalidated database

## Git Commit

`feat: complete Day 06 data quality manual review`

---

# 9. DAY 07 — SPRINT WRAP-UP & REVIEW

## Topic

**Sprint Validation, Queries and Review**

## Objective

Complete Sprint 1 validation and prepare the data foundation for Sprint 2.

## Work Completed

- Final database validation
- Final ETL test execution
- Exploratory database queries
- Final data-quality verification
- Sprint retrospective
- Sprint documentation
- Git repository update

## Exploratory Queries

The Sprint 1 plan included:

`notebooks/exploratory_queries.sql`

with approximately 10 exploratory queries.

## Final Validation

### Company Count

`SELECT COUNT(*) FROM companies`

Expected:

`92`

### Foreign-Key Check

`PRAGMA foreign_key_check`

Expected:

`0 rows`

### ETL Tests

Expected:

`35+ tests passing`

### Manual Review

Expected:

`5 companies reviewed`

## Deliverables

- `nifty100.db`
- Exploratory SQL queries
- ETL tests
- Sprint documentation
- Sprint retrospective

## Git Commit

`feat: complete Day 07 Sprint 1 wrap-up`

---

# 10. SPRINT 1 DELIVERABLES

The main Sprint 1 deliverables were:

- `nifty100.db`
- `output/load_audit.csv`
- `output/validation_failures.csv`
- `src/etl/loader.py`
- `src/etl/validator.py`
- `src/etl/normaliser.py`
- `db/schema.sql`
- `tests/etl/`
- `notebooks/exploratory_queries.sql`

---

# 11. DATA QUALITY FRAMEWORK

Sprint 1 established the project's data-quality foundation.

## Implemented Validation Areas

| Rule | Validation |
|---|---|
| DQ-01 | Primary-key uniqueness |
| DQ-02 | Company/year uniqueness |
| DQ-03 | Foreign-key integrity |
| DQ-04 | Balance-sheet validation |
| DQ-05 | OPM cross-check |
| DQ-06 | Positive sales |
| DQ-07 | Cash-flow validation |
| DQ-08 | Tax-rate validation |
| DQ-09 | Dividend-cap validation |
| DQ-10 | URL validation |
| DQ-11 | EPS-sign validation |
| DQ-12 | Net-cash / financial validation |
| DQ-13 | Year coverage |
| DQ-14 | Exact duplicates |
| DQ-15 | Required fields |
| DQ-16 | Numeric validity |

---

# 12. DATABASE FOUNDATION

Sprint 1 established the relational data foundation used by the subsequent sprints.

The company master table contains:

**92 companies**

The database uses company relationships through `company_id` and enforces foreign-key integrity.

The resulting database became the source for:

- Sprint 2 financial analytics
- Financial ratio calculations
- CAGR analysis
- Cash-flow analysis
- Capital allocation analysis
- Sprint 3 screeners
- Peer percentile analytics
- Radar charts
- Peer comparison reports

---

# 13. SPRINT 1 EXIT CRITERIA

| Criterion | Status |
|---|---|
| Companies = 92 | PASS |
| Foreign-key check = 0 | PASS |
| DQ framework implemented | PASS |
| Critical data issues addressed | PASS |
| 35+ ETL tests | PASS |
| Manual review of 5 companies | PASS |
| SQLite database established | PASS |
| ETL pipeline established | PASS |
| Sprint review documentation | COMPLETED |

---

# 14. SPRINT 1 GIT HISTORY

Important Sprint 1 commits:

1. `62fc8db` — `[S1] feat: initialize N100 financial intelligence platform`
2. `dbd8d69` — `[S1][Day02] feat: implement Excel loader and data normalisation`
3. `8504f25` — `[S1][Day03] feat: implement data quality validation rules`
4. `300b173` — `[S1][Day04] feat: implement SQLite database schema`
5. `5a94d6d` — `feat: complete Day 05 full data load and reconciliation`
6. `e1e1657` — `feat: complete Day 06 data quality manual review`
7. `6487f3f` — `feat: complete Day 07 Sprint 1 wrap-up`

---

# 15. SPRINT 1 OUTCOME

Sprint 1 successfully established the **Data Foundation** of the N100 Financial Intelligence Platform.

The project moved from raw Excel source files to a structured and validated SQLite database.

The major foundation created during this sprint was:

**Source Excel Files → ETL Loader → Normalisation → DQ Validation → SQLite Database → Validated Financial Data**

This foundation enabled Sprint 2 to focus on financial analytics and Sprint 3 to build the financial screener and peer-analysis capabilities.

---

# 16. DEFINITION OF DONE

Sprint 1 is considered **COMPLETED** when:

- The project environment is configured.
- Source Excel files can be loaded.
- Company identifiers and years are normalised.
- DQ-01 to DQ-16 validation rules are implemented.
- SQLite schema is established.
- Source datasets are loaded.
- `companies` contains 92 companies.
- Foreign-key integrity is verified.
- ETL tests pass.
- Manual review is completed.
- Exploratory queries are available.
- Sprint documentation is completed.
- Sprint work is committed to Git.

---

# FINAL STATUS

## SPRINT 1 — DATA FOUNDATION

**STATUS: COMPLETED**

**Days Completed:** 01–07  
**Story Points:** 34 SP  
**Primary Database:** `nifty100.db`  
**Master Companies:** 92  
**DQ Rules:** 16  
**ETL Tests:** 35+  
**Manual Review:** 5 companies  
**Outcome:** Data foundation established successfully.

