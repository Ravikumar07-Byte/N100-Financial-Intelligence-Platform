"""
Day 43 - Company Profile Performance Test

Measures the data-loading time used by the Streamlit
Company Profile screen for 5 representative tickers.

Target:
    Each ticker must complete in under 3 seconds.
"""

import time

import pytest

from src.dashboard.utils.db import (
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


@pytest.mark.parametrize("ticker", TICKERS)
def test_company_profile_load_time(ticker):
    """
    Measure the database/data-loading path used by
    the Company Profile dashboard.
    """

    start = time.perf_counter()

    # Same data-loading calls used by 02_profile.py
    companies = get_companies()
    sectors = get_sectors()
    ratios = get_ratios(ticker)
    pl = get_pl(ticker)

    elapsed = time.perf_counter() - start

    # Basic correctness checks
    assert companies is not None
    assert sectors is not None
    assert ratios is not None
    assert pl is not None

    print()
    print("=" * 70)
    print(f"COMPANY PROFILE PERFORMANCE — {ticker}")
    print("=" * 70)
    print(f"Companies rows : {len(companies)}")
    print(f"Sector rows    : {len(sectors)}")
    print(f"Ratio rows     : {len(ratios)}")
    print(f"P&L rows       : {len(pl)}")
    print(f"Load time      : {elapsed:.4f} sec")
    print("Target         : < 3.0000 sec")
    print("=" * 70)

    assert elapsed < 3.0, (
        f"Company Profile data load for {ticker} "
        f"took {elapsed:.4f} seconds; target is < 3 seconds."
    )
