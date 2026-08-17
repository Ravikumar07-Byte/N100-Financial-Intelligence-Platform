from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass
class ValidationFailure:
    rule_id: str
    severity: str
    table_name: str
    company_id: str | None
    year: str | None
    column_name: str | None
    message: str


def _failure(
    rule_id: str,
    severity: str,
    table_name: str,
    message: str,
    company_id: Any = None,
    year: Any = None,
    column_name: str | None = None,
) -> ValidationFailure:
    return ValidationFailure(
        rule_id=rule_id,
        severity=severity,
        table_name=table_name,
        company_id=None if pd.isna(company_id) else str(company_id),
        year=None if pd.isna(year) else str(year),
        column_name=column_name,
        message=message,
    )


def dq01_primary_key_uniqueness(
    df: pd.DataFrame,
    table_name: str,
    key: str = "id",
) -> list[ValidationFailure]:
    failures = []

    if key not in df.columns:
        return [
            _failure(
                "DQ-01",
                "CRITICAL",
                table_name,
                f"Required primary-key column '{key}' is missing.",
                column_name=key,
            )
        ]

    duplicates = df[df[key].duplicated(keep=False)]

    for _, row in duplicates.iterrows():
        failures.append(
            _failure(
                "DQ-01",
                "CRITICAL",
                table_name,
                f"Duplicate primary key: {row[key]}",
                company_id=row.get("company_id"),
                year=row.get("year"),
                column_name=key,
            )
        )

    return failures


def dq02_company_year_uniqueness(
    df: pd.DataFrame,
    table_name: str,
) -> list[ValidationFailure]:
    failures = []

    required = {"company_id", "year"}

    if not required.issubset(df.columns):
        return failures

    duplicates = df[df.duplicated(["company_id", "year"], keep=False)]

    for _, row in duplicates.iterrows():
        failures.append(
            _failure(
                "DQ-02",
                "CRITICAL",
                table_name,
                f"Duplicate company/year combination: "
                f"{row['company_id']} / {row['year']}",
                company_id=row["company_id"],
                year=row["year"],
            )
        )

    return failures


def dq03_foreign_key_integrity(
    df: pd.DataFrame,
    companies: pd.DataFrame,
    table_name: str,
) -> list[ValidationFailure]:
    failures = []

    if "company_id" not in df.columns or "id" not in companies.columns:
        return failures

    valid_ids = set(companies["id"].dropna().astype(str))

    invalid = df[
        df["company_id"].notna() & ~df["company_id"].astype(str).isin(valid_ids)
    ]

    for _, row in invalid.iterrows():
        failures.append(
            _failure(
                "DQ-03",
                "CRITICAL",
                table_name,
                f"Unknown company_id: {row['company_id']}",
                company_id=row["company_id"],
                year=row.get("year"),
                column_name="company_id",
            )
        )

    return failures


def dq04_balance_sheet_balance(
    df: pd.DataFrame,
    tolerance_pct: float = 1.0,
) -> list[ValidationFailure]:
    failures = []

    required = {"company_id", "year", "total_assets", "total_liabilities"}

    if not required.issubset(df.columns):
        return failures

    for _, row in df.iterrows():
        assets = pd.to_numeric(row["total_assets"], errors="coerce")
        liabilities = pd.to_numeric(
            row["total_liabilities"],
            errors="coerce",
        )

        if pd.isna(assets) or pd.isna(liabilities) or assets == 0:
            continue

        difference_pct = abs(assets - liabilities) / abs(assets) * 100

        if difference_pct >= tolerance_pct:
            failures.append(
                _failure(
                    "DQ-04",
                    "WARNING",
                    "balancesheet",
                    f"Balance-sheet difference is "
                    f"{difference_pct:.2f}% "
                    f"(assets={assets}, liabilities={liabilities}).",
                    company_id=row["company_id"],
                    year=row["year"],
                    column_name="total_assets",
                )
            )

    return failures


