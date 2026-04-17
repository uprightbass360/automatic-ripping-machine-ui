"""Additional tests for backend.routers.settings — uncovered lines."""

from __future__ import annotations

import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from backend.routers.settings import _drive_capabilities, _read_hb_presets


# --- _read_hb_presets ---


def test_read_hb_presets_success(tmp_path):
    presets_file = tmp_path / "presets.json"
    presets_file.write_text(json.dumps(["Very Fast 1080p30", "Fast 1080p30"]))
    with patch("backend.routers.settings.app_settings") as mock_settings:
        mock_settings.arm_hb_presets_path = str(presets_file)
        result = _read_hb_presets()
    assert result == ["Very Fast 1080p30", "Fast 1080p30"]


def test_read_hb_presets_missing_file():
    with patch("backend.routers.settings.app_settings") as mock_settings:
        mock_settings.arm_hb_presets_path = "/nonexistent/presets.json"
        result = _read_hb_presets()
    assert result is None


def test_read_hb_presets_none_path():
    with patch("backend.routers.settings.app_settings") as mock_settings:
        mock_settings.arm_hb_presets_path = None
        result = _read_hb_presets()
    assert result is None


def test_read_hb_presets_invalid_json(tmp_path):
    presets_file = tmp_path / "presets.json"
    presets_file.write_text("not valid json{{{")
    with patch("backend.routers.settings.app_settings") as mock_settings:
        mock_settings.arm_hb_presets_path = str(presets_file)
        result = _read_hb_presets()
    assert result is None


def test_read_hb_presets_non_list(tmp_path):
    presets_file = tmp_path / "presets.json"
    presets_file.write_text(json.dumps({"key": "value"}))
    with patch("backend.routers.settings.app_settings") as mock_settings:
        mock_settings.arm_hb_presets_path = str(presets_file)
        result = _read_hb_presets()
    assert result is None


# --- _drive_capabilities ---


def test_drive_capabilities_all():
    drive = MagicMock()
    drive.read_cd = True
    drive.read_dvd = True
    drive.read_bd = True
    drive.uhd_capable = True
    assert _drive_capabilities(drive) == ["CD", "DVD", "BD", "UHD"]


def test_drive_capabilities_none():
    drive = MagicMock()
    drive.read_cd = False
    drive.read_dvd = False
    drive.read_bd = False
    drive.uhd_capable = False
    assert _drive_capabilities(drive) == []


def test_drive_capabilities_partial():
    drive = MagicMock()
    drive.read_cd = True
    drive.read_dvd = True
    drive.read_bd = False
    drive.uhd_capable = False
    assert _drive_capabilities(drive) == ["CD", "DVD"]


# --- GET /api/settings ---


async def test_get_settings_all_sources(app_client):
    """get_settings with all data sources available."""
    arm_resp = {
        "config": {"RIPMETHOD": "mkv"},
        "comments": {"RIPMETHOD": "Rip method"},
        "naming_variables": {"title": "Movie title"},
    }
    tc_config = {"config": {"video_encoder": "x265"}, "updatable_keys": ["video_encoder"]}
    health = {
        "status": "healthy",
        "gpu_support": {"nvenc": True},
        "require_api_auth": False,
        "webhook_secret_configured": False,
    }
    with (
        patch("backend.routers.settings.arm_client.get_config", new_callable=AsyncMock, return_value=arm_resp),
        patch("backend.routers.settings.arm_db.get_all_config_safe", return_value=None),
        patch("backend.routers.settings.transcoder_client.get_config", new_callable=AsyncMock, return_value=tc_config),
        patch("backend.routers.settings.transcoder_client.health", new_callable=AsyncMock, return_value=health),
        patch("backend.routers.settings._read_hb_presets", return_value=["Fast 1080p30"]),
    ):
        resp = await app_client.get("/api/settings")
    assert resp.status_code == 200
    data = resp.json()
    assert data["arm_config"] == {"RIPMETHOD": "mkv"}
    assert data["arm_metadata"] == {"RIPMETHOD": "Rip method"}
    assert data["naming_variables"] == {"title": "Movie title"}
    assert data["transcoder_config"] == tc_config
    assert data["gpu_support"] == {"nvenc": True}
    assert data["arm_handbrake_presets"] == ["Fast 1080p30"]


