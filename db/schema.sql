PRAGMA foreign_keys = ON;

-- ============================================================
-- N100 FINANCIAL INTELLIGENCE PLATFORM
-- Sprint 1 - Day 04 / Day 05
-- SQLite Database Schema
-- ============================================================

-- ============================================================
-- 1. COMPANIES
-- ============================================================

CREATE TABLE IF NOT EXISTS companies (
    id TEXT PRIMARY KEY,
    company_logo TEXT,
    company_name TEXT NOT NULL,
    chart_link TEXT,
    about_company TEXT,
    website TEXT,
    nse_profile TEXT,
    bse_profile TEXT,
    face_value REAL,
    book_value REAL,
    roce_percentage REAL,
    roe_percentage REAL
);

-- ============================================================
-- 2. PROFIT AND LOSS
-- ============================================================

CREATE TABLE IF NOT EXISTS profitandloss (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL,
    year TEXT NOT NULL,
    sales INTEGER,
    expenses INTEGER,
    operating_profit REAL,
    opm_percentage REAL,
    other_income INTEGER,
    interest INTEGER,
    depreciation INTEGER,
    profit_before_tax INTEGER,
    tax_percentage REAL,
    net_profit INTEGER,
    eps REAL,
    dividend_payout REAL,

    FOREIGN KEY (company_id)
        REFERENCES companies(id),

    UNIQUE (company_id, year)
);

-- ============================================================
-- 3. BALANCE SHEET
-- ============================================================

CREATE TABLE IF NOT EXISTS balancesheet (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL,
    year TEXT NOT NULL,
    equity_capital REAL,
    reserves INTEGER,
    borrowings INTEGER,
    other_liabilities INTEGER,
    total_liabilities INTEGER,
    fixed_assets INTEGER,
    cwip INTEGER,
    investments INTEGER,
    other_asset INTEGER,
    total_assets INTEGER,

    FOREIGN KEY (company_id)
        REFERENCES companies(id),

    UNIQUE (company_id, year)
);

-- ============================================================
-- 4. CASH FLOW
-- ============================================================

CREATE TABLE IF NOT EXISTS cashflow (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL,
    year TEXT NOT NULL,
    operating_activity REAL,
    investing_activity REAL,
    financing_activity REAL,
    net_cash_flow REAL,

    FOREIGN KEY (company_id)
        REFERENCES companies(id),

    UNIQUE (company_id, year)
);

-- ============================================================
-- 5. ANALYSIS
-- ============================================================

CREATE TABLE IF NOT EXISTS analysis (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL,
    compounded_sales_growth REAL,
    compounded_profit_growth REAL,
    stock_price_cagr REAL,
    roe REAL,

    FOREIGN KEY (company_id)
        REFERENCES companies(id)
);

-- ============================================================
-- 6. DOCUMENTS
-- ============================================================

CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL,
    year TEXT NOT NULL,
    annual_report TEXT,

    FOREIGN KEY (company_id)
        REFERENCES companies(id)
);

-- ============================================================
-- 7. PROS AND CONS
-- ============================================================

CREATE TABLE IF NOT EXISTS prosandcons (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL,
    pros TEXT,
    cons TEXT,

    FOREIGN KEY (company_id)
        REFERENCES companies(id)
);

-- ============================================================
-- 8. SECTORS
-- Supporting dataset: sectors.xlsx
-- ============================================================

CREATE TABLE IF NOT EXISTS sectors (
    id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    broad_sector TEXT NOT NULL,
    sub_sector TEXT,
    index_weight_pct REAL,
    market_cap_category TEXT,

    FOREIGN KEY (company_id)
        REFERENCES companies(id),

    UNIQUE (company_id)
);

-- ============================================================
-- 9. STOCK PRICES
-- Supporting dataset: stock_prices.xlsx
-- ============================================================

CREATE TABLE IF NOT EXISTS stock_prices (
    id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    date TEXT NOT NULL,
    open_price REAL,
    high_price REAL,
    low_price REAL,
    close_price REAL,
    volume INTEGER,
    adjusted_close REAL,

    FOREIGN KEY (company_id)
        REFERENCES companies(id),

    UNIQUE (company_id, date)
);

CREATE INDEX IF NOT EXISTS idx_stock_prices_company
    ON stock_prices(company_id);

CREATE INDEX IF NOT EXISTS idx_stock_prices_date
    ON stock_prices(date);

-- ============================================================
-- 10. MARKET CAP
-- Supporting dataset: market_cap.xlsx
-- ============================================================

CREATE TABLE IF NOT EXISTS market_cap (
    id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    year TEXT NOT NULL,
    market_cap_crore REAL,
    enterprise_value_crore REAL,
    pe_ratio REAL,
    pb_ratio REAL,
    ev_ebitda REAL,
    dividend_yield_pct REAL,

    FOREIGN KEY (company_id)
        REFERENCES companies(id),

    UNIQUE (company_id, year)
);

CREATE INDEX IF NOT EXISTS idx_market_cap_company
    ON market_cap(company_id);

CREATE INDEX IF NOT EXISTS idx_market_cap_year
    ON market_cap(year);

-- ============================================================
-- 11. FINANCIAL RATIOS
-- Supporting dataset: financial_ratios.xlsx
-- ============================================================

CREATE TABLE IF NOT EXISTS financial_ratios (
    id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    year TEXT NOT NULL,

    net_profit_margin_pct REAL,
    operating_profit_margin_pct REAL,
    return_on_equity_pct REAL,
    debt_to_equity REAL,
    interest_coverage REAL,
    asset_turnover REAL,
    free_cash_flow_cr REAL,
    capex_cr REAL,
    earnings_per_share REAL,
    book_value_per_share REAL,
    dividend_payout_ratio_pct REAL,
    total_debt_cr REAL,
    cash_from_operations_cr REAL,

    FOREIGN KEY (company_id)
        REFERENCES companies(id),

    UNIQUE (company_id, year)
);

CREATE INDEX IF NOT EXISTS idx_financial_ratios_company
    ON financial_ratios(company_id);

CREATE INDEX IF NOT EXISTS idx_financial_ratios_year
    ON financial_ratios(year);

-- ============================================================
-- 12. PEER GROUPS
-- Supporting dataset: peer_groups.xlsx
-- ============================================================

CREATE TABLE IF NOT EXISTS peer_groups (
    id INTEGER PRIMARY KEY,
    peer_group_name TEXT NOT NULL,
    company_id TEXT NOT NULL,
    is_benchmark INTEGER NOT NULL DEFAULT 0,

    FOREIGN KEY (company_id)
        REFERENCES companies(id),

    UNIQUE (peer_group_name, company_id)
);

CREATE INDEX IF NOT EXISTS idx_peer_groups_company
    ON peer_groups(company_id);

CREATE INDEX IF NOT EXISTS idx_peer_groups_name
    ON peer_groups(peer_group_name);

-- ============================================================
-- CORE TABLE INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_profitandloss_company
    ON profitandloss(company_id);

CREATE INDEX IF NOT EXISTS idx_profitandloss_year
    ON profitandloss(year);

CREATE INDEX IF NOT EXISTS idx_balancesheet_company
    ON balancesheet(company_id);

CREATE INDEX IF NOT EXISTS idx_balancesheet_year
    ON balancesheet(year);

CREATE INDEX IF NOT EXISTS idx_cashflow_company
    ON cashflow(company_id);

CREATE INDEX IF NOT EXISTS idx_cashflow_year
    ON cashflow(year);

CREATE INDEX IF NOT EXISTS idx_documents_company
    ON documents(company_id);