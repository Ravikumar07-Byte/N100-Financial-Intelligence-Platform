"""
Day 43 - SQLite index verification.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


DB_PATH = Path("nifty100.db")


def main() -> None:
    """Check indexes on company_id and year columns."""
    if not DB_PATH.exists():
        print("FAIL: nifty100.db does not exist.")
        return

    connection = sqlite3.connect(DB_PATH)

    try:
        tables = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            ORDER BY name
            """
        ).fetchall()

        print("=" * 80)
        print("DAY 43 — SQLITE INDEX CHECK")
        print("=" * 80)

        print("\nTables:")
        for (table_name,) in tables:
            print(f"  {table_name}")

        print("\nIndexes:")
        indexes = connection.execute(
            """
            SELECT name, tbl_name, sql
            FROM sqlite_master
            WHERE type = 'index'
            ORDER BY tbl_name, name
            """
        ).fetchall()

        if not indexes:
            print("  NO INDEXES FOUND")

        for name, table, sql in indexes:
            print(f"\n  Index : {name}")
            print(f"  Table : {table}")
            print(f"  SQL   : {sql}")

        print("\nColumn/index analysis:")

        for (table_name,) in tables:
            columns = connection.execute(
                f'PRAGMA table_info("{table_name}")'
            ).fetchall()

            column_names = {
                row[1].lower()
                for row in columns
            }

            relevant_columns = [
                column
                for column in ("company_id", "year")
                if column in column_names
            ]

            if not relevant_columns:
                continue

            table_indexes = connection.execute(
                f'PRAGMA index_list("{table_name}")'
            ).fetchall()

            indexed_columns: set[str] = set()

            for index_row in table_indexes:
                index_name = index_row[1]

                index_columns = connection.execute(
                    f'PRAGMA index_info("{index_name}")'
                ).fetchall()

                for index_column in index_columns:
                    column_name = index_column[2]

                    if column_name:
                        indexed_columns.add(column_name.lower())

            print(f"\n  Table: {table_name}")

            for column in relevant_columns:
                if column in indexed_columns:
                    print(f"    PASS: {column} is indexed")
                else:
                    print(f"    CHECK: {column} is not indexed")

        print("\n" + "=" * 80)

    finally:
        connection.close()


if __name__ == "__main__":
    main()