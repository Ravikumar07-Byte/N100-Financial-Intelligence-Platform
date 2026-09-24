"""
Day 40 - Screener API

Provides company screening with optional financial filters.
Invalid query parameter values return HTTP 400 as required by Day 40.
"""

import sqlite3
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(
    prefix="/screener",
    tags=["Screener"],
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = PROJECT_ROOT / "nifty100.db"


def get_connection():
    """Get connection."""
    if not DB_PATH.exists():
        raise RuntimeError(f"Database not found: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def parse_optional_float(
    value: str | None,
    parameter_name: str,
) -> float | None:
    """
    Convert an optional query parameter to float.

    Invalid values must return HTTP 400 instead of FastAPI's
    default HTTP 422 response.
    """

    if value is None or value == "":
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid value for {parameter_name}: {value}",
        )


@router.get(
    "",
    summary="Screen and rank companies using financial filters",
)
def screener(
    min_roe: str | None = Query(
        None,
        description="Minimum ROE percentage",
    ),
    max_de: str | None = Query(
        None,
        description="Maximum debt-to-equity ratio",
    ),
    min_fcf: str | None = Query(
        None,
        description="Minimum free cash flow in crore",
    ),
    sector: str | None = Query(
        None,
        description="Broad sector",
    ),
    min_rev_cagr_5yr: str | None = Query(
        None,
        description="Minimum 5-year revenue CAGR percentage",
    ),
    min_pat_cagr_5yr: str | None = Query(
        None,
        description="Minimum 5-year PAT CAGR percentage",
    ),
    min_opm: str | None = Query(
        None,
        description="Minimum operating profit margin percentage",
    ),
    max_pe: str | None = Query(
        None,
        description="Maximum P/E ratio",
    ),
    max_pb: str | None = Query(
        None,
        description="Maximum P/B ratio",
    ),
    min_dividend_yield: str | None = Query(
        None,
        description="Minimum dividend yield percentage",
    ),
    min_icr: str | None = Query(
        None,
        description="Minimum interest coverage ratio",
    ),
):
    """Screener."""
    # ---------------------------------------------------------
    # Explicit conversion so invalid values return HTTP 400
    # ---------------------------------------------------------

    min_roe_value = parse_optional_float(min_roe, "min_roe")
    max_de_value = parse_optional_float(max_de, "max_de")
    min_fcf_value = parse_optional_float(min_fcf, "min_fcf")
    min_rev_cagr_value = parse_optional_float(
        min_rev_cagr_5yr,
        "min_rev_cagr_5yr",
    )
    min_pat_cagr_value = parse_optional_float(
        min_pat_cagr_5yr,
        "min_pat_cagr_5yr",
    )
    min_opm_value = parse_optional_float(
        min_opm,
        "min_opm",
    )
    max_pe_value = parse_optional_float(max_pe, "max_pe")
    max_pb_value = parse_optional_float(max_pb, "max_pb")
    min_dividend_yield_value = parse_optional_float(
        min_dividend_yield,
        "min_dividend_yield",
    )
    min_icr_value = parse_optional_float(
        min_icr,
        "min_icr",
    )

    # ---------------------------------------------------------
    # Parameter validation
    # ---------------------------------------------------------

    numeric_filters = {
        "min_roe": min_roe_value,
        "max_de": max_de_value,
        "min_fcf": min_fcf_value,
        "min_rev_cagr_5yr": min_rev_cagr_value,
        "min_pat_cagr_5yr": min_pat_cagr_value,
        "min_opm": min_opm_value,
        "max_pe": max_pe_value,
        "max_pb": max_pb_value,
        "min_dividend_yield": min_dividend_yield_value,
        "min_icr": min_icr_value,
    }

    for name, value in numeric_filters.items():
        if value is not None and pd.isna(value):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid value for {name}: NaN",
            )

    if max_de_value is not None and max_de_value < 0:
        raise HTTPException(
            status_code=400,
            detail="max_de cannot be negative",
        )

    if min_roe_value is not None and min_roe_value < 0:
        raise HTTPException(
            status_code=400,
            detail="min_roe cannot be negative",
        )

    if min_fcf_value is not None and min_fcf_value < 0:
        raise HTTPException(
            status_code=400,
            detail="min_fcf cannot be negative",
        )

    if max_pe_value is not None and max_pe_value < 0:
        raise HTTPException(
            status_code=400,
            detail="max_pe cannot be negative",
        )

    if max_pb_value is not None and max_pb_value < 0:
        raise HTTPException(
            status_code=400,
            detail="max_pb cannot be negative",
        )

    if min_dividend_yield_value is not None and min_dividend_yield_value < 0:
        raise HTTPException(
            status_code=400,
            detail="min_dividend_yield cannot be negative",
        )

    if min_icr_value is not None and min_icr_value < 0:
        raise HTTPException(
            status_code=400,
            detail="min_icr cannot be negative",
        )

    # ---------------------------------------------------------
    # Database query
    # ---------------------------------------------------------

    conn = get_connection()

    try:
        query = """
            SELECT
                c.id,
                c.company_name,
                s.broad_sector,
                s.sub_sector,
                s.market_cap_category,
                fr.year,
                fr.return_on_equity_pct AS roe_pct,
                fr.return_on_capital_employed_pct AS roce_pct,
                fr.net_profit_margin_pct,
                fr.operating_profit_margin_pct AS opm_pct,
                fr.debt_to_equity,
                fr.free_cash_flow_cr,
                fr.revenue_cagr_5yr,
                fr.pat_cagr_5yr,
                fr.interest_coverage AS icr,
                fr.earnings_per_share,
                mc.pe_ratio,
                mc.pb_ratio,
                mc.ev_ebitda,
                mc.dividend_yield_pct
            FROM companies c

            INNER JOIN sectors s
                ON s.company_id = c.id

            LEFT JOIN financial_ratios fr
                ON fr.company_id = c.id
               AND fr.year = (
                    SELECT MAX(fr2.year)
                    FROM financial_ratios fr2
                    WHERE fr2.company_id = c.id
               )

            LEFT JOIN market_cap mc
                ON mc.company_id = c.id
               AND mc.year = (
                    SELECT MAX(mc2.year)
                    FROM market_cap mc2
                    WHERE mc2.company_id = c.id
               )

            WHERE 1 = 1
        """

        params = []

        # -----------------------------------------------------
        # Filters
        # -----------------------------------------------------

        if min_roe_value is not None:
            query += """
                AND fr.return_on_equity_pct >= ?
            """
            params.append(min_roe_value)

        if max_de_value is not None:
            query += """
                AND fr.debt_to_equity <= ?
            """
            params.append(max_de_value)

        if min_fcf_value is not None:
            query += """
                AND fr.free_cash_flow_cr >= ?
            """
            params.append(min_fcf_value)

        if sector is not None:
            query += """
                AND LOWER(s.broad_sector) = LOWER(?)
            """
            params.append(sector)

        if min_rev_cagr_value is not None:
            query += """
                AND fr.revenue_cagr_5yr >= ?
            """
            params.append(min_rev_cagr_value)

        if min_pat_cagr_value is not None:
            query += """
                AND fr.pat_cagr_5yr >= ?
            """
            params.append(min_pat_cagr_value)

        if min_opm_value is not None:
            query += """
                AND fr.operating_profit_margin_pct >= ?
            """
            params.append(min_opm_value)

        if max_pe_value is not None:
            query += """
                AND mc.pe_ratio <= ?
            """
            params.append(max_pe_value)

        if max_pb_value is not None:
            query += """
                AND mc.pb_ratio <= ?
            """
            params.append(max_pb_value)

        if min_dividend_yield_value is not None:
            query += """
                AND mc.dividend_yield_pct >= ?
            """
            params.append(min_dividend_yield_value)

        if min_icr_value is not None:
            query += """
                AND fr.interest_coverage >= ?
            """
            params.append(min_icr_value)

        # -----------------------------------------------------
        # Ranking
        # -----------------------------------------------------

        query += """
            ORDER BY
                COALESCE(fr.return_on_equity_pct, -999999) DESC,
                c.company_name ASC
        """

        rows = conn.execute(
            query,
            params,
        ).fetchall()

        companies = [dict(row) for row in rows]

        return {
            "count": len(companies),
            "filters": {
                "min_roe": min_roe_value,
                "max_de": max_de_value,
                "min_fcf": min_fcf_value,
                "sector": sector,
                "min_rev_cagr_5yr": min_rev_cagr_value,
                "min_pat_cagr_5yr": min_pat_cagr_value,
                "min_opm": min_opm_value,
                "max_pe": max_pe_value,
                "max_pb": max_pb_value,
                "min_dividend_yield": min_dividend_yield_value,
                "min_icr": min_icr_value,
            },
            "companies": companies,
        }

    finally:
        conn.close()