def dq05_opm_cross_check(
    df: pd.DataFrame,
    tolerance_pct: float = 1.0,
) -> list[ValidationFailure]:
    failures = []

    required = {"company_id", "year", "sales", "operating_profit", "opm_percentage"}

    if not required.issubset(df.columns):
        return failures

    for _, row in df.iterrows():
        sales = pd.to_numeric(row["sales"], errors="coerce")
        operating_profit = pd.to_numeric(
            row["operating_profit"],
            errors="coerce",
        )
        source_opm = pd.to_numeric(
            row["opm_percentage"],
            errors="coerce",
        )

        if pd.isna(sales) or pd.isna(operating_profit) or pd.isna(source_opm):
            continue

        if sales == 0:
            continue

        calculated_opm = operating_profit / sales * 100

        if abs(calculated_opm - source_opm) > tolerance_pct:
            failures.append(
                _failure(
                    "DQ-05",
                    "WARNING",
                    "profitandloss",
                    f"OPM mismatch: calculated={calculated_opm:.2f}%, "
                    f"source={source_opm:.2f}%.",
                    company_id=row["company_id"],
                    year=row["year"],
                    column_name="opm_percentage",
                )
            )

    return failures


def dq06_positive_sales(df: pd.DataFrame) -> list[ValidationFailure]:
    failures = []

    if "sales" not in df.columns:
        return failures

    invalid = df[
        df["sales"].notna() & (pd.to_numeric(df["sales"], errors="coerce") <= 0)
    ]

    for _, row in invalid.iterrows():
        failures.append(
            _failure(
                "DQ-06",
                "WARNING",
                "profitandloss",
                f"Sales must be positive: {row['sales']}",
                company_id=row.get("company_id"),
                year=row.get("year"),
                column_name="sales",
            )
        )

    return failures


def dq07_net_cash_consistency(
    df: pd.DataFrame,
) -> list[ValidationFailure]:
    failures = []

    required = {
        "company_id",
        "year",
        "operating_activity",
        "investing_activity",
        "financing_activity",
        "net_cash_flow",
    }

    if not required.issubset(df.columns):
        return failures

    for _, row in df.iterrows():
        values = [
            pd.to_numeric(row[column], errors="coerce")
            for column in (
                "operating_activity",
                "investing_activity",
                "financing_activity",
                "net_cash_flow",
            )
        ]

        if any(pd.isna(value) for value in values):
            continue

        expected = values[0] + values[1] + values[2]

        if abs(expected - values[3]) > 0.01:
            failures.append(
                _failure(
                    "DQ-07",
                    "WARNING",
                    "cashflow",
                    f"Net cash mismatch: calculated={expected}, "
                    f"source={values[3]}.",
                    company_id=row["company_id"],
                    year=row["year"],
                    column_name="net_cash_flow",
                )
            )

    return failures


def dq08_tax_rate_validity(
    df: pd.DataFrame,
) -> list[ValidationFailure]:
    failures = []

    if "tax_percentage" not in df.columns:
        return failures

    tax = pd.to_numeric(df["tax_percentage"], errors="coerce")

    invalid = df[tax.notna() & ((tax < 0) | (tax > 100))]

    for _, row in invalid.iterrows():
        failures.append(
            _failure(
                "DQ-08",
                "WARNING",
                "profitandloss",
                f"Tax percentage outside 0-100: " f"{row['tax_percentage']}",
                company_id=row.get("company_id"),
                year=row.get("year"),
                column_name="tax_percentage",
            )
        )

    return failures


def dq09_dividend_payout_cap(
    df: pd.DataFrame,
) -> list[ValidationFailure]:
    failures = []

    if "dividend_payout" not in df.columns:
        return failures

    payout = pd.to_numeric(df["dividend_payout"], errors="coerce")

    invalid = df[payout.notna() & (payout > 100)]

    for _, row in invalid.iterrows():
        failures.append(
            _failure(
                "DQ-09",
                "WARNING",
                "profitandloss",
                f"Dividend payout exceeds 100%: " f"{row['dividend_payout']}",
                company_id=row.get("company_id"),
                year=row.get("year"),
                column_name="dividend_payout",
            )
        )

    return failures


def dq10_url_validity(
    df: pd.DataFrame,
) -> list[ValidationFailure]:
    failures = []

    url_columns = [
        column
        for column in ("website", "nse_profile", "bse_profile", "chart_link")
        if column in df.columns
    ]

    for column in url_columns:
        for _, row in df.iterrows():
            value = row[column]

            if pd.isna(value) or str(value).strip() == "":
                continue

            value = str(value).strip()

            if not value.startswith(("http://", "https://")):
                failures.append(
                    _failure(
                        "DQ-10",
                        "WARNING",
                        "companies",
                        f"Invalid URL: {value}",
                        company_id=row.get("id"),
                        column_name=column,
                    )
                )

    return failures


