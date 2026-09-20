from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)


# ============================================================
# 1. GET /screener -> HTTP 200
# ============================================================

def test_screener_returns_http_200():
    response = client.get("/api/v1/screener")

    assert response.status_code == 200


# ============================================================
# 2. GET /screener -> companies are returned
# ============================================================

def test_screener_returns_companies():
    response = client.get("/api/v1/screener")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, dict)
    assert "companies" in data
    assert "count" in data
    assert isinstance(data["companies"], list)
    assert data["count"] == len(data["companies"])


# ============================================================
# 3. min_roe=15 -> every returned company has ROE >= 15
# ============================================================

def test_screener_min_roe_returns_only_roe_15_or_above():
    response = client.get(
        "/api/v1/screener",
        params={"min_roe": 15},
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, dict)
    assert "companies" in data
    assert "count" in data

    companies = data["companies"]

    assert isinstance(companies, list)
    assert len(companies) == data["count"]

    # The API exposes ROE as `roe_pct`, not `roe`.
    for company in companies:
        assert isinstance(company, dict)
        assert "roe_pct" in company

        roe = company["roe_pct"]

        assert roe is not None
        assert float(roe) >= 15


# ============================================================
# 4. min_roe=15 -> filtered result is subset of all companies
# ============================================================

def test_screener_min_roe_filters_results():
    response_all = client.get("/api/v1/screener")

    response_filtered = client.get(
        "/api/v1/screener",
        params={"min_roe": 15},
    )

    assert response_all.status_code == 200
    assert response_filtered.status_code == 200

    all_data = response_all.json()
    filtered_data = response_filtered.json()

    assert isinstance(all_data, dict)
    assert isinstance(filtered_data, dict)

    all_companies = all_data["companies"]
    filtered_companies = filtered_data["companies"]

    assert isinstance(all_companies, list)
    assert isinstance(filtered_companies, list)

    # Current database contains 92 companies.
    assert len(all_companies) == 92

    # Filtering cannot increase the number of results.
    assert len(filtered_companies) <= len(all_companies)

    # Current API/database has matching companies for min_roe=15.
    assert len(filtered_companies) > 0

    # Every filtered company must satisfy the requested threshold.
    for company in filtered_companies:
        assert "roe_pct" in company
        assert company["roe_pct"] is not None
        assert float(company["roe_pct"]) >= 15


# ============================================================
# 5. Invalid screener parameter -> HTTP 400
# ============================================================

def test_screener_invalid_parameter_returns_400():
    response = client.get(
        "/api/v1/screener",
        params={"min_roe": "invalid"},
    )

    assert response.status_code == 400
