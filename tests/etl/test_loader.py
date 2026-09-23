"""Day 41 - ETL loader unit tests.

Exactly 10 tests covering loader row counts and column names.
"""

from src.etl.loader import (
    EXPECTED_COLUMNS,
    load_source_data,
)

RAW_DIR = "data/raw"
SUPPORTING_DIR = "data/supporting"


def test_load_source_data_returns_12_datasets():
    data = load_source_data(RAW_DIR, SUPPORTING_DIR)

    expected = {
        "companies",
        "profitandloss",
        "balancesheet",
        "cashflow",
        "analysis",
        "documents",
        "prosandcons",
        "financial_ratios",
        "market_cap",
        "peer_groups",
        "sectors",
        "stock_prices",
    }

    assert set(data.keys()) == expected
    assert len(data) == 12


def test_companies_row_count_and_columns():
    data = load_source_data(RAW_DIR, SUPPORTING_DIR)

    assert len(data["companies"]) == 92
    assert list(data["companies"].columns) == EXPECTED_COLUMNS["companies"]


def test_profitandloss_row_count_and_columns():
    data = load_source_data(RAW_DIR, SUPPORTING_DIR)

    assert len(data["profitandloss"]) == 1276
    assert list(data["profitandloss"].columns) == EXPECTED_COLUMNS["profitandloss"]


def test_balancesheet_row_count_and_columns():
    data = load_source_data(RAW_DIR, SUPPORTING_DIR)

    assert len(data["balancesheet"]) == 1312
    assert list(data["balancesheet"].columns) == EXPECTED_COLUMNS["balancesheet"]


def test_cashflow_row_count_and_columns():
    data = load_source_data(RAW_DIR, SUPPORTING_DIR)

    assert len(data["cashflow"]) == 1187
    assert list(data["cashflow"].columns) == EXPECTED_COLUMNS["cashflow"]


def test_analysis_row_count_and_columns():
    data = load_source_data(RAW_DIR, SUPPORTING_DIR)

    assert len(data["analysis"]) == 20
    assert list(data["analysis"].columns) == EXPECTED_COLUMNS["analysis"]


def test_documents_and_prosandcons():
    data = load_source_data(RAW_DIR, SUPPORTING_DIR)

    assert len(data["documents"]) == 1585
    assert list(data["documents"].columns) == EXPECTED_COLUMNS["documents"]

    assert len(data["prosandcons"]) == 16
    assert list(data["prosandcons"].columns) == EXPECTED_COLUMNS["prosandcons"]


def test_financial_ratios_and_market_cap():
    data = load_source_data(RAW_DIR, SUPPORTING_DIR)

    assert len(data["financial_ratios"]) == 1184
    assert (
        list(data["financial_ratios"].columns) == EXPECTED_COLUMNS["financial_ratios"]
    )

    assert len(data["market_cap"]) == 552
    assert list(data["market_cap"].columns) == EXPECTED_COLUMNS["market_cap"]


def test_peer_groups_and_sectors():
    data = load_source_data(RAW_DIR, SUPPORTING_DIR)

    assert len(data["peer_groups"]) == 56
    assert list(data["peer_groups"].columns) == EXPECTED_COLUMNS["peer_groups"]

    assert len(data["sectors"]) == 92
    assert list(data["sectors"].columns) == EXPECTED_COLUMNS["sectors"]


def test_stock_prices_row_count_and_columns():
    data = load_source_data(RAW_DIR, SUPPORTING_DIR)

    assert len(data["stock_prices"]) == 5520
    assert list(data["stock_prices"].columns) == EXPECTED_COLUMNS["stock_prices"]
