"""SQLite database creation and data loading utilities for the N100 platform."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from src.etl.loader import load_all_excel

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_SCHEMA = PROJECT_ROOT / "db" / "schema.sql"
DEFAULT_DATABASE = PROJECT_ROOT / "nifty100.db"
DEFAULT_RAW_DATA = PROJECT_ROOT / "data" / "raw"
DEFAULT_SUPPORTING_DATA = PROJECT_ROOT / "data" / "supporting"
DEFAULT_AUDIT = PROJECT_ROOT / "output" / "load_audit.csv"


TABLE_LOAD_ORDER = [
    "companies",
    "profitandloss",
    "balancesheet",
    "cashflow",
    "analysis",
    "documents",
    "prosandcons",
    "sectors",
    "stock_prices",
    "market_cap",
    "financial_ratios",
    "peer_groups",
]


BUSINESS_KEYS = {
    "profitandloss": ["company_id", "year"],
    "balancesheet": ["company_id", "year"],
    "cashflow": ["company_id", "year"],
    "sectors": ["company_id"],
    "stock_prices": ["company_id", "date"],
    "market_cap": ["company_id", "year"],
    "financial_ratios": ["company_id", "year"],
    "peer_groups": ["peer_group_name", "company_id"],
}


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

        foreign_keys = connection.execute(
            "PRAGMA foreign_keys"
        ).fetchone()[0]

        if foreign_keys != 1:
            raise RuntimeError(
                "SQLite foreign-key enforcement is disabled."
            )

    return database_path


def recreate_database(
    database_path: str | Path = DEFAULT_DATABASE,
    schema_path: str | Path = DEFAULT_SCHEMA,
) -> Path:
    """Create a completely fresh SQLite database for a full ETL reload."""

    database_path = Path(database_path)

    if database_path.exists():
        database_path.unlink()

    return create_database(
        database_path=database_path,
        schema_path=schema_path,
    )


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
        return connection.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()


def load_dataframe(
    connection: sqlite3.Connection,
    table_name: str,
    dataframe: pd.DataFrame,
) -> int:
    """Load a DataFrame into an existing SQLite table."""

    if dataframe.empty:
        return 0

    dataframe.to_sql(
        table_name,
        connection,
        if_exists="append",
        index=False,
    )

    return len(dataframe)


def deduplicate_dataframe(
    dataframe: pd.DataFrame,
    table_name: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Remove business-key duplicates and report conflicts."""

    business_keys = BUSINESS_KEYS.get(table_name)

    if not business_keys:
        return dataframe.copy(), pd.DataFrame()

    duplicate_mask = dataframe.duplicated(
        business_keys,
        keep=False,
    )

    duplicates = dataframe.loc[duplicate_mask].copy()

    if duplicates.empty:
        return dataframe.copy(), pd.DataFrame()

    conflict_records = []

    for key_values, group in duplicates.groupby(
        business_keys,
        dropna=False,
    ):
        if not isinstance(key_values, tuple):
            key_values = (key_values,)

        values = group.drop(
            columns=["id"],
            errors="ignore",
        )

        if values.nunique(dropna=False).max() > 1:
            record_base = dict(zip(business_keys, key_values))

            for _, row in group.iterrows():
                conflict_records.append(
                    {
                        "table_name": table_name,
                        **record_base,
                        "source_id": row.get("id"),
                        "issue": "CONFLICTING_DUPLICATE",
                    }
                )

    conflicts = pd.DataFrame(conflict_records)

    deduplicated = dataframe.drop_duplicates(
        subset=business_keys,
        keep="first",
    ).copy()

    return deduplicated, conflicts


