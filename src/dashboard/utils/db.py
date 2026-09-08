"""
N100 Financial Intelligence Platform
Sprint 4 - Day 22
Shared Streamlit database access layer.
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
    """Create a read/write SQLite connection."""
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
        return pd.read_sql_query(query, conn)


# -------------------------------------------------------------------
# FINANCIAL RATIOS
# -------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_ratios(ticker, year=None):
    """
    Return financial ratios for a company.

    If year is supplied, return that year.
    Otherwise return all available years.
    """

    query = """
        SELECT *
        FROM financial_ratios
        WHERE company_id = ?
    """

    params = [ticker]

    if year is not None:
        query += " AND year = ?"
        params.append(int(year))

    query += " ORDER BY year DESC"

    with _get_connection() as conn:
        return pd.read_sql_query(query, conn, params=params)


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
        return pd.read_sql_query(query, conn, params=[ticker])


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
        return pd.read_sql_query(query, conn, params=[ticker])


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
        return pd.read_sql_query(query, conn, params=[ticker])


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
        return pd.read_sql_query(query, conn)


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
# VALUATION
# -------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_valuation(ticker):
    """
    Return latest market valuation data for a company.
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
# DATABASE HEALTH CHECK
# -------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_database_info():
    """
    Basic database information used by the scaffold.
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
            "SELECT COUNT(*) AS count FROM companies",
            conn,
        )

    return {
        "tables": tables["name"].tolist(),
        "company_count": int(company_count.iloc[0]["count"]),
    }
