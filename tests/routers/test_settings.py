"""Tests for backend.routers.settings — transcoder test endpoints, auth status, bash script."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch


# --- POST /api/settings/transcoder/test-connection ---


async def test_connection_success(app_client):
    """test-connection returns all-green result."""
    result = {
        "reachable": True,
        "auth_ok": True,
        "auth_required": True,
        "gpu_support": {"nvenc": True},
        "worker_running": True,
        "queue_size": 0,
        "error": None,
    }
    with patch(
        "backend.routers.settings.transcoder_client.test_connection",
        new_callable=AsyncMock,
        return_value=result,
    ):
        resp = await app_client.post("/api/settings/transcoder/test-connection")
    assert resp.status_code == 200
    data = resp.json()
    assert data["reachable"] is True
    assert data["auth_ok"] is True


async def test_connection_offline(app_client):
    """test-connection returns reachable=False when transcoder is offline."""
    result = {
        "reachable": False,
        "auth_ok": False,
        "auth_required": False,
        "gpu_support": None,
        "worker_running": False,
        "queue_size": 0,
        "error": "Connection failed: refused",
    }
    with patch(
        "backend.routers.settings.transcoder_client.test_connection",
        new_callable=AsyncMock,
        return_value=result,
    ):
        resp = await app_client.post("/api/settings/transcoder/test-connection")
    assert resp.status_code == 200
    data = resp.json()
    assert data["reachable"] is False
    assert data["error"] is not None


async def test_connection_auth_failed(app_client):
    """test-connection returns auth_ok=False when API key is bad."""
    result = {
        "reachable": True,
        "auth_ok": False,
        "auth_required": True,
        "gpu_support": {},
        "worker_running": True,
        "queue_size": 0,
        "error": None,
    }
    with patch(
        "backend.routers.settings.transcoder_client.test_connection",
        new_callable=AsyncMock,
        return_value=result,
    ):
        resp = await app_client.post("/api/settings/transcoder/test-connection")
    assert resp.status_code == 200
    data = resp.json()
    assert data["reachable"] is True
    assert data["auth_ok"] is False


# --- POST /api/settings/transcoder/test-webhook ---


async def test_webhook_success(app_client):
    """test-webhook returns secret_ok=True on valid secret."""
    result = {"reachable": True, "secret_ok": True, "secret_required": False, "error": None}
    with patch(
        "backend.routers.settings.transcoder_client.test_webhook",
        new_callable=AsyncMock,
        return_value=result,
    ):
        resp = await app_client.post(
            "/api/settings/transcoder/test-webhook",
            json={"webhook_secret": "correct-secret"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["secret_ok"] is True


async def test_webhook_bad_secret(app_client):
    """test-webhook returns secret_ok=False on bad secret."""
    result = {"reachable": True, "secret_ok": False, "secret_required": True, "error": None}
    with patch(
        "backend.routers.settings.transcoder_client.test_webhook",
        new_callable=AsyncMock,
        return_value=result,
    ):
        resp = await app_client.post(
            "/api/settings/transcoder/test-webhook",
            json={"webhook_secret": "wrong"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["secret_ok"] is False
    assert data["secret_required"] is True


async def test_webhook_empty_body(app_client):
    """test-webhook defaults to empty secret when body has no webhook_secret."""
    result = {"reachable": True, "secret_ok": True, "secret_required": False, "error": None}
    with patch(
        "backend.routers.settings.transcoder_client.test_webhook",
        new_callable=AsyncMock,
        return_value=result,
    ) as mock_fn:
        resp = await app_client.post(
            "/api/settings/transcoder/test-webhook",
            json={},
        )
    assert resp.status_code == 200
    mock_fn.assert_awaited_once_with("")


# --- GET /api/settings (auth status) ---


async def test_settings_includes_auth_status(app_client):
    """get_settings includes transcoder_auth_status from health response."""
    health = {
        "status": "healthy",
        "gpu_support": {"nvenc": True},
        "config": {"video_encoder": "nvenc_h265"},
        "require_api_auth": True,
        "webhook_secret_configured": True,
    }
    with (
        patch("backend.routers.settings.arm_client.get_config", new_callable=AsyncMock, return_value=None),
        patch("backend.routers.settings.arm_db.get_all_config_safe", return_value={"RIPMETHOD": "mkv"}),
        patch("backend.routers.settings.arm_client.get_gpu_support", new_callable=AsyncMock, return_value=None),
        patch("backend.routers.settings.transcoder_client.get_config", new_callable=AsyncMock, return_value=None),
        patch("backend.routers.settings.transcoder_client.health", new_callable=AsyncMock, return_value=health),
        patch("backend.routers.settings._read_hb_presets", return_value=None),
    ):
        resp = await app_client.get("/api/settings")
    assert resp.status_code == 200
    data = resp.json()
    auth = data["transcoder_auth_status"]
    assert auth is not None
    assert auth["require_api_auth"] is True
    assert auth["webhook_secret_configured"] is True


# --- GET /api/settings/bash-script ---


async def test_get_bash_script(app_client):
    """GET bash-script returns script info with default_transcoder_url."""
    script_info = {
        "script_exists": True,
        "arm_path": "/etc/arm/config/notify_transcoder.sh",
        "variables": {
            "transcoder_url": "http://arm-transcoder:5000/webhook/arm",
            "webhook_secret": "",
            "local_raw_path": "",
            "shared_raw_path": "",
        },
        "content": "#!/usr/bin/env bash\necho hello",
    }
    with patch("backend.routers.settings.bash_script.read_script", return_value=script_info):
        resp = await app_client.get("/api/settings/bash-script")
    assert resp.status_code == 200
    data = resp.json()
    assert data["script_exists"] is True
    assert data["default_transcoder_url"] == "http://transcoder-test:5000/webhook/arm"
    assert data["variables"]["transcoder_url"] == "http://arm-transcoder:5000/webhook/arm"


# --- PUT /api/settings/bash-script ---


async def test_put_bash_script_success(app_client):
    """PUT bash-script returns success on write."""
    with patch(
        "backend.routers.settings.bash_script.write_script",
        return_value={"success": True, "arm_path": "/etc/arm/config/notify_transcoder.sh"},
    ):
        resp = await app_client.put(
            "/api/settings/bash-script",
            json={"transcoder_url": "http://arm-transcoder:5000/webhook/arm"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["arm_path"] == "/etc/arm/config/notify_transcoder.sh"


async def test_put_bash_script_failure(app_client):
    """PUT bash-script returns 500 on write failure."""
    with patch(
        "backend.routers.settings.bash_script.write_script",
        return_value={"success": False, "error": "Permission denied"},
    ):
        resp = await app_client.put(
            "/api/settings/bash-script",
            json={"transcoder_url": "http://arm-transcoder:5000/webhook/arm"},
        )
    assert resp.status_code == 500