def filter_valid_foreign_keys(
    dataframe: pd.DataFrame,
    valid_company_ids: set[str],
    table_name: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Keep rows with valid company IDs and report invalid foreign keys."""

    if "company_id" not in dataframe.columns:
        return dataframe.copy(), pd.DataFrame()

    normalized_ids = (
        dataframe["company_id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    valid_mask = normalized_ids.isin(valid_company_ids)

    invalid_rows = dataframe.loc[~valid_mask].copy()

    if invalid_rows.empty:
        return dataframe.copy(), pd.DataFrame()

    fk_records = []

    for _, row in invalid_rows.iterrows():
        fk_records.append(
            {
                "table_name": table_name,
                "company_id": row["company_id"],
                "source_id": row.get("id"),
                "issue": "INVALID_FOREIGN_KEY",
            }
        )

    fk_rejections = pd.DataFrame(fk_records)

    valid_dataframe = dataframe.loc[valid_mask].copy()

    return valid_dataframe, fk_rejections


def load_source_data(
    raw_data_path: str | Path,
    supporting_data_path: str | Path,
) -> dict[str, pd.DataFrame]:
    """Load core and supporting Excel datasets."""

    raw_data_path = Path(raw_data_path)
    supporting_data_path = Path(supporting_data_path)

    raw_data = load_all_excel(
        raw_data_path,
        header=1,
    )

    supporting_data = load_all_excel(
        supporting_data_path,
        header=0,
    )

    duplicate_names = set(raw_data).intersection(
        supporting_data
    )

    if duplicate_names:
        raise ValueError(
            "Duplicate dataset names found across raw and "
            "supporting directories: "
            + ", ".join(sorted(duplicate_names))
        )

    return {
        **raw_data,
        **supporting_data,
    }


def load_all_data(
    raw_data_path: str | Path = DEFAULT_RAW_DATA,
    supporting_data_path: str | Path = DEFAULT_SUPPORTING_DATA,
    database_path: str | Path = DEFAULT_DATABASE,
    audit_path: str | Path = DEFAULT_AUDIT,
) -> pd.DataFrame:
    """Load all 12 Excel datasets into a fresh SQLite database."""

    raw_data_path = Path(raw_data_path)
    supporting_data_path = Path(supporting_data_path)
    database_path = Path(database_path)
    audit_path = Path(audit_path)

    data = load_source_data(
        raw_data_path,
        supporting_data_path,
    )

    missing_tables = [
        table
        for table in TABLE_LOAD_ORDER
        if table not in data
    ]

    if missing_tables:
        raise FileNotFoundError(
            "Missing datasets: " + ", ".join(missing_tables)
        )

    database_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    audit_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # IMPORTANT:
    # Day-05 is a full reload. Always start with a fresh database.
    recreate_database(database_path)

    audit_records = []

    valid_company_ids = set(
        data["companies"]["id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "PRAGMA foreign_keys = ON"
        )

        for table_name in TABLE_LOAD_ORDER:
            print(
                f"LOADING: {table_name} | "
                f"columns={list(data[table_name].columns)} | "
                f"keys={BUSINESS_KEYS.get(table_name)}"
            )

            dataframe = data[table_name].copy()
            source_rows = len(dataframe)

            try:
                if table_name == "companies":
                    loaded_rows = load_dataframe(
                        connection,
                        table_name,
                        dataframe,
                    )

                    audit_records.append(
                        {
                            "table_name": table_name,
                            "source_rows": source_rows,
                            "loaded_rows": loaded_rows,
                            "rejected_rows": 0,
                            "conflict_rows": 0,
                            "status": "LOADED",
                        }
                    )

                    continue

                valid_dataframe, fk_rejections = (
                    filter_valid_foreign_keys(
                        dataframe,
                        valid_company_ids,
                        table_name,
                    )
                )

                (
                    deduplicated_dataframe,
                    conflicts,
                ) = deduplicate_dataframe(
                    valid_dataframe,
                    table_name,
                )

                loaded_rows = load_dataframe(
                    connection,
                    table_name,
                    deduplicated_dataframe,
                )

                rejected_rows = len(fk_rejections)
                conflict_rows = len(conflicts)

                if (
                    rejected_rows > 0
                    or conflict_rows > 0
                ):
                    status = "LOADED_WITH_REJECTIONS"
                else:
                    status = "LOADED"

                audit_records.append(
                    {
                        "table_name": table_name,
                        "source_rows": source_rows,
                        "loaded_rows": loaded_rows,
                        "rejected_rows": rejected_rows,
                        "conflict_rows": conflict_rows,
                        "status": status,
                    }
                )

            except (
                sqlite3.IntegrityError,
                ValueError,
            ) as error:
                connection.rollback()

                audit_records.append(
                    {
                        "table_name": table_name,
                        "source_rows": source_rows,
                        "loaded_rows": 0,
                        "rejected_rows": source_rows,
                        "conflict_rows": 0,
                        "status": f"REJECTED: {error}",
                    }
                )

    audit = pd.DataFrame(audit_records)

    audit.to_csv(
        audit_path,
        index=False,
    )

    return audit


if __name__ == "__main__":
    database = create_database()

    print(f"Database created: {database}")
    print("Tables:")

    for table in get_table_names(database):
        print(f"  - {table}")

    failures = check_foreign_keys(database)

    print(
        f"Foreign-key violations: {len(failures)}"
    )