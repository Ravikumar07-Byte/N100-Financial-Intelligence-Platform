"""
N100 Financial Intelligence Platform
Sprint 4 - Day 24
Shared Streamlit database access layer.

Supports:
- Company master data
- Financial ratios
- Profit & Loss
- Balance Sheet
- Cash Flow
- Sector classification
- Peer groups
- Market valuation
- Pros & Cons
- Dashboard-wide ratio and valuation queries
- Screener data
- Peer comparison data

All database query functions use Streamlit caching with
a TTL of 600 seconds (10 minutes).
"""

from pathlib import Path
import sqlite3

import pandas as pd
import streamlit as st


# ===================================================================
# DATABASE PATH
# ===================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DB_PATH = PROJECT_ROOT / "nifty100.db"


# ===================================================================
# DATABASE CONNECTION
# ===================================================================

def _get_connection():
    """
    Create and return a SQLite database connection.

    Raises:
        FileNotFoundError:
            If nifty100.db does not exist.
    """

    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DB_PATH}"
        )

    return sqlite3.connect(str(DB_PATH))


# ===================================================================
# COMPANY MASTER
# ===================================================================

@st.cache_data(ttl=600)
def get_companies():
    """
    Return the complete Nifty 100 company master list.

    Returns:
        pandas.DataFrame
    """

    query = """
        SELECT
            id,
            company_logo,
            company_name,
            chart_link,
            about_company,
            website,
            nse_profile,
            bse_profile,
            face_value,
            book_value,
            roce_percentage,
            roe_percentage
        FROM companies
        ORDER BY company_name
    """

    with _get_connection() as conn:

        return pd.read_sql_query(
            query,
            conn
        )


# ===================================================================
# FINANCIAL RATIOS - SINGLE COMPANY
# ===================================================================

@st.cache_data(ttl=600)
def get_ratios(ticker, year=None):
    """
    Return financial ratios for a single company.

    Database years are stored as strings such as:

        2019-03
        2020-03
        2021-03
        2022-03
        2023-03
        2024-03

    Accepted year formats:

        2024
        "2024"
        "2024-03"

    Args:
        ticker: Company NSE ticker / company_id.
        year: Optional financial year.

    Returns:
        pandas.DataFrame
    """

    query = """
        SELECT *
        FROM financial_ratios
        WHERE company_id = ?
    """

    params = [ticker]

    if year is not None:

        year_text = str(year)

        if len(year_text) == 4:

            query += """
                AND substr(year, 1, 4) = ?
            """

            params.append(year_text)

        else:

            query += """
                AND year = ?
            """

            params.append(year_text)

    query += """
        ORDER BY year DESC
    """

    with _get_connection() as conn:

        return pd.read_sql_query(
            query,
            conn,
            params=params
        )


# ===================================================================
# FINANCIAL RATIOS - ALL COMPANIES
# ===================================================================

@st.cache_data(ttl=600)
def get_all_ratios(year=None):
    """
    Return financial ratios for all companies.

    Used by:

    - Home dashboard
    - Screener
    - Sector analysis
    - Peer comparison
    - Capital allocation
    - Valuation

    Args:
        year:
            4-digit year such as 2024
            or complete year such as 2024-03.

    Returns:
        pandas.DataFrame
    """

    query = """
        SELECT *
        FROM financial_ratios
    """

    params = []

    if year is not None:

        year_text = str(year)

        if len(year_text) == 4:

            query += """
                WHERE substr(year, 1, 4) = ?
            """

            params.append(year_text)

        else:

            query += """
                WHERE year = ?
            """

            params.append(year_text)

    query += """
        ORDER BY company_id, year DESC
    """

    with _get_connection() as conn:

        return pd.read_sql_query(
            query,
            conn,
            params=params
        )


# ===================================================================
# PROFIT & LOSS
# ===================================================================

@st.cache_data(ttl=600)
def get_pl(ticker):
    """
    Return Profit & Loss history for one company.

    Used by Company Profile and Trend Analysis.
    """

    query = """
        SELECT *
        FROM profitandloss
        WHERE company_id = ?
        ORDER BY year DESC
    """

    with _get_connection() as conn:

        return pd.read_sql_query(
            query,
            conn,
            params=[ticker]
        )


# ===================================================================
# BALANCE SHEET
# ===================================================================

