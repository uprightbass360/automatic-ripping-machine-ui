"""Tests for backend.routers.folder — folder import proxy and poster proxy."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch, MagicMock

import httpx
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


# --- Poster proxy ---

async def test_poster_proxy_success(app_client):
    mock_resp = MagicMock()
    mock_resp.content = b"\xff\xd8\xff\xe0"  # JPEG header bytes
    mock_resp.headers = {"content-type": "image/jpeg"}
    mock_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)

    with patch("backend.routers.folder.httpx.AsyncClient", return_value=mock_client):
        resp = await app_client.get("/api/jobs/folder/poster-proxy?url=https://m.media-amazon.com/images/test.jpg")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/jpeg"


async def test_poster_proxy_disallowed_host(app_client):
    resp = await app_client.get("/api/jobs/folder/poster-proxy?url=https://evil.com/malware.jpg")
    assert resp.status_code == 400
    assert "not allowed" in resp.json()["detail"]


async def test_poster_proxy_bad_scheme(app_client):
    resp = await app_client.get("/api/jobs/folder/poster-proxy?url=ftp://m.media-amazon.com/test.jpg")
    assert resp.status_code == 400
    assert "HTTP" in resp.json()["detail"]


async def test_poster_proxy_fetch_error(app_client):
    from backend.routers.folder import _poster_cache
    _poster_cache.clear()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(side_effect=httpx.HTTPError("Connection failed"))

    with patch("backend.routers.folder.httpx.AsyncClient", return_value=mock_client):
        resp = await app_client.get("/api/jobs/folder/poster-proxy?url=https://m.media-amazon.com/images/error-test.jpg")
    assert resp.status_code == 502
    _poster_cache.clear()


async def test_poster_proxy_cache_hit(app_client):
    """Second request for same URL should use cache."""
    from backend.routers.folder import _poster_cache
    _poster_cache.clear()
    _poster_cache["https://m.media-amazon.com/images/cached.jpg"] = (b"\xff\xd8", "image/jpeg")

    resp = await app_client.get("/api/jobs/folder/poster-proxy?url=https://m.media-amazon.com/images/cached.jpg")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/jpeg"

    _poster_cache.clear()


async def test_poster_proxy_cache_eviction(app_client):
    """Cache evicts oldest entry when full."""
    from backend.routers.folder import _poster_cache, _POSTER_CACHE_MAX
    _poster_cache.clear()

    # Fill the cache
    for i in range(_POSTER_CACHE_MAX):
        _poster_cache[f"https://m.media-amazon.com/img/{i}.jpg"] = (b"x", "image/jpeg")

    assert len(_poster_cache) == _POSTER_CACHE_MAX

    # Add one more via the endpoint
    mock_resp = MagicMock()
    mock_resp.content = b"\xff\xd8"
    mock_resp.headers = {"content-type": "image/jpeg"}
    mock_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)

    with patch("backend.routers.folder.httpx.AsyncClient", return_value=mock_client):
        resp = await app_client.get("/api/jobs/folder/poster-proxy?url=https://m.media-amazon.com/images/new.jpg")
    assert resp.status_code == 200
    assert len(_poster_cache) == _POSTER_CACHE_MAX  # didn't exceed max

    _poster_cache.clear()
