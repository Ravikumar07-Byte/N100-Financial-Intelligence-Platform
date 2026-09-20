"""
Day 40 - Company Documents API

GET /api/v1/companies/{ticker}/documents

Returns annual report links with an is_url_valid boolean flag.
"""

import sqlite3
from pathlib import Path
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException


router = APIRouter(
    prefix="/companies",
    tags=["Company Documents"],
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = PROJECT_ROOT / "nifty100.db"


def get_connection():
    if not DB_PATH.exists():
        raise RuntimeError(f"Database not found: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def is_valid_url(url):
    """
    Validate URL structure without making an external HTTP request.

    This keeps the API deterministic and avoids depending on
    BSE availability during endpoint execution.
    """

    if not url:
        return False

    try:
        parsed = urlparse(str(url).strip())

        return (
            parsed.scheme in {"http", "https"}
            and bool(parsed.netloc)
        )

    except Exception:
        return False


@router.get(
    "/{ticker}/documents",
    summary="Get company annual reports",
)
def get_company_documents(ticker: str):

    ticker = ticker.strip().upper()

    if not ticker:
        raise HTTPException(
            status_code=404,
            detail="Company ticker not found",
        )

    conn = get_connection()

    try:

        # ----------------------------------------------------------
        # 1. Confirm company exists in canonical 92-company universe
        # ----------------------------------------------------------

        company = conn.execute(
            """
            SELECT
                id,
                company_name
            FROM companies
            WHERE UPPER(id) = ?
            LIMIT 1
            """,
            (ticker,),
        ).fetchone()

        if company is None:
            raise HTTPException(
                status_code=404,
                detail=f"Company '{ticker}' not found",
            )

        # ----------------------------------------------------------
        # 2. Get annual reports
        # ----------------------------------------------------------

        rows = conn.execute(
            """
            SELECT
                year,
                annual_report
            FROM documents
            WHERE UPPER(company_id) = ?
            ORDER BY year DESC
            """,
            (ticker,),
        ).fetchall()

        # ----------------------------------------------------------
        # 3. Build response
        # ----------------------------------------------------------

        reports = []

        for row in rows:

            url = row["annual_report"]

            reports.append(
                {
                    "year": row["year"],
                    "annual_report": url,
                    "is_url_valid": is_valid_url(url),
                }
            )

        return {
            "ticker": company["id"],
            "company_name": company["company_name"],
            "document_count": len(reports),
            "documents": reports,
        }

    finally:
        conn.close()
