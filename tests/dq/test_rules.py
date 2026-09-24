"""Day 41 - DQ rule unit tests.

Each test directly exercises one DQ rule with a minimal DataFrame
that violates that rule only.
"""

import pandas as pd

from src.etl.validator import (
    dq01_primary_key_uniqueness,
    dq02_company_year_uniqueness,
    dq03_foreign_key_integrity,
    dq04_balance_sheet_balance,
    dq05_opm_cross_check,
    dq06_positive_sales,
    dq07_net_cash_consistency,
    dq08_tax_rate_validity,
    dq09_dividend_payout_cap,
    dq10_url_validity,
    dq11_eps_sign_consistency,
    dq12_bse_balance,
    dq13_year_coverage,
    dq14_duplicate_records,
)

# ============================================================
# DQ-01 - Primary key uniqueness
# ============================================================


def test_dq01_primary_key_uniqueness():
    df = pd.DataFrame(
        {
            "id": ["C001", "C001"],
            "company_id": ["C001", "C001"],
        }
    )

    result = dq01_primary_key_uniqueness(
        df,
        "companies",
        "id",
    )

    assert len(result) == 2
    assert all(item.rule_id == "DQ-01" for item in result)
    assert all(item.severity == "CRITICAL" for item in result)


# ============================================================
# DQ-02 - Company/year uniqueness
# ============================================================


def test_dq02_company_year_uniqueness():
    df = pd.DataFrame(
        {
            "id": ["1", "2"],
            "company_id": ["RELIANCE", "RELIANCE"],
            "year": ["2024-03", "2024-03"],
        }
    )

    result = dq02_company_year_uniqueness(
        df,
        "profitandloss",
    )

    assert len(result) == 2
    assert all(item.rule_id == "DQ-02" for item in result)
    assert all(item.severity == "CRITICAL" for item in result)


# ============================================================
# DQ-03 - Foreign key integrity
# ============================================================


def test_dq03_foreign_key_integrity():
    df = pd.DataFrame(
        {
            "id": ["1"],
            "company_id": ["UNKNOWN"],
            "year": ["2024-03"],
        }
    )

    companies = pd.DataFrame(
        {
            "id": ["RELIANCE"],
        }
    )

    result = dq03_foreign_key_integrity(
        df,
        companies,
        "profitandloss",
    )

    assert len(result) == 1
    assert result[0].rule_id == "DQ-03"
    assert result[0].severity == "CRITICAL"


# ============================================================
# DQ-04 - Balance sheet balance
# ============================================================


def test_dq04_balance_sheet_balance():
    df = pd.DataFrame(
        {
            "company_id": ["RELIANCE"],
            "year": ["2024-03"],
            "total_assets": [1000.0],
            "total_liabilities": [900.0],
        }
    )

    result = dq04_balance_sheet_balance(df)

    assert len(result) == 1
    assert result[0].rule_id == "DQ-04"
    assert result[0].severity == "WARNING"


# ============================================================
# DQ-05 - OPM cross-check
# ============================================================


def test_dq05_opm_cross_check():
    df = pd.DataFrame(
        {
            "company_id": ["RELIANCE"],
            "year": ["2024-03"],
            "sales": [1000.0],
            "operating_profit": [200.0],
            "opm_percentage": [25.0],
        }
    )

    result = dq05_opm_cross_check(df)

    assert len(result) == 1
    assert result[0].rule_id == "DQ-05"
    assert result[0].severity == "WARNING"


# ============================================================
# DQ-06 - Positive sales
# ============================================================


def test_dq06_positive_sales():
    df = pd.DataFrame(
        {
            "company_id": ["RELIANCE"],
            "year": ["2024-03"],
            "sales": [0.0],
        }
    )

    result = dq06_positive_sales(df)

    assert len(result) == 1
    assert result[0].rule_id == "DQ-06"
    assert result[0].severity == "WARNING"


# ============================================================
# DQ-07 - Net cash consistency
# ============================================================


