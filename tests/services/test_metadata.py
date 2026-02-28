"""Tests for backend.services.metadata helpers."""

import pytest

from backend.services.metadata import _extract_year


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("2006-05-19", "2006"),
        ("2006\u20132008", "2006"),       # em-dash range
        ("2006\u2013", "2006"),           # open em-dash range
        ("2006-2008", "2006"),            # hyphen range
        ("2006", "2006"),                 # plain year
        ("", ""),                         # empty string
        ("N/A", "N/A"),                   # no digits
    ],
)
def test_extract_year(raw: str, expected: str) -> None:
    assert _extract_year(raw) == expected
