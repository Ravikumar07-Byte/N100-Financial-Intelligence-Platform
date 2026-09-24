"""
Dashboard API client.

Provides the Streamlit dashboard with a single interface for
consuming the FastAPI screener endpoint.
"""

import os
from typing import Any

import requests

DEFAULT_API_BASE_URL = "http://127.0.0.1:8000/api/v1"


def get_api_base_url() -> str:
    """
    Return the FastAPI base URL.

    Can be overridden with the N100_API_BASE_URL environment variable.
    """

    return os.getenv(
        "N100_API_BASE_URL",
        DEFAULT_API_BASE_URL,
    ).rstrip("/")


def get_screener(
    *,
    min_roe: float | None = None,
    max_de: float | None = None,
    min_fcf: float | None = None,
    sector: str | None = None,
    min_rev_cagr_5yr: float | None = None,
    min_pat_cagr_5yr: float | None = None,
    min_opm: float | None = None,
    max_pe: float | None = None,
    max_pb: float | None = None,
    min_dividend_yield: float | None = None,
    min_icr: float | None = None,
    timeout: float = 10.0,
) -> dict[str, Any]:
    """
    Fetch screener results from the FastAPI backend.

    Endpoint:
        GET /api/v1/screener

    All supported screener filters are passed through to the API.
    """

    params: dict[str, Any] = {}

    if min_roe is not None:
        params["min_roe"] = min_roe

    if max_de is not None:
        params["max_de"] = max_de

    if min_fcf is not None:
        params["min_fcf"] = min_fcf

    if sector:
        params["sector"] = sector

    if min_rev_cagr_5yr is not None:
        params["min_rev_cagr_5yr"] = min_rev_cagr_5yr

    if min_pat_cagr_5yr is not None:
        params["min_pat_cagr_5yr"] = min_pat_cagr_5yr

    if min_opm is not None:
        params["min_opm"] = min_opm

    if max_pe is not None:
        params["max_pe"] = max_pe

    if max_pb is not None:
        params["max_pb"] = max_pb

    if min_dividend_yield is not None:
        params["min_dividend_yield"] = min_dividend_yield

    if min_icr is not None:
        params["min_icr"] = min_icr

    url = f"{get_api_base_url()}/screener"

    response = requests.get(
        url,
        params=params,
        timeout=timeout,
    )

    response.raise_for_status()

    data = response.json()

    if not isinstance(data, dict):
        raise TypeError("Screener API returned an invalid response.")

    if "companies" not in data:
        raise ValueError("Screener API response is missing 'companies'.")

    if "count" not in data:
        raise ValueError("Screener API response is missing 'count'.")

    if "filters" not in data:
        raise ValueError("Screener API response is missing 'filters'.")

    if not isinstance(data["companies"], list):
        raise TypeError("Screener API response 'companies' must be a list.")

    return data