async def test_get_settings_arm_offline_falls_back_to_db(app_client):
    """get_settings falls back to arm_db when ARM API is unreachable."""
    db_config = {"RIPMETHOD": "mkv", "OMDB_API_KEY": "***"}
    with (
        patch("backend.routers.settings.arm_client.get_config", new_callable=AsyncMock, return_value=None),
        patch("backend.routers.settings.arm_db.get_all_config_safe", return_value=db_config),
        patch("backend.routers.settings.transcoder_client.get_config", new_callable=AsyncMock, return_value=None),
        patch("backend.routers.settings.transcoder_client.health", new_callable=AsyncMock, return_value=None),
        patch("backend.routers.settings._read_hb_presets", return_value=None),
    ):
        resp = await app_client.get("/api/settings")
    assert resp.status_code == 200
    data = resp.json()
    assert data["arm_config"] == db_config
    assert data["transcoder_config"] is None
    assert data["gpu_support"] is None


async def test_get_settings_transcoder_config_fallback_from_health(app_client):
    """When /config fails but /health succeeds, config is extracted from health."""
    health = {
        "status": "healthy",
        "gpu_support": None,
        "config": {"video_encoder": "x265"},
        "require_api_auth": False,
        "webhook_secret_configured": False,
    }
    with (
        patch("backend.routers.settings.arm_client.get_config", new_callable=AsyncMock, return_value=None),
        patch("backend.routers.settings.arm_db.get_all_config_safe", return_value=None),
        patch("backend.routers.settings.transcoder_client.get_config", new_callable=AsyncMock, return_value=None),
        patch("backend.routers.settings.transcoder_client.health", new_callable=AsyncMock, return_value=health),
        patch("backend.routers.settings._read_hb_presets", return_value=None),
    ):
        resp = await app_client.get("/api/settings")
    assert resp.status_code == 200
    data = resp.json()
    assert data["transcoder_config"]["config"] == {"video_encoder": "x265"}


# --- PUT /api/settings/arm ---


async def test_update_arm_config_success(app_client):
    with patch(
        "backend.routers.settings.arm_client.update_config",
        new_callable=AsyncMock,
        return_value={"success": True},
    ):
        resp = await app_client.put(
            "/api/settings/arm", json={"config": {"RIPMETHOD": "backup"}}
        )
    assert resp.status_code == 200
    assert resp.json()["success"] is True


async def test_update_arm_config_unreachable(app_client):
    with patch(
        "backend.routers.settings.arm_client.update_config",
        new_callable=AsyncMock,
        return_value=None,
    ):
        resp = await app_client.put(
            "/api/settings/arm", json={"config": {"RIPMETHOD": "backup"}}
        )
    assert resp.status_code == 502
    assert "unreachable" in resp.json()["detail"].lower()


async def test_update_arm_config_failure(app_client):
    with patch(
        "backend.routers.settings.arm_client.update_config",
        new_callable=AsyncMock,
        return_value={"success": False, "error": "Invalid key"},
    ):
        resp = await app_client.put(
            "/api/settings/arm", json={"config": {"BAD_KEY": "value"}}
        )
    assert resp.status_code == 400
    assert "Invalid key" in resp.json()["detail"]


# --- PATCH /api/settings/transcoder ---


async def test_update_transcoder_config_success(app_client):
    with patch(
        "backend.routers.settings.transcoder_client.update_config",
        new_callable=AsyncMock,
        return_value={"success": True},
    ):
        resp = await app_client.patch(
            "/api/settings/transcoder", json={"video_encoder": "nvenc_h265"}
        )
    assert resp.status_code == 200
    assert resp.json()["success"] is True


