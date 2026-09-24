import sqlite3

for p in ["data/nifty100.db", "nifty100.db"]:
    conn = sqlite3.connect(p)

    print("\n==============================")
    print("Database:", p)

    tables = [
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
    ]

    print("Tables:", tables)

    if "companies" in tables:
        print(
            "Companies:",
            conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0],
        )

    if "financial_ratios" in tables:
        print(
            "Financial ratios:",
            conn.execute("SELECT COUNT(*) FROM financial_ratios").fetchone()[0],
        )

    conn.close()
