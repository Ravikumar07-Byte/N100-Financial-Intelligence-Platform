from pathlib import Path

import pandas as pd

from src.etl.normaliser import normalize_ticker, normalize_year

# ---------------------------------------------------------------------------
# Dataset-specific configuration
# ---------------------------------------------------------------------------

RAW_HEADER_ROW = 1
SUPPORTING_HEADER_ROW = 0


# Expected columns for the 12 Day 5 datasets.
EXPECTED_COLUMNS = {
    "companies": [
        "id",
        "company_logo",
        "company_name",
        "chart_link",
        "about_company",
        "website",
        "nse_profile",
        "bse_profile",
        "face_value",
        "book_value",
        "roce_percentage",
        "roe_percentage",
    ],
    "profitandloss": [
        "id",
        "company_id",
        "year",
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
        "id",
        "company_id",
        "year",
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
        "id",
        "company_id",
        "year",
        "operating_activity",
        "investing_activity",
        "financing_activity",
        "net_cash_flow",
    ],
    "analysis": [
        "id",
        "company_id",
        "compounded_sales_growth",
        "compounded_profit_growth",
        "stock_price_cagr",
        "roe",
    ],
    "documents": [
        "id",
        "company_id",
        "year",
        "annual_report",
    ],
    "prosandcons": [
        "id",
        "company_id",
        "pros",
        "cons",
    ],
    "sectors": [
        "id",
        "company_id",
        "broad_sector",
        "sub_sector",
        "index_weight_pct",
        "market_cap_category",
    ],
    "stock_prices": [
        "id",
        "company_id",
        "date",
        "open_price",
        "high_price",
        "low_price",
        "close_price",
        "volume",
        "adjusted_close",
    ],
    "market_cap": [
        "id",
        "company_id",
        "year",
        "market_cap_crore",
        "enterprise_value_crore",
        "pe_ratio",
        "pb_ratio",
        "ev_ebitda",
        "dividend_yield_pct",
    ],
    "financial_ratios": [
        "id",
        "company_id",
        "year",
        "net_profit_margin_pct",
        "operating_profit_margin_pct",
        "return_on_equity_pct",
        "debt_to_equity",
        "interest_coverage",
        "asset_turnover",
        "free_cash_flow_cr",
        "capex_cr",
        "earnings_per_share",
        "book_value_per_share",
        "dividend_payout_ratio_pct",
        "total_debt_cr",
        "cash_from_operations_cr",
    ],
    "peer_groups": [
        "id",
        "peer_group_name",
        "company_id",
        "is_benchmark",
    ],
}


# ---------------------------------------------------------------------------
# Column normalization
# ---------------------------------------------------------------------------


def normalize_column_name(column: object) -> str:
    """Convert an Excel column name into a normalized database-style name."""

    return str(column).strip().lower().replace(" ", "_")


# ---------------------------------------------------------------------------
# Company ID normalization
# ---------------------------------------------------------------------------


COMPANY_ID_ALIASES = {
    "AGTL": "ATGL",
}


def normalize_company_id(value: object) -> str:
    """
    Normalize source company identifiers to canonical master IDs.

    Example
    -------
    AGTL -> ATGL

    Other valid tickers are returned unchanged after
    standard ticker normalization.
    """

    ticker = normalize_ticker(value)

    return COMPANY_ID_ALIASES.get(ticker, ticker)


# ---------------------------------------------------------------------------
# Excel loading
# ---------------------------------------------------------------------------


def load_excel(
    path: str | Path,
    header: int = 1,
) -> pd.DataFrame:
    """
    Load and clean one Bluestock Excel dataset.

    Parameters
    ----------
    path:
        Path to the Excel file.

    header:
        Excel header row:
        - 1 for core/raw Bluestock files.
        - 0 for supplementary supporting datasets.

    Returns
    -------
    pandas.DataFrame
        Cleaned DataFrame with normalized column names.
    """

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Excel file not found: {path}")

    if path.suffix.lower() != ".xlsx":
        raise ValueError(f"Expected an .xlsx file: {path}")

    dataframe = pd.read_excel(path, header=header)

    # Remove completely empty rows and columns.
    dataframe = dataframe.dropna(axis=0, how="all")
    dataframe = dataframe.dropna(axis=1, how="all")

    # Normalize column names.
    dataframe.columns = [
        normalize_column_name(column)
        for column in dataframe.columns
    ]

    # Remove accidental unnamed columns.
    dataframe = dataframe.loc[
        :,
        ~dataframe.columns.astype(str).str.startswith("unnamed:"),
    ]

    # Normalize identifiers.
    for column in ("id", "company_id"):
        if column in dataframe.columns:
            dataframe[column] = dataframe[column].apply(
                normalize_company_id
            )

    # Normalize financial year fields.
    if "year" in dataframe.columns:
        dataframe["year"] = dataframe["year"].apply(
            normalize_year
        )

    # Normalize dates without changing their meaning.
    if "date" in dataframe.columns:
        dataframe["date"] = pd.to_datetime(
            dataframe["date"],
            errors="coerce",
        ).dt.strftime("%Y-%m-%d")

    return dataframe.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Directory loading
