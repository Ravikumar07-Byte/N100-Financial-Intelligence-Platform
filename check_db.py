import sqlite3

p = "nifty100.db"
conn = sqlite3.connect(p)

print("Database:", p)

tables = [
    row[0]
    for row in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
]

print("Tables:")
for table in tables:
    print("  -", table)

print("Companies:", conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0])
print(
    "Financial ratios:",
    conn.execute("SELECT COUNT(*) FROM financial_ratios").fetchone()[0],
)
print(
    "FK violations:",
    len(conn.execute("PRAGMA foreign_key_check").fetchall()),
)

conn.close()
