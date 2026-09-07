# N100 FINANCIAL INTELLIGENCE PLATFORM
# SPRINT 3 — SCREENER & PEER COMPARISON ENGINE
## Complete Sprint Documentation — Day 15 to Day 21

---

## 1. Sprint Overview

**Sprint:** Sprint 3  
**Sprint Name:** Screener & Peer Comparison Engine  
**Duration:** Day 15 – Day 21  
**Sprint Goal:** Build a fully functional financial screener with six preset filters, custom threshold support, composite quality scoring, peer percentile rankings, radar visualizations, and Excel-based comparison reports.

### Sprint Objective

The main objective of Sprint 3 was to transform the financial ratio and company data prepared in previous sprints into an analyst-oriented financial intelligence layer.

The sprint focused on two major capabilities:

1. **Financial Screener**
   - Six predefined investment screening strategies.
   - Analyst-editable threshold configuration.
   - Financial metric filtering.
   - Composite quality score.
   - Excel export.

2. **Peer Comparison Engine**
   - 11 peer groups.
   - 10 financial metrics.
   - Percentile-based ranking.
   - D/E inverse ranking because lower leverage is better.
   - Peer comparison Excel report.
   - Radar chart visualization.

---

# 2. Day 15 — Filter Engine Core

## Objective

Implement the core screener engine that loads analyst-defined thresholds from:

`config/screener_config.yaml`

and applies those thresholds to the financial universe stored in SQLite.

## Main Work Completed

### Screener Configuration

Created an analyst-editable YAML configuration containing six screening strategies:

- Quality Compounder
- Value Pick
- Growth Accelerator
- Dividend Champion
- Debt-Free Blue Chip
- Turnaround Watch

### Supported Financial Metrics

The screener supports the required filterable metrics:

1. ROE
2. Debt-to-Equity
3. Free Cash Flow
4. Revenue CAGR 5yr
5. PAT CAGR 5yr
6. Operating Profit Margin
7. P/E
8. P/B
9. Dividend Yield
10. Interest Coverage
11. Market Capitalisation
12. Net Profit
13. EPS CAGR
14. Asset Turnover
15. Sales

### Special Business Rules

#### Financial-sector D/E handling

Debt-to-equity filtering is skipped for Financials where the metric is not directly comparable with non-financial companies.

#### Debt-Free ICR handling

Companies labelled `Debt Free` are treated as having infinite effective interest coverage so that they pass any positive ICR minimum threshold.

#### Latest Financial Data

The engine selects the latest available financial record for each company.

#### Historical Data

Historical financial data is used where required for:

- Revenue CAGR
- FCF CAGR
- D/E trend
- Turnaround analysis

## Main File

`src/screener/engine.py`

## Result

The screener engine successfully loads the 92-company master universe and applies the configured screening rules.

---

# 3. Day 16 — Six Preset Screeners

## Objective

Implement and test six predefined financial screening strategies.

## 3.1 Quality Compounder

### Rules

- ROE > 15%
- D/E < 1.0
- FCF > 0
- Revenue CAGR 5yr > 10%

### Result

**23 companies**

---

## 3.2 Value Pick

### Rules

- P/E < 20
- P/B < 3
- D/E < 2
- Dividend Yield > 1%

### Result

**2 companies**

This is a data-constrained result under the specified thresholds.

---

## 3.3 Growth Accelerator

### Rules

- PAT CAGR 5yr > 20%
- Revenue CAGR 5yr > 15%
- D/E < 2

### Result

**19 companies**

---

## 3.4 Dividend Champion

### Rules

- Dividend Yield > 2%
- Dividend Payout < 80%
- FCF > 0

### Result

**30 companies**

---

## 3.5 Debt-Free Blue Chip

### Rules

- D/E = 0
- ROE > 12%
- Sales > 5000 Crore

### Result

**2 companies**

This is a data-constrained result under the specified thresholds.

---

## 3.6 Turnaround Watch

### Rules

- Revenue CAGR 3yr > 10%
- Latest FCF positive
- D/E declining year-over-year

### Result

**33 companies**

---

## Day 16 Summary

| Screener | Companies |
|---|---:|
| Quality Compounder | 23 |
| Value Pick | 2 |
| Growth Accelerator | 19 |
| Dividend Champion | 30 |
| Debt-Free Blue Chip | 2 |
| Turnaround Watch | 33 |

