"""Tests for DELETE /api/logs/{filename} and GET /api/logs/{filename}/download."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch


# --- DELETE /api/logs/{filename} ---


async def test_delete_log_success(app_client):
    """DELETE /api/logs/{filename} returns 200 and success=True when file is deleted."""
    with patch("backend.routers.logs.log_reader.delete_log", return_value=True):
        resp = await app_client.delete("/api/logs/arm.log")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["filename"] == "arm.log"


async def test_delete_log_not_found(app_client):
    """DELETE /api/logs/{filename} returns 404 when file does not exist."""
    with patch("backend.routers.logs.log_reader.delete_log", return_value=False):
        resp = await app_client.delete("/api/logs/missing.log")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


# --- GET /api/logs/{filename}/download ---


async def test_download_log_success(app_client, tmp_path: Path):
    """GET /api/logs/{filename}/download returns 200 with file content."""
    log_file = tmp_path / "arm.log"
    log_file.write_text("log line 1\nlog line 2\n")
    with patch("backend.routers.logs.log_reader.resolve_log_path", return_value=log_file):
        resp = await app_client.get("/api/logs/arm.log/download")
    assert resp.status_code == 200
    assert b"log line 1" in resp.content


async def test_download_log_not_found(app_client):
    """GET /api/logs/{filename}/download returns 404 when file is not found."""
    with patch("backend.routers.logs.log_reader.resolve_log_path", return_value=None):
        resp = await app_client.get("/api/logs/nonexistent.log/download")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


