"""Financial ratio calculation engine for N100 data."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

DATABASE_PATH = Path("nifty100.db")


def safe_divide(
    numerator: Any,
    denominator: Any,
) -> float | None:
    """Safely divide two financial values."""

    if numerator is None or denominator is None:
        return None

    try:
        numerator_value = float(numerator)
        denominator_value = float(denominator)
    except (TypeError, ValueError):
        return None

    if pd.isna(numerator_value) or pd.isna(denominator_value):
        return None

    if denominator_value == 0:
        return None

    return numerator_value / denominator_value


def calculate_ratios(
    profitandloss: pd.DataFrame,
    balancesheet: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate financial ratios from normalized financial statements."""

    pnl = profitandloss.copy()
    bs = balancesheet.copy()

    pnl["company_id"] = pnl["company_id"].astype(str).str.strip().str.upper()
    bs["company_id"] = bs["company_id"].astype(str).str.strip().str.upper()

    merged = pnl.merge(
        bs,
        on=["company_id", "year"],
        how="inner",
        suffixes=("_pnl", "_bs"),
    )

    records: list[dict[str, Any]] = []

    for _, row in merged.iterrows():
        company_id = row["company_id"]
        year = row["year"]

        equity = safe_add(
            row.get("equity_capital"),
            row.get("reserves"),
        )

        borrowings = row.get("borrowings")
        sales = row.get("sales")
        net_profit = row.get("net_profit")
        operating_profit = row.get("operating_profit")
        profit_before_tax = row.get("profit_before_tax")
        interest = row.get("interest")
        total_assets = row.get("total_assets")

        records.append(
            {
                "company_id": company_id,
                "year": year,
                # Current assets/current liabilities are not
                # available in the source balance-sheet schema.
                "current_ratio": None,
                "debt_to_equity": safe_divide(
                    borrowings,
                    equity,
                ),
                "return_on_equity": safe_divide(
                    net_profit,
                    equity,
                ),
                "return_on_capital_employed": safe_divide(
                    operating_profit,
                    safe_add(
                        equity,
                        borrowings,
                    ),
                ),
                "net_profit_margin": safe_divide(
                    net_profit,
                    sales,
                ),
                "operating_profit_margin": safe_divide(
                    operating_profit,
                    sales,
                ),
                "interest_coverage_ratio": safe_divide(
                    profit_before_tax,
                    interest,
                ),
                "asset_turnover_ratio": safe_divide(
                    sales,
                    total_assets,
                ),
            }
        )

    return pd.DataFrame(records)


def safe_add(
    first: Any,
    second: Any,
) -> float | None:
    """Safely add two financial values."""

    values = []

    for value in (first, second):
        if value is None:
            continue

        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            continue

        if pd.isna(numeric_value):
            continue

        values.append(numeric_value)

    if not values:
        return None

    return sum(values)


def load_source_data(
    database_path: Path = DATABASE_PATH,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load profit-and-loss and balance-sheet data from SQLite."""

    connection = sqlite3.connect(database_path)

    try:
        profitandloss = pd.read_sql_query(
            """
            SELECT *
            FROM profitandloss
            """,
            connection,
        )

        balancesheet = pd.read_sql_query(
            """
            SELECT *
            FROM balancesheet
            """,
            connection,
        )
    finally:
        connection.close()

    return profitandloss, balancesheet


def write_ratios_to_database(
    ratios: pd.DataFrame,
    database_path: Path = DATABASE_PATH,
) -> int:
    """Replace the financial-ratio table with calculated ratios."""

    if ratios.empty:
        return 0

    connection = sqlite3.connect(database_path)

    try:
        cursor = connection.cursor()

        cursor.execute("DELETE FROM financial_ratios")

        rows = [
            (
                row["company_id"],
                row["year"],
                row["current_ratio"],
                row["debt_to_equity"],
                row["return_on_equity"],
                row["return_on_capital_employed"],
                row["net_profit_margin"],
                row["operating_profit_margin"],
                row["interest_coverage_ratio"],
                row["asset_turnover_ratio"],
            )
            for _, row in ratios.iterrows()
        ]

        cursor.executemany(
            """
            INSERT INTO financial_ratios (
                company_id,
                year,
                current_ratio,
                debt_to_equity,
                return_on_equity,
                return_on_capital_employed,
                net_profit_margin,
                operating_profit_margin,
                interest_coverage_ratio,
                asset_turnover_ratio
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )

        connection.commit()

        return len(rows)

    finally:
        connection.close()


def build_financial_ratios(
    database_path: Path = DATABASE_PATH,
) -> pd.DataFrame:
    """Build and store financial ratios."""

    profitandloss, balancesheet = load_source_data(
        database_path,
    )

    ratios = calculate_ratios(
        profitandloss,
        balancesheet,
    )

    write_ratios_to_database(
        ratios,
        database_path,
    )

    return ratios


if __name__ == "__main__":
    result = build_financial_ratios()

    print(f"Financial ratios generated: {len(result)}")