### Important Data Constraint

Value Pick and Debt-Free Blue Chip return fewer than five companies under the exact analyst-defined thresholds.

The thresholds were retained rather than artificially relaxed, and no financial data was fabricated.

---

# 4. Day 17 — Composite Quality Score & Excel Export

## Objective

Develop a composite quality score from 0–100 and generate the main screener Excel report.

## Composite Score Structure

### Profitability — 35%

- ROE — 15%
- ROCE — 10%
- Net Profit Margin — 10%

### Cash Quality — 30%

- FCF CAGR — 15%
- CFO/PAT Ratio — 10%
- FCF Positive Flag — 5%

### Growth — 20%

- Revenue CAGR — 10%
- PAT CAGR — 10%

### Leverage — 15%

- D/E Score — 10%
- Interest Coverage Score — 5%

Total:

**100%**

## Normalisation

Metrics are normalised using P10/P90 winsorisation.

Extreme values are capped at the 10th and 90th percentile before scaling to 0–100.

## Sector-relative Scoring

The score is calculated relative to the company's broad sector so that companies are compared against relevant sector peers.

## FCF CAGR

Historical FCF data is used to calculate a multi-year FCF growth rate where sufficient historical observations are available.

## Excel Export

Generated:

`output/screener_output.xlsx`

The workbook contains six sheets:

1. quality_compounder
2. value_pick
3. growth_accelerator
4. dividend_champion
5. debt_free_blue_chip
6. turnaround_watch

Each sheet contains 20 KPI columns and is sorted by composite score.

Threshold cells are colour-coded according to the screening rules.

---

# 5. Day 18 — Peer Percentile Rankings

## Objective

Build the peer analytics engine using the 11 defined peer groups.

## Peer Groups

1. Automobiles
2. Consumer Finance
3. FMCG
4. IT Services
5. Life Insurance
6. Oil & Gas
7. Pharmaceuticals
8. Power & Utilities
9. Private Banks
10. Public Sector Banks
11. Steel

## Ranking Metrics

The following 10 metrics are ranked:

1. ROE
2. ROCE
3. Net Profit Margin
4. D/E
5. FCF
6. PAT CAGR 5yr
7. Revenue CAGR 5yr
8. EPS CAGR 5yr
9. Interest Coverage
10. Asset Turnover

## Percentile Calculation

SQL-style percentile ranking is used:

`(RANK - 1) / (N - 1)`

This produces percentile values between 0 and 1.

## D/E Special Rule

For D/E, lower is better.

Therefore the percentile is inverted:

`1 - percentile`

This ensures companies with lower leverage receive higher D/E percentile scores.

## SQLite Table

Created:

`peer_percentiles`

Columns:

- company_id
- peer_group_name
- metric
- value
- percentile_rank
- year

## Results

- Peer groups: 11
- Metrics: 10
- Companies with peer assignments and financial data: 55
- Percentile rows: 533
- Invalid percentile values: 0

## Main File

`src/analytics/peer.py`

---

# 6. Day 19 — Radar Charts

## Objective

Generate visual peer comparison radar charts for companies.

## Radar Axes

Each peer radar chart uses eight dimensions:

1. ROE
2. ROCE
3. NPM
4. D/E
5. FCF Score
6. PAT CAGR 5yr
7. Revenue CAGR 5yr
8. Composite Score

## Peer Overlay

For companies assigned to a peer group:

- Company values are displayed as a polygon.
- Peer-group average is displayed as a comparison outline.

## No-peer Companies

Companies without a peer assignment use a Nifty 100 reference.

## Output Directory

`reports/radar_charts/`

## Result

**91 radar PNG files generated**

The master universe contains 92 companies, but SBIN has no available financial data, so it is intentionally skipped.

Therefore:

92 master companies - 1 without financial data = 91 charts.

Validation:

- Expected charts: 91
- Actual charts: 91
- Empty files: 0
- Suspicious files: 0
- Invalid filenames: 0

---

# 7. Day 20 — Peer Comparison Excel Report

## Objective

Generate an Excel workbook for detailed peer comparison.

## Output

`output/peer_comparison.xlsx`

## Workbook Structure

Exactly 11 sheets:

1. Automobiles
2. Consumer Finance
3. FMCG
4. IT Services
5. Life Insurance
6. Oil & Gas
7. Pharmaceuticals
8. Power & Utilities
9. Private Banks
10. Public Sector Banks
11. Steel