# ---------------------------------------------------------------------------


def load_all_excel(
    directory: str | Path,
    header: int = 1,
) -> dict[str, pd.DataFrame]:
    """
    Load every Excel file from a directory.

    Returns
    -------
    dict[str, pandas.DataFrame]
        Dictionary keyed by Excel filename stem.
    """

    directory = Path(directory)

    if not directory.exists():
        raise FileNotFoundError(
            f"Directory not found: {directory}"
        )

    if not directory.is_dir():
        raise NotADirectoryError(
            f"Expected a directory: {directory}"
        )

    files = sorted(directory.glob("*.xlsx"))

    if not files:
        raise FileNotFoundError(
            f"No .xlsx files found in: {directory}"
        )

    return {
        file.stem: load_excel(
            file,
            header=header,
        )
        for file in files
    }


# ---------------------------------------------------------------------------
# Dataset validation
# ---------------------------------------------------------------------------


def validate_dataset_columns(
    dataset_name: str,
    dataframe: pd.DataFrame,
) -> None:
    """
    Validate that a loaded dataset contains its expected columns.

    Raises
    ------
    ValueError
        If expected columns are missing.
    """

    expected = EXPECTED_COLUMNS.get(dataset_name)

    if expected is None:
        return

    actual = set(dataframe.columns)

    missing = [
        column
        for column in expected
        if column not in actual
    ]

    if missing:
        raise ValueError(
            f"Dataset '{dataset_name}' is missing required columns: "
            + ", ".join(missing)
        )


# ---------------------------------------------------------------------------
# Source data loading
# ---------------------------------------------------------------------------


def load_source_data(
    raw_directory: str | Path,
    supporting_directory: str | Path,
) -> dict[str, pd.DataFrame]:
    """
    Load the official 7 core and 5 supplementary Excel datasets.

    Only explicitly defined source files are loaded.
    Backup/reconciliation Excel files are intentionally ignored.
    """

    raw_directory = Path(raw_directory)
    supporting_directory = Path(supporting_directory)

    if not raw_directory.exists():
        raise FileNotFoundError(
            f"Raw directory not found: {raw_directory}"
        )

    if not supporting_directory.exists():
        raise FileNotFoundError(
            f"Supporting directory not found: {supporting_directory}"
        )

    # ---------------------------------------------------------------
    # Official Day-05 core datasets — exactly 7 files
    # ---------------------------------------------------------------

    raw_files = [
        "companies.xlsx",
        "profitandloss.xlsx",
        "balancesheet.xlsx",
        "cashflow.xlsx",
        "analysis.xlsx",
        "documents.xlsx",
        "prosandcons.xlsx",
    ]

    # ---------------------------------------------------------------
    # Official Day-05 supplementary datasets — exactly 5 files
    # ---------------------------------------------------------------

    supporting_files = [
        "financial_ratios.xlsx",
        "market_cap.xlsx",
        "peer_groups.xlsx",
        "sectors.xlsx",
        "stock_prices.xlsx",
    ]

    raw_data = {}

    for filename in raw_files:
        path = raw_directory / filename

        if not path.exists():
            raise FileNotFoundError(
                f"Required raw source file not found: {path}"
            )

        dataframe = load_excel(
            path,
            header=RAW_HEADER_ROW,
        )

        dataset_name = path.stem

        validate_dataset_columns(
            dataset_name,
            dataframe,
        )

        raw_data[dataset_name] = dataframe

    supporting_data = {}

    for filename in supporting_files:
        path = supporting_directory / filename

        if not path.exists():
            raise FileNotFoundError(
                f"Required supporting source file not found: {path}"
            )

        dataframe = load_excel(
            path,
            header=SUPPORTING_HEADER_ROW,
        )

        dataset_name = path.stem

        validate_dataset_columns(
            dataset_name,
            dataframe,
        )

        supporting_data[dataset_name] = dataframe

    return {
        **raw_data,
        **supporting_data,
    }