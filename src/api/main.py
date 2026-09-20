"""
N100 Financial Intelligence Platform API
FastAPI application entry point.
"""

from pathlib import Path
import sqlite3
import time
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import (
    companies,
    screener,
    sectors,
    peers,
    valuation,
    portfolio,
    documents,
    health,
    market_cap,
)

# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

API_VERSION = "3.2.1"
API_PREFIX = "/api/v1"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "nifty100.db"

START_TIME = time.time()


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("n100-api")


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="N100 Financial Intelligence Platform API",
    description=(
        "REST API for the N100 Financial Intelligence Platform "
        "providing company, screening, sector, peer, valuation, "
        "portfolio and document intelligence."
    ),
    version=API_VERSION,
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REQUEST LOGGING MIDDLEWARE
# ============================================================

@app.middleware("http")
async def request_logging_middleware(
    request: Request,
    call_next,
):
    start_time = time.perf_counter()

    response = await call_next(request)

    elapsed = time.perf_counter() - start_time

    logger.info(
        "%s %s -> %s | %.4f sec",
        request.method,
        request.url.path,
        response.status_code,
        elapsed,
    )

    return response


# ============================================================
# SQLITE CONNECTION
# ============================================================

def get_db_connection() -> sqlite3.Connection:
    """
    Create a SQLite connection to the N100 database.
    """

    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"N100 database not found: {DB_PATH}"
        )

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get(
    "/",
    tags=["Root"],
    summary="API root",
)
def api_root():
    """
    Basic API information.
    """

    return {
        "name": "N100 Financial Intelligence Platform API",
        "version": API_VERSION,
        "status": "online",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


# ============================================================
# REGISTER API ROUTERS
# ============================================================

app.include_router(
    market_cap.router,
    prefix=API_PREFIX,
)

app.include_router(
    companies.router,
    prefix=API_PREFIX,
)

app.include_router(
    screener.router,
    prefix=API_PREFIX,
)

app.include_router(
    sectors.router,
    prefix=API_PREFIX,
)

app.include_router(
    peers.router,
    prefix=API_PREFIX,
)

app.include_router(
    valuation.router,
    prefix=API_PREFIX,
)

app.include_router(
    portfolio.router,
    prefix=API_PREFIX,
)

app.include_router(
    documents.router,
    prefix=API_PREFIX,
)

app.include_router(
    health.router,
    prefix=API_PREFIX,
)


# ============================================================
# STARTUP INFORMATION
# ============================================================

@app.on_event("startup")
async def startup_event():
    """
    Verify database availability when the API starts.
    """

    logger.info("=" * 70)
    logger.info("N100 FINANCIAL INTELLIGENCE PLATFORM API")
    logger.info("=" * 70)
    logger.info("API version: %s", API_VERSION)
    logger.info("Database: %s", DB_PATH)
    logger.info("Database exists: %s", DB_PATH.exists())
    logger.info("API prefix: %s", API_PREFIX)
    logger.info("API documentation: /docs")
    logger.info("=" * 70)