"""Sprint 2 - Day 10: CAGR Engine - All Growth Metrics."""

from __future__ import annotations

from typing import Optional


# ---------------------------------------------------------------------------
# CAGR flags
# ---------------------------------------------------------------------------

CAGR_NORMAL = "NORMAL"
CAGR_DECLINE_TO_LOSS = "DECLINE_TO_LOSS"
CAGR_TURNAROUND = "TURNAROUND"
CAGR_BOTH_NEGATIVE = "BOTH_NEGATIVE"
CAGR_ZERO_BASE = "ZERO_BASE"
CAGR_INSUFFICIENT = "INSUFFICIENT"


# ---------------------------------------------------------------------------
# Core CAGR calculation
# ---------------------------------------------------------------------------

def calculate_cagr(
    start_value: float | None,
    end_value: float | None,
    years: int,
    years_available: int | None = None,
) -> tuple[Optional[float], str]:
    """
    Calculate CAGR with the required financial edge-case flags.

    Formula:
        ((end / start) ** (1 / years) - 1) * 100

    Returns:
        (cagr_percentage, flag)

    Normal case:
        Positive start and positive end -> CAGR calculated.

    Edge cases:
        Positive -> Negative : DECLINE_TO_LOSS
        Negative -> Positive : TURNAROUND
        Negative -> Negative : BOTH_NEGATIVE
        Zero base            : ZERO_BASE
        Insufficient data    : INSUFFICIENT
    """

    if years <= 0:
        raise ValueError("years must be greater than zero")

    if years_available is not None and years_available < years:
        return None, CAGR_INSUFFICIENT

    if start_value is None or end_value is None:
        return None, CAGR_INSUFFICIENT

    if start_value == 0:
        return None, CAGR_ZERO_BASE

    if start_value > 0 and end_value > 0:
        cagr = ((end_value / start_value) ** (1 / years) - 1) * 100
        return cagr, CAGR_NORMAL

    if start_value > 0 and end_value < 0:
        return None, CAGR_DECLINE_TO_LOSS

    if start_value < 0 and end_value > 0:
        return None, CAGR_TURNAROUND

    if start_value < 0 and end_value < 0:
        return None, CAGR_BOTH_NEGATIVE

    # Positive -> exactly zero is treated as decline to loss.
    if start_value > 0 and end_value == 0:
        return None, CAGR_DECLINE_TO_LOSS

    # Negative -> exactly zero is treated as turnaround.
    if start_value < 0 and end_value == 0:
        return None, CAGR_TURNAROUND

    return None, CAGR_INSUFFICIENT


# ---------------------------------------------------------------------------
# Year-window CAGR
# ---------------------------------------------------------------------------

def calculate_window_cagr(
    values: dict[str, float | None],
    window_years: int,
) -> tuple[Optional[float], str]:
    """
    Calculate CAGR between the latest available year and the year
    exactly `window_years` before it.

    Example:
        values = {
            "2021-03": 100,
            "2022-03": 110,
            "2023-03": 121,
            "2024-03": 133.1,
        }

        window_years=3

    Uses:
        2021 -> 2024
        n = 3
    """

    if window_years <= 0:
        raise ValueError("window_years must be greater than zero")

    valid_values = {
        str(year): value
        for year, value in values.items()
        if value is not None
        and str(year)[:4].isdigit()
        and str(year).strip().upper() != "TTM"
    }

    if len(valid_values) < window_years + 1:
        return None, CAGR_INSUFFICIENT

    sorted_years = sorted(
        valid_values,
        key=lambda year: int(str(year)[:4]),
    )

    end_year = sorted_years[-1]
    end_year_number = int(str(end_year)[:4])
    start_year_number = end_year_number - window_years

    start_year = next(
        (
            year
            for year in sorted_years
            if int(str(year)[:4]) == start_year_number
        ),
        None,
    )

    if start_year is None:
        return None, CAGR_INSUFFICIENT

    return calculate_cagr(
        valid_values[start_year],
        valid_values[end_year],
        window_years,
        years_available=window_years,
    )


# ---------------------------------------------------------------------------
# Revenue CAGR
# ---------------------------------------------------------------------------

def revenue_cagr(
    yearly_sales: dict[str, float | None],
    window_years: int,
) -> tuple[Optional[float], str]:
    """Calculate Revenue CAGR for the requested year window."""
    return calculate_window_cagr(yearly_sales, window_years)


# ---------------------------------------------------------------------------
# PAT / Net Profit CAGR
# ---------------------------------------------------------------------------

def pat_cagr(
    yearly_net_profit: dict[str, float | None],
    window_years: int,
) -> tuple[Optional[float], str]:
    """Calculate PAT / Net Profit CAGR for the requested year window."""
    return calculate_window_cagr(yearly_net_profit, window_years)


# ---------------------------------------------------------------------------
# EPS CAGR
# ---------------------------------------------------------------------------

def eps_cagr(
    yearly_eps: dict[str, float | None],
    window_years: int,
) -> tuple[Optional[float], str]:
    """Calculate EPS CAGR for the requested year window."""
    return calculate_window_cagr(yearly_eps, window_years)


# ---------------------------------------------------------------------------
# All required growth metrics
# ---------------------------------------------------------------------------

def calculate_all_growth_metrics(
    yearly_sales: dict[str, float | None],
    yearly_net_profit: dict[str, float | None],
    yearly_eps: dict[str, float | None],
) -> dict:
    """
    Calculate Revenue, PAT and EPS CAGR for 3-year, 5-year and 10-year
    windows.

    Each CAGR value is stored together with its separate flag.
    """

    result = {}

    for window in (3, 5, 10):
        revenue_value, revenue_flag = revenue_cagr(
            yearly_sales,
            window,
        )

        pat_value, pat_flag = pat_cagr(
            yearly_net_profit,
            window,
        )

        eps_value, eps_flag = eps_cagr(
            yearly_eps,
            window,
        )

        result[f"revenue_cagr_{window}yr"] = revenue_value
        result[f"revenue_cagr_{window}yr_flag"] = revenue_flag

        result[f"pat_cagr_{window}yr"] = pat_value
        result[f"pat_cagr_{window}yr_flag"] = pat_flag

        result[f"eps_cagr_{window}yr"] = eps_value
        result[f"eps_cagr_{window}yr_flag"] = eps_flag

    return result
