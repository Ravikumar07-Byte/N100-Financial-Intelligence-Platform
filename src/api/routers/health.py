"""
N100 Financial Intelligence Platform
Health API Router

Day 38 — FastAPI Server Scaffold
"""

import sqlite3
from pathlib import Path
from time import monotonic

from fastapi import APIRouter, Request

# ============================================================================
# ROUTER
# ============================================================================

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


# ============================================================================
# DATABASE PATH
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DB_PATH = PROJECT_ROOT / "nifty100.db"


# ============================================================================
# DATABASE ROW COUNTS
# ============================================================================


def get_db_row_counts() -> dict:
    """
    Return row counts for all user tables in the SQLite database.

    The function discovers the tables dynamically instead of hard-coding
    table names. This makes the health endpoint resilient to the existing
    N100 database schema.
    """

    if not DB_PATH.exists():
        return {"_database_error": f"Database not found: {DB_PATH}"}

    connection = None

    try:
        connection = sqlite3.connect(
            str(DB_PATH),
            check_same_thread=False,
        )

        cursor = connection.cursor()

        # ------------------------------------------------------------------
        # Discover user tables
        # ------------------------------------------------------------------

        cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """)

        tables = [row[0] for row in cursor.fetchall()]

        row_counts = {}

        # ------------------------------------------------------------------
        # Count rows in every table
        # ------------------------------------------------------------------

        for table_name in tables:

            # SQLite table names are obtained directly from sqlite_master.
            # Double quotes safely handle names containing special characters.
            safe_table_name = table_name.replace('"', '""')

            cursor.execute(f'SELECT COUNT(*) FROM "{safe_table_name}"')

            count = cursor.fetchone()[0]

            row_counts[table_name] = count

        return row_counts

    except Exception as exc:

        return {"_database_error": str(exc)}

    finally:

        if connection is not None:
            connection.close()


# ============================================================================
# HEALTH ENDPOINT
# ============================================================================


@router.get(
    "",
    summary="API health check",
    description=(
        "Returns API status, SQLite database row counts, "
        "server uptime and API version."
    ),
)
def health_check(request: Request):
    """
    GET /api/v1/health

    Returns:

    - status
    - db_row_counts
    - uptime_seconds
    - version
    """

    # ----------------------------------------------------------------------
    # Calculate uptime
    # ----------------------------------------------------------------------

    start_time = getattr(
        request.app.state,
        "start_time",
        monotonic(),
    )

    uptime_seconds = monotonic() - start_time

    # ----------------------------------------------------------------------
    # Get application version
    # ----------------------------------------------------------------------

    version = getattr(
        request.app.state,
        "app_version",
        "3.2.1",
    )

    # ----------------------------------------------------------------------
    # Database row counts
    # ----------------------------------------------------------------------

    db_row_counts = get_db_row_counts()

    # ----------------------------------------------------------------------
    # Return health information
    # ----------------------------------------------------------------------

    return {
        "status": "ok",
        "db_row_counts": db_row_counts,
        "uptime_seconds": round(
            uptime_seconds,
            3,
        ),
        "version": version,
    }
