"""Sprint 2 - Day 08 Financial Ratio Engine."""

from typing import Optional


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
) -> bool:
    """Check calculated OPM against source OPM."""
    if calculated_opm is None or source_opm is None:
        return True
    return abs(calculated_opm - source_opm) <= tolerance


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
    """ROCE = EBIT / (Equity + Reserves + Borrowings) * 100."""
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


def return_on_assets(
    net_profit: float | None,
    total_assets: float | None,
) -> Optional[float]:
    """ROA = Net Profit / Total Assets * 100."""
    if net_profit is None or total_assets in (None, 0):
        return None

    return (net_profit / total_assets) * 100


def calculate_profitability_ratios(row: dict) -> dict:
    """Calculate all Day 08 profitability ratios."""

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
        row.get("ebit"),
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
    )

    return {
        "net_profit_margin_pct": npm,
        "operating_profit_margin_pct": opm,
        "return_on_equity_pct": roe,
        "return_on_capital_employed_pct": roce,
        "return_on_assets_pct": roa,
        "opm_crosscheck_pass": opm_matches_source,
    }
