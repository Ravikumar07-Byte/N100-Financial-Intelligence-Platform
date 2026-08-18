"""Tests for the N100 SQLite database schema."""

import sqlite3

from src.etl.db_loader import (
    check_foreign_keys,
    create_database,
    get_table_names,
)

EXPECTED_TABLES = {
    "companies",
    "profitandloss",
    "balancesheet",
    "cashflow",
    "analysis",
    "documents",
    "prosandcons",
    "sectors",
    "stock_prices",
    "financial_ratios",
    "peer_groups",
}


def test_database_creates_successfully(tmp_path):
    """Database should be created from schema.sql."""

    database = tmp_path / "test_nifty100.db"

    result = create_database(database)

    assert result.exists()


def test_all_required_tables_exist(tmp_path):
    """All required project tables should exist."""

    database = tmp_path / "test_nifty100.db"

    create_database(database)

    tables = set(get_table_names(database))

    assert EXPECTED_TABLES.issubset(tables)


def test_foreign_keys_are_enabled(tmp_path):
    """SQLite foreign-key enforcement should be enabled per connection."""

    database = tmp_path / "test_nifty100.db"

    create_database(database)

    with sqlite3.connect(database) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        enabled = connection.execute("PRAGMA foreign_keys").fetchone()[0]

    assert enabled == 1


def test_companies_primary_key(tmp_path):
    """Companies must use ticker/id as the primary key."""

    database = tmp_path / "test_nifty100.db"

    create_database(database)

    with sqlite3.connect(database) as connection:
        columns = connection.execute("PRAGMA table_info(companies)").fetchall()

    primary_keys = {row[1] for row in columns if row[5] == 1}

    assert primary_keys == {"id"}


def test_profitandloss_company_year_unique(tmp_path):
    """P&L must prevent duplicate company/year records."""

    database = tmp_path / "test_nifty100.db"

    create_database(database)

    with sqlite3.connect(database) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        connection.execute("""
            INSERT INTO companies (id, company_name)
            VALUES ('TEST', 'Test Company')
            """)

        connection.execute("""
            INSERT INTO profitandloss
            (id, company_id, year, sales)
            VALUES ('1', 'TEST', '2024-03', 100)
            """)

        try:
            connection.execute("""
                INSERT INTO profitandloss
                (id, company_id, year, sales)
                VALUES ('2', 'TEST', '2024-03', 200)
                """)
        except sqlite3.IntegrityError:
            duplicate_rejected = True
        else:
            duplicate_rejected = False

    assert duplicate_rejected


def test_invalid_foreign_key_is_rejected(tmp_path):
    """Child records must reference an existing company."""

    database = tmp_path / "test_nifty100.db"

    create_database(database)

    with sqlite3.connect(database) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        try:
            connection.execute("""
                INSERT INTO profitandloss
                (id, company_id, year, sales)
                VALUES ('1', 'INVALID', '2024-03', 100)
                """)
        except sqlite3.IntegrityError:
            rejected = True
        else:
            rejected = False

    assert rejected


def test_foreign_key_check_is_clean_for_empty_database(tmp_path):
    """Fresh database should have no foreign-key violations."""

    database = tmp_path / "test_nifty100.db"

    create_database(database)

    assert check_foreign_keys(database) == []
