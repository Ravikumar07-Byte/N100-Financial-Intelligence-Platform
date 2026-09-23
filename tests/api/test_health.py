from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_health_returns_http_200():
    response = client.get("/api/v1/health")

    assert response.status_code == 200


def test_health_status_is_ok():
    response = client.get("/api/v1/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"


def test_health_contains_db_row_counts():
    response = client.get("/api/v1/health")

    assert response.status_code == 200

    data = response.json()

    assert "db_row_counts" in data
    assert isinstance(data["db_row_counts"], dict)


def test_health_contains_all_required_tables():
    response = client.get("/api/v1/health")

    assert response.status_code == 200

    data = response.json()

    db_row_counts = data["db_row_counts"]

    required_tables = {
        "companies",
        "profitandloss",
        "balancesheet",
        "cashflow",
        "analysis",
        "documents",
        "prosandcons",
        "sectors",
        "stock_prices",
        "financial_ratios",
    }

    assert required_tables.issubset(db_row_counts.keys())


def test_health_contains_uptime_and_version():
    response = client.get("/api/v1/health")

    assert response.status_code == 200

    data = response.json()

    assert "uptime_seconds" in data
    assert "version" in data
