PRAGMA foreign_keys = ON;

-- ============================================================
-- N100 FINANCIAL INTELLIGENCE PLATFORM
-- Sprint 1 - Day 04
-- SQLite Database Schema
-- ============================================================

-- ============================================================
-- 1. COMPANIES
-- Master company reference table
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
-- One financial record per company and financial year
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
-- Supplementary/reference table
-- ============================================================

CREATE TABLE IF NOT EXISTS sectors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    sector_name TEXT NOT NULL,
    industry_name TEXT,

    FOREIGN KEY (company_id)
        REFERENCES companies(id),

    UNIQUE (company_id)
);

-- ============================================================
-- 9. STOCK PRICES
-- Supplementary market-data table
-- ============================================================

CREATE TABLE IF NOT EXISTS stock_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    trade_date TEXT NOT NULL,
    open_price REAL,
    high_price REAL,
    low_price REAL,
    close_price REAL,
    volume INTEGER,

    FOREIGN KEY (company_id)
        REFERENCES companies(id),

    UNIQUE (company_id, trade_date)
);

-- ============================================================
-- 10. FINANCIAL RATIOS
-- Derived financial metrics
-- ============================================================

CREATE TABLE IF NOT EXISTS financial_ratios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    year TEXT NOT NULL,

    current_ratio REAL,
    debt_to_equity REAL,
    return_on_equity REAL,
    return_on_capital_employed REAL,
    net_profit_margin REAL,
    operating_profit_margin REAL,
    interest_coverage_ratio REAL,
    asset_turnover_ratio REAL,

    FOREIGN KEY (company_id)
        REFERENCES companies(id),

    UNIQUE (company_id, year)
);

-- ============================================================
-- 11. PEER GROUPS
-- Company peer-group classification
-- ============================================================

CREATE TABLE IF NOT EXISTS peer_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    peer_group TEXT NOT NULL,

    FOREIGN KEY (company_id)
        REFERENCES companies(id),

    UNIQUE (company_id, peer_group)
);

-- ============================================================
-- INDEXES
-- Improve common company/year lookups
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

CREATE INDEX IF NOT EXISTS idx_stock_prices_company
    ON stock_prices(company_id);

CREATE INDEX IF NOT EXISTS idx_financial_ratios_company
    ON financial_ratios(company_id);

CREATE INDEX IF NOT EXISTS idx_peer_groups_company
    ON peer_groups(company_id);