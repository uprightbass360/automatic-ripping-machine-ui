"""Tests for backend.routers.folder — folder import proxy and poster proxy."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


# --- Scan endpoint ---

async def test_scan_success(app_client):
    result = {"success": True, "disc_type": "bluray", "label": "TEST"}
    with patch("backend.routers.folder.arm_client.scan_folder", new_callable=AsyncMock, return_value=result):
        resp = await app_client.post("/api/jobs/folder/scan", json={"path": "/ingress/movie"})
    assert resp.status_code == 200
    assert resp.json()["disc_type"] == "bluray"


async def test_scan_unreachable(app_client):
    with patch("backend.routers.folder.arm_client.scan_folder", new_callable=AsyncMock, return_value=None):
        resp = await app_client.post("/api/jobs/folder/scan", json={"path": "/ingress/movie"})
    assert resp.status_code == 503


async def test_scan_backend_error(app_client):
    result = {"success": False, "error": "Not a valid disc folder"}
    with patch("backend.routers.folder.arm_client.scan_folder", new_callable=AsyncMock, return_value=result):
        resp = await app_client.post("/api/jobs/folder/scan", json={"path": "/ingress/bad"})
    assert resp.status_code == 502
    assert "Not a valid disc folder" in resp.json()["detail"]


async def test_scan_backend_error_no_message(app_client):
    result = {"success": False}
    with patch("backend.routers.folder.arm_client.scan_folder", new_callable=AsyncMock, return_value=result):
        resp = await app_client.post("/api/jobs/folder/scan", json={"path": "/ingress/bad"})
    assert resp.status_code == 502


# --- Create endpoint ---

async def test_create_success(app_client):
    result = {"success": True, "job_id": 1, "status": "ripping", "source_type": "folder"}
    with patch("backend.routers.folder.arm_client.create_folder_job", new_callable=AsyncMock, return_value=result):
        resp = await app_client.post("/api/jobs/folder", json={
            "source_path": "/ingress/movie",
            "title": "Test Movie",
            "video_type": "movie",
            "disctype": "bluray",
        })
    assert resp.status_code == 201
    assert resp.json()["job_id"] == 1


async def test_create_unreachable(app_client):
    with patch("backend.routers.folder.arm_client.create_folder_job", new_callable=AsyncMock, return_value=None):
        resp = await app_client.post("/api/jobs/folder", json={
            "source_path": "/ingress/movie",
            "title": "Test Movie",
            "video_type": "movie",
            "disctype": "bluray",
        })
    assert resp.status_code == 503


async def test_create_backend_error(app_client):
    result = {"success": False, "error": "Active job already exists"}
    with patch("backend.routers.folder.arm_client.create_folder_job", new_callable=AsyncMock, return_value=result):
        resp = await app_client.post("/api/jobs/folder", json={
            "source_path": "/ingress/movie",
            "title": "Test Movie",
            "video_type": "movie",
            "disctype": "bluray",
        })
    assert resp.status_code == 502


# --- Poster proxy redirect (backward compat) ---

async def test_poster_proxy_redirects(app_client):
    """Old poster-proxy URL redirects to /api/images/proxy."""
    resp = await app_client.get(
        "/api/jobs/folder/poster-proxy?url=https://m.media-amazon.com/test.jpg",
        follow_redirects=False,
    )
    assert resp.status_code == 301
    assert "/api/images/proxy" in resp.headers["location"]
