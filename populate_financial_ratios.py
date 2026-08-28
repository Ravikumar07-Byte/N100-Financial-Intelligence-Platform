import sqlite3

from src.analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    return_on_equity,
    return_on_capital_employed,
    return_on_assets,
    debt_to_equity,
    interest_coverage_ratio,
    asset_turnover,
)

from src.analytics.cashflow_kpis import (
    free_cash_flow,
    capex_intensity,
    fcf_conversion_rate,
)

from src.analytics.cagr import calculate_cagr


DB_PATH = "nifty100.db"


# ============================================================
# Helpers
# ============================================================

def safe(value):
    """Convert SQLite numeric values to float."""
    if value is None:
        return None

    return float(value)


def is_annual_year(year):
    """
    Accept normal annual financial years such as:
        2019-03
        2024-03
        2012-12

    Reject:
        TTM
        2023-03-15M
        2016-03-9M
    """
    if year is None:
        return False

    year = str(year).strip()

    if year.upper() == "TTM":
        return False

    if len(year) < 7:
        return False

    return year[:4].isdigit()


# ============================================================
# 5-Year CAGR
# ============================================================

def get_cagr(conn, company_id, metric, end_year, window_years=5):
    """
    Calculate CAGR for a specific company-year.

    Example:
        End year = 2024-03
        Window = 5 years

    Uses:
        Start = 2019-03
        End   = 2024-03

    CAGR is calculated only when the exact start year exists.

    Returns:
        CAGR value
        None when the required window is unavailable
    """

    if not is_annual_year(end_year):
        return None

    end_year_number = int(str(end_year)[:4])
    start_year_number = end_year_number - window_years

    start_row = conn.execute(
        f"""
        SELECT year, {metric}
        FROM profitandloss
        WHERE company_id = ?
          AND year != 'TTM'
          AND length(year) >= 7
          AND substr(year,1,4)
              GLOB '[0-9][0-9][0-9][0-9]'
          AND CAST(substr(year,1,4) AS INTEGER) = ?
        ORDER BY year
        LIMIT 1
        """,
        (
            company_id,
            start_year_number,
        ),
    ).fetchone()

    end_row = conn.execute(
        f"""
        SELECT year, {metric}
        FROM profitandloss
        WHERE company_id = ?
          AND year = ?
        LIMIT 1
        """,
        (
            company_id,
            end_year,
        ),
    ).fetchone()

    # Exact start or end year unavailable.
    if start_row is None or end_row is None:
        return None

    start_value = safe(start_row[1])
    end_value = safe(end_row[1])

    # Calculate CAGR using the project's CAGR engine.
    value, flag = calculate_cagr(
        start_value,
        end_value,
        window_years,
        years_available=window_years,
    )

    return value


# ============================================================
# Composite Quality Score
# ============================================================

def calculate_composite(row):
    """
    Calculate a 0-100 style composite quality score.

    Components:
        ROE
        Net Profit Margin
        Debt-to-Equity
        Interest Coverage
        5-year Revenue CAGR

    Missing metrics are excluded.
    """

    scores = []

    roe = row["return_on_equity_pct"]
    npm = row["net_profit_margin_pct"]
    de = row["debt_to_equity"]
    icr = row["interest_coverage"]
    cagr = row["revenue_cagr_5yr"]

    # ROE
    if roe is not None:
        scores.append(
            min(max(roe, 0), 30) / 30 * 100
        )

    # Net Profit Margin
    if npm is not None:
        scores.append(
            min(max(npm, 0), 30) / 30 * 100
        )

    # Debt-to-Equity
    if de is not None:
        scores.append(
            max(
                0,
                100 - min(de, 5) / 5 * 100
            )
        )

    # Interest Coverage
    if icr is not None:
        scores.append(
            min(max(icr, 0), 5) / 5 * 100
        )

    # Revenue CAGR
    if cagr is not None:
        scores.append(
            min(max(cagr, 0), 30) / 30 * 100
        )

    if not scores:
        return None

    return sum(scores) / len(scores)


# ============================================================
# Database
# ============================================================

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row


# ============================================================
# Source rows
# ============================================================

