"""Tests for backend.services.music_metadata."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from backend.services.music_metadata import (
    _build_artist_credit,
    _escape_lucene,
    _extract_catalog_number,
    _extract_format,
    _extract_label,
    get_details,
    search,
)


# ---------------------------------------------------------------------------
# Helper function tests (synchronous)
# ---------------------------------------------------------------------------


class TestBuildArtistCredit:
    def test_single_artist(self):
        credits = [{"name": "The Beatles"}]
        assert _build_artist_credit(credits) == "The Beatles"

    def test_two_artists_with_joinphrase(self):
        credits = [
            {"name": "David Bowie", "joinphrase": " & "},
            {"name": "Queen"},
        ]
        assert _build_artist_credit(credits) == "David Bowie & Queen"

    def test_three_artists_with_mixed_joinphrases(self):
        credits = [
            {"name": "A", "joinphrase": ", "},
            {"name": "B", "joinphrase": " feat. "},
            {"name": "C"},
        ]
        assert _build_artist_credit(credits) == "A, B feat. C"

    def test_empty_list(self):
        assert _build_artist_credit([]) == ""

    def test_missing_name_key(self):
        credits = [{"joinphrase": " & "}, {"name": "Solo"}]
        assert _build_artist_credit(credits) == " & Solo"


class TestExtractLabel:
    def test_extracts_label_name(self):
        info = [{"label": {"name": "Apple Records"}}]
        assert _extract_label(info) == "Apple Records"

    def test_empty_list(self):
        assert _extract_label([]) is None

    def test_no_label_key(self):
        info = [{"catalog-number": "ABC-123"}]
        assert _extract_label(info) is None

    def test_label_without_name(self):
        info = [{"label": {}}]
        assert _extract_label(info) is None


class TestExtractCatalogNumber:
    def test_extracts_catalog(self):
        info = [{"catalog-number": "PCS 7027"}]
        assert _extract_catalog_number(info) == "PCS 7027"

    def test_empty_list(self):
        assert _extract_catalog_number([]) is None

    def test_no_catalog_key(self):
        info = [{"label": {"name": "EMI"}}]
        assert _extract_catalog_number(info) is None


class TestExtractFormat:
    def test_extracts_format(self):
        media = [{"format": "CD"}]
        assert _extract_format(media) == "CD"

    def test_empty_list(self):
        assert _extract_format([]) is None

    def test_no_format_key(self):
        media = [{"track-count": 12}]
        assert _extract_format(media) is None


class TestEscapeLucene:
    def test_plain_text_unchanged(self):
        assert _escape_lucene("Abbey Road") == "Abbey Road"

    def test_escapes_special_characters(self):
        assert _escape_lucene("AC/DC") == r"AC\/DC"
        assert _escape_lucene("test+query") == r"test\+query"
        assert _escape_lucene('say "hello"') == r'say \"hello\"'

    def test_escapes_boolean_operators(self):
        assert _escape_lucene("this & that") == r"this \& that"
        assert _escape_lucene("a | b") == r"a \| b"

    def test_escapes_parentheses_and_brackets(self):
        assert _escape_lucene("test (1)") == r"test \(1\)"
        assert _escape_lucene("test [1]") == r"test \[1\]"

    def test_escapes_wildcards(self):
        assert _escape_lucene("foo*bar?") == r"foo\*bar\?"

    def test_empty_string(self):
        assert _escape_lucene("") == ""


# ---------------------------------------------------------------------------
# Async function tests
# ---------------------------------------------------------------------------

# Sample MusicBrainz search API response
SEARCH_RESPONSE = {
    "releases": [
        {
            "id": "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d",
            "title": "Abbey Road",
            "date": "1969-09-26",
            "country": "GB",
            "track-count": 17,
            "artist-credit": [{"name": "The Beatles"}],
            "media": [{"format": "CD"}],
            "label-info": [{"label": {"name": "Apple Records"}}],
            "release-group": {"primary-type": "Album"},
        },
        {
            "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "title": "Abbey Road (Remaster)",
            "date": "2019",
            "country": "US",
            "track-count": 17,
            "artist-credit": [{"name": "The Beatles"}],
            "media": [{"format": "CD"}],
            "label-info": [],
            "release-group": {"primary-type": "Album"},
        },
    ]
}

# Sample MusicBrainz release lookup response
DETAIL_RESPONSE = {
    "id": "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d",
    "title": "Abbey Road",
    "date": "1969-09-26",
    "country": "GB",
    "barcode": "0077774644020",
    "status": "Official",
    "artist-credit": [{"name": "The Beatles"}],
    "release-group": {"primary-type": "Album"},
    "label-info": [
        {
            "catalog-number": "PCS 7027",
            "label": {"name": "Apple Records"},
        }
    ],
    "media": [
        {
            "format": "CD",
            "track-count": 2,
            "tracks": [
                {
                    "number": "1",
                    "length": 259000,
                    "recording": {"title": "Come Together", "length": 259000},
                },
                {
                    "number": "2",
                    "length": 185000,
                    "recording": {"title": "Something", "length": 185000},
                },
            ],
        }
    ],
}


def _mock_response(json_data, status_code=200):
    """Build a mock httpx.Response."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "error", request=MagicMock(), response=resp
        )
    return resp


