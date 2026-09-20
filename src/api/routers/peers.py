"""
Day 40 - Peer Intelligence API
"""

import sqlite3
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter(
    prefix="/peers",
    tags=["Peers"],
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = PROJECT_ROOT / "nifty100.db"


# ---------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------

def get_connection():
    if not DB_PATH.exists():
        raise RuntimeError(f"Database not found: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------
# Peer Group
# ---------------------------------------------------------------------

@router.get(
    "/{group_name}",
    summary="Get companies in a peer group with percentile ranks",
)
def get_peer_group(group_name: str):

    conn = get_connection()

    try:
        group = conn.execute(
            """
            SELECT 1
            FROM peer_groups
            WHERE LOWER(peer_group_name) = LOWER(?)
            LIMIT 1
            """,
            (group_name,),
        ).fetchone()

        if group is None:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown peer group: {group_name}",
            )

        rows = conn.execute(
            """
            SELECT
                pp.company_id,
                c.company_name,
                pp.peer_group_name,
                pp.metric,
                pp.value,
                pp.percentile_rank,
                pp.year
            FROM peer_percentiles pp
            LEFT JOIN companies c
                ON c.id = pp.company_id
            WHERE LOWER(pp.peer_group_name) = LOWER(?)
            ORDER BY
                pp.company_id,
                pp.metric
            """,
            (group_name,),
        ).fetchall()

        companies = {}

        for row in rows:

            company_id = row["company_id"]

            if company_id not in companies:
                companies[company_id] = {
                    "company_id": company_id,
                    "company_name": row["company_name"],
                    "peer_group": row["peer_group_name"],
                    "year": row["year"],
                    "metrics": {},
                }

            companies[company_id]["metrics"][row["metric"]] = {
                "value": row["value"],
                "percentile_rank": row["percentile_rank"],
            }

        result = list(companies.values())

        return {
            "peer_group": group_name,
            "count": len(result),
            "companies": result,
        }

    finally:
        conn.close()


# ---------------------------------------------------------------------
# Peer Comparison / Radar
# ---------------------------------------------------------------------

@router.get(
    "/companies/{ticker}/compare",
    summary="Compare a company with peer-group average and benchmark",
)
def compare_company_with_peers(ticker: str):

    conn = get_connection()

    try:

        # -------------------------------------------------------------
        # 1. Verify company
        # -------------------------------------------------------------

        company = conn.execute(
            """
            SELECT
                id,
                company_name
            FROM companies
            WHERE UPPER(id) = UPPER(?)
            LIMIT 1
            """,
            (ticker,),
        ).fetchone()

        if company is None:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown company ticker: {ticker}",
            )

        company_id = company["id"]

        # -------------------------------------------------------------
        # 2. Find peer group
        # -------------------------------------------------------------

        peer_group = conn.execute(
            """
            SELECT
                peer_group_name
            FROM peer_groups
            WHERE company_id = ?
            ORDER BY id
            LIMIT 1
            """,
            (company_id,),
        ).fetchone()

        if peer_group is None:
            raise HTTPException(
                status_code=404,
                detail=f"No peer group found for company: {ticker}",
            )

        group_name = peer_group["peer_group_name"]

        # -------------------------------------------------------------
        # 3. Find benchmark company
        # -------------------------------------------------------------

        benchmark = conn.execute(
            """
            SELECT
                pg.company_id,
                c.company_name
            FROM peer_groups pg
            LEFT JOIN companies c
                ON c.id = pg.company_id
            WHERE LOWER(pg.peer_group_name) = LOWER(?)
              AND pg.is_benchmark = 1
            LIMIT 1
            """,
            (group_name,),
        ).fetchone()

        if benchmark is None:
            raise HTTPException(
                status_code=404,
                detail=f"No benchmark company found for peer group: {group_name}",
            )

        benchmark_id = benchmark["company_id"]

        # -------------------------------------------------------------
        # 4. Eight radar metrics
        # -------------------------------------------------------------

        metrics = [
            "ROE",
            "ROCE",
            "Net Profit Margin",
            "D/E",
            "FCF",
            "Revenue CAGR 5yr",
            "PAT CAGR 5yr",
            "Asset Turnover",
        ]

        placeholders = ",".join("?" for _ in metrics)

        # -------------------------------------------------------------
        # 5. Get all peer percentile records
        # -------------------------------------------------------------

        rows = conn.execute(
            f"""
            SELECT
                company_id,
                peer_group_name,
                metric,
                value,
                year
            FROM peer_percentiles
            WHERE LOWER(peer_group_name) = LOWER(?)
              AND metric IN ({placeholders})
            """,
            [group_name, *metrics],
        ).fetchall()

        # -------------------------------------------------------------
        # 6. Organise data by metric
        # -------------------------------------------------------------

        metric_data = {}

        for row in rows:

            metric = row["metric"]

            if metric not in metric_data:
                metric_data[metric] = []

            metric_data[metric].append(row)

        # -------------------------------------------------------------
        # 7. Build radar data
        # -------------------------------------------------------------

        radar = []

        for metric in metrics:

            records = metric_data.get(metric, [])

            company_value = None
            benchmark_value = None

            peer_values = []

            year = None

            for record in records:

                value = record["value"]

                if value is None:
                    continue

                peer_values.append(float(value))

                year = record["year"]

                if str(record["company_id"]).upper() == str(company_id).upper():
                    company_value = float(value)

                if str(record["company_id"]).upper() == str(benchmark_id).upper():
                    benchmark_value = float(value)

            peer_average = None

            if peer_values:
                peer_average = sum(peer_values) / len(peer_values)

            radar.append(
                {
                    "metric": metric,
                    "company_value": company_value,
                    "peer_group_average": peer_average,
                    "benchmark_value": benchmark_value,
                    "year": year,
                }
            )

        # -------------------------------------------------------------
        # 8. Return comparison
        # -------------------------------------------------------------

        return {
            "ticker": company_id,
            "company_name": company["company_name"],
            "peer_group": group_name,
            "benchmark": {
                "ticker": benchmark["company_id"],
                "company_name": benchmark["company_name"],
            },
            "axis_count": len(radar),
            "radar_data": radar,
        }

    finally:
        conn.close()
