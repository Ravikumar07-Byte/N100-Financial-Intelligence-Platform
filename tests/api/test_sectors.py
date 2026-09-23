from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


# ============================================================
# 1. GET /sectors -> HTTP 200
# ============================================================


def test_get_sectors_returns_http_200():
    response = client.get("/api/v1/sectors")

    assert response.status_code == 200


# ============================================================
# 2. GET /sectors -> correct response structure
# ============================================================


def test_get_sectors_returns_sector_list():
    response = client.get("/api/v1/sectors")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, dict)
    assert "count" in data
    assert "sectors" in data

    assert isinstance(data["count"], int)
    assert isinstance(data["sectors"], list)


# ============================================================
# 3. Current database contains exactly 10 sectors
# ============================================================


def test_get_sectors_returns_10_sectors():
    response = client.get("/api/v1/sectors")

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 10
    assert len(data["sectors"]) == 10


# ============================================================
# 4. Every sector has the expected fields
# ============================================================


def test_sector_objects_have_expected_fields():
    response = client.get("/api/v1/sectors")

    assert response.status_code == 200

    data = response.json()

    required_fields = {
        "sector",
        "company_count",
        "median_roe",
        "median_pe",
        "median_de",
    }

    for sector in data["sectors"]:
        assert isinstance(sector, dict)
        assert required_fields.issubset(sector.keys())


# ============================================================
# 5. Information Technology sector exists
# ============================================================


def test_information_technology_sector_exists():
    response = client.get("/api/v1/sectors")

    assert response.status_code == 200

    data = response.json()

    sector_names = {sector["sector"] for sector in data["sectors"]}

    assert "Information Technology" in sector_names


# ============================================================
# 6. GET Information Technology companies -> HTTP 200
# ============================================================


def test_information_technology_companies_returns_http_200():
    response = client.get("/api/v1/sectors/Information%20Technology/companies")

    assert response.status_code == 200


# ============================================================
# 7. Information Technology response structure
# ============================================================


def test_information_technology_companies_response_structure():
    response = client.get("/api/v1/sectors/Information%20Technology/companies")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, dict)

    assert "sector" in data
    assert "count" in data
    assert "companies" in data

    assert data["sector"] == "Information Technology"
    assert isinstance(data["count"], int)
    assert isinstance(data["companies"], list)


# ============================================================
# 8. Current IT sector contains 5 companies
# ============================================================


def test_information_technology_contains_5_companies():
    response = client.get("/api/v1/sectors/Information%20Technology/companies")

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 5
    assert len(data["companies"]) == 5


# ============================================================
# 9. Every returned company belongs to IT
# ============================================================


def test_information_technology_contains_only_it_companies():
    response = client.get("/api/v1/sectors/Information%20Technology/companies")

    assert response.status_code == 200

    data = response.json()

    companies = data["companies"]

    assert len(companies) > 0

    for company in companies:
        assert company["broad_sector"] == "Information Technology"


# ============================================================
# 10. Expected IT companies are present
# ============================================================


def test_information_technology_contains_expected_companies():
    response = client.get("/api/v1/sectors/Information%20Technology/companies")

    assert response.status_code == 200

    data = response.json()

    company_ids = {company["id"] for company in data["companies"]}

    expected_companies = {
        "HCLTECH",
        "INFY",
        "LTIM",
        "TCS",
        "TECHM",
    }

    assert expected_companies.issubset(company_ids)


# ============================================================
# 11. IT companies contain expected fields
# ============================================================


def test_information_technology_company_fields():
    response = client.get("/api/v1/sectors/Information%20Technology/companies")

    assert response.status_code == 200

    data = response.json()

    required_fields = {
        "id",
        "company_name",
        "broad_sector",
        "sub_sector",
        "market_cap_category",
    }

    for company in data["companies"]:
        assert required_fields.issubset(company.keys())


# ============================================================
# 12. Unknown sector returns HTTP 404
# ============================================================


def test_unknown_sector_returns_404():
    response = client.get("/api/v1/sectors/INVALID_SECTOR/companies")

    assert response.status_code == 404


# ============================================================
# 13. Short IT alias is not currently an implemented route
# ============================================================


def test_it_short_alias_is_not_implemented():
    response = client.get("/api/v1/sectors/IT/companies")

    assert response.status_code == 404
