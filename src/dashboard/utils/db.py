"""
N100 Financial Intelligence Platform
Sprint 4 - Day 23
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
"""

from pathlib import Path
import sqlite3

import pandas as pd
import streamlit as st


# -------------------------------------------------------------------
# DATABASE PATH
# -------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = PROJECT_ROOT / "nifty100.db"


def _get_connection():
    """Create a SQLite database connection."""

    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DB_PATH}"
        )

    return sqlite3.connect(str(DB_PATH))


# -------------------------------------------------------------------
# COMPANY MASTER
# -------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_companies():
    """
    Return the complete company master list.
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


# -------------------------------------------------------------------
# FINANCIAL RATIOS - SINGLE COMPANY
# -------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_ratios(ticker, year=None):
    """
    Return financial ratios for one company.

    Database years are stored as strings such as:
        2019-03
        2020-03
        2021-03
        2022-03
        2023-03
        2024-03

    The year parameter can therefore be:
        2024
        "2024"
        "2024-03"
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


# -------------------------------------------------------------------
# FINANCIAL RATIOS - ALL COMPANIES
# -------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_all_ratios(year=None):
    """
    Return financial ratios for all companies.

    Used by the Home Dashboard.

    Year can be:
        2019
        2020
        ...
        2024

    or the complete database year:
        2019-03
        2024-03
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


# -------------------------------------------------------------------
# PROFIT & LOSS
# -------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_pl(ticker):
    """
    Return Profit & Loss history for a company.
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


# -------------------------------------------------------------------
# BALANCE SHEET
# -------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_bs(ticker):
    """
    Return Balance Sheet history for a company.
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


# -------------------------------------------------------------------
# CASH FLOW
# -------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_cf(ticker):
    """
    Return Cash Flow history for a company.
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


# -------------------------------------------------------------------
# SECTORS
# -------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_sectors():
    """
    Return sector and company classification data.
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


# -------------------------------------------------------------------
# PEER GROUPS
# -------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_peers(group_name):
    """
    Return companies belonging to a peer group.
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


# -------------------------------------------------------------------
# VALUATION - SINGLE COMPANY
# -------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_valuation(ticker):
    """
    Return market valuation history for a company.
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


# -------------------------------------------------------------------
# VALUATION - ALL COMPANIES
# -------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_market_valuations(year=None):
    """
    Return market valuation data for all companies.

    Used by the Home Dashboard for:
    - Median P/E
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
        ORDER BY mc.company_id, mc.year DESC
    """

    with _get_connection() as conn:
        return pd.read_sql_query(
            query,
            conn,
            params=params
        )


# -------------------------------------------------------------------
# PROS & CONS
# -------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_pros_cons(ticker):
    """
    Return pros and cons for a company.
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


# -------------------------------------------------------------------
# DATABASE HEALTH CHECK
# -------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_database_info():
    """
    Return basic database information.
    """

    with _get_connection() as conn:

        tables = pd.read_sql_query(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            ORDER BY name
            """,
            conn,
        )

        company_count = pd.read_sql_query(
            """
            SELECT COUNT(*) AS count
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