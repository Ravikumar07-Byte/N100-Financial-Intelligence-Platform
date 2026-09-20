"""
Day 40 - Portfolio Statistics API

GET /api/v1/portfolio/stats

Returns P10 through P90 percentile statistics for the
10 core financial KPIs across the 92-company universe.
"""

import sqlite3
from pathlib import Path
from statistics import quantiles

from fastapi import APIRouter, HTTPException


router = APIRouter(
    prefix="/portfolio",
    tags=["Portfolio"],
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = PROJECT_ROOT / "nifty100.db"


CORE_KPIS = {
    "ROE": "return_on_equity_pct",
    "ROCE": "return_on_capital_employed_pct",
    "D/E": "debt_to_equity",
    "FCF": "free_cash_flow_cr",
    "Revenue CAGR 5yr": "revenue_cagr_5yr",
    "PAT CAGR 5yr": "pat_cagr_5yr",
    "EPS CAGR 5yr": "eps_cagr_5yr",
    "Interest Coverage": "interest_coverage",
    "Net Profit Margin": "net_profit_margin_pct",
    "Asset Turnover": "asset_turnover",
}


PERCENTILES = [10, 20, 30, 40, 50, 60, 70, 80, 90]


def get_connection():
    if not DB_PATH.exists():
        raise RuntimeError(f"Database not found: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def percentile_value(values, percentile):
    """
    Calculate a percentile using linear interpolation.

    This avoids requiring NumPy and keeps the API
    self-contained.
    """

    if not values:
        return None

    values = sorted(float(v) for v in values)

    if len(values) == 1:
        return values[0]

    position = (len(values) - 1) * (percentile / 100)

    lower = int(position)
    upper = min(lower + 1, len(values) - 1)

    if lower == upper:
        return values[lower]

    fraction = position - lower

    return (
        values[lower]
        + fraction * (values[upper] - values[lower])
    )


@router.get(
    "/stats",
    summary="Get portfolio percentile statistics",
)
def get_portfolio_stats():

    conn = get_connection()

    try:

        # ----------------------------------------------------------
        # 1. Confirm the canonical 92-company universe
        # ----------------------------------------------------------

        company_rows = conn.execute(
            """
            SELECT id
            FROM companies
            WHERE id IS NOT NULL
            ORDER BY id
            """
        ).fetchall()

        company_ids = [
            row["id"]
            for row in company_rows
        ]

        company_count = len(company_ids)

        if company_count != 92:
            raise HTTPException(
                status_code=500,
                detail=(
                    "Portfolio universe mismatch: "
                    f"expected 92 companies, found {company_count}"
                ),
            )

        # ----------------------------------------------------------
        # 2. Get latest financial-ratio row for every company
        # ----------------------------------------------------------
        #
        # financial_ratios currently contains 91 distinct companies.
        # Therefore the LEFT JOIN intentionally preserves all 92
        # companies in the portfolio universe.
        #
        # The endpoint calculates percentiles only from non-null
        # KPI values.
        # ----------------------------------------------------------

        rows = conn.execute(
            """
            SELECT
                c.id AS company_id,
                c.company_name,

                fr.year,

                fr.return_on_equity_pct,
                fr.return_on_capital_employed_pct,
                fr.debt_to_equity,
                fr.free_cash_flow_cr,
                fr.revenue_cagr_5yr,
                fr.pat_cagr_5yr,
                fr.eps_cagr_5yr,
                fr.interest_coverage,
                fr.net_profit_margin_pct,
                fr.asset_turnover

            FROM companies c

            LEFT JOIN financial_ratios fr
                ON fr.id = (
                    SELECT fr2.id
                    FROM financial_ratios fr2
                    WHERE fr2.company_id = c.id
                    ORDER BY
                        CASE
                            WHEN fr2.year = '2024-03' THEN 0
                            ELSE 1
                        END,
                        fr2.year DESC
                    LIMIT 1
                )

            ORDER BY c.id
            """
        ).fetchall()

        if len(rows) != 92:
            raise HTTPException(
                status_code=500,
                detail=(
                    "Portfolio query did not preserve the "
                    f"92-company universe. Returned {len(rows)} rows."
                ),
            )

        # ----------------------------------------------------------
        # 3. Calculate P10-P90 for each KPI
        # ----------------------------------------------------------

        percentile_table = {}

        coverage = {}

        for kpi_name, column_name in CORE_KPIS.items():

            values = []

            for row in rows:

                value = row[column_name]

                if value is None:
                    continue

                try:
                    values.append(float(value))
                except (TypeError, ValueError):
                    continue

            coverage[kpi_name] = {
                "available_company_count": len(values),
                "unavailable_company_count": (
                    company_count - len(values)
                ),
            }

            percentile_table[kpi_name] = {
                f"P{p}": percentile_value(values, p)
                for p in PERCENTILES
            }

        # ----------------------------------------------------------
        # 4. Return API response
        # ----------------------------------------------------------

        return {
            "company_count": company_count,
            "kpi_count": len(CORE_KPIS),
            "percentile_levels": [
                f"P{p}"
                for p in PERCENTILES
            ],
            "year_basis": "Latest available financial ratio year per company, prioritising 2024-03",
            "kpis": percentile_table,
            "coverage": coverage,
        }

    finally:
        conn.close()
