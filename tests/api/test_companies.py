from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


# ============================================================
# 1. GET /companies -> HTTP 200
# ============================================================


def test_get_companies_returns_http_200():
    response = client.get("/api/v1/companies")

    assert response.status_code == 200


# ============================================================
# 2. GET /companies -> exactly 92 records
# ============================================================


def test_get_companies_returns_92_records():
    response = client.get("/api/v1/companies")

    assert response.status_code == 200

    data = response.json()

    # API returns an object containing companies + count
    assert isinstance(data, dict)

    assert "companies" in data
    assert "count" in data

    companies = data["companies"]

    assert isinstance(companies, list)

    # API-reported count
    assert data["count"] == 92

    # Actual returned records
    assert len(companies) == 92


# ============================================================
# 3. GET /companies -> expected fields
# ============================================================


def test_get_companies_contains_expected_fields():
    response = client.get("/api/v1/companies")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, dict)
    assert "companies" in data
    assert "count" in data

    companies = data["companies"]

    assert isinstance(companies, list)
    assert len(companies) == 92

    first_company = companies[0]

    assert isinstance(first_company, dict)

    assert "id" in first_company
    assert "company_name" in first_company


# ============================================================
# 4. GET /companies/TCS -> HTTP 200
# ============================================================


def test_get_tcs_returns_http_200():
    response = client.get("/api/v1/companies/TCS")

    assert response.status_code == 200


# ============================================================
# 5. GET /companies/TCS -> correct company data
# ============================================================


def test_get_tcs_returns_correct_company():
    response = client.get("/api/v1/companies/TCS")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, dict)

    # Required API response sections
    assert "company" in data
    assert "sector" in data
    assert "latest_kpis" in data
    assert "latest_market_data" in data

    company = data["company"]

    assert isinstance(company, dict)

    # TCS identifier
    assert company["id"] == "TCS"

    # Database/API currently stores the name without
    # the optional final period.
    assert company["company_name"].rstrip(".") == ("Tata Consultancy Services Ltd")


# ============================================================
# 6. GET /companies/INVALID -> HTTP 404
# ============================================================


def test_get_invalid_company_returns_404():
    response = client.get("/api/v1/companies/INVALID")

    assert response.status_code == 404