async def test_update_transcoder_config_unreachable(app_client):
    with patch(
        "backend.routers.settings.transcoder_client.update_config",
        new_callable=AsyncMock,
        return_value=None,
    ):
        resp = await app_client.patch(
            "/api/settings/transcoder", json={"video_encoder": "x265"}
        )
    assert resp.status_code == 502
    assert "unreachable" in resp.json()["detail"].lower()


async def test_update_transcoder_config_failure(app_client):
    with patch(
        "backend.routers.settings.transcoder_client.update_config",
        new_callable=AsyncMock,
        return_value={"success": False, "detail": "Invalid encoder"},
    ):
        resp = await app_client.patch(
            "/api/settings/transcoder", json={"video_encoder": "bad"}
        )
    assert resp.status_code == 400
    assert "Invalid encoder" in resp.json()["detail"]


# --- GET /api/settings/test-metadata ---


async def test_test_metadata_key_success(app_client):
    with patch(
        "backend.routers.settings.arm_client.test_metadata_key",
        new_callable=AsyncMock,
        return_value={"success": True, "message": "OMDb key valid", "provider": "omdb"},
    ):
        resp = await app_client.get("/api/settings/test-metadata")
    assert resp.status_code == 200
    assert resp.json()["success"] is True


async def test_test_metadata_key_http_error(app_client):
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 502
    mock_resp.json.return_value = {"detail": "Upstream error"}
    with patch(
        "backend.routers.settings.arm_client.test_metadata_key",
        new_callable=AsyncMock,
        side_effect=httpx.HTTPStatusError("error", request=MagicMock(), response=mock_resp),
    ):
        resp = await app_client.get("/api/settings/test-metadata")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert data["message"] == "Upstream error"


async def test_test_metadata_key_connect_error(app_client):
    with patch(
        "backend.routers.settings.arm_client.test_metadata_key",
        new_callable=AsyncMock,
        side_effect=httpx.ConnectError("refused"),
    ):
        resp = await app_client.get("/api/settings/test-metadata")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert "unreachable" in data["message"].lower()


# --- GET /api/settings/transcoder/scheme ---


async def test_get_transcoder_scheme_success(app_client):
    data = {"slug": "default", "name": "Default Scheme", "presets": []}
    with patch(
        "backend.routers.settings.transcoder_client.get_scheme",
        new_callable=AsyncMock,
        return_value=data,
    ):
        resp = await app_client.get("/api/settings/transcoder/scheme")
    assert resp.status_code == 200
    assert resp.json()["slug"] == "default"


async def test_get_transcoder_scheme_unreachable(app_client):
    with patch(
        "backend.routers.settings.transcoder_client.get_scheme",
        new_callable=AsyncMock,
        return_value=None,
    ):
        resp = await app_client.get("/api/settings/transcoder/scheme")
    assert resp.status_code == 502
    assert "unreachable" in resp.json()["detail"].lower()


# --- GET /api/settings/transcoder/presets ---


async def test_get_transcoder_presets_success(app_client):
    data = {"presets": [{"slug": "hq-1080p", "name": "HQ 1080p"}]}
    with patch(
        "backend.routers.settings.transcoder_client.get_presets",
        new_callable=AsyncMock,
        return_value=data,
    ):
        resp = await app_client.get("/api/settings/transcoder/presets")
    assert resp.status_code == 200
    assert resp.json()["presets"][0]["slug"] == "hq-1080p"


async def test_get_transcoder_presets_unreachable(app_client):
    with patch(
        "backend.routers.settings.transcoder_client.get_presets",
        new_callable=AsyncMock,
        return_value=None,
    ):
        resp = await app_client.get("/api/settings/transcoder/presets")
    assert resp.status_code == 502
    assert "unreachable" in resp.json()["detail"].lower()


# --- PUT /api/settings/abcde failure ---


async def test_put_abcde_config_failure(app_client):
    with patch(
        "backend.routers.settings.arm_client.update_abcde_config",
        new_callable=AsyncMock,
        return_value={"success": False, "error": "Parse error"},
    ):
        resp = await app_client.put(
            "/api/settings/abcde", json={"content": "invalid\x00content"}
        )
    assert resp.status_code == 400
    assert "Parse error" in resp.json()["detail"]


