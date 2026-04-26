"""Tests for POST /api/jobs/bulk-delete and /api/jobs/bulk-purge."""
from __future__ import annotations
from unittest.mock import AsyncMock, patch
from tests.factories import make_job_dict


async def test_bulk_delete_by_ids(app_client):
    mock_del = AsyncMock(return_value={"success": True})
    with patch("backend.routers.jobs.arm_client.delete_job", mock_del):
        resp = await app_client.post("/api/jobs/bulk-delete", json={"job_ids": [1, 2]})
    assert resp.status_code == 200
    assert resp.json()["deleted"] == 2
    assert mock_del.call_count == 2


async def test_bulk_delete_empty_ids(app_client):
    resp = await app_client.post("/api/jobs/bulk-delete", json={"job_ids": []})
    assert resp.status_code == 200
    assert resp.json()["deleted"] == 0


async def test_bulk_delete_by_status(app_client):
    paginated = {
        "jobs": [make_job_dict(job_id=i, status="fail") for i in range(1, 4)],
        "total": 3, "page": 1, "per_page": 10000, "pages": 1,
    }
    mock_del = AsyncMock(return_value={"success": True})
    with patch(
        "backend.routers.jobs.arm_client.get_jobs_paginated",
        new_callable=AsyncMock, return_value=paginated,
    ), patch("backend.routers.jobs.arm_client.delete_job", mock_del):
        resp = await app_client.post("/api/jobs/bulk-delete", json={"status": "fail"})
    assert resp.status_code == 200
    assert resp.json()["deleted"] == 3


async def test_bulk_purge_by_ids(app_client):
    detail = {
        "job": make_job_dict(job_id=1, logfile="test.log",
                             raw_path="/raw", transcode_path="/trans", path="/done"),
        "config": None, "tracks": [], "track_counts": {"total": 0, "ripped": 0},
    }
    mock_del = AsyncMock(return_value={"success": True})
    mock_log = AsyncMock(return_value={"success": True})
    mock_folder = AsyncMock(return_value={"success": True})
    with patch(
        "backend.routers.jobs.arm_client.get_job_detail",
        new_callable=AsyncMock, return_value=detail,
    ), patch("backend.routers.jobs.arm_client.delete_job", mock_del), \
       patch("backend.routers.jobs.arm_client.delete_orphan_log", mock_log), \
       patch("backend.routers.jobs.arm_client.delete_orphan_folder", mock_folder):
        resp = await app_client.post("/api/jobs/bulk-purge", json={"job_ids": [1]})
    assert resp.status_code == 200
    assert resp.json()["purged"] == 1


async def test_bulk_purge_empty_ids(app_client):
    resp = await app_client.post("/api/jobs/bulk-purge", json={"job_ids": []})
    assert resp.status_code == 200
    assert resp.json()["purged"] == 0
