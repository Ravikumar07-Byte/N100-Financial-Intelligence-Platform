"""
Day 40 - Sector API
"""

import sqlite3
from pathlib import Path
from statistics import median

from fastapi import APIRouter, HTTPException

router = APIRouter(
    prefix="/sectors",
    tags=["Sectors"],
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


def latest_ratio_rows(conn, sector):
    """Latest ratio rows."""
    return conn.execute(
        """
        SELECT
            fr.company_id,
            fr.return_on_equity_pct AS roe,
            fr.debt_to_equity AS de
        FROM financial_ratios fr
        INNER JOIN sectors s
            ON s.company_id = fr.company_id
        WHERE LOWER(s.broad_sector) = LOWER(?)
          AND fr.year = (
              SELECT MAX(fr2.year)
              FROM financial_ratios fr2
              WHERE fr2.company_id = fr.company_id
          )
        """,
        (sector,),
    ).fetchall()


def latest_market_rows(conn, sector):
    """Latest market rows."""
    return conn.execute(
        """
        SELECT
            mc.company_id,
            mc.pe_ratio AS pe
        FROM market_cap mc
        INNER JOIN sectors s
            ON s.company_id = mc.company_id
        WHERE LOWER(s.broad_sector) = LOWER(?)
          AND mc.year = (
              SELECT MAX(mc2.year)
              FROM market_cap mc2
              WHERE mc2.company_id = mc.company_id
          )
        """,
        (sector,),
    ).fetchall()


@router.get(
    "",
    summary="Get sector statistics",
)
def get_sectors():
    """Get sectors."""
    conn = get_connection()

    try:
        sector_rows = conn.execute("""
            SELECT
                broad_sector AS sector,
                COUNT(DISTINCT company_id) AS company_count
            FROM sectors
            GROUP BY broad_sector
            ORDER BY broad_sector
            """).fetchall()

        result = []

        for sector_row in sector_rows:
            sector = sector_row["sector"]

            ratio_rows = latest_ratio_rows(conn, sector)
            market_rows = latest_market_rows(conn, sector)

            roe_values = [row["roe"] for row in ratio_rows if row["roe"] is not None]

            de_values = [row["de"] for row in ratio_rows if row["de"] is not None]

            pe_values = [row["pe"] for row in market_rows if row["pe"] is not None]

            result.append(
                {
                    "sector": sector,
                    "company_count": sector_row["company_count"],
                    "median_roe": median(roe_values) if roe_values else None,
                    "median_pe": median(pe_values) if pe_values else None,
                    "median_de": median(de_values) if de_values else None,
                }
            )

        return {
            "count": len(result),
            "sectors": result,
        }

    finally:
        conn.close()


@router.get(
    "/{sector}/companies",
    summary="Get companies in a sector",
)
def get_sector_companies(sector: str):
    """Get sector companies."""
    conn = get_connection()

    try:
        sector_exists = conn.execute(
            """
            SELECT 1
            FROM sectors
            WHERE LOWER(broad_sector) = LOWER(?)
            LIMIT 1
            """,
            (sector,),
        ).fetchone()

        if sector_exists is None:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown sector: {sector}",
            )

        rows = conn.execute(
            """
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
                fr.debt_to_equity,
                fr.free_cash_flow_cr,
                fr.revenue_cagr_5yr,
                fr.pat_cagr_5yr,
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
            WHERE LOWER(s.broad_sector) = LOWER(?)
            ORDER BY c.company_name
            """,
            (sector,),
        ).fetchall()

        return {
            "sector": sector,
            "count": len(rows),
            "companies": [dict(row) for row in rows],
        }

    finally:
        conn.close()