## Sheet Columns

Each sheet contains:

- company_id
- company_name
- 20 financial metric columns
- 20 percentile columns

Total:

**42 columns per sheet**

## 20 Metrics

1. ROE
2. ROCE
3. Net Profit Margin
4. Operating Profit Margin
5. D/E
6. Interest Coverage
7. Asset Turnover
8. Free Cash Flow
9. Cash From Operations
10. PAT CAGR 5yr
11. Revenue CAGR 5yr
12. EPS CAGR 5yr
13. Net Profit
14. Sales
15. P/E
16. P/B
17. EV/EBITDA
18. Dividend Yield
19. Dividend Payout
20. Composite Score

## Percentile Colour Coding

- Green: >= 75th percentile
- Yellow: 25th to 75th percentile
- Red: <= 25th percentile

## Benchmark Highlighting

Each peer group has one benchmark company.

The benchmark row is highlighted using a gold/amber background.

## Peer Median

A `Peer Median` summary row is added at the bottom of each peer-group sheet.

## Validation

- Sheets: 11
- Columns per sheet: 42
- Benchmark rows: 11
- Peer Median rows: 11
- Invalid percentile values: 0

---

# 8. Day 21 — Tests & Sprint Review

## Objective

Perform final validation and prepare Sprint 3 for review and closure.

## DQ Tests

The Sprint specification refers to 14 DQ tests.

The current repository contains 15 DQ tests:

- DQ01
- DQ02
- DQ03
- DQ04
- DQ05
- DQ06
- DQ07
- DQ08
- DQ09
- DQ10
- DQ11
- DQ13
- DQ14
- DQ15
- DQ16

All passed.

## Overall Test Result

`132 passed`

No test failures.

---

# 9. Quality Compounder Manual Verification

Top five results:

| Rank | Company | ROE | D/E | Composite Score |
|---:|---|---:|---:|---:|
| 1 | IRCTC | 34.40% | 0.0186 | 89.24 |
| 2 | ADANIPOWER | 48.28% | 0.8023 | 87.51 |
| 3 | TRENT | 36.31% | 0.4309 | 86.23 |
| 4 | LTIM | 22.90% | 0.1035 | 83.46 |
| 5 | INDIGO | 892.57% | 0.0186 | 80.70 |

Validation:

- ROE violations: 0
- D/E violations: 0

Therefore all top five satisfy:

**ROE > 15%**

and

**D/E < 1**

---

# 10. IT Services Peer Verification

IT Services ROE ranking:

| Company | ROE | Percentile |
|---|---:|---:|
| TCS | 50.94% | 1.00 |
| INFY | 29.79% | 0.75 |
| HCLTECH | 23.01% | 0.50 |
| LTIM | 22.90% | 0.25 |
| TECHM | 8.99% | 0.00 |

Result:

**Highest ROE = TCS**

**Highest ROE percentile = TCS**

Therefore:

**PASS**

---

# 11. FMCG Peer Verification

FMCG ROE ranking:

| Company | ROE | Percentile |
|---|---:|---:|
| NESTLEIND | 117.75% | 1.0000 |
| BRITANNIA | 54.15% | 0.8333 |
| ITC | 27.85% | 0.6667 |
| HINDUNILVR | 20.07% | 0.5000 |
| DABUR | 18.36% | 0.3333 |
| TATACONSUM | 7.57% | 0.1667 |
| GODREJCP | -4.45% | 0.0000 |

Result:

**Highest ROE = NESTLEIND**

**Highest ROE percentile = NESTLEIND**

Therefore:

**PASS**

---

# 12. Final Technical Validation

## Tests

- Total tests: 132
- Passed: 132
- Failed: 0

## Excel Reports

### Screener Report

`output/screener_output.xlsx`

- 6 sheets
- 20 KPI columns
- Composite-score ordering
- Threshold formatting

### Peer Report

`output/peer_comparison.xlsx`

- 11 sheets
- 42 columns per sheet
- Percentile colour coding
- Benchmark highlighting
- Peer Median row

## Radar Charts

`reports/radar_charts/`

- 91 PNG files
- 0 empty files

## Peer Percentiles

SQLite table:

`peer_percentiles`

- 533 rows
- 11 peer groups
- 10 metrics
- 0 invalid percentile values

---

# 13. Complete Sprint 3 Deliverables

