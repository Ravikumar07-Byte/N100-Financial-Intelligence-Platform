"""Utilities for normalising N100 source data."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

import pandas as pd


def normalize_year(value: Any) -> str:
    """Normalise a financial year value to YYYY-MM."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "PARSE_ERROR"

    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m")

    if isinstance(value, datetime):
        return value.strftime("%Y-%m")

    text = str(value).strip()

    if not text:
        return "PARSE_ERROR"

    # Already normalised: YYYY-MM
    if re.fullmatch(r"\d{4}-\d{2}", text):
        try:
            parsed = pd.to_datetime(text, format="%Y-%m")
            return parsed.strftime("%Y-%m")
        except ValueError:
            return "PARSE_ERROR"

    # FY23 / FY2023
    fy_match = re.fullmatch(r"FY\s*(\d{2}|\d{4})", text, flags=re.IGNORECASE)
    if fy_match:
        year_text = fy_match.group(1)
        year = int(year_text)

        if len(year_text) == 2:
            year += 2000

        return f"{year:04d}-03"

    # Four-digit year such as 2023
    if re.fullmatch(r"\d{4}", text):
        return f"{int(text):04d}-03"

    # Common month-year formats.
    # Examples: Mar-23, Mar 23, March-2023, Dec-22, Jun-23
    cleaned = re.sub(r"\s+", " ", text)

    for fmt in (
        "%b-%y",
        "%b %y",
        "%B-%Y",
        "%B %Y",
        "%b-%Y",
        "%b %Y",
    ):
        try:
            parsed = datetime.strptime(cleaned, fmt).replace(tzinfo=timezone.utc)
            return parsed.strftime("%Y-%m")
        except ValueError:
            continue

    return "PARSE_ERROR"


def normalize_ticker(value: Any) -> str:
    """Normalise a company ticker to uppercase without surrounding whitespace."""
    if value is None:
        return "MISSING"

    if isinstance(value, float) and pd.isna(value):
        return "MISSING"

    text = str(value).strip()

    if not text:
        return "MISSING"

    return text.upper()
