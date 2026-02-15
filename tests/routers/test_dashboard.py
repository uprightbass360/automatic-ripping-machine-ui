"""Tests for backend.routers.dashboard — orchestration, DB-unavailable degradation."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from tests.factories import make_drive, make_job


# --- GET /api/dashboard ---


async def test_dashboard_full(app_client):
    """Dashboard returns all fields when DB and services are available."""
    job = make_job(job_id=1, status="ripping")
    drive = make_drive()
    arm_hw = {"cpu": "AMD Ryzen 7", "memory_total_gb": 32.0}
    stats = {"cpu_percent": 45.0, "cpu_temp": 55.0, "memory": None, "storage": []}

    with (
        patch("backend.routers.dashboard.arm_db.is_available", return_value=True),
        patch("backend.routers.dashboard.arm_db.get_active_jobs", return_value=[job]),
        patch("backend.routers.dashboard.arm_db.get_drives", return_value=[drive]),
        patch("backend.routers.dashboard.arm_db.get_notification_count", return_value=3),
        patch("backend.routers.dashboard.arm_db.get_ripping_paused", return_value=False),
        patch("backend.routers.dashboard.transcoder_client.health", new_callable=AsyncMock, return_value={"status": "ok"}),
        patch("backend.routers.dashboard.transcoder_client.get_stats", new_callable=AsyncMock, return_value={"active": 1}),
        patch("backend.routers.dashboard.transcoder_client.get_jobs", new_callable=AsyncMock, return_value={"jobs": []}),
        patch("backend.routers.dashboard.arm_client.get_system_stats", new_callable=AsyncMock, return_value=stats),
        patch("backend.routers.dashboard.system_cache.get_arm_info", return_value=arm_hw),
        patch("backend.routers.dashboard.system_cache.get_transcoder_info", return_value=None),
    ):
        resp = await app_client.get("/api/dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert data["db_available"] is True
    assert data["drives_online"] == 1
    assert data["notification_count"] == 3
    assert data["ripping_enabled"] is True
    assert data["transcoder_online"] is True
    assert data["system_stats"]["cpu_percent"] == 45.0
    assert data["system_info"]["cpu"] == "AMD Ryzen 7"
    assert len(data["active_jobs"]) == 1


async def test_dashboard_db_unavailable(app_client):
    """Dashboard degrades gracefully when DB is unavailable."""
    with (
        patch("backend.routers.dashboard.arm_db.is_available", return_value=False),
        patch("backend.routers.dashboard.transcoder_client.health", new_callable=AsyncMock, return_value=None),
        patch("backend.routers.dashboard.arm_client.get_system_stats", new_callable=AsyncMock, return_value=None),
        patch("backend.routers.dashboard.system_cache.get_arm_info", return_value=None),
        patch("backend.routers.dashboard.system_cache.get_transcoder_info", return_value=None),
    ):
        resp = await app_client.get("/api/dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert data["db_available"] is False
    assert data["active_jobs"] == []
    assert data["drives_online"] == 0
    assert data["notification_count"] == 0
    assert data["transcoder_online"] is False
    assert data["system_stats"] is None


async def test_dashboard_transcoder_offline(app_client):
    """Dashboard shows transcoder_online=False when health returns None."""
    with (
        patch("backend.routers.dashboard.arm_db.is_available", return_value=True),
        patch("backend.routers.dashboard.arm_db.get_active_jobs", return_value=[]),
        patch("backend.routers.dashboard.arm_db.get_drives", return_value=[]),
        patch("backend.routers.dashboard.arm_db.get_notification_count", return_value=0),
        patch("backend.routers.dashboard.arm_db.get_ripping_paused", return_value=False),
        patch("backend.routers.dashboard.transcoder_client.health", new_callable=AsyncMock, return_value=None),
        patch("backend.routers.dashboard.arm_client.get_system_stats", new_callable=AsyncMock, return_value=None),
        patch("backend.routers.dashboard.system_cache.get_arm_info", return_value=None),
        patch("backend.routers.dashboard.system_cache.get_transcoder_info", return_value=None),
    ):
        resp = await app_client.get("/api/dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert data["transcoder_online"] is False
    assert data["transcoder_stats"] is None