@st.cache_data(ttl=600)
def get_bs(ticker):
    """
    Return Balance Sheet history for one company.
    """

    query = """
        SELECT *
        FROM balancesheet
        WHERE company_id = ?
        ORDER BY year DESC
    """

    with _get_connection() as conn:

        return pd.read_sql_query(
            query,
            conn,
            params=[ticker]
        )


# ===================================================================
# CASH FLOW
# ===================================================================

@st.cache_data(ttl=600)
def get_cf(ticker):
    """
    Return Cash Flow history for one company.
    """

    query = """
        SELECT *
        FROM cashflow
        WHERE company_id = ?
        ORDER BY date DESC
    """

    with _get_connection() as conn:

        return pd.read_sql_query(
            query,
            conn,
            params=[ticker]
        )


# ===================================================================
# SECTORS
# ===================================================================

@st.cache_data(ttl=600)
def get_sectors():
    """
    Return sector and company classification data.

    Includes:

    - Company ID
    - Company name
    - Broad sector
    - Sub-sector
    - Index weight
    - Market cap category

    Used by:
    - Home dashboard
    - Sector Analysis
    - Capital Allocation
    """

    query = """
        SELECT
            s.id,
            s.company_id,
            c.company_name,
            s.broad_sector,
            s.sub_sector,
            s.index_weight_pct,
            s.market_cap_category
        FROM sectors s
        LEFT JOIN companies c
            ON c.id = s.company_id
        ORDER BY
            s.broad_sector,
            c.company_name
    """

    with _get_connection() as conn:

        return pd.read_sql_query(
            query,
            conn
        )


# ===================================================================
# PEER GROUPS - ALL / SINGLE GROUP
# ===================================================================

@st.cache_data(ttl=600)
def get_peers(group_name=None):
    """
    Return peer-group assignments.

    If group_name is supplied:
        Return only companies in that peer group.

    If group_name is None:
        Return all peer-group assignments.

    This allows Day 24 Peer Comparison to populate
    the peer-group dropdown dynamically.

    Args:
        group_name:
            Peer group name or None.

    Returns:
        pandas.DataFrame
    """

    query = """
        SELECT
            pg.id,
            pg.peer_group_name,
            pg.company_id,
            c.company_name,
            pg.is_benchmark
        FROM peer_groups pg
        LEFT JOIN companies c
            ON c.id = pg.company_id
    """

    params = []

    if group_name is not None:

        query += """
            WHERE pg.peer_group_name = ?
        """

        params.append(group_name)

    query += """
        ORDER BY
            pg.peer_group_name,
            pg.is_benchmark DESC,
            c.company_name
    """

    with _get_connection() as conn:

        return pd.read_sql_query(
            query,
            conn,
            params=params
        )


# ===================================================================
# PEER GROUP NAMES
# ===================================================================

@st.cache_data(ttl=600)
def get_peer_groups():
    """
    Return the list of all available peer groups.

    Used by Day 24 Peer Comparison screen.

    Returns:
        List[str]
    """

    query = """
        SELECT DISTINCT
            peer_group_name
        FROM peer_groups
        WHERE peer_group_name IS NOT NULL
          AND TRIM(peer_group_name) <> ''
        ORDER BY peer_group_name
    """

    with _get_connection() as conn:

        df = pd.read_sql_query(
            query,
            conn
        )

    return df["peer_group_name"].tolist()


# ===================================================================
# PEER GROUP MEMBERS
# ===================================================================

@st.cache_data(ttl=600)
def get_peer_members(group_name):
    """
    Return all companies belonging to one peer group.

    Includes benchmark information.
    """

    query = """
        SELECT
            pg.id,
            pg.peer_group_name,
            pg.company_id,
            c.company_name,
            pg.is_benchmark
        FROM peer_groups pg
        LEFT JOIN companies c
            ON c.id = pg.company_id
        WHERE pg.peer_group_name = ?
        ORDER BY
            pg.is_benchmark DESC,
            c.company_name
    """

    with _get_connection() as conn:

        return pd.read_sql_query(
            query,
            conn,
            params=[group_name]
        )


# ===================================================================
# VALUATION - SINGLE COMPANY
# ===================================================================

