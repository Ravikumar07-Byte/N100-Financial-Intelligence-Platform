import csv
import sqlite3
from pathlib import Path

from src.analytics.cashflow_kpis import build_capital_allocation_row

DB_PATH = "nifty100.db"
OUTPUT_PATH = Path("output/capital_allocation.csv")

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

rows = conn.execute("""
    SELECT
        company_id,
        year,
        operating_activity,
        investing_activity,
        financing_activity
    FROM cashflow
    ORDER BY company_id, year
""").fetchall()

conn.close()

with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=[
            "company_id",
            "year",
            "cfo_sign",
            "cfi_sign",
            "cff_sign",
            "pattern_label",
        ],
    )

    writer.writeheader()

    for row in rows:
        result = build_capital_allocation_row(
            company_id=row["company_id"],
            year=row["year"],
            cfo=row["operating_activity"],
            cfi=row["investing_activity"],
            cff=row["financing_activity"],
        )
        writer.writerow(result)

print(f"Created: {OUTPUT_PATH}")
print(f"Rows written: {len(rows)}")
