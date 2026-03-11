"""Tests for jobs router: multi-title, track title, transcode config, retranscode."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


# --- POST /api/jobs/{id}/multi-title ---


async def test_toggle_multi_title_success(app_client):
    with patch(
        "backend.routers.jobs.arm_client.toggle_multi_title",
        new_callable=AsyncMock,
        return_value={"success": True, "multi_title": True},
    ):
        resp = await app_client.post("/api/jobs/1/multi-title", json={"enabled": True})
    assert resp.status_code == 200
    assert resp.json()["multi_title"] is True


async def test_toggle_multi_title_arm_unreachable(app_client):
    with patch(
        "backend.routers.jobs.arm_client.toggle_multi_title",
        new_callable=AsyncMock,
        return_value=None,
    ):
        resp = await app_client.post("/api/jobs/1/multi-title", json={"enabled": True})
    assert resp.status_code == 502


async def test_toggle_multi_title_not_found(app_client):
    with patch(
        "backend.routers.jobs.arm_client.toggle_multi_title",
        new_callable=AsyncMock,
        return_value={"success": False, "error": "Job not found"},
    ):
        resp = await app_client.post("/api/jobs/99/multi-title", json={"enabled": True})
    assert resp.status_code == 404


async def test_toggle_multi_title_error_400(app_client):
    with patch(
        "backend.routers.jobs.arm_client.toggle_multi_title",
        new_callable=AsyncMock,
        return_value={"success": False, "error": "Invalid request"},
    ):
        resp = await app_client.post("/api/jobs/1/multi-title", json={"enabled": True})
    assert resp.status_code == 400


# --- PUT /api/jobs/{id}/tracks/{id}/title ---


async def test_update_track_title_success(app_client):
    with patch(
        "backend.routers.jobs.arm_client.update_track_title",
        new_callable=AsyncMock,
        return_value={"success": True, "updated": {"title": "New Title"}},
    ):
        resp = await app_client.put(
            "/api/jobs/1/tracks/5/title", json={"title": "New Title"}
        )
    assert resp.status_code == 200
    assert resp.json()["updated"]["title"] == "New Title"


async def test_update_track_title_arm_unreachable(app_client):
    with patch(
        "backend.routers.jobs.arm_client.update_track_title",
        new_callable=AsyncMock,
        return_value=None,
    ):
        resp = await app_client.put(
            "/api/jobs/1/tracks/5/title", json={"title": "X"}
        )
    assert resp.status_code == 502


async def test_update_track_title_not_found(app_client):
    with patch(
        "backend.routers.jobs.arm_client.update_track_title",
        new_callable=AsyncMock,
        return_value={"success": False, "error": "Track not found"},
    ):
        resp = await app_client.put(
            "/api/jobs/1/tracks/999/title", json={"title": "X"}
        )
    assert resp.status_code == 404


# --- DELETE /api/jobs/{id}/tracks/{id}/title ---


async def test_clear_track_title_success(app_client):
    with patch(
        "backend.routers.jobs.arm_client.clear_track_title",
        new_callable=AsyncMock,
        return_value={"success": True},
    ):
        resp = await app_client.delete("/api/jobs/1/tracks/5/title")
    assert resp.status_code == 200


async def test_clear_track_title_arm_unreachable(app_client):
    with patch(
        "backend.routers.jobs.arm_client.clear_track_title",
        new_callable=AsyncMock,
        return_value=None,
    ):
        resp = await app_client.delete("/api/jobs/1/tracks/5/title")
    assert resp.status_code == 502


async def test_clear_track_title_not_found(app_client):
    with patch(
        "backend.routers.jobs.arm_client.clear_track_title",
        new_callable=AsyncMock,
        return_value={"success": False, "error": "Track not found"},
    ):
        resp = await app_client.delete("/api/jobs/1/tracks/999/title")
    assert resp.status_code == 404


# --- PATCH /api/jobs/{id}/transcode-config ---


async def test_update_transcode_config_success(app_client):
    with patch(
        "backend.routers.jobs.arm_db.update_job_transcode_overrides",
        return_value={"video_encoder": "x265", "video_quality": 20},
    ):
        resp = await app_client.patch(
            "/api/jobs/1/transcode-config",
            json={"video_encoder": "x265", "video_quality": "20"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["overrides"]["video_encoder"] == "x265"


async def test_update_transcode_config_invalid_keys(app_client):
    with patch(
        "backend.routers.jobs.arm_db.update_job_transcode_overrides",
        side_effect=ValueError("Unknown keys: bad_key"),
    ):
        resp = await app_client.patch(
            "/api/jobs/1/transcode-config", json={"bad_key": "val"}
        )
    assert resp.status_code == 400


async def test_update_transcode_config_not_found(app_client):
    with patch(
        "backend.routers.jobs.arm_db.update_job_transcode_overrides",
        return_value=None,
    ):
        resp = await app_client.patch(
            "/api/jobs/999/transcode-config", json={"video_encoder": "x265"}
        )
    assert resp.status_code == 404


# --- PATCH /api/jobs/{id}/tracks/{id} ---


async def test_update_track_fields_success(app_client):
    with patch(
        "backend.routers.jobs.arm_db.update_track_fields",
        return_value={"enabled": True},
    ):
        resp = await app_client.patch(
            "/api/jobs/1/tracks/5", json={"enabled": True}
        )
    assert resp.status_code == 200
    assert resp.json()["updated"]["enabled"] is True


async def test_update_track_fields_invalid(app_client):
    with patch(
        "backend.routers.jobs.arm_db.update_track_fields",
        side_effect=ValueError("Unknown fields: bad"),
    ):
        resp = await app_client.patch(
            "/api/jobs/1/tracks/5", json={"bad": "val"}
        )
    assert resp.status_code == 400


async def test_update_track_fields_not_found(app_client):
    with patch(
        "backend.routers.jobs.arm_db.update_track_fields",
        return_value=None,
    ):
        resp = await app_client.patch(
            "/api/jobs/1/tracks/999", json={"enabled": True}
        )
    assert resp.status_code == 404


# --- POST /api/jobs/{id}/retranscode ---


async def test_retranscode_job_success(app_client):
    payload = {"title": "Movie", "path": "/raw/Movie", "status": "success"}
    with patch("backend.routers.jobs.arm_db.get_job_retranscode_info", return_value=payload), \
         patch("backend.routers.jobs.transcoder_client.send_webhook", new_callable=AsyncMock, return_value={"success": True}):
        resp = await app_client.post("/api/jobs/1/retranscode")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


async def test_retranscode_job_not_found(app_client):
    with patch("backend.routers.jobs.arm_db.get_job_retranscode_info", return_value=None):
        resp = await app_client.post("/api/jobs/999/retranscode")
    assert resp.status_code == 404


async def test_retranscode_job_transcoder_unavailable(app_client):
    payload = {"title": "Movie", "path": "/raw/Movie", "status": "success"}
    with patch("backend.routers.jobs.arm_db.get_job_retranscode_info", return_value=payload), \
         patch("backend.routers.jobs.transcoder_client.send_webhook", new_callable=AsyncMock, return_value={"success": False, "error": "offline"}):
        resp = await app_client.post("/api/jobs/1/retranscode")
    assert resp.status_code == 503
