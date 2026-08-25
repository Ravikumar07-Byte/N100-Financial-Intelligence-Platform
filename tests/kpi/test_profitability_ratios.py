import logging

import pytest

from src.analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    check_opm_crosscheck,
    return_on_equity,
    return_on_capital_employed,
    return_on_assets,
    roce_benchmark_check,
    calculate_profitability_ratios,
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


def test_opm_crosscheck_logs_difference_above_one_percent(caplog):
    with caplog.at_level(logging.WARNING):
        result = check_opm_crosscheck(
            calculated_opm=30.0,
            source_opm=32.5,
            company_id="TEST001",
            year="2025-03",
        )

    assert result is False
    assert "OPM mismatch" in caplog.text
    assert "TEST001" in caplog.text
    assert "2025-03" in caplog.text


def test_opm_crosscheck_does_not_flag_difference_within_one_percent(caplog):
    with caplog.at_level(logging.WARNING):
        result = check_opm_crosscheck(
            calculated_opm=30.0,
            source_opm=30.5,
        )

    assert result is True
    assert "OPM mismatch" not in caplog.text


def test_financials_roce_uses_sector_benchmark():
    assert roce_benchmark_check(
        company_roce=12.0,
        broad_sector="Financials",
        sector_roce_benchmark=10.0,
    ) is True

    assert roce_benchmark_check(
        company_roce=8.0,
        broad_sector="Financials",
        sector_roce_benchmark=10.0,
    ) is False


def test_non_financial_roce_uses_absolute_threshold():
    assert roce_benchmark_check(
        company_roce=12.0,
        broad_sector="Industrials",
        absolute_threshold=10.0,
    ) is True

    assert roce_benchmark_check(
        company_roce=8.0,
        broad_sector="Industrials",
        absolute_threshold=10.0,
    ) is False


def test_calculate_profitability_ratios():
    result = calculate_profitability_ratios(
        {
            "company_id": "TEST001",
            "year": "2025-03",
            "net_profit": 200,
            "sales": 1000,
            "operating_profit": 300,
            "equity_capital": 500,
            "reserves": 500,
            "borrowings": 200,
            "total_assets": 2000,
            "opm_percentage": 30,
            "broad_sector": "Industrials",
            "absolute_roce_threshold": 10,
        }
    )

    assert result["net_profit_margin_pct"] == pytest.approx(20.0)
    assert result["operating_profit_margin_pct"] == pytest.approx(30.0)
    assert result["return_on_equity_pct"] == pytest.approx(20.0)
    assert result["return_on_capital_employed_pct"] == pytest.approx(25.0)
    assert result["return_on_assets_pct"] == pytest.approx(10.0)
    assert result["opm_crosscheck_pass"] is True
    assert result["roce_benchmark_pass"] is True
