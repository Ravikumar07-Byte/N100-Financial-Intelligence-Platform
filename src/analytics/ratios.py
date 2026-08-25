"""Sprint 2 - Day 08 Financial Ratio Engine - Profitability Ratios."""

from __future__ import annotations

import logging
from typing import Optional


logger = logging.getLogger(__name__)


def net_profit_margin(
    net_profit: float | None,
    sales: float | None,
) -> Optional[float]:
    """Net Profit Margin = Net Profit / Sales * 100."""
    if net_profit is None or sales in (None, 0):
        return None

    return (net_profit / sales) * 100


def operating_profit_margin(
    operating_profit: float | None,
    sales: float | None,
) -> Optional[float]:
    """Operating Profit Margin = Operating Profit / Sales * 100."""
    if operating_profit is None or sales in (None, 0):
        return None

    return (operating_profit / sales) * 100


def check_opm_crosscheck(
    calculated_opm: float | None,
    source_opm: float | None,
    tolerance: float = 1.0,
    company_id: str | None = None,
    year: str | None = None,
) -> bool:
    """
    Cross-check calculated OPM against the source opm_percentage.

    Returns True when the difference is within tolerance.

    When the absolute difference is greater than 1 percentage point,
    an anomaly is logged for later review.
    """
    if calculated_opm is None or source_opm is None:
        return True

    difference = abs(calculated_opm - source_opm)

    if difference > tolerance:
        logger.warning(
            "OPM mismatch: company_id=%s, year=%s, "
            "calculated_opm=%.4f, source_opm=%.4f, "
            "difference=%.4f percentage_points",
            company_id,
            year,
            calculated_opm,
            source_opm,
            difference,
        )
        return False

    return True


def return_on_equity(
    net_profit: float | None,
    equity_capital: float | None,
    reserves: float | None,
) -> Optional[float]:
    """ROE = Net Profit / (Equity Capital + Reserves) * 100."""
    if net_profit is None:
        return None

    equity = (equity_capital or 0) + (reserves or 0)

    if equity <= 0:
        return None

    return (net_profit / equity) * 100


def return_on_capital_employed(
    ebit: float | None,
    equity_capital: float | None,
    reserves: float | None,
    borrowings: float | None,
) -> Optional[float]:
    """
    ROCE = EBIT / (Equity Capital + Reserves + Borrowings) * 100.

    Returns None when capital employed is zero or negative.
    """
    if ebit is None:
        return None

    capital_employed = (
        (equity_capital or 0)
        + (reserves or 0)
        + (borrowings or 0)
    )

    if capital_employed <= 0:
        return None

    return (ebit / capital_employed) * 100


def financials_roce_benchmark(
    sector_roce: float | None,
    company_roce: float | None,
) -> Optional[float]:
    """
    Calculate the company's ROCE relative to the Financials sector.

    Result is expressed as:
        company ROCE - sector benchmark ROCE

    Positive value:
        Company ROCE is above the sector benchmark.

    Negative value:
        Company ROCE is below the sector benchmark.

    None is returned when either value is unavailable.
    """
    if sector_roce is None or company_roce is None:
        return None

    return company_roce - sector_roce


def roce_benchmark_check(
    company_roce: float | None,
    broad_sector: str | None,
    sector_roce_benchmark: float | None = None,
    absolute_threshold: float | None = None,
) -> Optional[bool]:
    """
    Apply the appropriate ROCE benchmark.

    Financials:
        Uses the supplied sector-relative benchmark.

    Other sectors:
        Uses an absolute ROCE threshold when supplied.

    Returns:
        True  -> passes benchmark
        False -> fails benchmark
        None  -> benchmark cannot be evaluated
    """
    if company_roce is None:
        return None

    sector = (broad_sector or "").strip().lower()

    if sector == "financials":
        if sector_roce_benchmark is None:
            return None

        return company_roce >= sector_roce_benchmark

    if absolute_threshold is None:
        return None

    return company_roce >= absolute_threshold


def return_on_assets(
    net_profit: float | None,
    total_assets: float | None,
) -> Optional[float]:
    """ROA = Net Profit / Total Assets * 100."""
    if net_profit is None or total_assets in (None, 0):
        return None

    return (net_profit / total_assets) * 100


