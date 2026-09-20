import requests
import json

BASE_URL = "http://127.0.0.1:8000"

session = requests.Session()


def check(name, method, url, expected_status=200, params=None):
    print("\n" + "=" * 80)
    print(name)
    print("=" * 80)

    try:
        response = session.request(
            method,
            BASE_URL + url,
            params=params,
            timeout=20,
        )

        print("URL:", response.url)
        print("STATUS:", response.status_code)
        print("EXPECTED:", expected_status)

        if response.status_code == expected_status:
            print("PASS")

            try:
                data = response.json()

                if isinstance(data, dict):
                    print("Response keys:", list(data.keys()))
                elif isinstance(data, list):
                    print("Response type: list")
                    print("Items:", len(data))

                print(
                    json.dumps(
                        data,
                        indent=2,
                        default=str
                    )[:3000]
                )

            except Exception:
                print("Response:")
                print(response.text[:3000])

            return True

        else:
            print("FAIL")
            print("Response:")
            print(response.text[:3000])
            return False

    except Exception as e:
        print("ERROR:", repr(e))
        return False


results = []


# ------------------------------------------------------------------
# 1. SCREENER
# ------------------------------------------------------------------

results.append(
    check(
        "1. GET /api/v1/screener",
        "GET",
        "/api/v1/screener",
        200,
        params={
            "min_roe": 15,
            "max_de": 1,
            "min_fcf": 0,
            "min_rev_cagr_5yr": 5,
            "min_pat_cagr_5yr": 5,
            "max_pe": 50,
        },
    )
)


# Screener with sector
results.append(
    check(
        "2. GET /api/v1/screener?sector=...",
        "GET",
        "/api/v1/screener",
        200,
        params={
            "sector": "Information Technology"
        },
    )
)


# Invalid screener parameter
results.append(
    check(
        "3. Screener invalid parameter",
        "GET",
        "/api/v1/screener",
        400,
        params={
            "min_roe": "INVALID"
        },
    )
)


# ------------------------------------------------------------------
# 2. SECTORS
# ------------------------------------------------------------------

results.append(
    check(
        "4. GET /api/v1/sectors",
        "GET",
        "/api/v1/sectors",
        200,
    )
)


# ------------------------------------------------------------------
# 3. SECTOR COMPANIES
# ------------------------------------------------------------------

# Change this if your actual sector name differs.
TEST_SECTOR = "Information Technology"


results.append(
    check(
        "5. GET /api/v1/sectors/{sector}/companies",
        "GET",
        f"/api/v1/sectors/{TEST_SECTOR}/companies",
        200,
    )
)


# Unknown sector
results.append(
    check(
        "6. Unknown sector -> 404",
        "GET",
        "/api/v1/sectors/THIS_SECTOR_DOES_NOT_EXIST/companies",
        404,
    )
)


# ------------------------------------------------------------------
# 4. PEERS
# ------------------------------------------------------------------

# Change this to an actual peer group from your database.
TEST_PEER_GROUP = "IT Services"


results.append(
    check(
        "7. GET /api/v1/peers/{group_name}",
        "GET",
        f"/api/v1/peers/{TEST_PEER_GROUP}",
        200,
    )
)


# Unknown peer group
results.append(
    check(
        "8. Unknown peer group -> 404",
        "GET",
        "/api/v1/peers/THIS_GROUP_DOES_NOT_EXIST",
        404,
    )
)


# ------------------------------------------------------------------
# 5. PEER COMPARISON
# ------------------------------------------------------------------

# Change to an actual ticker in your database.
TEST_TICKER = "RELIANCE"


results.append(
    check(
        "9. GET /api/v1/companies/{ticker}/peers/compare",
        "GET",
        f"/api/v1/companies/{TEST_TICKER}/peers/compare",
        200,
    )
)


# ------------------------------------------------------------------
# 6. MARKET CAP / VALUATION HISTORY
# ------------------------------------------------------------------

results.append(
    check(
        "10. GET /api/v1/market-cap/{ticker}",
        "GET",
        f"/api/v1/market-cap/{TEST_TICKER}",
        200,
    )
)


# ------------------------------------------------------------------
# 7. PORTFOLIO STATS
# ------------------------------------------------------------------

results.append(
    check(
        "11. GET /api/v1/portfolio/stats",
        "GET",
        "/api/v1/portfolio/stats",
        200,
    )
)


# ------------------------------------------------------------------
# 8. COMPANY DOCUMENTS
# ------------------------------------------------------------------

results.append(
    check(
        "12. GET /api/v1/companies/{ticker}/documents",
        "GET",
        f"/api/v1/companies/{TEST_TICKER}/documents",
        200,
    )
)


# ------------------------------------------------------------------
# SUMMARY
# ------------------------------------------------------------------

print("\n")
print("=" * 80)
print("DAY 40 API TEST SUMMARY")
print("=" * 80)

passed = sum(results)
total = len(results)
failed = total - passed

print(f"Passed : {passed}")
print(f"Failed : {failed}")
print(f"Total  : {total}")

if failed == 0:
    print("\nALL DAY 40 API TESTS PASSED")
else:
    print("\nSOME DAY 40 API TESTS FAILED")

print("=" * 80)