@pytest.fixture
def mock_client():
    """Patch _http_client to return a mock AsyncClient."""
    client = AsyncMock(spec=httpx.AsyncClient)
    # Make it work as async context manager
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)

    with patch("backend.services.music_metadata._http_client", return_value=client):
        yield client


# ---------------------------------------------------------------------------
# search() tests
# ---------------------------------------------------------------------------


class TestSearch:
    @pytest.mark.asyncio
    async def test_basic_search(self, mock_client):
        mock_client.get.return_value = _mock_response(SEARCH_RESPONSE)

        results = await search("Abbey Road")

        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert "/release" in call_args.args[0]
        params = call_args.kwargs["params"]
        assert params["query"] == "Abbey Road"

        assert len(results) == 2
        assert results[0]["title"] == "Abbey Road"
        assert results[0]["artist"] == "The Beatles"
        assert results[0]["year"] == "1969"
        assert results[0]["release_id"] == "b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d"
        assert results[0]["media_type"] == "music"
        assert results[0]["country"] == "GB"
        assert results[0]["release_type"] == "Album"
        assert results[0]["format"] == "CD"
        assert results[0]["label"] == "Apple Records"
        assert results[0]["track_count"] == 17
        assert "front-250" in results[0]["poster_url"]

    @pytest.mark.asyncio
    async def test_search_with_artist_filter(self, mock_client):
        mock_client.get.return_value = _mock_response({"releases": []})

        await search("Abbey Road", artist="The Beatles")

        params = mock_client.get.call_args.kwargs["params"]
        assert 'release:"Abbey Road"' in params["query"]
        assert 'artist:"The Beatles"' in params["query"]

    @pytest.mark.asyncio
    async def test_search_with_all_filters(self, mock_client):
        mock_client.get.return_value = _mock_response({"releases": []})

        await search(
            "test",
            artist="artist",
            release_type="album",
            format="CD",
            country="US",
            status="official",
        )

        params = mock_client.get.call_args.kwargs["params"]
        query = params["query"]
        assert "type:album" in query
        assert 'format:"CD"' in query
        assert "country:US" in query
        assert "status:official" in query

    @pytest.mark.asyncio
    async def test_search_escapes_special_chars(self, mock_client):
        mock_client.get.return_value = _mock_response({"releases": []})

        await search("AC/DC", artist="AC/DC")

        params = mock_client.get.call_args.kwargs["params"]
        query = params["query"]
        assert r"AC\/DC" in query

    @pytest.mark.asyncio
    async def test_empty_results(self, mock_client):
        mock_client.get.return_value = _mock_response({"releases": []})

        results = await search("nonexistent album xyz")
        assert results == []

    @pytest.mark.asyncio
    async def test_missing_date_yields_empty_year(self, mock_client):
        mock_client.get.return_value = _mock_response(
            {"releases": [{"id": "abc", "title": "No Date", "artist-credit": [{"name": "X"}]}]}
        )

        results = await search("No Date")
        assert results[0]["year"] == ""

    @pytest.mark.asyncio
    async def test_missing_id_yields_no_poster(self, mock_client):
        mock_client.get.return_value = _mock_response(
            {"releases": [{"title": "X", "artist-credit": [{"name": "Y"}]}]}
        )

        results = await search("X")
        assert results[0]["poster_url"] is None
        assert results[0]["release_id"] == ""

    @pytest.mark.asyncio
    async def test_http_error_propagates(self, mock_client):
        mock_client.get.return_value = _mock_response({}, status_code=500)

        with pytest.raises(httpx.HTTPStatusError):
            await search("test")


