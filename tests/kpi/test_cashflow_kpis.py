import pytest

from src.analytics.cashflow_kpis import (
    free_cash_flow,
    cfo_quality_ratio,
    cfo_quality_label,
    cfo_quality_score_5yr,
    capex_intensity,
    capex_intensity_label,
    fcf_conversion_rate,
    capital_allocation_pattern,
    build_capital_allocation_row,
)


def test_free_cash_flow():
    assert free_cash_flow(100, -40) == pytest.approx(60)


def test_free_cash_flow_negative_allowed():
    assert free_cash_flow(50, -100) == pytest.approx(-50)


def test_cfo_quality_ratio():
    assert cfo_quality_ratio(120, 100) == pytest.approx(1.2)


def test_cfo_quality_pat_zero_returns_none():
    assert cfo_quality_ratio(100, 0) is None


def test_cfo_quality_labels():
    assert cfo_quality_label(1.2) == "High Quality"
    assert cfo_quality_label(0.75) == "Moderate"
    assert cfo_quality_label(0.3) == "Accrual Risk"


def test_cfo_quality_score_5yr():
    cfo = [100, 110, 120, 130, 140]
    pat = [100, 100, 100, 100, 100]

    score, label = cfo_quality_score_5yr(cfo, pat)

    assert score == pytest.approx(1.2)
    assert label == "High Quality"


def test_capex_intensity():
    assert capex_intensity(-50, 1000) == pytest.approx(5.0)


def test_capex_intensity_labels():
    assert capex_intensity_label(2.5) == "Asset Light"
    assert capex_intensity_label(5.0) == "Moderate"
    assert capex_intensity_label(10.0) == "Capital Intensive"


def test_fcf_conversion_rate():
    assert fcf_conversion_rate(60, 100) == pytest.approx(60.0)


def test_fcf_conversion_zero_operating_profit():
    assert fcf_conversion_rate(60, 0) is None


def test_capital_allocation_reinvestor():
    assert capital_allocation_pattern(100, -50, -30) == "Reinvestor"


def test_capital_allocation_shareholder_returns():
    assert (
        capital_allocation_pattern(150, -50, -30, cfo_pat_ratio=1.5)
        == "Shareholder Returns"
    )


def test_capital_allocation_liquidating_assets():
    assert capital_allocation_pattern(100, 50, -30) == "Liquidating Assets"


def test_capital_allocation_distress_signal():
    assert capital_allocation_pattern(-100, 50, 30) == "Distress Signal"


def test_capital_allocation_growth_funded_by_debt():
    assert capital_allocation_pattern(-100, -50, 100) == "Growth Funded by Debt"


def test_capital_allocation_cash_accumulator():
    assert capital_allocation_pattern(100, 50, 30) == "Cash Accumulator"


def test_capital_allocation_pre_revenue():
    assert capital_allocation_pattern(-100, -50, -30) == "Pre-Revenue"


def test_capital_allocation_mixed():
    assert capital_allocation_pattern(100, -50, 30) == "Mixed"


def test_build_capital_allocation_row():
    result = build_capital_allocation_row(
        company_id="TCS",
        year="2025-03",
        cfo=100,
        cfi=-50,
        cff=-30,
    )

    assert result == {
        "company_id": "TCS",
        "year": "2025-03",
        "cfo_sign": "+",
        "cfi_sign": "-",
        "cff_sign": "-",
        "pattern_label": "Reinvestor",
    }
