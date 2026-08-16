"""Tests for N100 year and ticker normalisation."""

import pytest

from src.etl.normaliser import normalize_ticker, normalize_year


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("Mar-23", "2023-03"),
        ("Mar 23", "2023-03"),
        ("March-2023", "2023-03"),
        ("March 2023", "2023-03"),
        ("Mar-2023", "2023-03"),
        ("Mar 2023", "2023-03"),
        ("2023", "2023-03"),
        ("FY23", "2023-03"),
        ("FY24", "2024-03"),
        ("FY2023", "2023-03"),
        ("Dec-22", "2022-12"),
        ("Jun-23", "2023-06"),
        ("2023-03", "2023-03"),
        ("  Mar-23  ", "2023-03"),
        ("mar-23", "2023-03"),
        ("MAR-23", "2023-03"),
        ("  FY23  ", "2023-03"),
        (" 2023 ", "2023-03"),
        ("", "PARSE_ERROR"),
        (None, "PARSE_ERROR"),
        ("garbage", "PARSE_ERROR"),
    ],
)
def test_normalize_year(value, expected):
    """Test supported and invalid year formats."""
    assert normalize_year(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("TCS", "TCS"),
        ("tcs", "TCS"),
        (" TCS", "TCS"),
        ("TCS ", "TCS"),
        (" TCS ", "TCS"),
        ("bajaj-auto", "BAJAJ-AUTO"),
        ("BAJAJ-AUTO", "BAJAJ-AUTO"),
        (" Bajaj-Auto ", "BAJAJ-AUTO"),
        ("M&M", "M&M"),
        ("m&m", "M&M"),
        (" M&M ", "M&M"),
        ("INFY", "INFY"),
        (" infy ", "INFY"),
        ("RELIANCE", "RELIANCE"),
        (" reliance ", "RELIANCE"),
        ("", "MISSING"),
        (None, "MISSING"),
    ],
)
def test_normalize_ticker(value, expected):
    """Test ticker whitespace and case normalisation."""
    assert normalize_ticker(value) == expected
