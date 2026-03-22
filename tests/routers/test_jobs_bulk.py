"""Tests for POST /api/jobs/bulk-delete and /api/jobs/bulk-purge."""
from __future__ import annotations
from unittest.mock import AsyncMock, MagicMock, patch
from tests.factories import make_job


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
    jobs = [make_job(job_id=i, status="fail") for i in range(1, 4)]
    mock_del = AsyncMock(return_value={"success": True})
    with patch("backend.routers.jobs.arm_db.get_jobs_paginated", return_value=(jobs, 3)), \
         patch("backend.routers.jobs.arm_client.delete_job", mock_del):
        resp = await app_client.post("/api/jobs/bulk-delete", json={"status": "fail"})
    assert resp.status_code == 200
    assert resp.json()["deleted"] == 3


async def test_bulk_purge_by_ids(app_client):
    job_mock = make_job(job_id=1, logfile="test.log")
    mock_del = AsyncMock(return_value={"success": True})
    mock_log = AsyncMock(return_value={"success": True})
    mock_folder = AsyncMock(return_value={"success": True})
    with patch("backend.routers.jobs.arm_db.get_job", return_value=job_mock), \
         patch("backend.routers.jobs.arm_client.delete_job", mock_del), \
         patch("backend.routers.jobs.arm_client.delete_orphan_log", mock_log), \
         patch("backend.routers.jobs.arm_client.delete_orphan_folder", mock_folder):
        resp = await app_client.post("/api/jobs/bulk-purge", json={"job_ids": [1]})
    assert resp.status_code == 200
    assert resp.json()["purged"] == 1


async def test_bulk_purge_empty_ids(app_client):
    resp = await app_client.post("/api/jobs/bulk-purge", json={"job_ids": []})
    assert resp.status_code == 200
    assert resp.json()["purged"] == 0