source_rows = conn.execute(
    """
    SELECT
        p.company_id,
        p.year,

        p.sales,
        p.operating_profit,
        p.other_income,
        p.interest,
        p.net_profit,
        p.eps,
        p.dividend_payout,

        b.equity_capital,
        b.reserves,
        b.borrowings,
        b.investments,
        b.total_assets

    FROM profitandloss p

    JOIN balancesheet b
      ON b.company_id = p.company_id
     AND b.year = p.year

    WHERE p.year != 'TTM'
      AND length(p.year) >= 7
      AND substr(p.year,1,4)
          GLOB '[0-9][0-9][0-9][0-9]'

    ORDER BY
        p.company_id,
        CAST(substr(p.year,1,4) AS INTEGER),
        p.year
    """
).fetchall()


print("Source annual rows:", len(source_rows))


# ============================================================
# Clear previous ratio population
# ============================================================

conn.execute(
    "DELETE FROM financial_ratios"
)


# ============================================================
# Insert SQL
# ============================================================

insert_sql = """
INSERT INTO financial_ratios (
    company_id,
    year,

    net_profit_margin_pct,
    operating_profit_margin_pct,
    return_on_equity_pct,
    debt_to_equity,
    interest_coverage,
    asset_turnover,

    free_cash_flow_cr,
    capex_cr,

    earnings_per_share,
    book_value_per_share,
    dividend_payout_ratio_pct,
    total_debt_cr,
    cash_from_operations_cr,

    revenue_cagr_5yr,
    pat_cagr_5yr,
    eps_cagr_5yr,
    composite_quality_score,

    high_leverage_flag,
    icr_label,
    icr_warning_flag,
    net_debt,
    return_on_capital_employed_pct,
    return_on_assets_pct
)
VALUES (
    ?, ?, ?, ?, ?, ?, ?, ?,
    ?, ?, ?, ?, ?, ?, ?,
    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
)
"""


# ============================================================
# Population
# ============================================================

inserted = 0

cagr_populated = {
    "revenue": 0,
    "pat": 0,
    "eps": 0,
}


