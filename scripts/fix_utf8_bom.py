from pathlib import Path

files = [
    "src/analytics/cagr.py",
    "src/analytics/cashflow_kpis.py",
    "src/analytics/ratios.py",
    "src/api/routers/documents.py",
    "src/api/routers/market_cap.py",
    "src/api/routers/peers.py",
    "src/api/routers/portfolio.py",
    "src/api/routers/screener.py",
    "src/api/routers/sectors.py",
    "src/dashboard/app.py",
    "src/dashboard/pages/01_home.py",
    "src/dashboard/utils/api_client.py",
    "src/dashboard/utils/db.py",
    "src/reports/batch_reports.py",
    "src/reports/portfolio_summary.py",
]

print("=" * 80)
print("DAY 44 — UTF-8 BOM CLEANUP")
print("=" * 80)

for file in files:
    path = Path(file)

    data = path.read_bytes()

    if data.startswith(b"\xef\xbb\xbf"):
        path.write_bytes(data[3:])
        print(f"FIXED: {file}")
    else:
        print(f"OK:    {file}")

print()
print("BOM cleanup complete.")
print("=" * 80)
