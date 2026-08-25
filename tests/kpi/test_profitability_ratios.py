import pytest

from src.analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    check_opm_crosscheck,
    return_on_equity,
    return_on_capital_employed,
    return_on_assets,
)


def test_net_profit_margin_normal():
    assert net_profit_margin(200, 1000) == pytest.approx(20.0)


def test_net_profit_margin_zero_sales():
    assert net_profit_margin(200, 0) is None


def test_operating_profit_margin_normal():
    assert operating_profit_margin(300, 1000) == pytest.approx(30.0)


def test_opm_crosscheck_mismatch():
    assert check_opm_crosscheck(30.0, 32.0) is False


def test_roe_normal():
    assert return_on_equity(200, 500, 500) == pytest.approx(20.0)


def test_roe_negative_equity():
    assert return_on_equity(200, -600, 500) is None


def test_roce_normal():
    assert return_on_capital_employed(
        300,
        500,
        300,
        200,
    ) == pytest.approx(30.0)


def test_roa_zero_assets():
    assert return_on_assets(200, 0) is None
