"""Tests for backend.services.arm_client — HTTP method patterns and error handling."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from backend.services import arm_client


def _mock_response(json_data, status_code: int = 200) -> MagicMock:
    """Create a mock httpx.Response."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.is_success = 200 <= status_code < 300
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "error", request=MagicMock(), response=resp
        )
    return resp


# --- abandon_job (uses _request) ---


async def test_abandon_job_success():
    """abandon_job returns JSON on success."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.request.return_value = _mock_response({"success": True})
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.abandon_job(42)
    assert result == {"success": True}
    mock_client.request.assert_awaited_once_with("POST", "/api/v1/jobs/42/abandon")


async def test_abandon_job_connect_error():
    """abandon_job returns None on ConnectError."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.request.side_effect = httpx.ConnectError("refused")
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.abandon_job(42)
    assert result is None


# --- skip_and_finalize ---


async def test_skip_and_finalize_success():
    """skip_and_finalize returns JSON on success."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.request.return_value = _mock_response({"success": True, "message": "Job finalized"})
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.skip_and_finalize(7)
    assert result == {"success": True, "message": "Job finalized"}
    mock_client.request.assert_awaited_once_with("POST", "/api/v1/jobs/7/skip-and-finalize")


async def test_skip_and_finalize_connect_error():
    """skip_and_finalize returns None on ConnectError."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.request.side_effect = httpx.ConnectError("refused")
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.skip_and_finalize(7)
    assert result is None


# --- get_config ---


async def test_get_config_success():
    """get_config returns JSON on success."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.request.return_value = _mock_response({"RIPMETHOD": "mkv"})
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.get_config()
    assert result == {"RIPMETHOD": "mkv"}


async def test_get_config_http_error():
    """get_config returns error dict on HTTP 500 (not None)."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.request.return_value = _mock_response(
        {"error": "Internal error"}, status_code=500
    )
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.get_config()
    assert result is not None
    assert result["success"] is False
    assert "500" in result["error"]


# --- update_title ---


async def test_update_title_success():
    """update_title sends PUT with JSON body."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.request.return_value = _mock_response({"success": True})
    data = {"title": "New Title", "year": "2024"}
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.update_title(1, data)
    assert result == {"success": True}
    mock_client.request.assert_awaited_once_with(
        "PUT", "/api/v1/jobs/1/title", json=data
    )


async def test_update_title_connect_error():
    """update_title returns None on ConnectError."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.request.side_effect = httpx.ConnectError("refused")
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.update_title(1, {"title": "X"})
    assert result is None


# --- set_ripping_enabled ---


async def test_set_ripping_enabled_success():
    """set_ripping_enabled sends POST with JSON body."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.request.return_value = _mock_response({"success": True})
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.set_ripping_enabled(True)
    assert result == {"success": True}
    mock_client.request.assert_awaited_once_with(
        "POST", "/api/v1/system/ripping-enabled", json={"enabled": True}
    )


async def test_set_ripping_enabled_connect_error():
    """set_ripping_enabled returns None on ConnectError."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.request.side_effect = httpx.ConnectError("refused")
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.set_ripping_enabled(False)
    assert result is None


# --- update_drive ---


async def test_update_drive_success():
    """update_drive sends PATCH with JSON body."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.request.return_value = _mock_response({"success": True})
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.update_drive(3, {"name": "Drive A"})
    assert result == {"success": True}
    mock_client.request.assert_awaited_once_with(
        "PATCH", "/api/v1/drives/3", json={"name": "Drive A"}
    )


async def test_update_drive_http_error():
    """update_drive returns error dict on HTTP 404."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.request.return_value = _mock_response(
        {"error": "Not found"}, status_code=404
    )
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.update_drive(3, {"name": "X"})
    assert result is not None
    assert result["success"] is False


# --- pause_waiting_job ---


