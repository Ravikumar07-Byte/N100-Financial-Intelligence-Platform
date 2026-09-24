"""
Day 43 — Company Profile Performance Verification.

Measures the Company Profile data-loading path for five representative
Nifty 100 companies and verifies that each completes within 3 seconds.
"""

from __future__ import annotations

import statistics
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


from dashboard.utils.db import (  # noqa: E402
    get_companies,
    get_pl,
    get_ratios,
    get_sectors,
)


TICKERS = [
    "TCS",
    "HDFCBANK",
    "HINDUNILVR",
    "RELIANCE",
    "SUNPHARMA",
]

TARGET_SECONDS = 3.0


def measure_profile_data(ticker: str) -> float:
    """
    Measure the Company Profile database/data preparation path.
    """
    start = time.perf_counter()

    companies = get_companies()
    sectors = get_sectors()
    pl = get_pl(ticker)
    ratios = get_ratios(ticker)

    # Touch the returned objects so the complete data-loading path
    # is exercised.
    _ = len(companies)
    _ = len(sectors)
    _ = len(pl)
    _ = len(ratios)

    return time.perf_counter() - start


def main() -> int:
    """
    Run the Day 43 Company Profile performance verification.
    """
    print("=" * 80)
    print("DAY 43 — COMPANY PROFILE PERFORMANCE VERIFICATION")
    print("=" * 80)
    print(f"Tickers : {len(TICKERS)}")
    print(f"Target  : < {TARGET_SECONDS:.1f} seconds each")
    print()

    results: list[tuple[str, float, bool]] = []

    for ticker in TICKERS:
        elapsed = measure_profile_data(ticker)
        passed = elapsed < TARGET_SECONDS

        results.append((ticker, elapsed, passed))

        print(
            f"{ticker:<12} | "
            f"{elapsed:.4f}s | "
            f"{'PASS' if passed else 'FAIL'}"
        )

    times = [elapsed for _, elapsed, _ in results]

    print()
    print("-" * 80)
    print(f"Minimum : {min(times):.4f}s")
    print(f"Maximum : {max(times):.4f}s")
    print(f"Average : {statistics.mean(times):.4f}s")
    print(f"Median  : {statistics.median(times):.4f}s")

    all_pass = all(passed for _, _, passed in results)

    print()
    print("=" * 80)

    if all_pass:
        print("PASS")
        print(
            "All five Company Profile data-loading measurements "
            "completed within 3 seconds."
        )
        print("=" * 80)
        return 0

    print("FAIL")
    print("One or more Company Profile measurements exceeded 3 seconds.")
    print("=" * 80)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())