def calculate_profitability_ratios(row: dict) -> dict:
    """
    Calculate all Day-08 profitability ratios.

    Expected keys:
        company_id
        year
        net_profit
        sales
        operating_profit
        equity_capital
        reserves
        borrowings
        total_assets
        opm_percentage
        broad_sector
        sector_roce_benchmark
        absolute_roce_threshold
    """

    npm = net_profit_margin(
        row.get("net_profit"),
        row.get("sales"),
    )

    opm = operating_profit_margin(
        row.get("operating_profit"),
        row.get("sales"),
    )

    roe = return_on_equity(
        row.get("net_profit"),
        row.get("equity_capital"),
        row.get("reserves"),
    )

    roce = return_on_capital_employed(
        row.get("operating_profit"),
        row.get("equity_capital"),
        row.get("reserves"),
        row.get("borrowings"),
    )

    roa = return_on_assets(
        row.get("net_profit"),
        row.get("total_assets"),
    )

    opm_matches_source = check_opm_crosscheck(
        opm,
        row.get("opm_percentage"),
        company_id=row.get("company_id"),
        year=row.get("year"),
    )

    roce_benchmark_pass = roce_benchmark_check(
        company_roce=roce,
        broad_sector=row.get("broad_sector"),
        sector_roce_benchmark=row.get("sector_roce_benchmark"),
        absolute_threshold=row.get("absolute_roce_threshold"),
    )

    return {
        "net_profit_margin_pct": npm,
        "operating_profit_margin_pct": opm,
        "return_on_equity_pct": roe,
        "return_on_capital_employed_pct": roce,
        "return_on_assets_pct": roa,
        "opm_crosscheck_pass": opm_matches_source,
        "roce_benchmark_pass": roce_benchmark_pass,
    }

# ---------------------------------------------------------------------------
# Sprint 2 - Day 09: Leverage and Efficiency Ratios
# ---------------------------------------------------------------------------

def debt_to_equity(
    borrowings: float | None,
    equity_capital: float | None,
    reserves: float | None,
) -> Optional[float]:
    """
    Debt-to-Equity = Borrowings / (Equity Capital + Reserves).

    Debt-free companies return 0.
    Returns None when equity is zero or negative.
    """
    if borrowings is None:
        return None

    equity = (equity_capital or 0) + (reserves or 0)

    if borrowings == 0:
        return 0.0

    if equity <= 0:
        return None

    return borrowings / equity


def high_leverage_flag(
    debt_equity: float | None,
    broad_sector: str | None,
    threshold: float = 5.0,
) -> bool:
    """
    Flag companies with D/E > 5.

    Financials companies are excluded because high leverage
    is structurally normal in banks, NBFCs and insurers.
    """
    if debt_equity is None:
        return False

    if (broad_sector or "").strip().lower() == "financials":
        return False

    return debt_equity > threshold


def interest_coverage_ratio(
    operating_profit: float | None,
    other_income: float | None,
    interest: float | None,
) -> Optional[float]:
    """
    Interest Coverage Ratio =
    (Operating Profit + Other Income) / Interest.

    Returns None when interest is zero or unavailable.
    """
    if operating_profit is None:
        return None

    if interest in (None, 0):
        return None

    return ((operating_profit or 0) + (other_income or 0)) / interest


def interest_coverage_label(
    icr: float | None,
) -> Optional[str]:
    """Return Debt Free label when ICR is unavailable."""
    if icr is None:
        return "Debt Free"

    return None


def interest_coverage_warning(
    icr: float | None,
    threshold: float = 1.5,
) -> bool:
    """Flag companies with ICR below 1.5."""
    if icr is None:
        return False

    return icr < threshold


def net_debt(
    borrowings: float | None,
    investments: float | None,
) -> Optional[float]:
    """
    Net Debt = Borrowings - Investments.

    Investments are used as the liquid asset proxy.
    """
    if borrowings is None and investments is None:
        return None

    return (borrowings or 0) - (investments or 0)


def asset_turnover(
    sales: float | None,
    total_assets: float | None,
) -> Optional[float]:
    """Asset Turnover = Sales / Total Assets."""
    if sales is None or total_assets in (None, 0):
        return None

    return sales / total_assets


def calculate_leverage_efficiency_ratios(row: dict) -> dict:
    """Calculate all Day-09 leverage and efficiency ratios."""

    de = debt_to_equity(
        row.get("borrowings"),
        row.get("equity_capital"),
        row.get("reserves"),
    )

    icr = interest_coverage_ratio(
        row.get("operating_profit"),
        row.get("other_income"),
        row.get("interest"),
    )

    return {
        "debt_to_equity": de,
        "high_leverage_flag": high_leverage_flag(
            de,
            row.get("broad_sector"),
        ),
        "interest_coverage": icr,
        "icr_label": interest_coverage_label(icr),
        "icr_warning_flag": interest_coverage_warning(icr),
        "net_debt": net_debt(
            row.get("borrowings"),
            row.get("investments"),
        ),
        "asset_turnover": asset_turnover(
            row.get("sales"),
            row.get("total_assets"),
        ),
    }