async def test_pause_waiting_job_success():
    """pause_waiting_job returns JSON on success."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.request.return_value = _mock_response({"success": True, "paused": True})
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.pause_waiting_job(42)
    assert result == {"success": True, "paused": True}
    mock_client.request.assert_awaited_once_with("POST", "/api/v1/jobs/42/pause")


async def test_pause_waiting_job_connect_error():
    """pause_waiting_job returns None on ConnectError."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.request.side_effect = httpx.ConnectError("refused")
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.pause_waiting_job(42)
    assert result is None


# --- search_metadata (direct httpx, not _request) ---


async def test_search_metadata_success():
    """search_metadata returns list of results."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = _mock_response(
        [{"title": "Matrix", "year": "1999"}])
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.search_metadata("Matrix")
    assert result == [{"title": "Matrix", "year": "1999"}]
    # Verify year not included in params when None
    call_kwargs = mock_client.get.call_args
    assert "year" not in call_kwargs[1].get("params", {})


async def test_search_metadata_with_year():
    """search_metadata includes year param when provided."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = _mock_response([])
    with patch.object(arm_client, "get_client", return_value=mock_client):
        await arm_client.search_metadata("Matrix", year="1999")
    call_kwargs = mock_client.get.call_args
    assert call_kwargs[1]["params"]["year"] == "1999"


async def test_search_metadata_raises_on_error():
    """search_metadata raises HTTPStatusError on 5xx."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = _mock_response({}, status_code=503)
    with patch.object(arm_client, "get_client", return_value=mock_client):
        with pytest.raises(httpx.HTTPStatusError):
            await arm_client.search_metadata("Matrix")


# --- get_media_detail ---


async def test_get_media_detail_success():
    """get_media_detail returns detail dict on 200."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = _mock_response(
        {"title": "Matrix", "imdb_id": "tt0133093"})
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.get_media_detail("tt0133093")
    assert result["title"] == "Matrix"


async def test_get_media_detail_404_returns_none():
    """get_media_detail returns None on 404 (not found)."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = 404
    resp.json.return_value = {}
    resp.raise_for_status = MagicMock()  # not called — 404 handled before
    mock_client.get.return_value = resp
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.get_media_detail("tt9999999")
    assert result is None


async def test_get_media_detail_raises_on_500():
    """get_media_detail raises on 500 (not 404)."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = _mock_response({}, status_code=500)
    with patch.object(arm_client, "get_client", return_value=mock_client):
        with pytest.raises(httpx.HTTPStatusError):
            await arm_client.get_media_detail("tt0133093")


# --- search_music_metadata ---


async def test_search_music_metadata_success():
    """search_music_metadata returns results."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = _mock_response(
        {"results": [{"title": "Master of Puppets"}], "total": 1})
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.search_music_metadata("Metallica")
    assert result["total"] == 1


async def test_search_music_metadata_filters_none_kwargs():
    """search_music_metadata excludes None kwargs from params."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = _mock_response({"results": [], "total": 0})
    with patch.object(arm_client, "get_client", return_value=mock_client):
        await arm_client.search_music_metadata(
            "Metallica", artist="Metallica", format=None, country="US")
    call_kwargs = mock_client.get.call_args
    params = call_kwargs[1]["params"]
    assert params["artist"] == "Metallica"
    assert params["country"] == "US"
    assert "format" not in params


async def test_search_music_metadata_converts_to_str():
    """search_music_metadata converts non-string kwargs to str."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = _mock_response({"results": [], "total": 0})
    with patch.object(arm_client, "get_client", return_value=mock_client):
        await arm_client.search_music_metadata("test", offset=25)
    call_kwargs = mock_client.get.call_args
    params = call_kwargs[1]["params"]
    assert params["offset"] == "25"


# --- get_music_detail ---


async def test_get_music_detail_success():
    """get_music_detail returns detail dict on 200."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = _mock_response(
        {"title": "Master of Puppets", "artist": "Metallica"})
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.get_music_detail("mbid-123")
    assert result["title"] == "Master of Puppets"


