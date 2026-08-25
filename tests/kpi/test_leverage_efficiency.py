import pytest

from src.analytics.ratios import (
    debt_to_equity,
    high_leverage_flag,
    interest_coverage_ratio,
    interest_coverage_label,
    interest_coverage_warning,
    net_debt,
    asset_turnover,
)


def test_debt_to_equity_normal():
    assert debt_to_equity(200, 500, 500) == pytest.approx(0.2)


def test_debt_to_equity_debt_free_returns_zero():
    assert debt_to_equity(0, 500, 500) == 0


def test_debt_to_equity_negative_equity():
    assert debt_to_equity(200, -600, 500) is None


def test_high_leverage_flag():
    assert high_leverage_flag(6.0, "Industrials") is True


def test_financials_high_leverage_is_suppressed():
    assert high_leverage_flag(6.0, "Financials") is False


def test_interest_coverage_interest_zero_returns_none():
    assert interest_coverage_ratio(300, 50, 0) is None


def test_interest_coverage_debt_free_label_and_warning():
    icr = interest_coverage_ratio(300, 50, 0)

    assert interest_coverage_label(icr) == "Debt Free"
    assert interest_coverage_warning(icr) is False


def test_net_debt_and_asset_turnover():
    assert net_debt(500, 200) == 300
    assert asset_turnover(1000, 500) == pytest.approx(2.0)
