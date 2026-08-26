import pytest

from src.analytics.cagr import (
    CAGR_NORMAL,
    CAGR_DECLINE_TO_LOSS,
    CAGR_TURNAROUND,
    CAGR_BOTH_NEGATIVE,
    CAGR_ZERO_BASE,
    CAGR_INSUFFICIENT,
    calculate_cagr,
    calculate_window_cagr,
    revenue_cagr,
    pat_cagr,
    eps_cagr,
    calculate_all_growth_metrics,
)


def test_normal_cagr():
    cagr, flag = calculate_cagr(100, 121, 2)

    assert cagr == pytest.approx(10.0)
    assert flag == CAGR_NORMAL


def test_turnaround_flag():
    cagr, flag = calculate_cagr(-100, 200, 3)

    assert cagr is None
    assert flag == CAGR_TURNAROUND


def test_decline_to_loss_flag():
    cagr, flag = calculate_cagr(100, -50, 3)

    assert cagr is None
    assert flag == CAGR_DECLINE_TO_LOSS


def test_both_negative_flag():
    cagr, flag = calculate_cagr(-100, -50, 3)

    assert cagr is None
    assert flag == CAGR_BOTH_NEGATIVE


def test_zero_base_flag():
    cagr, flag = calculate_cagr(0, 100, 3)

    assert cagr is None
    assert flag == CAGR_ZERO_BASE


def test_insufficient_data_flag():
    cagr, flag = calculate_cagr(
        100,
        150,
        5,
        years_available=3,
    )

    assert cagr is None
    assert flag == CAGR_INSUFFICIENT


def test_revenue_cagr_3_year():
    values = {
        "2022-03": 100,
        "2023-03": 110,
        "2024-03": 121,
        "2025-03": 133.1,
    }

    cagr, flag = revenue_cagr(values, 3)

    assert cagr == pytest.approx(10.0)
    assert flag == CAGR_NORMAL


def test_pat_cagr_decline_to_loss():
    values = {
        "2022-03": 100,
        "2023-03": 120,
        "2024-03": 80,
        "2025-03": -20,
    }

    cagr, flag = pat_cagr(values, 3)

    assert cagr is None
    assert flag == CAGR_DECLINE_TO_LOSS


def test_eps_cagr_insufficient_data():
    values = {
        "2023-03": 10,
        "2024-03": 11,
        "2025-03": 12,
    }

    cagr, flag = eps_cagr(values, 5)

    assert cagr is None
    assert flag == CAGR_INSUFFICIENT


def test_all_growth_metrics_contains_required_windows_and_flags():
    sales = {
        "2015-03": 100,
        "2016-03": 105,
        "2017-03": 110,
        "2018-03": 115,
        "2019-03": 120,
        "2020-03": 125,
        "2021-03": 130,
        "2022-03": 135,
        "2023-03": 140,
        "2024-03": 145,
        "2025-03": 150,
    }

    net_profit = sales.copy()
    eps = sales.copy()

    result = calculate_all_growth_metrics(
        yearly_sales=sales,
        yearly_net_profit=net_profit,
        yearly_eps=eps,
    )

    for metric in ("revenue", "pat", "eps"):
        for window in (3, 5, 10):
            assert f"{metric}_cagr_{window}yr" in result
            assert f"{metric}_cagr_{window}yr_flag" in result

    assert result["revenue_cagr_3yr"] is not None
    assert result["revenue_cagr_3yr_flag"] == CAGR_NORMAL
