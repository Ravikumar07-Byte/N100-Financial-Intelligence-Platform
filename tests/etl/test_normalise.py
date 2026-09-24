"""Day 41 - Unit tests for year normalisation."""

from datetime import datetime

import pandas as pd
import pytest

from src.etl.normaliser import normalize_year


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        # 1. Already normalised YYYY-MM
        ("2023-03", "2023-03"),
        # 2. Four-digit year
        ("2023", "2023-03"),
        # 3. FY two-digit year
        ("FY23", "2023-03"),
        # 4. FY four-digit year
        ("FY2023", "2023-03"),
        # 5. Short month-year with hyphen
        ("Mar-23", "2023-03"),
        # 6. Short month-year with space
        ("Mar 23", "2023-03"),
        # 7. Full month-year with hyphen
        ("March-2023", "2023-03"),
        # 8. Full month-year with space
        ("March 2023", "2023-03"),
        # 9. Excel decimal .5 period
        ("2024.5", "2024-09"),
        # 10. Excel decimal .0 period
        ("2024.0", "2024-03"),
        # 11. TTM period
        ("TTM", "TTM"),
        # 12. Timestamp input
        (pd.Timestamp("2024-06-30"), "2024-06"),
        # 13. datetime input
        (datetime(2024, 9, 30), "2024-09"),  # noqa: DTZ001
        # 14. Month-year with duration
        ("Mar 2023 9m", "2023-03-9M"),
        # 15. Month-year with another duration
        ("Mar 2023 15", "2023-03-15M"),
        # 16. Whitespace around valid input
        ("  Mar-23  ", "2023-03"),
        # 17. Case-insensitive month input
        ("mar-23", "2023-03"),
        # 18. Empty string
        ("", "PARSE_ERROR"),
        # 19. None
        (None, "PARSE_ERROR"),
        # 20. Invalid text
        ("not-a-valid-period", "PARSE_ERROR"),
    ],
)
def test_normalize_year(value, expected):
    """Verify all required normalize_year() formats and edge cases."""
    assert normalize_year(value) == expected
