"""
Day 42 - Dashboard / API Integration Tests.

Verifies that the dashboard API client receives the same
screener results as the FastAPI screener endpoint.
"""

from unittest.mock import patch

import requests

from fastapi.testclient import TestClient

from src.api.main import app
from src.dashboard.utils.api_client import get_screener


client = TestClient(app)


def _api_response_to_requests_response(
    fastapi_response,
) -> requests.Response:
    """
    Convert a FastAPI TestClient response into a requests.Response
    so the dashboard API client can consume it.
    """

    response = requests.Response()

    response.status_code = fastapi_response.status_code
    response._content = fastapi_response.content
    response.headers.update(
        dict(fastapi_response.headers)
    )
    response.url = str(fastapi_response.url)

    return response


def test_dashboard_screener_matches_fastapi_api():
    """
    Verify that the dashboard API client returns the same
    screener companies as the FastAPI endpoint.
    """

    filters = {
        "min_roe": 15,
    }

    # ---------------------------------------------------------
    # 1. Get the expected result directly from FastAPI
    # ---------------------------------------------------------

    api_response = client.get(
        "/api/v1/screener",
        params=filters,
    )

    assert api_response.status_code == 200

    api_data = api_response.json()

    # ---------------------------------------------------------
    # 2. Mock requests.get used by the dashboard API client
    # ---------------------------------------------------------
    #
    # This keeps the test self-contained.
    # No separate uvicorn server is required.
    # ---------------------------------------------------------

    fastapi_as_requests_response = (
        _api_response_to_requests_response(api_response)
    )

    with patch(
        "src.dashboard.utils.api_client.requests.get",
        return_value=fastapi_as_requests_response,
    ) as mock_get:

        dashboard_data = get_screener(
            **filters
        )

    # ---------------------------------------------------------
    # 3. Verify dashboard client called the screener endpoint
    # ---------------------------------------------------------

    mock_get.assert_called_once()

    called_url = mock_get.call_args.args[0]

    assert called_url.endswith(
        "/api/v1/screener"
    )

    # ---------------------------------------------------------
    # 4. Verify result count
    # ---------------------------------------------------------

    assert dashboard_data["count"] == api_data["count"]

    # ---------------------------------------------------------
    # 5. Verify company IDs
    # ---------------------------------------------------------

    api_ids = {
        company["id"]
        for company in api_data["companies"]
    }

    dashboard_ids = {
        company["id"]
        for company in dashboard_data["companies"]
    }

    assert dashboard_ids == api_ids

    # ---------------------------------------------------------
    # 6. Verify company names
    # ---------------------------------------------------------

    api_names = {
        company["id"]: company["company_name"]
        for company in api_data["companies"]
    }

    dashboard_names = {
        company["id"]: company["company_name"]
        for company in dashboard_data["companies"]
    }

    assert dashboard_names == api_names

    # ---------------------------------------------------------
    # 7. Verify sectors
    # ---------------------------------------------------------

    api_sectors = {
        company["id"]: company["broad_sector"]
        for company in api_data["companies"]
    }

    dashboard_sectors = {
        company["id"]: company["broad_sector"]
        for company in dashboard_data["companies"]
    }

    assert dashboard_sectors == api_sectors

    # ---------------------------------------------------------
    # 8. Verify ROE values
    # ---------------------------------------------------------

    api_roe = {
        company["id"]: company["roe_pct"]
        for company in api_data["companies"]
    }

    dashboard_roe = {
        company["id"]: company["roe_pct"]
        for company in dashboard_data["companies"]
    }

    assert dashboard_roe == api_roe

    # ---------------------------------------------------------
    # 9. Verify filters
    # ---------------------------------------------------------

    assert dashboard_data["filters"] == api_data["filters"]