def dq11_eps_sign_consistency(
    df: pd.DataFrame,
) -> list[ValidationFailure]:
    failures = []

    required = {"company_id", "year", "net_profit", "eps"}

    if not required.issubset(df.columns):
        return failures

    for _, row in df.iterrows():
        net_profit = pd.to_numeric(row["net_profit"], errors="coerce")
        eps = pd.to_numeric(row["eps"], errors="coerce")

        if pd.isna(net_profit) or pd.isna(eps):
            continue

        if net_profit > 0 and eps < 0:
            failures.append(
                _failure(
                    "DQ-11",
                    "WARNING",
                    "profitandloss",
                    f"Positive net profit with negative EPS: "
                    f"net_profit={net_profit}, eps={eps}.",
                    company_id=row["company_id"],
                    year=row["year"],
                    column_name="eps",
                )
            )

        if net_profit < 0 and eps > 0:
            failures.append(
                _failure(
                    "DQ-11",
                    "WARNING",
                    "profitandloss",
                    f"Negative net profit with positive EPS: "
                    f"net_profit={net_profit}, eps={eps}.",
                    company_id=row["company_id"],
                    year=row["year"],
                    column_name="eps",
                )
            )

    return failures


def dq12_bse_balance(
    df: pd.DataFrame,
) -> list[ValidationFailure]:
    failures = []

    if "bse_profile" not in df.columns:
        return failures

    for _, row in df.iterrows():
        value = row["bse_profile"]

        if pd.isna(value) or str(value).strip() == "":
            continue

        if not str(value).startswith(("http://", "https://")):
            failures.append(
                _failure(
                    "DQ-12",
                    "WARNING",
                    "companies",
                    f"Invalid BSE profile: {value}",
                    company_id=row.get("id"),
                    column_name="bse_profile",
                )
            )

    return failures


def dq13_year_coverage(
    df: pd.DataFrame,
    minimum_years: int = 5,
) -> list[ValidationFailure]:
    failures = []

    required = {"company_id", "year"}

    if not required.issubset(df.columns):
        return failures

    coverage = df.groupby("company_id")["year"].nunique()

    for company_id, count in coverage.items():
        if count < minimum_years:
            failures.append(
                _failure(
                    "DQ-13",
                    "WARNING",
                    "profitandloss",
                    f"Only {count} years of data available; "
                    f"minimum expected is {minimum_years}.",
                    company_id=company_id,
                )
            )

    return failures


def dq14_duplicate_records(
    df: pd.DataFrame,
    table_name: str,
) -> list[ValidationFailure]:
    failures = []

    duplicates = df[df.duplicated(keep=False)]

    for _, row in duplicates.iterrows():
        failures.append(
            _failure(
                "DQ-14",
                "WARNING",
                table_name,
                "Exact duplicate record detected.",
                company_id=row.get("company_id"),
                year=row.get("year"),
            )
        )

    return failures


def dq15_required_fields(
    df: pd.DataFrame,
    table_name: str,
    required_columns: list[str],
) -> list[ValidationFailure]:
    failures = []

    for column in required_columns:
        if column not in df.columns:
            failures.append(
                _failure(
                    "DQ-15",
                    "CRITICAL",
                    table_name,
                    f"Required column missing: {column}",
                    column_name=column,
                )
            )
            continue

        missing = df[df[column].isna()]

        for _, row in missing.iterrows():
            failures.append(
                _failure(
                    "DQ-15",
                    "CRITICAL",
                    table_name,
                    f"Required value missing in {column}.",
                    company_id=row.get("company_id"),
                    year=row.get("year"),
                    column_name=column,
                )
            )

    return failures


def dq16_numeric_validity(
    df: pd.DataFrame,
    table_name: str,
    numeric_columns: list[str],
) -> list[ValidationFailure]:
    failures = []

    for column in numeric_columns:
        if column not in df.columns:
            continue

        values = pd.to_numeric(df[column], errors="coerce")

        invalid = df[df[column].notna() & values.isna()]

        for _, row in invalid.iterrows():
            failures.append(
                _failure(
                    "DQ-16",
                    "WARNING",
                    table_name,
                    f"Non-numeric value found in numeric column: " f"{row[column]}",
                    company_id=row.get("company_id"),
                    year=row.get("year"),
                    column_name=column,
                )
            )

    return failures


