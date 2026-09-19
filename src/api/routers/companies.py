"""
Companies API endpoints.

Day 39 — API Endpoints — Company Data
"""

from pathlib import Path
import re
import sqlite3
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse


router = APIRouter(
    prefix="/companies",
    tags=["Companies"],
)


# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = PROJECT_ROOT / "nifty100.db"
TEARSHEET_DIR = PROJECT_ROOT / "reports" / "tearsheets"


# ---------------------------------------------------------------------
# Database helper
# ---------------------------------------------------------------------

def get_connection() -> sqlite3.Connection:
    """
    Create a SQLite connection to the main N100 database.
    """
    if not DB_PATH.exists():
        raise RuntimeError(f"Database not found: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def rows_to_dict(rows):
    """Convert sqlite3.Row objects into dictionaries."""
    return [dict(row) for row in rows]


def validate_year(value: Optional[str], parameter_name: str) -> None:
    """Validate YYYY-MM format."""
    if value is None:
        return

    if not re.fullmatch(r"\d{4}-\d{2}", value):
        raise HTTPException(
            status_code=400,
            detail=f"{parameter_name} must use YYYY-MM format",
        )


# ---------------------------------------------------------------------
# GET /api/v1/companies
# ---------------------------------------------------------------------

@router.get("")
def list_companies(
    sector: Optional[str] = Query(
        default=None,
        description="Filter by broad sector",
    ),
    market_cap_category: Optional[str] = Query(
        default=None,
        description="Filter by market cap category",
    ),
    search: Optional[str] = Query(
        default=None,
        description="Partial company name or ticker search",
    ),
):
    """
    Return all 92 companies with basic financial and classification data.
    """

    query = """
        SELECT
            c.id AS id,
            c.company_name,
            s.broad_sector,
            s.sub_sector,
            c.roe_percentage AS roe_pct,
            c.roce_percentage AS roce_pct
        FROM companies c
        LEFT JOIN sectors s
            ON c.id = s.company_id
        WHERE 1 = 1
    """

    params = []

    if sector:
        query += """
            AND LOWER(s.broad_sector) = LOWER(?)
        """
        params.append(sector)

    if market_cap_category:
        query += """
            AND LOWER(s.market_cap_category) = LOWER(?)
        """
        params.append(market_cap_category)

    if search:
        query += """
            AND (
                LOWER(c.id) LIKE LOWER(?)
                OR LOWER(c.company_name) LIKE LOWER(?)
            )
        """
        search_pattern = f"%{search}%"
        params.extend([search_pattern, search_pattern])

    query += " ORDER BY c.company_name"

    conn = get_connection()

    try:
        rows = conn.execute(query, params).fetchall()

        return {
            "count": len(rows),
            "companies": rows_to_dict(rows),
        }

    finally:
        conn.close()


# ---------------------------------------------------------------------
# GET /api/v1/companies/{ticker}
# ---------------------------------------------------------------------

@router.get("/{ticker}")
def get_company_profile(ticker: str):
    """
    Return complete company profile including latest KPIs and sector data.
    """

    ticker = ticker.upper()

    conn = get_connection()

    try:
        company = conn.execute(
            """
            SELECT *
            FROM companies
            WHERE UPPER(id) = ?
            """,
            (ticker,),
        ).fetchone()

        if company is None:
            raise HTTPException(
                status_code=404,
                detail=f"Company ticker '{ticker}' not found",
            )

        sector = conn.execute(
            """
            SELECT
                broad_sector,
                sub_sector,
                index_weight_pct,
                market_cap_category
            FROM sectors
            WHERE company_id = ?
            """,
            (ticker,),
        ).fetchone()

        latest_ratios = conn.execute(
            """
            SELECT *
            FROM financial_ratios
            WHERE company_id = ?
            ORDER BY year DESC
            LIMIT 1
            """,
            (ticker,),
        ).fetchone()

        latest_market = conn.execute(
            """
            SELECT *
            FROM market_cap
            WHERE company_id = ?
            ORDER BY year DESC
            LIMIT 1
            """,
            (ticker,),
        ).fetchone()

        return {
            "company": dict(company),
            "sector": dict(sector) if sector else None,
            "latest_kpis": dict(latest_ratios) if latest_ratios else None,
            "latest_market_data": (
                dict(latest_market)
                if latest_market
                else None
            ),
        }

    finally:
        conn.close()


# ---------------------------------------------------------------------
# GET /api/v1/companies/{ticker}/pl
# ---------------------------------------------------------------------

@router.get("/{ticker}/pl")
def get_profit_and_loss(
    ticker: str,
    from_year: Optional[str] = Query(
        default=None,
        description="Starting year in YYYY-MM format",
    ),
    to_year: Optional[str] = Query(
        default=None,
        description="Ending year in YYYY-MM format",
    ),
):
    """
    Return P&L history for a company.
    """

    validate_year(from_year, "from_year")
    validate_year(to_year, "to_year")

    ticker = ticker.upper()

    conn = get_connection()

    try:
        company_exists = conn.execute(
            """
            SELECT 1
            FROM companies
            WHERE UPPER(id) = ?
            """,
            (ticker,),
        ).fetchone()

        if company_exists is None:
            raise HTTPException(
                status_code=404,
                detail=f"Company ticker '{ticker}' not found",
            )

        query = """
            SELECT *
            FROM profitandloss
            WHERE company_id = ?
        """

        params = [ticker]

        if from_year:
            query += " AND year >= ?"
            params.append(from_year)

        if to_year:
            query += " AND year <= ?"
            params.append(to_year)

        query += " ORDER BY year"

        rows = conn.execute(query, params).fetchall()

        return {
            "ticker": ticker,
            "count": len(rows),
            "history": rows_to_dict(rows),
        }

    finally:
        conn.close()


# ---------------------------------------------------------------------
# GET /api/v1/companies/{ticker}/bs
# ---------------------------------------------------------------------

@router.get("/{ticker}/bs")
def get_balance_sheet(
    ticker: str,
    from_year: Optional[str] = Query(
        default=None,
        description="Starting year in YYYY-MM format",
    ),
    to_year: Optional[str] = Query(
        default=None,
        description="Ending year in YYYY-MM format",
    ),
):
    """
    Return balance sheet history for a company.
    """

    validate_year(from_year, "from_year")
    validate_year(to_year, "to_year")

    ticker = ticker.upper()

    conn = get_connection()

    try:
        company_exists = conn.execute(
            """
            SELECT 1
            FROM companies
            WHERE UPPER(id) = ?
            """,
            (ticker,),
        ).fetchone()

        if company_exists is None:
            raise HTTPException(
                status_code=404,
                detail=f"Company ticker '{ticker}' not found",
            )

        query = """
            SELECT *
            FROM balancesheet
            WHERE company_id = ?
        """

        params = [ticker]

        if from_year:
            query += " AND year >= ?"
            params.append(from_year)

        if to_year:
            query += " AND year <= ?"
            params.append(to_year)

        query += " ORDER BY year"

        rows = conn.execute(query, params).fetchall()

        return {
            "ticker": ticker,
            "count": len(rows),
            "history": rows_to_dict(rows),
        }

    finally:
        conn.close()


# ---------------------------------------------------------------------
# GET /api/v1/companies/{ticker}/cashflow
# ---------------------------------------------------------------------

@router.get("/{ticker}/cashflow")
def get_cash_flow(
    ticker: str,
    from_year: Optional[str] = Query(
        default=None,
        description="Starting year in YYYY-MM format",
    ),
    to_year: Optional[str] = Query(
        default=None,
        description="Ending year in YYYY-MM format",
    ),
):
    """
    Return cash flow history for a company.
    """

    validate_year(from_year, "from_year")
    validate_year(to_year, "to_year")

    ticker = ticker.upper()

    conn = get_connection()

    try:
        company_exists = conn.execute(
            """
            SELECT 1
            FROM companies
            WHERE UPPER(id) = ?
            """,
            (ticker,),
        ).fetchone()

        if company_exists is None:
            raise HTTPException(
                status_code=404,
                detail=f"Company ticker '{ticker}' not found",
            )

        query = """
            SELECT *
            FROM cashflow
            WHERE company_id = ?
        """

        params = [ticker]

        if from_year:
            query += " AND year >= ?"
            params.append(from_year)

        if to_year:
            query += " AND year <= ?"
            params.append(to_year)

        query += " ORDER BY year"

        rows = conn.execute(query, params).fetchall()

        return {
            "ticker": ticker,
            "count": len(rows),
            "history": rows_to_dict(rows),
        }

    finally:
        conn.close()


# ---------------------------------------------------------------------
# GET /api/v1/companies/{ticker}/ratios
# ---------------------------------------------------------------------

@router.get("/{ticker}/ratios")
def get_company_ratios(
    ticker: str,
    year: Optional[str] = Query(
        default=None,
        description="Optional year in YYYY-MM format",
    ),
):
    """
    Return all computed KPIs per year for a company.
    """

    validate_year(year, "year")

    ticker = ticker.upper()

    conn = get_connection()

    try:
        company_exists = conn.execute(
            """
            SELECT 1
            FROM companies
            WHERE UPPER(id) = ?
            """,
            (ticker,),
        ).fetchone()

        if company_exists is None:
            raise HTTPException(
                status_code=404,
                detail=f"Company ticker '{ticker}' not found",
            )

        query = """
            SELECT *
            FROM financial_ratios
            WHERE company_id = ?
        """

        params = [ticker]

        if year:
            query += " AND year = ?"
            params.append(year)

        query += " ORDER BY year"

        rows = conn.execute(query, params).fetchall()

        return {
            "ticker": ticker,
            "count": len(rows),
            "ratios": rows_to_dict(rows),
        }

    finally:
        conn.close()


# ---------------------------------------------------------------------
# GET /api/v1/companies/{ticker}/tearsheet
# ---------------------------------------------------------------------

@router.get("/{ticker}/tearsheet")
def download_tearsheet(ticker: str):
    """
    Download the pre-generated company tearsheet PDF.
    """

    ticker = ticker.upper()

    conn = get_connection()

    try:
        company_exists = conn.execute(
            """
            SELECT 1
            FROM companies
            WHERE UPPER(id) = ?
            """,
            (ticker,),
        ).fetchone()

    finally:
        conn.close()

    if company_exists is None:
        raise HTTPException(
            status_code=404,
            detail=f"Company ticker '{ticker}' not found",
        )

    pdf_path = TEARSHEET_DIR / f"{ticker}_tearsheet.pdf"

    if not pdf_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Tearsheet PDF not found for ticker '{ticker}'",
        )

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"{ticker}_tearsheet.pdf",
    )