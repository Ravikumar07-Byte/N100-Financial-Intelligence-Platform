from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)

print("=" * 80)
print("DAY 40 — FASTAPI ENDPOINT FUNCTIONAL TEST")
print("=" * 80)


def test(name, method, url, expected_status=200):
    print(f"\n{name}")
    print("-" * 80)
    print(f"{method} {url}")

    response = client.request(method, url)

    print("Status:", response.status_code)

    if response.status_code != expected_status:
        print("FAIL")
        print("Response:", response.text[:1000])
        return False

    print("PASS")

    try:
        data = response.json()
        print("Response keys:", list(data.keys()) if isinstance(data, dict) else type(data).__name__)

        if isinstance(data, dict):
            if "count" in data:
                print("Count:", data["count"])

            if "companies" in data and data["companies"]:
                print("First company:", data["companies"][0])

            if "sectors" in data:
                print("Sector count:", len(data["sectors"]))

    except Exception:
        print("Response:", response.text[:500])

    return True


results = []


# ------------------------------------------------------------
# SCREENER
# ------------------------------------------------------------

results.append(
    test(
        "Screener — default",
        "GET",
        "/api/v1/screener",
    )
)

results.append(
    test(
        "Screener — filters",
        "GET",
        "/api/v1/screener?min_roe=10&max_de=2&min_fcf=100&max_pe=80",
    )
)


# ------------------------------------------------------------
# SECTORS
# ------------------------------------------------------------

results.append(
    test(
        "All sectors",
        "GET",
        "/api/v1/sectors",
    )
)

results.append(
    test(
        "Sector companies",
        "GET",
        "/api/v1/sectors/Industrials/companies",
    )
)

results.append(
    test(
        "Unknown sector",
        "GET",
        "/api/v1/sectors/THIS_SECTOR_DOES_NOT_EXIST/companies",
        expected_status=404,
    )
)


# ------------------------------------------------------------
# PEERS
# ------------------------------------------------------------

results.append(
    test(
        "Peer group",
        "GET",
        "/api/v1/peers/THIS_GROUP",
        expected_status=200,
    )
)


# ------------------------------------------------------------
# VALUATION
# ------------------------------------------------------------

results.append(
    test(
        "Valuation",
        "GET",
        "/api/v1/valuation",
    )
)


# ------------------------------------------------------------
# PORTFOLIO
# ------------------------------------------------------------

results.append(
    test(
        "Portfolio",
        "GET",
        "/api/v1/portfolio",
    )
)


# ------------------------------------------------------------
# DOCUMENTS
# ------------------------------------------------------------

results.append(
    test(
        "Documents",
        "GET",
        "/api/v1/documents",
    )
)


# ------------------------------------------------------------
# HEALTH
# ------------------------------------------------------------

results.append(
    test(
        "Health",
        "GET",
        "/api/v1/health",
    )
)


# ------------------------------------------------------------
# SUMMARY
# ------------------------------------------------------------

print("\n" + "=" * 80)
print("DAY 40 TEST SUMMARY")
print("=" * 80)

passed = sum(results)
total = len(results)

print(f"Passed: {passed}/{total}")

if passed == total:
    print("RESULT: PASS")
else:
    print("RESULT: SOME TESTS FAILED")

print("=" * 80)