# --- POST /api/settings/transcoder/presets ---


async def test_create_preset_proxy_success(app_client):
    with patch(
        "backend.routers.settings.transcoder_client.create_preset",
        new_callable=AsyncMock,
        return_value={"slug": "x", "name": "X"},
    ):
        resp = await app_client.post(
            "/api/settings/transcoder/presets",
            json={"name": "X", "parent_slug": "y", "overrides": {}},
        )
    assert resp.status_code == 201
    assert resp.json() == {"slug": "x", "name": "X"}


async def test_create_preset_proxy_offline(app_client):
    with patch(
        "backend.routers.settings.transcoder_client.create_preset",
        new_callable=AsyncMock,
        return_value=None,
    ):
        resp = await app_client.post(
            "/api/settings/transcoder/presets",
            json={"name": "X", "parent_slug": "y"},
        )
    assert resp.status_code == 502


async def test_create_preset_proxy_forwards_4xx_detail(app_client):
    err_resp = httpx.Response(409, json={"detail": "Slug exists"})
    err = httpx.HTTPStatusError("conflict", request=None, response=err_resp)
    with patch(
        "backend.routers.settings.transcoder_client.create_preset",
        new_callable=AsyncMock,
        side_effect=err,
    ):
        resp = await app_client.post(
            "/api/settings/transcoder/presets",
            json={"name": "X", "parent_slug": "y"},
        )
    assert resp.status_code == 409
    assert resp.json()["detail"] == "Slug exists"


# --- PATCH /api/settings/transcoder/presets/{slug} ---


async def test_update_preset_proxy_success(app_client):
    with patch(
        "backend.routers.settings.transcoder_client.update_preset",
        new_callable=AsyncMock,
        return_value={"slug": "x", "name": "Y"},
    ):
        resp = await app_client.patch(
            "/api/settings/transcoder/presets/x", json={"name": "Y"}
        )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Y"


async def test_update_preset_proxy_offline(app_client):
    with patch(
        "backend.routers.settings.transcoder_client.update_preset",
        new_callable=AsyncMock,
        return_value=None,
    ):
        resp = await app_client.patch(
            "/api/settings/transcoder/presets/x", json={}
        )
    assert resp.status_code == 502


async def test_update_preset_proxy_forwards_404(app_client):
    err_resp = httpx.Response(404, json={"detail": "Cannot update built-in"})
    err = httpx.HTTPStatusError("not found", request=None, response=err_resp)
    with patch(
        "backend.routers.settings.transcoder_client.update_preset",
        new_callable=AsyncMock,
        side_effect=err,
    ):
        resp = await app_client.patch(
            "/api/settings/transcoder/presets/x", json={}
        )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Cannot update built-in"


# --- DELETE /api/settings/transcoder/presets/{slug} ---


async def test_delete_preset_proxy_success(app_client):
    with patch(
        "backend.routers.settings.transcoder_client.delete_preset",
        new_callable=AsyncMock,
        return_value={"success": True, "deleted": "x"},
    ):
        resp = await app_client.delete("/api/settings/transcoder/presets/x")
    assert resp.status_code == 200
    assert resp.json()["deleted"] == "x"


async def test_delete_preset_proxy_offline(app_client):
    with patch(
        "backend.routers.settings.transcoder_client.delete_preset",
        new_callable=AsyncMock,
        return_value=None,
    ):
        resp = await app_client.delete("/api/settings/transcoder/presets/x")
    assert resp.status_code == 502


async def test_delete_preset_proxy_forwards_404(app_client):
    err_resp = httpx.Response(404, json={"detail": "Preset not found"})
    err = httpx.HTTPStatusError("not found", request=None, response=err_resp)
    with patch(
        "backend.routers.settings.transcoder_client.delete_preset",
        new_callable=AsyncMock,
        side_effect=err,
    ):
        resp = await app_client.delete("/api/settings/transcoder/presets/x")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Preset not found"
