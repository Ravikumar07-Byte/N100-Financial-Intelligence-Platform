"""
Day 43 - Screener API concurrent performance test.

Requirement:
    Run 10 concurrent screener API calls.
    All 10 requests must complete within 10 seconds.
"""

from __future__ import annotations

import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests


API_URL = "http://127.0.0.1:8000/api/v1/screener"
REQUEST_COUNT = 10
TIME_LIMIT_SECONDS = 10.0
REQUEST_TIMEOUT_SECONDS = 30.0


def make_request(request_number: int) -> dict:
    """Execute one screener API request and return timing information."""
    start = time.perf_counter()

    try:
        response = requests.get(
            API_URL,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

        elapsed = time.perf_counter() - start

        return {
            "request": request_number,
            "status": response.status_code,
            "elapsed": elapsed,
            "success": response.ok,
            "error": None,
        }

    except requests.RequestException as exc:
        elapsed = time.perf_counter() - start

        return {
            "request": request_number,
            "status": None,
            "elapsed": elapsed,
            "success": False,
            "error": str(exc),
        }


def main() -> None:
    """Run the 10-request concurrent performance test."""
    print("=" * 80)
    print("DAY 43 — SCREENER API LOAD TEST")
    print("=" * 80)
    print(f"Endpoint : {API_URL}")
    print(f"Requests : {REQUEST_COUNT}")
    print()

    overall_start = time.perf_counter()

    results: list[dict] = []

    with ThreadPoolExecutor(max_workers=REQUEST_COUNT) as executor:
        futures = [
            executor.submit(make_request, request_number)
            for request_number in range(1, REQUEST_COUNT + 1)
        ]

        for future in as_completed(futures):
            results.append(future.result())

    total_elapsed = time.perf_counter() - overall_start

    results.sort(key=lambda item: item["request"])

    print("Individual requests:")
    print("-" * 80)

    for result in results:
        if result["success"]:
            print(
                f"Request {result['request']:02d} | "
                f"HTTP {result['status']} | "
                f"{result['elapsed']:.3f}s"
            )
        else:
            print(
                f"Request {result['request']:02d} | "
                f"FAILED | "
                f"{result['elapsed']:.3f}s | "
                f"{result['error']}"
            )

    successful = [
        result["elapsed"]
        for result in results
        if result["success"]
    ]

    failed = [
        result
        for result in results
        if not result["success"]
    ]

    print()
    print("=" * 80)
    print("RESULT")
    print("=" * 80)

    print(f"Total wall-clock time : {total_elapsed:.3f}s")
    print(f"Successful requests   : {len(successful)}/{REQUEST_COUNT}")
    print(f"Failed requests       : {len(failed)}")

    if successful:
        print(f"Minimum response      : {min(successful):.3f}s")
        print(f"Maximum response      : {max(successful):.3f}s")
        print(f"Average response      : {statistics.mean(successful):.3f}s")
        print(f"Median response       : {statistics.median(successful):.3f}s")

    print()

    if len(successful) == REQUEST_COUNT and total_elapsed <= TIME_LIMIT_SECONDS:
        print("PASS")
        print(
            f"All {REQUEST_COUNT} concurrent screener requests "
            f"completed within {TIME_LIMIT_SECONDS:.0f} seconds."
        )
    else:
        print("FAIL")

        if len(successful) != REQUEST_COUNT:
            print("Reason: one or more API requests failed.")

        if total_elapsed > TIME_LIMIT_SECONDS:
            print(
                f"Reason: total execution time "
                f"({total_elapsed:.3f}s) exceeded "
                f"{TIME_LIMIT_SECONDS:.0f}s."
            )

    print("=" * 80)


if __name__ == "__main__":
    main()