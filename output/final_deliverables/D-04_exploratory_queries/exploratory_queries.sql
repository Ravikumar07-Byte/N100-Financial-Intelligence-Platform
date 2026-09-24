-- ============================================================
-- N100 FINANCIAL INTELLIGENCE PLATFORM
-- DAY-07 — EXPLORATORY SQL QUERIES
-- ============================================================

-- Q01. Total number of companies
SELECT COUNT(*) AS total_companies
FROM companies;


-- Q02. Companies with their latest available P&L year
SELECT
    c.id AS company_id,
    c.company_name,
    MAX(p.year) AS latest_pnl_year
FROM companies c
LEFT JOIN profitandloss p
    ON c.id = p.company_id
GROUP BY
    c.id,
    c.company_name
ORDER BY
    latest_pnl_year DESC,
    c.company_name;


-- Q03. Companies with fewer than 5 P&L years
SELECT
    c.id AS company_id,
    c.company_name,
    COUNT(DISTINCT p.year) AS pnl_years
FROM companies c
LEFT JOIN profitandloss p
    ON c.id = p.company_id
GROUP BY
    c.id,
    c.company_name
HAVING COUNT(DISTINCT p.year) < 5
ORDER BY
    pnl_years,
    c.company_name;


-- Q04. Top 10 companies by latest net profit
WITH latest_pnl AS (
    SELECT
        p.*
    FROM profitandloss p
    INNER JOIN (
        SELECT
            company_id,
            MAX(year) AS latest_year
        FROM profitandloss
        WHERE year <> 'TTM'
        GROUP BY company_id
    ) latest
        ON p.company_id = latest.company_id
       AND p.year = latest.latest_year
)
SELECT
    c.company_name,
    l.year,
    l.net_profit
FROM latest_pnl l
JOIN companies c
    ON c.id = l.company_id
ORDER BY
    l.net_profit DESC
LIMIT 10;


-- Q05. Top 10 companies by latest operating profit margin
WITH latest_pnl AS (
    SELECT
        p.*
    FROM profitandloss p
    INNER JOIN (
        SELECT
            company_id,
            MAX(year) AS latest_year
        FROM profitandloss
        WHERE year <> 'TTM'
        GROUP BY company_id
    ) latest
        ON p.company_id = latest.company_id
       AND p.year = latest.latest_year
)
SELECT
    c.company_name,
    l.year,
    l.opm_percentage
FROM latest_pnl l
JOIN companies c
    ON c.id = l.company_id
WHERE l.opm_percentage IS NOT NULL
ORDER BY
    l.opm_percentage DESC
LIMIT 10;


-- Q06. Companies with negative latest net profit
WITH latest_pnl AS (
    SELECT
        p.*
    FROM profitandloss p
    INNER JOIN (
        SELECT
            company_id,
            MAX(year) AS latest_year
        FROM profitandloss
        WHERE year <> 'TTM'
        GROUP BY company_id
    ) latest
        ON p.company_id = latest.company_id
       AND p.year = latest.latest_year
)
SELECT
    c.company_name,
    l.year,
    l.net_profit
FROM latest_pnl l
JOIN companies c
    ON c.id = l.company_id
WHERE l.net_profit < 0
ORDER BY
    l.net_profit;


-- Q07. Latest financial ratios for companies
WITH latest_ratios AS (
    SELECT
        r.*
    FROM financial_ratios r
    INNER JOIN (
        SELECT
            company_id,
            MAX(year) AS latest_year
        FROM financial_ratios
        GROUP BY company_id
    ) latest
        ON r.company_id = latest.company_id
       AND r.year = latest.latest_year
)
SELECT
    c.company_name,
    r.year,
    r.net_profit_margin_pct,
    r.return_on_equity_pct,
    r.debt_to_equity,
    r.asset_turnover
FROM latest_ratios r
JOIN companies c
    ON c.id = r.company_id
ORDER BY
    r.return_on_equity_pct DESC;


-- Q08. Companies with high debt-to-equity ratio
SELECT
    c.company_name,
    r.year,
    r.debt_to_equity
FROM financial_ratios r
JOIN companies c
    ON c.id = r.company_id
WHERE r.debt_to_equity IS NOT NULL
  AND r.debt_to_equity > 2
ORDER BY
    r.debt_to_equity DESC;


-- Q09. Companies with positive free cash flow
WITH latest_ratios AS (
    SELECT
        r.*
    FROM financial_ratios r
    INNER JOIN (
        SELECT
            company_id,
            MAX(year) AS latest_year
        FROM financial_ratios
        GROUP BY company_id
    ) latest
        ON r.company_id = latest.company_id
       AND r.year = latest.latest_year
)
SELECT
    c.company_name,
    r.year,
    r.free_cash_flow_cr,
    r.cash_from_operations_cr
FROM latest_ratios r
JOIN companies c
    ON c.id = r.company_id
WHERE r.free_cash_flow_cr > 0
ORDER BY
    r.free_cash_flow_cr DESC;


-- Q10. Stock price coverage by company
SELECT
    c.company_name,
    COUNT(*) AS price_records,
    MIN(s.date) AS first_price_date,
    MAX(s.date) AS last_price_date
FROM companies c
JOIN stock_prices s
    ON c.id = s.company_id
GROUP BY
    c.id,
    c.company_name
ORDER BY
    price_records DESC;

-- ============================================================
-- END OF DAY-07 EXPLORATORY QUERIES
-- ============================================================
