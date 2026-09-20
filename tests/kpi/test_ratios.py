import pytest

from src.analytics.ratios import (
    return_on_equity,
    debt_to_equity,
    high_leverage_flag,
    interest_coverage_ratio,
    interest_coverage_warning,
    check_opm_crosscheck,
    net_profit_margin,
    operating_profit_margin,
    return_on_assets,
    asset_turnover,
)


# ============================================================
# 1. ROE — positive equity
# ============================================================

def test_roe_with_positive_equity():
    result = return_on_equity(
        net_profit=100,
        equity_capital=500,
        reserves=500,
    )

    assert result == pytest.approx(10.0)


# ============================================================
# 2. ROE — negative equity
# ============================================================

def test_roe_with_negative_equity_returns_none():
    result = return_on_equity(
        net_profit=100,
        equity_capital=-600,
        reserves=100,
    )

    assert result is None


# ============================================================
# 3. ROE — zero equity
# ============================================================

def test_roe_with_zero_equity_returns_none():
    result = return_on_equity(
        net_profit=100,
        equity_capital=500,
        reserves=-500,
    )

    assert result is None


# ============================================================
# 4. D/E — normal calculation
# ============================================================

def test_debt_to_equity_normal_calculation():
    result = debt_to_equity(
        borrowings=300,
        equity_capital=500,
        reserves=500,
    )

    assert result == pytest.approx(0.3)


# ============================================================
# 5. D/E — debt free
# ============================================================

def test_debt_to_equity_debt_free_returns_zero():
    result = debt_to_equity(
        borrowings=0,
        equity_capital=500,
        reserves=500,
    )

    assert result == 0.0


# ============================================================
# 6. D/E — negative equity
# ============================================================

def test_debt_to_equity_negative_equity_returns_none():
    result = debt_to_equity(
        borrowings=300,
        equity_capital=-700,
        reserves=100,
    )

    assert result is None


# ============================================================
# 7. D/E — zero equity
# ============================================================

def test_debt_to_equity_zero_equity_returns_none():
    result = debt_to_equity(
        borrowings=300,
        equity_capital=500,
        reserves=-500,
    )

    assert result is None


# ============================================================
# 8. D/E > 5 — non-financial flag
# ============================================================

def test_debt_to_equity_above_five_flags_non_financial():
    result = high_leverage_flag(
        debt_equity=6.0,
        broad_sector="Industrials",
    )

    assert result is True


# ============================================================
# 9. D/E = 5 — threshold does not flag
# ============================================================

def test_debt_to_equity_at_five_does_not_flag():
    result = high_leverage_flag(
        debt_equity=5.0,
        broad_sector="Industrials",
    )

    assert result is False


# ============================================================
# 10. Financial company high D/E — no flag
# ============================================================

def test_high_leverage_financial_company_not_flagged():
    result = high_leverage_flag(
        debt_equity=10.0,
        broad_sector="Financials",
    )

    assert result is False


# ============================================================
# 11. ICR — normal calculation
# ============================================================

def test_interest_coverage_normal_calculation():
    result = interest_coverage_ratio(
        operating_profit=500,
        other_income=100,
        interest=100,
    )

    assert result == pytest.approx(6.0)


# ============================================================
# 12. ICR — interest = 0
# ============================================================

def test_interest_coverage_interest_zero_returns_none():
    result = interest_coverage_ratio(
        operating_profit=100,
        other_income=20,
        interest=0,
    )

    assert result is None


# ============================================================
# 13. ICR — missing interest
# ============================================================

def test_interest_coverage_missing_interest_returns_none():
    result = interest_coverage_ratio(
        operating_profit=100,
        other_income=20,
        interest=None,
    )

    assert result is None


# ============================================================
# 14. ICR warning — below threshold
# ============================================================

def test_interest_coverage_warning_below_threshold():
    result = interest_coverage_warning(
        icr=1.2,
    )

    assert result is True


# ============================================================
# 15. ICR warning — safe
# ============================================================

def test_interest_coverage_warning_above_threshold():
    result = interest_coverage_warning(
        icr=2.0,
    )

    assert result is False


# ============================================================
# 16. OPM cross-check — within tolerance
# ============================================================

def test_opm_crosscheck_within_tolerance():
    result = check_opm_crosscheck(
        calculated_opm=20.0,
        source_opm=20.5,
    )

    assert result is True


# ============================================================
# 17. OPM cross-check — divergence
# ============================================================

def test_opm_crosscheck_divergence_flag():
    result = check_opm_crosscheck(
        calculated_opm=20.0,
        source_opm=25.0,
    )

    assert result is False


# ============================================================
# 18. Net profit margin
# ============================================================

def test_net_profit_margin_calculation():
    result = net_profit_margin(
        net_profit=150,
        sales=1000,
    )

    assert result == pytest.approx(15.0)


# ============================================================
# 19. Operating profit margin
# ============================================================

def test_operating_profit_margin_calculation():
    result = operating_profit_margin(
        operating_profit=200,
        sales=1000,
    )

    assert result == pytest.approx(20.0)


# ============================================================
# 20. Return on assets
# ============================================================

def test_return_on_assets_calculation():
    result = return_on_assets(
        net_profit=100,
        total_assets=1000,
    )

    assert result == pytest.approx(10.0)
