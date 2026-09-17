import sqlite3
import pandas as pd

DB = "nifty100.db"

conn = sqlite3.connect(DB)

print("=" * 70)
print("WIPRO DATABASE CHECK")
print("=" * 70)

print("\n[1] WIPRO in companies table")

query = """
SELECT id, company_name
FROM companies
WHERE id = 'WIPRO'
   OR company_name LIKE '%WIPRO%'
"""

companies = pd.read_sql_query(query, conn)

print(companies.to_string(index=False))

print("\n[2] WIPRO in financial_ratios table")

query = """
SELECT
    company_id,
    year,
    revenue_cagr_5yr,
    pat_cagr_5yr
FROM financial_ratios
WHERE company_id = 'WIPRO'
ORDER BY year
"""

ratios = pd.read_sql_query(query, conn)

print(ratios.to_string(index=False))

print("\n[3] Financial Ratio company IDs containing WIPRO")

query = """
SELECT DISTINCT company_id
FROM financial_ratios
WHERE UPPER(company_id) LIKE '%WIPRO%'
"""

matches = pd.read_sql_query(query, conn)

print(matches.to_string(index=False))

print("\n[4] Total companies in financial_ratios")

query = """
SELECT COUNT(DISTINCT company_id) AS company_count
FROM financial_ratios
"""

count = pd.read_sql_query(query, conn)

print(count.to_string(index=False))

conn.close()

print("\n" + "=" * 70)
print("CHECK COMPLETE")
print("=" * 70)