| Deliverable | Status |
|---|---|
| output/screener_output.xlsx | COMPLETE |
| output/peer_comparison.xlsx | COMPLETE |
| reports/radar_charts/ | COMPLETE |
| peer_percentiles SQLite table | COMPLETE |
| config/screener_config.yaml | COMPLETE |
| src/screener/engine.py | COMPLETE |
| src/analytics/peer.py | COMPLETE |
| Sprint 3 retrospective | COMPLETE |

---

# 14. Git / Version Control

Sprint 3 implementation commits:

- Day 18 — Peer percentile rankings
- Day 19 — Radar charts
- Day 20 — Peer comparison report
- Sprint 3 review documentation

Latest documentation commit:

`9bedfb6 — docs: add Sprint 3 review and retrospective`

The documentation commit was created locally. GitHub push should be completed once network connectivity is available.

---

# 15. Data Constraints

## SBIN Financial Data

The master company universe contains 92 companies.

Financial data is available for 91 companies.

SBIN is the only company without the required financial data.

No artificial financial data was created.

## Screener Constraints

Two screeners return fewer than five companies:

- Value Pick: 2
- Debt-Free Blue Chip: 2

These results are caused by the specified financial thresholds and available data.

The thresholds were intentionally not relaxed just to satisfy the numerical target.

---

# 16. Sprint 3 Retrospective

## What Went Well

- Successfully implemented the core financial screener.
- Implemented six analyst-editable screener presets.
- Implemented composite quality scoring.
- Added sector-relative scoring.
- Generated the screener Excel workbook.
- Implemented peer percentile analytics.
- Added inverse D/E percentile ranking.
- Generated peer comparison Excel workbook.
- Generated radar charts for companies with available financial data.
- Maintained a green regression test suite.
- Successfully validated IT Services and FMCG peer rankings.

## Challenges

- One master company, SBIN, does not have available financial data.
- Value Pick and Debt-Free Blue Chip are data-constrained.
- Some PowerShell verification commands initially had quoting issues.
- Financial coverage varies across source datasets.

## Improvements for Future Work

- Improve source-data coverage.
- Add more targeted analytics tests.
- Improve automated workbook formatting validation.
- Add more peer-ranking validation cases.
- Continue documenting data coverage limitations.
- Improve handling and presentation of data-constrained screeners.

---

# 17. Sprint 3 Definition of Done

| Exit Criterion | Result |
|---|---|
| Six screeners implemented | PASS |
| Each screener between 5–50 | PARTIAL — 4/6 satisfy; 2 data-constrained |
| Peer comparison workbook has exactly 11 sheets | PASS |
| All 11 peer groups included | PASS |
| Peer percentile rankings validated | PASS |
| IT Services spot check | PASS |
| FMCG spot check | PASS |
| DQ tests | PASS — 15/15 |
| Overall tests | PASS — 132/132 |
| Sprint retrospective | COMPLETE |
| Team-lead demo | Pending/To be recorded |
| Team-lead sign-off | Pending/To be recorded |

---

# 18. Sprint 3 Final Status

## Technical Implementation

**COMPLETE**

## Testing

**COMPLETE**

## Deliverables

**COMPLETE**

## Documentation

**COMPLETE**

## Team Review

**Pending team-lead confirmation**

## Final Closure

Sprint 3 is ready for team-lead review and formal closure.

---

# 19. Final Summary

Sprint 3 delivered the financial screener and peer comparison intelligence layer for the N100 Financial Intelligence Platform.

The implementation includes:

- Six financial screening strategies.
- Analyst-editable thresholds.
- Composite quality scoring.
- Sector-relative normalisation.
- Peer percentile ranking across 11 peer groups.
- Ten peer-ranking metrics.
- D/E inverse percentile logic.
- Six-sheet screener Excel report.
- Eleven-sheet peer comparison Excel report.
- Benchmark and percentile visualisation.
- Peer Median summaries.
- Radar chart visualisations.
- SQLite peer percentile storage.
- Automated data-quality and regression testing.

The final technical validation achieved:

**132/132 tests passed**

**15/15 DQ tests passed**

**6 screener sheets**

**11 peer comparison sheets**

**91 radar charts**

**533 peer percentile records**

**11 peer groups**

**0 invalid percentile values**

Sprint 3 technical work is therefore complete and ready for final team-lead review and sign-off.