@st.cache_data(ttl=600)
def get_valuation(ticker):
    """
    Return market valuation history for one company.

    Includes:

    - Market capitalization
    - Enterprise value
    - P/E
    - P/B
    - EV/EBITDA
    - Dividend Yield
    """

    query = """
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
        WHERE mc.company_id = ?
        ORDER BY mc.year DESC
    """

    with _get_connection() as conn:

        return pd.read_sql_query(
            query,
            conn,
            params=[ticker]
        )


# ===================================================================
# VALUATION - ALL COMPANIES
# ===================================================================

@st.cache_data(ttl=600)
def get_market_valuations(year=None):
    """
    Return market valuation data for all companies.

    Used by:

    - Home Dashboard
    - Screener
    - Sector Analysis
    - Valuation Module
    """

    query = """
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
    """

    params = []

    if year is not None:

        year_text = str(year)

        if len(year_text) == 4:

            query += """
                WHERE substr(mc.year, 1, 4) = ?
            """

            params.append(year_text)

        else:

            query += """
                WHERE mc.year = ?
            """

            params.append(year_text)

    query += """
        ORDER BY
            mc.company_id,
            mc.year DESC
    """

    with _get_connection() as conn:

        return pd.read_sql_query(
            query,
            conn,
            params=params
        )


# ===================================================================
# LATEST VALUATION - ONE ROW PER COMPANY
# ===================================================================

@st.cache_data(ttl=600)
def get_latest_market_valuations(year=None):
    """
    Return one valuation row per company.

    If year is supplied:
        Return that year's valuation.

    If year is not supplied:
        Return the latest available valuation for each company.

    Useful for:
        - Screener
        - Sector bubble chart
        - Dashboard
        - Valuation analysis
    """

    if year is not None:

        year_text = str(year)

        if len(year_text) == 4:
            year_condition = """
                AND substr(mc.year, 1, 4) = ?
            """
            params = [year_text]

        else:
            year_condition = """
                AND mc.year = ?
            """
            params = [year_text]

        query = f"""
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
            WHERE 1=1
            {year_condition}
            ORDER BY mc.company_id
        """

    else:

        query = """
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
            INNER JOIN (
                SELECT
                    company_id,
                    MAX(year) AS latest_year
                FROM market_cap
                GROUP BY company_id
            ) latest
                ON latest.company_id = mc.company_id
               AND latest.latest_year = mc.year
            ORDER BY mc.company_id
        """

        params = []

    with _get_connection() as conn:

        return pd.read_sql_query(
            query,
            conn,
            params=params
        )


# ===================================================================
# PROS & CONS
# ===================================================================

@st.cache_data(ttl=600)
def get_pros_cons(ticker):
    """
    Return pros and cons for one company.
    """

    query = """
        SELECT
            id,
            company_id,
            pros,
            cons
        FROM prosandcons
        WHERE company_id = ?
        ORDER BY id
    """

    with _get_connection() as conn:

        return pd.read_sql_query(
            query,
            conn,
            params=[ticker]
        )


# ===================================================================
# DATABASE HEALTH CHECK
# ===================================================================

@st.cache_data(ttl=600)
def get_database_info():
    """
    Return basic database information.

    Includes:
        - Available tables
        - Company count
    """

    with _get_connection() as conn:

        tables = pd.read_sql_query(
            """
            SELECT
                name
            FROM sqlite_master
            WHERE type = 'table'
            ORDER BY name
            """,
            conn,
        )

        company_count = pd.read_sql_query(
            """
            SELECT
                COUNT(*) AS count
            FROM companies
            """,
            conn,
        )

    return {
        "tables": tables["name"].tolist(),
        "company_count": int(
            company_count.iloc[0]["count"]
        ),
    }


# ===================================================================
# DATABASE TABLE COUNTS
# ===================================================================

@st.cache_data(ttl=600)
def get_table_counts():
    """
    Return row counts for important database tables.

    Useful for dashboard verification and debugging.
    """

    tables = [
        "companies",
        "profitandloss",
        "balancesheet",
        "cashflow",
        "financial_ratios",
        "sectors",
        "peer_groups",
        "market_cap",
        "prosandcons",
    ]

    results = {}

    with _get_connection() as conn:

        for table in tables:

            try:

                query = f"""
                    SELECT COUNT(*) AS count
                    FROM "{table}"
                """

                count_df = pd.read_sql_query(
                    query,
                    conn
                )

                results[table] = int(
                    count_df.iloc[0]["count"]
                )

            except Exception:

                results[table] = 0

    return results