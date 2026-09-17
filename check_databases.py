import sqlite3
from pathlib import Path

databases = [
    Path("nifty100.db"),
    Path("data/nifty100.db"),
]

tables_to_check = [
    "companies",
    "financial_ratios",
    "profitandloss",
    "balancesheet",
    "cashflow",
    "sectors",
    "stock_prices",
]

print("=" * 70)
print("N100 DATABASE CHECK")
print("=" * 70)

for db_path in databases:

    print()
    print("DATABASE:")
    print(db_path.resolve())

    if not db_path.exists():
        print("  FILE NOT FOUND")
        continue

    conn = sqlite3.connect(db_path)

    cursor = conn.cursor()

    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )

    tables = [
        row[0]
        for row in cursor.fetchall()
    ]

    print("  Tables found:")

    if not tables:
        print("    NONE")

    else:

        for table in tables:
            print(f"    {table}")

    print()
    print("  Row counts:")

    for table in tables_to_check:

        if table in tables:

            cursor.execute(
                f'SELECT COUNT(*) FROM "{table}"'
            )

            count = cursor.fetchone()[0]

            print(
                f"    {table}: {count}"
            )

        else:

            print(
                f"    {table}: TABLE NOT FOUND"
            )

    conn.close()

print()
print("=" * 70)
print("DATABASE CHECK COMPLETE")
print("=" * 70)