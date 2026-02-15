"""Tests for backend.services.arm_client — HTTP method patterns and error handling."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from backend.services import arm_client


def _mock_response(json_data: dict, status_code: int = 200) -> MagicMock:
    """Create a mock httpx.Response."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "error", request=MagicMock(), response=resp
        )
    return resp


# --- abandon_job ---


async def test_abandon_job_success():
    """abandon_job returns JSON on success."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = _mock_response({"success": True})
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.abandon_job(42)
    assert result == {"success": True}
    mock_client.post.assert_awaited_once_with("/api/v1/jobs/42/abandon")


async def test_abandon_job_connect_error():
    """abandon_job returns None on ConnectError."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.side_effect = httpx.ConnectError("refused")
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.abandon_job(42)
    assert result is None


# --- get_config ---


async def test_get_config_success():
    """get_config returns JSON on success."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = _mock_response({"RIPMETHOD": "mkv"})
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.get_config()
    assert result == {"RIPMETHOD": "mkv"}


async def test_get_config_http_error():
    """get_config returns None on HTTP error (e.g. 500)."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = _mock_response({}, status_code=500)
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.get_config()
    assert result is None


# --- update_title ---


async def test_update_title_success():
    """update_title sends PUT with JSON body."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.put.return_value = _mock_response({"success": True})
    data = {"title": "New Title", "year": "2024"}
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.update_title(1, data)
    assert result == {"success": True}
    mock_client.put.assert_awaited_once_with("/api/v1/jobs/1/title", json=data)


async def test_update_title_connect_error():
    """update_title returns None on ConnectError."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.put.side_effect = httpx.ConnectError("refused")
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.update_title(1, {"title": "X"})
    assert result is None


# --- set_ripping_enabled ---


async def test_set_ripping_enabled_success():
    """set_ripping_enabled sends POST with JSON body."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = _mock_response({"success": True})
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.set_ripping_enabled(True)
    assert result == {"success": True}
    mock_client.post.assert_awaited_once_with(
        "/api/v1/system/ripping-enabled", json={"enabled": True}
    )


async def test_set_ripping_enabled_connect_error():
    """set_ripping_enabled returns None on ConnectError."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.side_effect = httpx.ConnectError("refused")
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.set_ripping_enabled(False)
    assert result is None


# --- update_drive ---


async def test_update_drive_success():
    """update_drive sends PATCH with JSON body."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.patch.return_value = _mock_response({"success": True})
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.update_drive(3, {"name": "Drive A"})
    assert result == {"success": True}
    mock_client.patch.assert_awaited_once_with(
        "/api/v1/drives/3", json={"name": "Drive A"}
    )


async def test_update_drive_http_error():
    """update_drive returns None on HTTPError."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.patch.return_value = _mock_response({}, status_code=404)
    with patch.object(arm_client, "get_client", return_value=mock_client):
        result = await arm_client.update_drive(3, {"name": "X"})
    assert result is None
