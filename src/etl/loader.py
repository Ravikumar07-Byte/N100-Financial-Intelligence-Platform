from pathlib import Path

import pandas as pd

from src.etl.normaliser import normalize_ticker, normalize_year


def load_excel(path: str | Path) -> pd.DataFrame:
    """
    Load a Bluestock Excel file.

    Bluestock source files contain:
    - Row 1: descriptive title
    - Row 2: actual column headers
    - Remaining rows: data

    Returns a clean DataFrame with normalized column names.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Excel file not found: {path}")

    df = pd.read_excel(path, header=1)

    # Remove completely empty rows/columns.
    df = df.dropna(axis=0, how="all")
    df = df.dropna(axis=1, how="all")

    # Normalize column names.
    df.columns = [
        str(column).strip().lower().replace(" ", "_") for column in df.columns
    ]

    # Remove accidental unnamed columns.
    df = df.loc[:, ~df.columns.astype(str).str.startswith("unnamed:")]

    # Normalize ticker/company identifiers.
    for column in ("id", "company_id"):
        if column in df.columns:
            df[column] = df[column].apply(normalize_ticker)

    # Normalize year/date fields.
    if "year" in df.columns:
        df["year"] = df["year"].apply(normalize_year)

    return df.reset_index(drop=True)


def load_all_excel(directory: str | Path) -> dict[str, pd.DataFrame]:
    """
    Load all Excel files from a directory.

    Returns:
        Dictionary keyed by filename stem.
    """
    directory = Path(directory)

    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    files = sorted(directory.glob("*.xlsx"))

    return {file.stem: load_excel(file) for file in files}