def validate_all(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Execute DQ-01 through DQ-16 against loaded datasets.
    """
    failures: list[ValidationFailure] = []

    companies = data.get("companies", pd.DataFrame())
    pnl = data.get("profitandloss", pd.DataFrame())
    balance = data.get("balancesheet", pd.DataFrame())
    cashflow = data.get("cashflow", pd.DataFrame())

    # DQ-01
    for table_name, df in data.items():
        failures.extend(
            dq01_primary_key_uniqueness(
                df,
                table_name,
                "id",
            )
        )

    # DQ-02
    for table_name, df in data.items():
        if {"company_id", "year"}.issubset(df.columns):
            failures.extend(
                dq02_company_year_uniqueness(
                    df,
                    table_name,
                )
            )

    # DQ-03
    for table_name, df in data.items():
        if "company_id" in df.columns:
            failures.extend(
                dq03_foreign_key_integrity(
                    df,
                    companies,
                    table_name,
                )
            )

    # DQ-04
    failures.extend(dq04_balance_sheet_balance(balance))

    # DQ-05
    failures.extend(dq05_opm_cross_check(pnl))

    # DQ-06
    failures.extend(dq06_positive_sales(pnl))

    # DQ-07
    failures.extend(dq07_net_cash_consistency(cashflow))

    # DQ-08
    failures.extend(dq08_tax_rate_validity(pnl))

    # DQ-09
    failures.extend(dq09_dividend_payout_cap(pnl))

    # DQ-10
    failures.extend(dq10_url_validity(companies))

    # DQ-11
    failures.extend(dq11_eps_sign_consistency(pnl))

    # DQ-12
    failures.extend(dq12_bse_balance(companies))

    # DQ-13
    failures.extend(dq13_year_coverage(pnl))

    # DQ-14
    for table_name, df in data.items():
        failures.extend(
            dq14_duplicate_records(
                df,
                table_name,
            )
        )

    # DQ-15
    required_fields = {
        "companies": ["id", "company_name"],
        "profitandloss": ["id", "company_id", "year", "sales"],
        "balancesheet": ["id", "company_id", "year"],
        "cashflow": ["id", "company_id", "year"],
    }

    for table_name, columns in required_fields.items():
        if table_name in data:
            failures.extend(
                dq15_required_fields(
                    data[table_name],
                    table_name,
                    columns,
                )
            )

    # DQ-16
    numeric_fields = {
        "profitandloss": [
            "sales",
            "expenses",
            "operating_profit",
            "opm_percentage",
            "other_income",
            "interest",
            "depreciation",
            "profit_before_tax",
            "tax_percentage",
            "net_profit",
            "eps",
            "dividend_payout",
        ],
        "balancesheet": [
            "equity_capital",
            "reserves",
            "borrowings",
            "other_liabilities",
            "total_liabilities",
            "fixed_assets",
            "cwip",
            "investments",
            "other_asset",
            "total_assets",
        ],
        "cashflow": [
            "operating_activity",
            "investing_activity",
            "financing_activity",
            "net_cash_flow",
        ],
    }

    for table_name, columns in numeric_fields.items():
        if table_name in data:
            failures.extend(
                dq16_numeric_validity(
                    data[table_name],
                    table_name,
                    columns,
                )
            )

    result = pd.DataFrame(
        [
            {
                "rule_id": item.rule_id,
                "severity": item.severity,
                "table_name": item.table_name,
                "company_id": item.company_id,
                "year": item.year,
                "column_name": item.column_name,
                "message": item.message,
            }
            for item in failures
        ]
    )

    if result.empty:
        return pd.DataFrame(
            columns=[
                "rule_id",
                "severity",
                "table_name",
                "company_id",
                "year",
                "column_name",
                "message",
            ]
        )

    return result


def validate_and_save(
    data: dict[str, pd.DataFrame],
    output_path: str | Path = "output/validation_failures.csv",
) -> pd.DataFrame:
    """Run all DQ checks and save failures to CSV."""
    result = validate_all(data)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    result.to_csv(output_path, index=False)

    return result
