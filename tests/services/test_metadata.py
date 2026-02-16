"""Tests for backend.services.metadata — normalizers, search/details routing."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from backend.services import metadata
from backend.services.metadata import MetadataConfigError


# --- _normalize_omdb ---


def test_normalize_omdb_movie():
    """Movie type is normalized correctly."""
    item = {
        "Title": "The Matrix", "Year": "1999", "imdbID": "tt0133093",
        "Type": "movie", "Poster": "https://poster.jpg",
    }
    result = metadata._normalize_omdb(item)
    assert result["title"] == "The Matrix"
    assert result["year"] == "1999"
    assert result["imdb_id"] == "tt0133093"
    assert result["media_type"] == "movie"
    assert result["poster_url"] == "https://poster.jpg"


def test_normalize_omdb_series_type():
    """Series type is preserved as 'series'."""
    item = {"Title": "Breaking Bad", "Year": "2008", "imdbID": "tt0903747", "Type": "series", "Poster": "N/A"}
    result = metadata._normalize_omdb(item)
    assert result["media_type"] == "series"


def test_normalize_omdb_na_poster():
    """'N/A' poster is converted to None."""
    item = {"Title": "Test", "Year": "2020", "imdbID": "tt0000001", "Type": "movie", "Poster": "N/A"}
    result = metadata._normalize_omdb(item)
    assert result["poster_url"] is None


def test_normalize_omdb_unknown_type_defaults_to_movie():
    """Unknown types (e.g. 'game') default to 'movie'."""
    item = {"Title": "Game", "Year": "2020", "imdbID": "tt0000002", "Type": "game", "Poster": "N/A"}
    result = metadata._normalize_omdb(item)
    assert result["media_type"] == "movie"


def test_normalize_omdb_missing_fields():
    """Missing fields produce empty strings / None."""
    result = metadata._normalize_omdb({})
    assert result["title"] == ""
    assert result["year"] == ""
    assert result["imdb_id"] is None
    assert result["media_type"] == "movie"


# --- search() routing ---


async def test_search_routes_to_omdb():
    """search() calls _omdb_search when provider=omdb and key exists."""
    keys = {"provider": "omdb", "omdb_key": "test_key", "tmdb_key": None}
    with (
        patch.object(metadata, "_get_api_keys", return_value=keys),
        patch.object(metadata, "_omdb_search", new_callable=AsyncMock, return_value=[{"title": "Test"}]) as mock_omdb,
    ):
        result = await metadata.search("test")
    mock_omdb.assert_awaited_once_with("test", None, "test_key")
    assert result == [{"title": "Test"}]


async def test_search_routes_to_tmdb():
    """search() calls _tmdb_search when provider=tmdb and key exists."""
    keys = {"provider": "tmdb", "omdb_key": None, "tmdb_key": "tmdb_key"}
    with (
        patch.object(metadata, "_get_api_keys", return_value=keys),
        patch.object(metadata, "_tmdb_search", new_callable=AsyncMock, return_value=[]) as mock_tmdb,
    ):
        result = await metadata.search("test", "2024")
    mock_tmdb.assert_awaited_once_with("test", "2024", "tmdb_key")
    assert result == []


async def test_search_raises_on_no_key():
    """search() raises MetadataConfigError when no API key is configured."""
    keys = {"provider": "omdb", "omdb_key": None, "tmdb_key": None}
    with patch.object(metadata, "_get_api_keys", return_value=keys):
        with pytest.raises(MetadataConfigError):
            await metadata.search("test")


# --- get_details() routing ---


async def test_get_details_routes_to_omdb():
    """get_details() calls _omdb_details when provider=omdb."""
    keys = {"provider": "omdb", "omdb_key": "key", "tmdb_key": None}
    detail = {
        "title": "Matrix", "year": "1999", "imdb_id": "tt0133093",
        "media_type": "movie", "poster_url": None,
        "plot": "A hacker...", "background_url": None,
    }
    with (
        patch.object(metadata, "_get_api_keys", return_value=keys),
        patch.object(metadata, "_omdb_details", new_callable=AsyncMock, return_value=detail) as mock_det,
    ):
        result = await metadata.get_details("tt0133093")
    mock_det.assert_awaited_once_with("tt0133093", "key")
    assert result["title"] == "Matrix"


async def test_get_details_routes_to_tmdb():
    """get_details() calls _tmdb_find when provider=tmdb."""
    keys = {"provider": "tmdb", "omdb_key": None, "tmdb_key": "tkey"}
    with (
        patch.object(metadata, "_get_api_keys", return_value=keys),
        patch.object(metadata, "_tmdb_find", new_callable=AsyncMock, return_value=None) as mock_find,
    ):
        result = await metadata.get_details("tt9999999")
    mock_find.assert_awaited_once_with("tt9999999", "tkey")
    assert result is None


async def test_get_details_raises_on_no_key():
    """get_details() raises MetadataConfigError when no key configured."""
    keys = {"provider": "tmdb", "omdb_key": None, "tmdb_key": None}
    with patch.object(metadata, "_get_api_keys", return_value=keys):
        with pytest.raises(MetadataConfigError):
            await metadata.get_details("tt0133093")