async def test_get_music_detail_404_returns_none():
    """get_music_detail returns None on 404."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = 404
    resp.json.return_value = {}
    resp.raise_for_status = MagicMock()
    mock_client.get.return_value = resp
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.get_music_detail("bad-mbid")
    assert result is None


# --- lookup_crc ---


async def test_lookup_crc_success():
    """lookup_crc returns CRC result dict."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = _mock_response(
        {"found": True, "results": [{"title": "Matrix"}], "has_api_key": True})
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.lookup_crc("abc123")
    assert result["found"] is True
    mock_client.get.assert_awaited_once_with("/api/v1/metadata/crc/abc123")


async def test_lookup_crc_raises_on_error():
    """lookup_crc raises HTTPStatusError on failure."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = _mock_response({}, status_code=500)
    with patch.object(arm_client, "get_client", return_value=mock_client):
        with pytest.raises(httpx.HTTPStatusError):
            await arm_client.lookup_crc("abc123")


# --- test_metadata_key ---


async def test_metadata_key_success():
    """test_metadata_key returns result dict."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = _mock_response(
        {"success": True, "message": "OMDb key valid", "provider": "omdb"})
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.test_metadata_key()
    assert result["success"] is True
    mock_client.get.assert_awaited_once_with("/api/v1/metadata/test-key", params={})


async def test_metadata_key_with_key_and_provider():
    """test_metadata_key includes key and provider in params when provided."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = _mock_response(
        {"success": True, "message": "Key valid", "provider": "tmdb"})
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.test_metadata_key(key="abc123", provider="tmdb")
    assert result["success"] is True
    mock_client.get.assert_awaited_once_with(
        "/api/v1/metadata/test-key", params={"key": "abc123", "provider": "tmdb"})


async def test_metadata_key_raises_on_error():
    """test_metadata_key raises HTTPStatusError on failure."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = _mock_response({}, status_code=502)
    with patch.object(arm_client, "get_client", return_value=mock_client):
        with pytest.raises(httpx.HTTPStatusError):
            await arm_client.test_metadata_key()


# --- get_setup_status ---


async def test_get_setup_status_success():
    """get_setup_status returns JSON on success."""
    data = {"first_run": True, "db_initialized": True}
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.request.return_value = _mock_response(data)
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.get_setup_status()
    assert result == data
    mock_client.request.assert_awaited_once_with("GET", "/api/v1/setup/status")


async def test_get_setup_status_unreachable():
    """get_setup_status returns None on ConnectError."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.request.side_effect = httpx.ConnectError("refused")
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.get_setup_status()
    assert result is None


# --- complete_setup ---


async def test_complete_setup_success():
    """complete_setup returns JSON on success."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.request.return_value = _mock_response({"success": True})
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.complete_setup()
    assert result == {"success": True}
    mock_client.request.assert_awaited_once_with("POST", "/api/v1/setup/complete")


async def test_complete_setup_unreachable():
    """complete_setup returns None on ConnectError."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.request.side_effect = httpx.ConnectError("refused")
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.complete_setup()
    assert result is None


# --- eject_drive ---


async def test_eject_drive_success():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.request.return_value = _mock_response({"success": True, "method": "eject"})
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.eject_drive(1, "eject")
    assert result["success"] is True
    mock_client.request.assert_awaited_once()


async def test_eject_drive_unreachable():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.request.side_effect = httpx.ConnectError("refused")
    with patch.object(arm_client, "get_client", return_value=mock_client):
        assert await arm_client.eject_drive(1) is None


# --- get_job_stats ---


async def test_get_job_stats_success():
    data = {"by_status": {"success": 5}, "by_type": {"movie": 3}, "total": 5}
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.request.return_value = _mock_response(data)
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.get_job_stats()
    assert result["total"] == 5


async def test_get_job_stats_unreachable():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.request.side_effect = httpx.ConnectError("refused")
    with patch.object(arm_client, "get_client", return_value=mock_client):
        assert await arm_client.get_job_stats() is None


# --- restart_arm ---


async def test_restart_arm_success():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.request.return_value = _mock_response({"success": True})
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.restart_arm()
    assert result["success"] is True


async def test_restart_arm_unreachable():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.request.side_effect = httpx.ConnectError("refused")
    with patch.object(arm_client, "get_client", return_value=mock_client):
        assert await arm_client.restart_arm() is None
