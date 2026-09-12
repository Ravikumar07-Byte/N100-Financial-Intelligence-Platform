"""
N100 Financial Intelligence Platform
Sprint 4 - Day 27
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
- Home dashboard data
- Company Profile historical data
- Latest company metrics

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

    Database years may be stored as:
        2019
        2019-03
        2019-03-31
        etc.

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
                AND substr(CAST(year AS TEXT), 1, 4) = ?
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
    - Home
    - Screener
    - Sector Analysis
    - Peer Comparison
    - Capital Allocation
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
                WHERE substr(CAST(year AS TEXT), 1, 4) = ?
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

    Used by:
    - Company Profile
    - Trend Analysis
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
                WHERE substr(CAST(mc.year AS TEXT), 1, 4) = ?
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
    """

    if year is not None:

        year_text = str(year)

        if len(year_text) == 4:

            year_condition = """
                AND substr(CAST(mc.year AS TEXT), 1, 4) = ?
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


# ===================================================================
# DAY 27 - HOME DASHBOARD FINANCIAL DATA
# ===================================================================

@st.cache_data(ttl=600)
def get_home_financial_data(year=None):
    """
    Return financial ratio data for the Home dashboard.

    Handles different database year formats such as:
        2020
        2020-03
        2020-03-31

    Args:
        year:
            Optional four-digit financial year.

    Returns:
        pandas.DataFrame
    """

    query = """
        SELECT
            company_id,
            year,
            net_profit_margin_pct,
            operating_profit_margin_pct,
            return_on_equity_pct,
            debt_to_equity,
            interest_coverage,
            free_cash_flow_cr,
            revenue_cagr_5yr,
            pat_cagr_5yr,
            composite_quality_score,
            return_on_capital_employed_pct,
            return_on_assets_pct
        FROM financial_ratios
    """

    params = []

    if year is not None:

        query += """
            WHERE substr(CAST(year AS TEXT), 1, 4) = ?
        """

        params.append(str(year))

    query += """
        ORDER BY
            company_id,
            year DESC
    """

    with _get_connection() as conn:

        return pd.read_sql_query(
            query,
            conn,
            params=params
        )


# ===================================================================
# DAY 27 - HOME MARKET DATA
# ===================================================================

@st.cache_data(ttl=600)
def get_market_data_for_year(year=None):
    """
    Return market valuation data for a selected year.

    Used by:
        - Home
        - Screener
        - Sector Analysis
        - Valuation
    """

    query = """
        SELECT
            company_id,
            year,
            market_cap_crore,
            enterprise_value_crore,
            pe_ratio,
            pb_ratio,
            ev_ebitda,
            dividend_yield_pct
        FROM market_cap
    """

    params = []

    if year is not None:

        query += """
            WHERE substr(CAST(year AS TEXT), 1, 4) = ?
        """

        params.append(str(year))

    query += """
        ORDER BY
            company_id,
            year DESC
    """

    with _get_connection() as conn:

        return pd.read_sql_query(
            query,
            conn,
            params=params
        )


# ===================================================================
# DAY 27 - COMPANY PROFILE COMPLETE HISTORY
# ===================================================================

@st.cache_data(ttl=600)
def get_profile_history(ticker):
    """
    Return complete financial history for one company.

    Combines:
        companies
        sectors
        profitandloss
        financial_ratios
        market_cap

    IMPORTANT:
    Financial records are matched using company_id + the
    four-digit year extracted from each source.

    This prevents failures caused by differences such as:

        2024
        2024-03
        2024-03-31

    Returns:
        pandas.DataFrame
    """

    # ---------------------------------------------------------------
    # Load each dataset independently.
    # This is more reliable than joining all three tables directly.
    # ---------------------------------------------------------------

    company_query = """
        SELECT
            id AS company_id,
            company_name
        FROM companies
        WHERE UPPER(id) = UPPER(?)
        LIMIT 1
    """

    sector_query = """
        SELECT
            company_id,
            broad_sector,
            sub_sector
        FROM sectors
        WHERE UPPER(company_id) = UPPER(?)
    """

    pl_query = """
        SELECT
            company_id,
            year,
            sales,
            net_profit,
            operating_profit,
            opm_percentage,
            eps,
            dividend_payout
        FROM profitandloss
        WHERE UPPER(company_id) = UPPER(?)
    """

    ratio_query = """
        SELECT
            company_id,
            year,
            net_profit_margin_pct,
            operating_profit_margin_pct,
            return_on_equity_pct,
            return_on_capital_employed_pct,
            return_on_assets_pct,
            debt_to_equity,
            interest_coverage,
            free_cash_flow_cr,
            revenue_cagr_5yr,
            pat_cagr_5yr,
            composite_quality_score
        FROM financial_ratios
        WHERE UPPER(company_id) = UPPER(?)
    """

    market_query = """
        SELECT
            company_id,
            year,
            market_cap_crore,
            pe_ratio,
            pb_ratio,
            ev_ebitda,
            dividend_yield_pct
        FROM market_cap
        WHERE UPPER(company_id) = UPPER(?)
    """

    with _get_connection() as conn:

        company_df = pd.read_sql_query(
            company_query,
            conn,
            params=[ticker]
        )

        sector_df = pd.read_sql_query(
            sector_query,
            conn,
            params=[ticker]
        )

        pl_df = pd.read_sql_query(
            pl_query,
            conn,
            params=[ticker]
        )

        ratio_df = pd.read_sql_query(
            ratio_query,
            conn,
            params=[ticker]
        )

        market_df = pd.read_sql_query(
            market_query,
            conn,
            params=[ticker]
        )

    # ---------------------------------------------------------------
    # Company existence check
    # ---------------------------------------------------------------

    if company_df.empty:

        return pd.DataFrame()

    # ---------------------------------------------------------------
    # Normalize year helper
    # ---------------------------------------------------------------

    def normalize_year(series):

        return pd.to_numeric(
            series.astype(str).str.extract(
                r"(\d{4})"
            )[0],
            errors="coerce"
        )

    # ---------------------------------------------------------------
    # Normalize Profit & Loss
    # ---------------------------------------------------------------

    if not pl_df.empty:

        pl_df = pl_df.copy()

        pl_df["year"] = normalize_year(
            pl_df["year"]
        )

        numeric_columns = [
            "sales",
            "net_profit",
            "operating_profit",
            "opm_percentage",
            "eps",
            "dividend_payout",
        ]

        for col in numeric_columns:

            if col in pl_df.columns:

                pl_df[col] = pd.to_numeric(
                    pl_df[col],
                    errors="coerce"
                )

        # If duplicate rows exist for the same year,
        # keep the last available row.
        pl_df = (
            pl_df
            .dropna(subset=["year"])
            .sort_values("year")
            .drop_duplicates(
                subset=["year"],
                keep="last"
            )
        )

    # ---------------------------------------------------------------
    # Normalize Financial Ratios
    # ---------------------------------------------------------------

    if not ratio_df.empty:

        ratio_df = ratio_df.copy()

        ratio_df["year"] = normalize_year(
            ratio_df["year"]
        )

        numeric_columns = [
            "net_profit_margin_pct",
            "operating_profit_margin_pct",
            "return_on_equity_pct",
            "return_on_capital_employed_pct",
            "return_on_assets_pct",
            "debt_to_equity",
            "interest_coverage",
            "free_cash_flow_cr",
            "revenue_cagr_5yr",
            "pat_cagr_5yr",
            "composite_quality_score",
        ]

        for col in numeric_columns:

            if col in ratio_df.columns:

                ratio_df[col] = pd.to_numeric(
                    ratio_df[col],
                    errors="coerce"
                )

        ratio_df = (
            ratio_df
            .dropna(subset=["year"])
            .sort_values("year")
            .drop_duplicates(
                subset=["year"],
                keep="last"
            )
        )

    # ---------------------------------------------------------------
    # Normalize Market Data
    # ---------------------------------------------------------------

    if not market_df.empty:

        market_df = market_df.copy()

        market_df["year"] = normalize_year(
            market_df["year"]
        )

        numeric_columns = [
            "market_cap_crore",
            "pe_ratio",
            "pb_ratio",
            "ev_ebitda",
            "dividend_yield_pct",
        ]

        for col in numeric_columns:

            if col in market_df.columns:

                market_df[col] = pd.to_numeric(
                    market_df[col],
                    errors="coerce"
                )

        market_df = (
            market_df
            .dropna(subset=["year"])
            .sort_values("year")
            .drop_duplicates(
                subset=["year"],
                keep="last"
            )
        )

    # ---------------------------------------------------------------
    # Prepare base financial-history table
    # ---------------------------------------------------------------

    if not pl_df.empty:

        result = pl_df.copy()

    elif not ratio_df.empty:

        result = ratio_df[
            ["company_id", "year"]
        ].copy()

    elif not market_df.empty:

        result = market_df[
            ["company_id", "year"]
        ].copy()

    else:

        return pd.DataFrame()

    # ---------------------------------------------------------------
    # Merge Financial Ratios
    # ---------------------------------------------------------------

    if not ratio_df.empty:

        ratio_columns = [
            "year",
            "net_profit_margin_pct",
            "operating_profit_margin_pct",
            "return_on_equity_pct",
            "return_on_capital_employed_pct",
            "return_on_assets_pct",
            "debt_to_equity",
            "interest_coverage",
            "free_cash_flow_cr",
            "revenue_cagr_5yr",
            "pat_cagr_5yr",
            "composite_quality_score",
        ]

        ratio_columns = [
            col
            for col in ratio_columns
            if col in ratio_df.columns
        ]

        result = result.merge(
            ratio_df[ratio_columns],
            on="year",
            how="outer",
            suffixes=("", "_ratio")
        )

    # ---------------------------------------------------------------
    # Merge Market Data
    # ---------------------------------------------------------------

    if not market_df.empty:

        market_columns = [
            "year",
            "market_cap_crore",
            "pe_ratio",
            "pb_ratio",
            "ev_ebitda",
            "dividend_yield_pct",
        ]

        market_columns = [
            col
            for col in market_columns
            if col in market_df.columns
        ]

        result = result.merge(
            market_df[market_columns],
            on="year",
            how="outer",
            suffixes=("", "_market")
        )

    # ---------------------------------------------------------------
    # Add company details
    # ---------------------------------------------------------------

    result["company_id"] = ticker

    result["company_name"] = (
        company_df.iloc[0]["company_name"]
    )

    # ---------------------------------------------------------------
    # Add sector information
    # ---------------------------------------------------------------

    if not sector_df.empty:

        result["broad_sector"] = (
            sector_df.iloc[0]["broad_sector"]
        )

        result["sub_sector"] = (
            sector_df.iloc[0]["sub_sector"]
        )

    else:

        result["broad_sector"] = None
        result["sub_sector"] = None

    # ---------------------------------------------------------------
    # Clean duplicate financial columns if created
    # ---------------------------------------------------------------

    for base_column in [
        "net_profit_margin_pct",
        "operating_profit_margin_pct",
        "return_on_equity_pct",
        "return_on_capital_employed_pct",
        "return_on_assets_pct",
        "debt_to_equity",
        "interest_coverage",
        "free_cash_flow_cr",
        "revenue_cagr_5yr",
        "pat_cagr_5yr",
        "composite_quality_score",
    ]:

        duplicate_column = f"{base_column}_ratio"

        if duplicate_column in result.columns:

            if base_column in result.columns:

                result[base_column] = (
                    result[base_column]
                    .combine_first(
                        result[duplicate_column]
                    )
                )

            else:

                result[base_column] = (
                    result[duplicate_column]
                )

            result.drop(
                columns=[duplicate_column],
                inplace=True
            )

    # ---------------------------------------------------------------
    # Normalize final numeric columns
    # ---------------------------------------------------------------

    numeric_columns = [
        "sales",
        "net_profit",
        "operating_profit",
        "opm_percentage",
        "eps",
        "dividend_payout",
        "net_profit_margin_pct",
        "operating_profit_margin_pct",
        "return_on_equity_pct",
        "return_on_capital_employed_pct",
        "return_on_assets_pct",
        "debt_to_equity",
        "interest_coverage",
        "free_cash_flow_cr",
        "revenue_cagr_5yr",
        "pat_cagr_5yr",
        "composite_quality_score",
        "market_cap_crore",
        "pe_ratio",
        "pb_ratio",
        "ev_ebitda",
        "dividend_yield_pct",
    ]

    for col in numeric_columns:

        if col in result.columns:

            result[col] = pd.to_numeric(
                result[col],
                errors="coerce"
            )

    # ---------------------------------------------------------------
    # Final year cleanup
    # ---------------------------------------------------------------

    result["year"] = pd.to_numeric(
        result["year"],
        errors="coerce"
    )

    result = (
        result
        .dropna(subset=["year"])
        .sort_values("year")
        .drop_duplicates(
            subset=["year"],
            keep="last"
        )
        .reset_index(drop=True)
    )

    # Convert year to integer where possible
    result["year"] = result["year"].astype(int)

    return result


# ===================================================================
# DAY 27 - LATEST PROFILE METRICS
# ===================================================================

@st.cache_data(ttl=600)
def get_latest_profile_metrics(ticker):
    """
    Return the latest available financial metrics for one company.

    The function prefers the latest year with financial-ratio data.
    """

    history = get_profile_history(ticker)

    if history.empty:
        return {}

    # ---------------------------------------------------------------
    # Prefer latest year containing ratio information
    # ---------------------------------------------------------------

    ratio_columns = [
        "return_on_equity_pct",
        "return_on_capital_employed_pct",
        "net_profit_margin_pct",
        "debt_to_equity",
        "revenue_cagr_5yr",
        "free_cash_flow_cr",
    ]

    available_ratio_columns = [
        col
        for col in ratio_columns
        if col in history.columns
    ]

    if available_ratio_columns:

        ratio_history = history[
            history[available_ratio_columns]
            .notna()
            .any(axis=1)
        ]

    else:

        ratio_history = history

    if not ratio_history.empty:

        latest = ratio_history.sort_values(
            "year"
        ).iloc[-1]

    else:

        latest = history.sort_values(
            "year"
        ).iloc[-1]

    return latest.to_dict()


# ===================================================================
# DAY 27 - PROFILE PROS & CONS
# ===================================================================

@st.cache_data(ttl=600)
def get_company_pros_cons(ticker):
    """
    Return the first pros-and-cons record for one company.

    Returns:
        dict
    """

    query = """
        SELECT
            company_id,
            pros,
            cons
        FROM prosandcons
        WHERE UPPER(company_id) = UPPER(?)
        ORDER BY id
        LIMIT 1
    """

    with _get_connection() as conn:

        df = pd.read_sql_query(
            query,
            conn,
            params=[ticker]
        )

    if df.empty:
        return {}

    return df.iloc[0].to_dict()