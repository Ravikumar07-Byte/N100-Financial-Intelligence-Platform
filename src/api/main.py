"""
N100 Financial Intelligence Platform
FastAPI Application Entry Point

Day 38 — FastAPI Server Scaffold
"""

from pathlib import Path
from time import monotonic

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
)


# ============================================================================
# APPLICATION CONFIGURATION
# ============================================================================

API_VERSION = "v1"
APP_VERSION = "3.2.1"

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = PROJECT_ROOT / "nifty100.db"


# ============================================================================
# DATABASE CONNECTION
# ============================================================================

def get_db_connection():
    """
    Create a SQLite database connection.

    The connection uses the project-level nifty100.db database.
    """

    import sqlite3

    connection = sqlite3.connect(
        str(DB_PATH),
        check_same_thread=False,
    )

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="N100 Financial Intelligence Platform API",
    description=(
        "REST API for the N100 Financial Intelligence Platform "
        "providing company, screening, sector, peer, valuation, "
        "portfolio and document intelligence."
    ),
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ============================================================================
# APPLICATION STATE
# ============================================================================

# Store process start time on app.state so routers do not need
# to import anything from main.py.

app.state.start_time = monotonic()
app.state.api_version = API_VERSION
app.state.app_version = APP_VERSION
app.state.db_path = str(DB_PATH)


# ============================================================================
# CORS MIDDLEWARE
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# REQUEST LOGGING MIDDLEWARE
# ============================================================================

@app.middleware("http")
async def request_logging_middleware(
    request: Request,
    call_next,
):
    """
    Log HTTP method, request path and response time
    for every request.
    """

    import logging

    logger = logging.getLogger("n100.api")

    start_time = monotonic()

    try:
        response = await call_next(request)

        elapsed = monotonic() - start_time

        logger.info(
            "%s %s -> %s | %.4fs",
            request.method,
            request.url.path,
            response.status_code,
            elapsed,
        )

        return response

    except Exception:
        elapsed = monotonic() - start_time

        logger.exception(
            "%s %s -> ERROR | %.4fs",
            request.method,
            request.url.path,
            elapsed,
        )

        raise


# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get(
    "/",
    tags=["Root"],
    summary="API root",
)
def root():
    """
    Basic API information.
    """

    return {
        "name": "N100 Financial Intelligence Platform API",
        "version": APP_VERSION,
        "api_version": API_VERSION,
        "status": "ok",
        "docs": "/docs",
    }


# ============================================================================
# ROUTER REGISTRATION
# ============================================================================

API_PREFIX = "/api/v1"


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


# ============================================================================
# STARTUP / SHUTDOWN EVENTS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """
    Application startup handler.
    """

    import logging

    logger = logging.getLogger("n100.api")

    logger.info("=" * 70)
    logger.info("N100 FINANCIAL INTELLIGENCE PLATFORM API")
    logger.info("=" * 70)
    logger.info("API version : %s", API_VERSION)
    logger.info("Application : %s", APP_VERSION)
    logger.info("Database    : %s", DB_PATH)
    logger.info("Docs        : http://127.0.0.1:8000/docs")
    logger.info("=" * 70)


@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown handler.
    """

    import logging

    logger = logging.getLogger("n100.api")

    logger.info("N100 API server shutting down.")


# ============================================================================
# DIRECT EXECUTION
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )