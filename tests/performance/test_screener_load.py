"""
Day 43 - Screener API Load Test

Runs 10 concurrent requests against the FastAPI screener endpoint
and measures individual and total response times.
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

API_URL = "http://127.0.0.1:8000/api/v1/screener"

TOTAL_REQUESTS = 10
TIMEOUT = 10


def make_request(request_number: int) -> dict:
    start = time.perf_counter()

    response = requests.get(
        API_URL,
        params={"min_roe": 15},
        timeout=TIMEOUT,
    )

    elapsed = time.perf_counter() - start

    return {
        "request": request_number,
        "status_code": response.status_code,
        "elapsed": elapsed,
        "success": response.ok,
    }


def test_10_concurrent_screener_requests():
    overall_start = time.perf_counter()

    results = []

    with ThreadPoolExecutor(max_workers=TOTAL_REQUESTS) as executor:
        futures = [executor.submit(make_request, i + 1) for i in range(TOTAL_REQUESTS)]

        for future in as_completed(futures):
            results.append(future.result())

    total_elapsed = time.perf_counter() - overall_start

    results.sort(key=lambda item: item["request"])

    print("\n" + "=" * 70)
    print("DAY 43 — SCREENER API LOAD TEST")
    print("=" * 70)

    for result in results:
        print(
            f"Request {result['request']:02d} | "
            f"HTTP {result['status_code']} | "
            f"{result['elapsed']:.4f} sec"
        )

    print("-" * 70)
    print(f"Requests:       {TOTAL_REQUESTS}")
    print(f"Total time:     {total_elapsed:.4f} sec")
    print(f"Max request:    " f"{max(r['elapsed'] for r in results):.4f} sec")
    print(
        f"Average:        "
        f"{sum(r['elapsed'] for r in results) / len(results):.4f} sec"
    )
    print("=" * 70)

    assert len(results) == TOTAL_REQUESTS
    assert all(result["success"] for result in results)

    # Day 43 requirement
    assert total_elapsed < 10, (
        f"10 concurrent requests took " f"{total_elapsed:.4f} seconds"
    )
