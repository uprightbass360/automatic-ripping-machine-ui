"""Tests for backend.routers.drives — delegation to arm_db + arm_client."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch


# --- GET /api/drives ---


async def test_list_drives(app_client):
    """GET /api/drives returns drives with current_job."""
    drives = [
        {
            "drive_id": 1,
            "name": "BD Drive",
            "mount": "/mnt/dev/sr0",
            "job_id_current": None,
            "job_id_previous": None,
            "description": "Primary",
            "drive_mode": "auto",
            "maker": "LG",
            "model": "WH16NS60",
            "serial": "ABC",
            "connection": "SATA",
            "read_cd": True,
            "read_dvd": True,
            "read_bd": True,
            "firmware": "1.0",
            "location": "0:0:0:0",
            "stale": False,
            "mdisc": 0,
            "serial_id": "lg-abc",
            "current_job": None,
        }
    ]
    with patch("backend.routers.drives.arm_db.get_drives_with_jobs", return_value=drives):
        resp = await app_client.get("/api/drives")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "BD Drive"


# --- PATCH /api/drives/{drive_id} ---


async def test_update_drive_success(app_client):
    """PATCH /api/drives/{id} returns result from ARM."""
    with patch("backend.routers.drives.arm_client.update_drive", new_callable=AsyncMock, return_value={"success": True}):
        resp = await app_client.patch("/api/drives/1", json={"name": "New Name"})
    assert resp.status_code == 200
    assert resp.json()["success"] is True


async def test_update_drive_arm_unreachable(app_client):
    """PATCH /api/drives/{id} returns 502 when ARM is down."""
    with patch("backend.routers.drives.arm_client.update_drive", new_callable=AsyncMock, return_value=None):
        resp = await app_client.patch("/api/drives/1", json={"name": "X"})
    assert resp.status_code == 502
