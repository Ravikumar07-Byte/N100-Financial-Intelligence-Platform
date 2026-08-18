"""SQLite database creation utilities for the N100 platform."""

import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCHEMA = PROJECT_ROOT / "db" / "schema.sql"
DEFAULT_DATABASE = PROJECT_ROOT / "nifty100.db"


def create_database(
    database_path: str | Path = DEFAULT_DATABASE,
    schema_path: str | Path = DEFAULT_SCHEMA,
) -> Path:
    """Create the SQLite database using the project's schema."""

    database_path = Path(database_path)
    schema_path = Path(schema_path)

    database_path.parent.mkdir(parents=True, exist_ok=True)

    schema = schema_path.read_text(encoding="utf-8")

    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(schema)

        foreign_keys = connection.execute("PRAGMA foreign_keys").fetchone()[0]

        if foreign_keys != 1:
            raise RuntimeError("SQLite foreign-key enforcement is disabled.")

    return database_path


def get_table_names(
    database_path: str | Path = DEFAULT_DATABASE,
) -> list[str]:
    """Return all user-defined SQLite tables."""

    with sqlite3.connect(database_path) as connection:
        rows = connection.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """).fetchall()

    return [row[0] for row in rows]


def check_foreign_keys(
    database_path: str | Path = DEFAULT_DATABASE,
) -> list[tuple]:
    """Return rows reported by SQLite foreign-key validation."""

    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        return connection.execute("PRAGMA foreign_key_check").fetchall()


if __name__ == "__main__":
    database = create_database()

    print(f"Database created: {database}")
    print("Tables:")

    for table in get_table_names(database):
        print(f"  - {table}")

    failures = check_foreign_keys(database)

    print(f"Foreign-key violations: {len(failures)}")
