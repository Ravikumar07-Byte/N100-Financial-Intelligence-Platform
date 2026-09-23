"""
Day 40 - Historical Market Cap / Valuation API
"""

import sqlite3
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter(
    prefix="/market-cap",
    tags=["Market Cap"],
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


@router.get(
    "/{ticker}",
    summary="Get historical valuation multiples for a company",
)
def get_market_cap_history(ticker: str):
    """Get market cap history."""
    conn = get_connection()

    try:
        rows = conn.execute(
            """
            SELECT
                mc.company_id,
                c.company_name,
                mc.year,
                mc.market_cap_crore,
                mc.enterprise_value_crore,
                mc.pe_ratio,
                mc.pb_ratio,
                mc.ev_ebitda,
                mc.dividend_yield_pct
            FROM market_cap mc
            LEFT JOIN companies c
                ON c.id = mc.company_id
            WHERE UPPER(mc.company_id) = UPPER(?)
            ORDER BY mc.year
            """,
            (ticker,),
        ).fetchall()

        if not rows:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown company ticker: {ticker}",
            )

        history = []

        for row in rows:
            history.append(
                {
                    "year": row["year"],
                    "market_cap_crore": row["market_cap_crore"],
                    "enterprise_value_crore": row["enterprise_value_crore"],
                    "pe_ratio": row["pe_ratio"],
                    "pb_ratio": row["pb_ratio"],
                    "ev_ebitda": row["ev_ebitda"],
                    "dividend_yield_pct": row["dividend_yield_pct"],
                }
            )

        return {
            "company_id": rows[0]["company_id"],
            "company_name": rows[0]["company_name"],
            "count": len(history),
            "history": history,
        }

    finally:
        conn.close()
