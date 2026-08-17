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
    dq13_year_coverage,
    dq14_duplicate_records,
    dq15_required_fields,
    dq16_numeric_validity,
)


def test_dq01_duplicate_primary_key():
    df = pd.DataFrame({"id": [1, 1, 2]})

    failures = dq01_primary_key_uniqueness(df, "test")

    assert len(failures) == 2
    assert failures[0].rule_id == "DQ-01"


def test_dq02_duplicate_company_year():
    df = pd.DataFrame(
        {
            "company_id": ["TCS", "TCS", "INFY"],
            "year": ["2024-03", "2024-03", "2024-03"],
        }
    )

    failures = dq02_company_year_uniqueness(df, "profitandloss")

    assert len(failures) == 2


def test_dq03_invalid_foreign_key():
    df = pd.DataFrame(
        {
            "company_id": ["TCS", "UNKNOWN"],
        }
    )

    companies = pd.DataFrame({"id": ["TCS"]})

    failures = dq03_foreign_key_integrity(
        df,
        companies,
        "profitandloss",
    )

    assert len(failures) == 1
    assert failures[0].company_id == "UNKNOWN"


def test_dq04_balance_sheet():
    df = pd.DataFrame(
        {
            "company_id": ["TCS"],
            "year": ["2024-03"],
            "total_assets": [1000],
            "total_liabilities": [900],
        }
    )

    failures = dq04_balance_sheet_balance(df)

    assert len(failures) == 1
    assert failures[0].rule_id == "DQ-04"


def test_dq05_opm_mismatch():
    df = pd.DataFrame(
        {
            "company_id": ["TCS"],
            "year": ["2024-03"],
            "sales": [1000],
            "operating_profit": [200],
            "opm_percentage": [10],
        }
    )

    failures = dq05_opm_cross_check(df)

    assert len(failures) == 1


def test_dq06_negative_sales():
    df = pd.DataFrame({"sales": [100, -50, 200]})

    failures = dq06_positive_sales(df)

    assert len(failures) == 1


def test_dq07_cashflow_mismatch():
    df = pd.DataFrame(
        {
            "company_id": ["TCS"],
            "year": ["2024-03"],
            "operating_activity": [100],
            "investing_activity": [-50],
            "financing_activity": [-10],
            "net_cash_flow": [100],
        }
    )

    failures = dq07_net_cash_consistency(df)

    assert len(failures) == 1


def test_dq08_invalid_tax():
    df = pd.DataFrame({"tax_percentage": [20, 150, -5]})

    failures = dq08_tax_rate_validity(df)

    assert len(failures) == 2


def test_dq09_dividend_cap():
    df = pd.DataFrame({"dividend_payout": [20, 100, 120]})

    failures = dq09_dividend_payout_cap(df)

    assert len(failures) == 1


def test_dq10_invalid_url():
    df = pd.DataFrame(
        {
            "website": [
                "https://example.com",
                "not-a-url",
            ]
        }
    )

    failures = dq10_url_validity(df)

    assert len(failures) == 1


def test_dq11_eps_sign():
    df = pd.DataFrame(
        {
            "company_id": ["TCS"],
            "year": ["2024-03"],
            "net_profit": [100],
            "eps": [-5],
        }
    )

    failures = dq11_eps_sign_consistency(df)

    assert len(failures) == 1


def test_dq13_year_coverage():
    df = pd.DataFrame(
        {
            "company_id": ["TCS", "TCS", "TCS"],
            "year": ["2022", "2023", "2024"],
        }
    )

    failures = dq13_year_coverage(df, minimum_years=5)

    assert len(failures) == 1


def test_dq14_exact_duplicate():
    df = pd.DataFrame(
        {
            "id": [1, 1],
            "company_id": ["TCS", "TCS"],
        }
    )

    failures = dq14_duplicate_records(df, "test")

    assert len(failures) == 2


def test_dq15_required_fields():
    df = pd.DataFrame(
        {
            "id": [1, 2],
            "company_id": ["TCS", None],
        }
    )

    failures = dq15_required_fields(
        df,
        "test",
        ["id", "company_id"],
    )

    assert len(failures) == 1


def test_dq16_numeric_validity():
    df = pd.DataFrame(
        {
            "sales": [100, "invalid", 300],
        }
    )

    failures = dq16_numeric_validity(
        df,
        "profitandloss",
        ["sales"],
    )

    assert len(failures) == 1