# ---------------------------------------------------------------------------
# get_details() tests
# ---------------------------------------------------------------------------


class TestGetDetails:
    @pytest.mark.asyncio
    async def test_returns_full_details(self, mock_client):
        mock_client.get.return_value = _mock_response(DETAIL_RESPONSE)

        result = await get_details("b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d")

        assert result is not None
        assert result["title"] == "Abbey Road"
        assert result["artist"] == "The Beatles"
        assert result["year"] == "1969"
        assert result["country"] == "GB"
        assert result["barcode"] == "0077774644020"
        assert result["status"] == "Official"
        assert result["label"] == "Apple Records"
        assert result["catalog_number"] == "PCS 7027"
        assert result["release_type"] == "Album"
        assert result["format"] == "CD"
        assert result["media_type"] == "music"
        assert result["track_count"] == 2

    @pytest.mark.asyncio
    async def test_track_listing(self, mock_client):
        mock_client.get.return_value = _mock_response(DETAIL_RESPONSE)

        result = await get_details("b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d")

        tracks = result["tracks"]
        assert len(tracks) == 2
        assert tracks[0]["number"] == "1"
        assert tracks[0]["title"] == "Come Together"
        assert tracks[0]["length_ms"] == 259000
        assert tracks[1]["title"] == "Something"

    @pytest.mark.asyncio
    async def test_404_returns_none(self, mock_client):
        resp = MagicMock(spec=httpx.Response)
        resp.status_code = 404
        mock_client.get.return_value = resp

        result = await get_details("nonexistent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_empty_barcode_becomes_none(self, mock_client):
        data = {**DETAIL_RESPONSE, "barcode": ""}
        mock_client.get.return_value = _mock_response(data)

        result = await get_details("test-id")
        assert result["barcode"] is None

    @pytest.mark.asyncio
    async def test_poster_url_constructed(self, mock_client):
        mock_client.get.return_value = _mock_response(DETAIL_RESPONSE)

        result = await get_details("b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d")
        assert result["poster_url"] == (
            "https://coverartarchive.org/release/b10bbbfc-cf9e-42e0-be17-e2c3e1d2600d/front-250"
        )

    @pytest.mark.asyncio
    async def test_track_count_falls_back_to_len(self, mock_client):
        data = {
            **DETAIL_RESPONSE,
            "media": [
                {
                    "format": "CD",
                    "tracks": [
                        {"number": "1", "recording": {"title": "Track 1"}},
                    ],
                    # No track-count key
                }
            ],
        }
        mock_client.get.return_value = _mock_response(data)

        result = await get_details("test-id")
        assert result["track_count"] == 1

    @pytest.mark.asyncio
    async def test_track_length_falls_back_to_recording(self, mock_client):
        data = {
            **DETAIL_RESPONSE,
            "media": [
                {
                    "format": "CD",
                    "track-count": 1,
                    "tracks": [
                        {
                            "number": "1",
                            # No track-level length
                            "recording": {"title": "Song", "length": 300000},
                        },
                    ],
                }
            ],
        }
        mock_client.get.return_value = _mock_response(data)

        result = await get_details("test-id")
        assert result["tracks"][0]["length_ms"] == 300000

    @pytest.mark.asyncio
    async def test_http_error_propagates(self, mock_client):
        mock_client.get.return_value = _mock_response({}, status_code=500)

        with pytest.raises(httpx.HTTPStatusError):
            await get_details("test-id")