for source in source_rows:

    company_id = source["company_id"]
    year = source["year"]

    # --------------------------------------------------------
    # P&L
    # --------------------------------------------------------

    sales = safe(source["sales"])

    operating_profit = safe(
        source["operating_profit"]
    )

    other_income = safe(
        source["other_income"]
    )

    interest = safe(
        source["interest"]
    )

    net_profit = safe(
        source["net_profit"]
    )

    eps = safe(
        source["eps"]
    )

    dividend_payout = safe(
        source["dividend_payout"]
    )

    # --------------------------------------------------------
    # Balance Sheet
    # --------------------------------------------------------

    equity_capital = safe(
        source["equity_capital"]
    )

    reserves = safe(
        source["reserves"]
    )

    borrowings = safe(
        source["borrowings"]
    )

    investments = safe(
        source["investments"]
    )

    total_assets = safe(
        source["total_assets"]
    )

    # --------------------------------------------------------
    # Cash Flow
    # --------------------------------------------------------

    cashflow = conn.execute(
        """
        SELECT
            operating_activity,
            investing_activity,
            financing_activity
        FROM cashflow
        WHERE company_id = ?
          AND year = ?
        LIMIT 1
        """,
        (
            company_id,
            year,
        ),
    ).fetchone()

    if cashflow:

        cfo = safe(
            cashflow["operating_activity"]
        )

        cfi = safe(
            cashflow["investing_activity"]
        )

    else:

        cfo = None
        cfi = None

    # --------------------------------------------------------
    # Sector
    # --------------------------------------------------------

    sector_row = conn.execute(
        """
        SELECT broad_sector
        FROM sectors
        WHERE company_id = ?
        LIMIT 1
        """,
        (company_id,),
    ).fetchone()

    broad_sector = (
        sector_row["broad_sector"]
        if sector_row
        else None
    )

    # --------------------------------------------------------
    # Profitability Ratios
    # --------------------------------------------------------

    npm = net_profit_margin(
        net_profit,
        sales,
    )

    opm = operating_profit_margin(
        operating_profit,
        sales,
    )

    roe = return_on_equity(
        net_profit,
        equity_capital,
        reserves,
    )

    roce = return_on_capital_employed(
        operating_profit,
        equity_capital,
        reserves,
        borrowings,
    )

    roa = return_on_assets(
        net_profit,
        total_assets,
    )

    # --------------------------------------------------------
    # Leverage / Efficiency
    # --------------------------------------------------------

    de = debt_to_equity(
        borrowings,
        equity_capital,
        reserves,
    )

    icr = interest_coverage_ratio(
        operating_profit,
        other_income,
        interest,
    )

    turnover = asset_turnover(
        sales,
        total_assets,
    )

    # --------------------------------------------------------
    # Cash Flow KPIs
    # --------------------------------------------------------

    fcf = free_cash_flow(
        cfo,
        cfi,
    )

    capex = (
        abs(cfi)
        if cfi is not None
        else None
    )

    # Calculate for validation/future use.
    _fcf_conversion = fcf_conversion_rate(
        fcf,
        operating_profit,
    )

    _capex_intensity = capex_intensity(
        cfi,
        sales,
    )

    # --------------------------------------------------------
    # Book Value Per Share
    # --------------------------------------------------------

    equity = (
        (equity_capital or 0)
        + (reserves or 0)
    )

    book_value_per_share = (
        equity / equity_capital
        if equity_capital not in (None, 0)
        else None
    )

    # --------------------------------------------------------
    # 5-Year CAGR
    # --------------------------------------------------------

    revenue_cagr = get_cagr(
        conn,
        company_id,
        "sales",
        year,
        5,
    )

    pat_cagr = get_cagr(
        conn,
        company_id,
        "net_profit",
        year,
        5,
    )

    eps_cagr = get_cagr(
        conn,
        company_id,
        "eps",
        year,
        5,
    )

    if revenue_cagr is not None:
        cagr_populated["revenue"] += 1

    if pat_cagr is not None:
        cagr_populated["pat"] += 1

    if eps_cagr is not None:
        cagr_populated["eps"] += 1

    # --------------------------------------------------------
    # Composite Score
    # --------------------------------------------------------

    composite = calculate_composite(
        {
            "return_on_equity_pct": roe,
            "net_profit_margin_pct": npm,
            "debt_to_equity": de,
            "interest_coverage": icr,
            "revenue_cagr_5yr": revenue_cagr,
        }
    )

    # --------------------------------------------------------
    # Flags
    # --------------------------------------------------------

    high_leverage = (
        1
        if (
            de is not None
            and de > 5
            and (broad_sector or "").strip().lower()
                != "financials"
        )
        else 0
    )

    icr_label = (
        "Debt Free"
        if icr is None
        else None
    )

    icr_warning = (
        1
        if (
            icr is not None
            and icr < 1.5
        )
        else 0
    )

    # --------------------------------------------------------
    # Net Debt
    # --------------------------------------------------------

    net_debt_value = (
        (borrowings or 0)
        - (investments or 0)
        if (
            borrowings is not None
            or investments is not None
        )
        else None
    )

    # --------------------------------------------------------
    # Insert
    # --------------------------------------------------------

    conn.execute(
        insert_sql,
        (
            company_id,
            year,

            npm,
            opm,
            roe,
            de,
            icr,
            turnover,

            fcf,
            capex,

            eps,
            book_value_per_share,
            dividend_payout,
            borrowings,
            cfo,

            revenue_cagr,
            pat_cagr,
            eps_cagr,
            composite,

            high_leverage,
            icr_label,
            icr_warning,
            net_debt_value,
            roce,
            roa,
        ),
    )

    inserted += 1


# ============================================================
# Commit
# ============================================================

conn.commit()


# ============================================================
# Final verification
# ============================================================

final_count = conn.execute(
    """
    SELECT COUNT(*)
    FROM financial_ratios
    """
).fetchone()[0]


print()
print("=" * 50)
print("DAY 12 POPULATION COMPLETE")
print("=" * 50)

print(
    "Source annual rows :", len(source_rows)
)

print(
    "Inserted rows      :", inserted
)

print(
    "Final ratio rows   :", final_count
)

print()
print("5-Year CAGR populated:")

print(
    "Revenue CAGR :", cagr_populated["revenue"]
)

print(
    "PAT CAGR     :", cagr_populated["pat"]
)

print(
    "EPS CAGR     :", cagr_populated["eps"]
)

print("=" * 50)


conn.close()