def test_dq07_net_cash_consistency():
    df = pd.DataFrame(
        {
            "company_id": ["RELIANCE"],
            "year": ["2024-03"],
            "operating_activity": [100.0],
            "investing_activity": [-40.0],
            "financing_activity": [-10.0],
            "net_cash_flow": [100.0],
        }
    )

    result = dq07_net_cash_consistency(df)

    assert len(result) == 1
    assert result[0].rule_id == "DQ-07"
    assert result[0].severity == "WARNING"


# ============================================================
# DQ-08 - Tax rate validity
# ============================================================


def test_dq08_tax_rate_validity():
    df = pd.DataFrame(
        {
            "company_id": ["RELIANCE"],
            "year": ["2024-03"],
            "tax_percentage": [125.0],
        }
    )

    result = dq08_tax_rate_validity(df)

    assert len(result) == 1
    assert result[0].rule_id == "DQ-08"
    assert result[0].severity == "WARNING"


# ============================================================
# DQ-09 - Dividend payout cap
# ============================================================


def test_dq09_dividend_payout_cap():
    df = pd.DataFrame(
        {
            "company_id": ["RELIANCE"],
            "year": ["2024-03"],
            "dividend_payout": [150.0],
        }
    )

    result = dq09_dividend_payout_cap(df)

    assert len(result) == 1
    assert result[0].rule_id == "DQ-09"
    assert result[0].severity == "WARNING"


# ============================================================
# DQ-10 - URL validity
# ============================================================


def test_dq10_url_validity():
    df = pd.DataFrame(
        {
            "id": ["RELIANCE"],
            "website": ["invalid-url"],
        }
    )

    result = dq10_url_validity(df)

    assert len(result) == 1
    assert result[0].rule_id == "DQ-10"
    assert result[0].severity == "WARNING"


# ============================================================
# DQ-11 - EPS sign consistency
# ============================================================


def test_dq11_eps_sign_consistency():
    df = pd.DataFrame(
        {
            "company_id": ["RELIANCE"],
            "year": ["2024-03"],
            "net_profit": [100.0],
            "eps": [-5.0],
        }
    )

    result = dq11_eps_sign_consistency(df)

    assert len(result) == 1
    assert result[0].rule_id == "DQ-11"
    assert result[0].severity == "WARNING"


# ============================================================
# DQ-12 - BSE profile validity
# ============================================================


def test_dq12_bse_balance():
    df = pd.DataFrame(
        {
            "id": ["RELIANCE"],
            "bse_profile": ["invalid-bse-profile"],
        }
    )

    result = dq12_bse_balance(df)

    assert len(result) == 1
    assert result[0].rule_id == "DQ-12"
    assert result[0].severity == "WARNING"


# ============================================================
# DQ-13 - Year coverage
# ============================================================


def test_dq13_year_coverage():
    df = pd.DataFrame(
        {
            "company_id": [
                "RELIANCE",
                "RELIANCE",
                "RELIANCE",
                "RELIANCE",
            ],
            "year": [
                "2021-03",
                "2022-03",
                "2023-03",
                "2024-03",
            ],
        }
    )

    result = dq13_year_coverage(
        df,
        minimum_years=5,
    )

    assert len(result) == 1
    assert result[0].rule_id == "DQ-13"
    assert result[0].severity == "WARNING"


# ============================================================
# DQ-14 - Duplicate records
# ============================================================


def test_dq14_duplicate_records():
    df = pd.DataFrame(
        {
            "id": ["1", "1"],
            "company_id": ["RELIANCE", "RELIANCE"],
            "year": ["2024-03", "2024-03"],
            "sales": [1000.0, 1000.0],
        }
    )

    result = dq14_duplicate_records(
        df,
        "profitandloss",
    )

    assert len(result) == 2
    assert all(item.rule_id == "DQ-14" for item in result)
    assert all(item.severity == "WARNING" for item in result)
