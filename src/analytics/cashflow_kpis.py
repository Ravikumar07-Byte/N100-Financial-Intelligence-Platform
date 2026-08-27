"""Sprint 2 - Day 11: Cash Flow KPIs & Capital Allocation."""

from __future__ import annotations

from typing import Optional


# ---------------------------------------------------------------------------
# Free Cash Flow
# ---------------------------------------------------------------------------

def free_cash_flow(
    operating_activity: float | None,
    investing_activity: float | None,
) -> Optional[float]:
    """Calculate Free Cash Flow = CFO + CFI."""
    if operating_activity is None or investing_activity is None:
        return None

    return operating_activity + investing_activity


# ---------------------------------------------------------------------------
# CFO Quality Score
# ---------------------------------------------------------------------------

def cfo_quality_ratio(
    cfo: float | None,
    pat: float | None,
) -> Optional[float]:
    """Calculate CFO / PAT. Returns None when PAT is zero."""
    if cfo is None or pat is None or pat == 0:
        return None

    return cfo / pat


def cfo_quality_label(
    ratio: float | None,
) -> Optional[str]:
    """Classify CFO quality."""
    if ratio is None:
        return None

    if ratio > 1.0:
        return "High Quality"

    if ratio >= 0.5:
        return "Moderate"

    return "Accrual Risk"


def cfo_quality_score_5yr(
    cfo_values: list[float | None],
    pat_values: list[float | None],
) -> tuple[Optional[float], Optional[str]]:
    """
    Calculate the average CFO/PAT ratio over the available 5-year period.

    PAT = 0 or missing years are excluded from the average.
    Returns (None, None) when no valid ratios are available.
    """
    ratios = []

    for cfo, pat in zip(cfo_values[-5:], pat_values[-5:]):
        ratio = cfo_quality_ratio(cfo, pat)

        if ratio is not None:
            ratios.append(ratio)

    if not ratios:
        return None, None

    average_ratio = sum(ratios) / len(ratios)

    return average_ratio, cfo_quality_label(average_ratio)


# ---------------------------------------------------------------------------
# CapEx Intensity
# ---------------------------------------------------------------------------

def capex_intensity(
    investing_activity: float | None,
    sales: float | None,
) -> Optional[float]:
    """Calculate CapEx Intensity = abs(CFI) / Sales * 100."""
    if investing_activity is None or sales is None or sales == 0:
        return None

    return abs(investing_activity) / sales * 100


def capex_intensity_label(
    intensity: float | None,
) -> Optional[str]:
    """Classify CapEx intensity."""
    if intensity is None:
        return None

    if intensity < 3:
        return "Asset Light"

    if intensity <= 8:
        return "Moderate"

    return "Capital Intensive"


# ---------------------------------------------------------------------------
# FCF Conversion Rate
# ---------------------------------------------------------------------------

def fcf_conversion_rate(
    fcf: float | None,
    operating_profit: float | None,
) -> Optional[float]:
    """Calculate FCF Conversion Rate = FCF / Operating Profit * 100."""
    if fcf is None or operating_profit is None or operating_profit == 0:
        return None

    return fcf / operating_profit * 100


# ---------------------------------------------------------------------------
# Capital Allocation Pattern
# ---------------------------------------------------------------------------

def _sign(value: float | None) -> str:
    """Return + for positive, - for negative and 0 for zero/missing."""
    if value is None or value == 0:
        return "0"

    return "+" if value > 0 else "-"


def capital_allocation_pattern(
    cfo: float | None,
    cfi: float | None,
    cff: float | None,
    cfo_pat_ratio: float | None = None,
) -> str:
    """
    Classify capital allocation using CFO, CFI and CFF signs.

    Special case:
        (+,-,-) with high CFO/PAT -> Shareholder Returns
    """
    pattern = (
        _sign(cfo),
        _sign(cfi),
        _sign(cff),
    )

    if pattern == ("+", "-", "-"):
        if cfo_pat_ratio is not None and cfo_pat_ratio > 1.0:
            return "Shareholder Returns"

        return "Reinvestor"

    if pattern == ("+", "+", "-"):
        return "Liquidating Assets"

    if pattern == ("-", "+", "+"):
        return "Distress Signal"

    if pattern == ("-", "-", "+"):
        return "Growth Funded by Debt"

    if pattern == ("+", "+", "+"):
        return "Cash Accumulator"

    if pattern == ("-", "-", "-"):
        return "Pre-Revenue"

    if pattern == ("+", "-", "+"):
        return "Mixed"

    return "Mixed"


# ---------------------------------------------------------------------------
# Capital Allocation CSV row
# ---------------------------------------------------------------------------

def build_capital_allocation_row(
    company_id: str,
    year: str,
    cfo: float | None,
    cfi: float | None,
    cff: float | None,
    cfo_pat_ratio: float | None = None,
) -> dict:
    """Build one capital-allocation output row."""
    return {
        "company_id": company_id,
        "year": year,
        "cfo_sign": _sign(cfo),
        "cfi_sign": _sign(cfi),
        "cff_sign": _sign(cff),
        "pattern_label": capital_allocation_pattern(
            cfo,
            cfi,
            cff,
            cfo_pat_ratio,
        ),
    }
