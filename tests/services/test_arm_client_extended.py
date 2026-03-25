"""Tests for arm_client: multi-title, track title, set_job_tracks, abcde config."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from backend.services import arm_client


def _mock_response(json_data, status_code: int = 200) -> MagicMock:
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


# --- toggle_multi_title ---


async def test_toggle_multi_title_success():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.request.return_value = _mock_response({"success": True, "multi_title": True})
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.toggle_multi_title(1, {"enabled": True})
    assert result == {"success": True, "multi_title": True}
    mock_client.request.assert_awaited_once_with(
        "POST", "/api/v1/jobs/1/multi-title", json={"enabled": True}
    )


async def test_toggle_multi_title_connect_error():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.request.side_effect = httpx.ConnectError("refused")
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.toggle_multi_title(1, {"enabled": True})
    assert result is None


# --- update_track_title ---


async def test_update_track_title_success():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.request.return_value = _mock_response({"success": True, "updated": {"title": "X"}})
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.update_track_title(1, 5, {"title": "X"})
    assert result["success"] is True
    mock_client.request.assert_awaited_once_with(
        "PUT", "/api/v1/jobs/1/tracks/5/title", json={"title": "X"}
    )


async def test_update_track_title_connect_error():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.request.side_effect = httpx.ConnectError("refused")
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.update_track_title(1, 5, {"title": "X"})
    assert result is None


# --- clear_track_title ---


async def test_clear_track_title_success():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.request.return_value = _mock_response({"success": True})
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.clear_track_title(1, 5)
    assert result == {"success": True}
    mock_client.request.assert_awaited_once_with(
        "DELETE", "/api/v1/jobs/1/tracks/5/title"
    )


async def test_clear_track_title_connect_error():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.request.side_effect = httpx.ConnectError("refused")
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.clear_track_title(1, 5)
    assert result is None


# --- set_job_tracks ---


async def test_set_job_tracks_success():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.request.return_value = _mock_response({"success": True})
    tracks = [{"track_number": "1", "title": "Track 1"}]
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.set_job_tracks(1, tracks)
    assert result == {"success": True}
    mock_client.request.assert_awaited_once_with(
        "PUT", "/api/v1/jobs/1/tracks", json={"tracks": tracks}
    )


async def test_set_job_tracks_connect_error():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.request.side_effect = httpx.ConnectError("refused")
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.set_job_tracks(1, [])
    assert result is None


# --- update_abcde_config ---


async def test_update_abcde_config_success():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.request.return_value = _mock_response({"success": True})
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.update_abcde_config("OUTPUTTYPE=flac\n")
    assert result == {"success": True}
    mock_client.request.assert_awaited_once_with(
        "PUT", "/api/v1/settings/abcde", json={"content": "OUTPUTTYPE=flac\n"}
    )


async def test_update_abcde_config_connect_error():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.request.side_effect = httpx.ConnectError("refused")
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.update_abcde_config("content")
    assert result is None


# --- get_abcde_config ---


async def test_get_abcde_config_success():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.request.return_value = _mock_response(
        {"content": "# abcde.conf", "path": "/etc/abcde.conf", "exists": True}
    )
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.get_abcde_config()
    assert result["exists"] is True
    assert result["content"] == "# abcde.conf"


# --- naming_preview ---


async def test_naming_preview_success():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.request.return_value = _mock_response({"result": "Movie (2024)"})
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.naming_preview("{title} ({year})", {"title": "Movie", "year": "2024"})
    assert result["result"] == "Movie (2024)"
    mock_client.request.assert_awaited_once_with(
        "POST", "/api/v1/naming/preview",
        json={"pattern": "{title} ({year})", "variables": {"title": "Movie", "year": "2024"}},
    )


# --- update_job_naming ---


async def test_update_job_naming_success():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.request.return_value = _mock_response({
        "success": True, "title_pattern_override": "{title} - E{episode}", "folder_pattern_override": None
    })
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.update_job_naming(1, {"title_pattern_override": "{title} - E{episode}"})
    assert result["success"] is True
    assert result["title_pattern_override"] == "{title} - E{episode}"
    mock_client.request.assert_awaited_once_with(
        "PATCH", "/api/v1/jobs/1/naming",
        json={"title_pattern_override": "{title} - E{episode}"},
    )


# --- validate_naming_pattern ---


async def test_validate_naming_pattern_invalid():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.request.return_value = _mock_response({
        "valid": False, "invalid_vars": ["episde"], "suggestions": {"episde": "episode"}
    })
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.validate_naming_pattern("{title} {episde}")
    assert result["valid"] is False
    assert "episde" in result["invalid_vars"]


# --- get_naming_variables ---


async def test_get_naming_variables():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.request.return_value = _mock_response({
        "variables": ["album", "artist", "episode", "label", "season", "title", "video_type", "year"],
        "descriptions": {"title": "Disc title"}
    })
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.get_naming_variables()
    assert len(result["variables"]) == 8
    assert "title" in result["variables"]
