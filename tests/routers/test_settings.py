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


# --- GET /api/settings/abcde ---


async def test_get_abcde_config_success(app_client):
    """GET abcde config returns content from ARM."""
    result = {"content": "# abcde config\nCDDBMETHOD=musicbrainz\n", "success": True}
    with patch(
        "backend.routers.settings.arm_client.get_abcde_config",
        new_callable=AsyncMock,
        return_value=result,
    ):
        resp = await app_client.get("/api/settings/abcde")
    assert resp.status_code == 200
    data = resp.json()
    assert data["content"] == "# abcde config\nCDDBMETHOD=musicbrainz\n"
    assert data["success"] is True


async def test_get_abcde_config_arm_unreachable(app_client):
    """GET abcde config returns 502 when ARM is unreachable."""
    with patch(
        "backend.routers.settings.arm_client.get_abcde_config",
        new_callable=AsyncMock,
        return_value=None,
    ):
        resp = await app_client.get("/api/settings/abcde")
    assert resp.status_code == 502
    assert "unreachable" in resp.json()["detail"].lower()


# --- PUT /api/settings/abcde ---


async def test_put_abcde_config_success(app_client):
    """PUT abcde config writes content via ARM."""
    result = {"success": True}
    with patch(
        "backend.routers.settings.arm_client.update_abcde_config",
        new_callable=AsyncMock,
        return_value=result,
    ) as mock_fn:
        resp = await app_client.put(
            "/api/settings/abcde",
            json={"content": "CDDBMETHOD=musicbrainz\n"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    mock_fn.assert_awaited_once_with("CDDBMETHOD=musicbrainz\n")


async def test_put_abcde_config_arm_unreachable(app_client):
    """PUT abcde config returns 502 when ARM is unreachable."""
    with patch(
        "backend.routers.settings.arm_client.update_abcde_config",
        new_callable=AsyncMock,
        return_value=None,
    ):
        resp = await app_client.put(
            "/api/settings/abcde",
            json={"content": "CDDBMETHOD=musicbrainz\n"},
        )
    assert resp.status_code == 502
    assert "unreachable" in resp.json()["detail"].lower()


# --- GET /api/settings/system-info ---


def _system_info_patches(arm_version_resp, tc_health_resp=None):
    """Return a context-manager stack patching all system-info dependencies."""
    from contextlib import contextmanager

    @contextmanager
    def _ctx():
        with (
            patch("backend.routers.settings.arm_client.get_version", new_callable=AsyncMock, return_value=arm_version_resp),
            patch("backend.routers.settings.transcoder_client.health", new_callable=AsyncMock, return_value=tc_health_resp),
            patch("backend.routers.settings.asyncio.to_thread", new_callable=AsyncMock, return_value="11.0.0"),
            patch("backend.routers.settings.arm_client.get_paths", new_callable=AsyncMock, return_value=[]),
            patch("backend.routers.settings.arm_db.get_drives", return_value=[]),
            patch("backend.routers.settings.arm_db.is_available", return_value=True),
            patch("backend.routers.settings.app_settings", arm_db_path="/home/arm/db/arm.db", arm_url="https://arm:8080", transcoder_url="https://tc:5000"),
            patch("backend.routers.settings.os.path.isfile", return_value=False),
        ):
            yield

    return _ctx()


async def test_system_info_includes_db_migration(app_client):
    """system-info includes migration fields; matching versions → up_to_date True."""
    arm_ver = {"arm_version": "10.2.0", "makemkv_version": "1.18.3", "db_version": "abc123", "db_head": "abc123"}
    with _system_info_patches(arm_ver):
        resp = await app_client.get("/api/settings/system-info")
    assert resp.status_code == 200
    db = resp.json()["database"]
    assert db["migration_current"] == "abc123"
    assert db["migration_head"] == "abc123"
    assert db["up_to_date"] is True


async def test_system_info_db_needs_migration(app_client):
    """Mismatched db_version and db_head → up_to_date False."""
    arm_ver = {"arm_version": "10.2.0", "makemkv_version": "1.18.3", "db_version": "abc123", "db_head": "def456"}
    with _system_info_patches(arm_ver):
        resp = await app_client.get("/api/settings/system-info")
    assert resp.status_code == 200
    db = resp.json()["database"]
    assert db["migration_current"] == "abc123"
    assert db["migration_head"] == "def456"
    assert db["up_to_date"] is False


async def test_system_info_db_migration_unknown_when_arm_offline(app_client):
    """ARM offline → migration fields show 'offline', up_to_date is None."""
    with _system_info_patches(None):
        resp = await app_client.get("/api/settings/system-info")
    assert resp.status_code == 200
    db = resp.json()["database"]
    assert db["migration_current"] == "offline"
    assert db["migration_head"] == "offline"
    assert db["up_to_date"] is None


async def test_system_info_transcoder_version(app_client):
    """Transcoder version populated from health response."""
    arm_ver = {"arm_version": "10.2.0", "makemkv_version": "1.18.3", "db_version": "abc", "db_head": "abc"}
    tc_health = {"version": "10.9.1", "status": "healthy"}
    with _system_info_patches(arm_ver, tc_health):
        resp = await app_client.get("/api/settings/system-info")
    assert resp.status_code == 200
    assert resp.json()["versions"]["transcoder"] == "10.9.1"
