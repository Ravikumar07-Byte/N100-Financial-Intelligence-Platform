"""Utilities for normalising N100 source data."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

import pandas as pd


def normalize_year(value: Any) -> str:
    """Normalise financial period values to a consistent YYYY-MM format."""

    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "PARSE_ERROR"

    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m")

    if isinstance(value, datetime):
        return value.strftime("%Y-%m")

    text = str(value).strip()

    if not text:
        return "PARSE_ERROR"

    text = re.sub(r"\s+", " ", text)

    # TTM is a valid financial reporting period.
    if text.upper() == "TTM":
        return "TTM"

    # Special source periods such as:
    # Mar 2016 9m
    # Mar 2023 15
    duration_match = re.fullmatch(
        r"(.+?)\s+(\d+)(?:m)?",
        text,
        flags=re.IGNORECASE,
    )

    duration = None

    if duration_match:
        base_period = duration_match.group(1).strip()
        suffix = duration_match.group(2)

        # Only interpret the suffix as a duration if the base
        # is a recognizable month-year value.
        if re.fullmatch(
            r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
            r"(?:uary|ruary|ch|il|y|e|ust|tember|ober|ember)?"
            r"(?:[- ](?:\d{2}|\d{4}))",
            base_period,
            flags=re.IGNORECASE,
        ):
            text = base_period
            duration = int(suffix)

    # Already normalised: YYYY-MM
    if re.fullmatch(r"\d{4}-\d{2}", text):
        try:
            parsed = pd.to_datetime(text, format="%Y-%m")
            result = parsed.strftime("%Y-%m")

            if duration is not None:
                return f"{result}-{duration}M"

            return result
        except ValueError:
            return "PARSE_ERROR"

    # FY23 / FY2023
    fy_match = re.fullmatch(
        r"FY\s*(\d{2}|\d{4})",
        text,
        flags=re.IGNORECASE,
    )

    if fy_match:
        year_text = fy_match.group(1)
        year = int(year_text)

        if len(year_text) == 2:
            year += 2000

        result = f"{year:04d}-03"

        if duration is not None:
            return f"{result}-{duration}M"

        return result

    # Four-digit year.
    if re.fullmatch(r"\d{4}", text):
        return f"{int(text):04d}-03"

    # Excel may return decimal-coded financial periods.
    # In this N100 source dataset, 2024.5 represents
    # the September 2024 balance-sheet period.
    if re.fullmatch(r"\d{4}\.5", text):
        year = int(float(text))
        return f"{year:04d}-09"

    # Excel may return 2024.0 for a year value.
    if re.fullmatch(r"\d{4}\.0+", text):
        return f"{int(float(text)):04d}-03"

    # Standard month-year formats.
    for fmt in (
        "%b-%y",
        "%b %y",
        "%B-%Y",
        "%B %Y",
        "%b-%Y",
        "%b %Y",
    ):
        try:
            parsed = datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)

            result = parsed.strftime("%Y-%m")

            if duration is not None:
                return f"{result}-{duration}M"

            return result
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
