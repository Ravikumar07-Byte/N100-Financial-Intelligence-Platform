"""
Sprint 3 - Day 15
Screener Engine Tests
"""

import pytest

from src.screener.engine import ScreenerEngine


@pytest.fixture
def engine():
    """Create screener engine."""
    return ScreenerEngine()


# -------------------------------------------------------------------
# Configuration tests
# -------------------------------------------------------------------

def test_screener_configuration(engine):
    """Verify all six screener presets are configured."""

    expected = {
        "quality_compounder",
        "value_pick",
        "growth_accelerator",
        "dividend_champion",
        "debt_free_blue_chip",
        "turnaround_watch",
    }

    assert set(engine.get_screener_names()) == expected
    assert len(engine.get_screener_names()) == 6


# -------------------------------------------------------------------
# Universe tests
# -------------------------------------------------------------------

def test_universe_has_92_companies(engine):
    """Verify the N100 company universe."""

    df = engine.load_universe()

    assert len(df) == 92
    assert df["company_id"].nunique() == 92


def test_universe_has_required_columns(engine):
    """Verify required screener metrics exist."""

    df = engine.load_universe()

    required_columns = {
        "company_id",
        "company_name",
        "broad_sector",
        "return_on_equity_pct",
        "debt_to_equity",
        "free_cash_flow_cr",
        "revenue_cagr_5yr",
        "pat_cagr_5yr",
        "pe_ratio",
        "pb_ratio",
        "dividend_yield_pct",
        "dividend_payout_ratio_pct",
        "sales",
    }

    assert required_columns.issubset(df.columns)


# -------------------------------------------------------------------
# Quality Compounder
# -------------------------------------------------------------------

def test_quality_compounder_filters(engine):
    """Verify Quality Compounder thresholds."""

    result = engine.run("quality_compounder")

    assert len(result) > 0
    assert result["return_on_equity_pct"].gt(15).all()
    assert result["free_cash_flow_cr"].gt(0).all()
    assert result["revenue_cagr_5yr"].gt(10).all()

    non_financial = result[
        result["broad_sector"] != "Financials"
    ]

    assert non_financial["debt_to_equity"].lt(1).all()


# -------------------------------------------------------------------
# Value Pick
# -------------------------------------------------------------------

def test_value_pick_filters(engine):
    """Verify Value Pick thresholds."""

    result = engine.run("value_pick")

    assert len(result) > 0
    assert result["pe_ratio"].lt(20).all()
    assert result["pb_ratio"].lt(3).all()
    assert result["dividend_yield_pct"].gt(1).all()

    non_financial = result[
        result["broad_sector"] != "Financials"
    ]

    assert non_financial["debt_to_equity"].lt(2).all()


# -------------------------------------------------------------------
# Growth Accelerator
# -------------------------------------------------------------------

def test_growth_accelerator_filters(engine):
    """Verify Growth Accelerator thresholds."""

    result = engine.run("growth_accelerator")

    assert len(result) > 0
    assert result["pat_cagr_5yr"].gt(20).all()
    assert result["revenue_cagr_5yr"].gt(15).all()

    non_financial = result[
        result["broad_sector"] != "Financials"
    ]

    assert non_financial["debt_to_equity"].lt(2).all()


# -------------------------------------------------------------------
# Dividend Champion
# -------------------------------------------------------------------

def test_dividend_champion_filters(engine):
    """Verify Dividend Champion thresholds."""

    result = engine.run("dividend_champion")

    assert len(result) > 0
    assert result["dividend_yield_pct"].gt(2).all()
    assert result["dividend_payout_ratio_pct"].lt(80).all()
    assert result["free_cash_flow_cr"].gt(0).all()


# -------------------------------------------------------------------
# Debt-Free Blue Chip
# -------------------------------------------------------------------

def test_debt_free_blue_chip_filters(engine):
    """Verify Debt-Free Blue Chip thresholds."""

    result = engine.run("debt_free_blue_chip")

    assert len(result) > 0
    assert result["return_on_equity_pct"].gt(12).all()
    assert result["sales"].gt(5000).all()

    non_financial = result[
        result["broad_sector"] != "Financials"
    ]

    assert non_financial["debt_to_equity"].le(0).all()


# -------------------------------------------------------------------
# Turnaround Watch
# -------------------------------------------------------------------

def test_turnaround_metrics(engine):
    """Verify historical Turnaround metrics are calculated."""

    historical = engine.load_historical_metrics()

    assert len(historical) > 0
    assert "company_id" in historical.columns
    assert "year" in historical.columns
    assert "debt_to_equity" in historical.columns
    assert "sales" in historical.columns

    metrics = engine.calculate_turnaround_metrics(
        historical
    )

    assert len(metrics) > 0
    assert "company_id" in metrics.columns
    assert "revenue_cagr_3yr" in metrics.columns
    assert "debt_to_equity_declining" in metrics.columns


def test_turnaround_watch_filters(engine):
    """Verify Turnaround Watch thresholds."""

    result = engine.run("turnaround_watch")

    assert len(result) > 0

    assert result["revenue_cagr_3yr"].gt(10).all()
    assert result["free_cash_flow_cr"].gt(0).all()
    assert result["debt_to_equity_declining"].eq(True).all()


# -------------------------------------------------------------------
# Duplicate protection
# -------------------------------------------------------------------

@pytest.mark.parametrize(
    "screener_name",
    [
        "quality_compounder",
        "value_pick",
        "growth_accelerator",
        "dividend_champion",
        "debt_free_blue_chip",
        "turnaround_watch",
    ],
)
def test_no_duplicate_companies(
    engine,
    screener_name,
):
    """Every screener should return one row per company."""

    result = engine.run(screener_name)

    assert len(result) == result["company_id"].nunique()


# -------------------------------------------------------------------
# Result range validation
# -------------------------------------------------------------------

@pytest.mark.parametrize(
    "screener_name",
    [
        "quality_compounder",
        "value_pick",
        "growth_accelerator",
        "dividend_champion",
        "debt_free_blue_chip",
        "turnaround_watch",
    ],
)
def test_screener_result_not_empty(
    engine,
    screener_name,
):
    """Every configured screener must return at least one company."""

    result = engine.run(screener_name)

    assert len(result) > 0