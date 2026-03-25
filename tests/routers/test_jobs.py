"""Tests for backend.routers.jobs — list/detail/metadata endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from tests.factories import make_job, make_track


# --- GET /api/jobs ---


async def test_list_jobs(app_client):
    """GET /api/jobs returns paginated job list."""
    job = make_job(job_id=1, title="Test Movie")
    paginated = {
        "jobs": [job],
        "total": 1,
        "page": 1,
        "per_page": 25,
        "pages": 1,
    }
    with patch("backend.routers.jobs.arm_db.get_jobs_paginated_response", return_value=paginated):
        resp = await app_client.get("/api/jobs")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert len(data["jobs"]) == 1
    assert data["jobs"][0]["title"] == "Test Movie"


async def test_list_jobs_with_pagination_params(app_client):
    """GET /api/jobs passes pagination params through."""
    paginated = {"jobs": [], "total": 0, "page": 3, "per_page": 10, "pages": 1}
    with patch("backend.routers.jobs.arm_db.get_jobs_paginated_response", return_value=paginated) as mock_fn:
        resp = await app_client.get("/api/jobs?page=3&per_page=10&status=active")
    assert resp.status_code == 200
    mock_fn.assert_called_once_with(3, 10, "active", None, None, None, None, None, None)


# --- GET /api/jobs/{job_id} ---


async def test_get_job_detail(app_client):
    """GET /api/jobs/{id} returns job with tracks and config."""
    job = make_job(job_id=5, title="Detail Movie")
    track = make_track(track_id=1, job_id=5)
    job.tracks = [track]
    config_dict = {"RIPMETHOD": "mkv", "MINLENGTH": "600"}
    with patch("backend.routers.jobs.arm_db.get_job_with_config", return_value=(job, config_dict)):
        resp = await app_client.get("/api/jobs/5")
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Detail Movie"
    assert len(data["tracks"]) == 1
    assert data["config"]["RIPMETHOD"] == "mkv"


async def test_get_job_404(app_client):
    """GET /api/jobs/{id} returns 404 when job not found."""
    with patch("backend.routers.jobs.arm_db.get_job_with_config", return_value=(None, None)):
        resp = await app_client.get("/api/jobs/999")
    assert resp.status_code == 404


# --- GET /api/metadata/search ---


async def test_metadata_search(app_client):
    """GET /api/metadata/search returns search results (proxied through ARM)."""
    results = [{"title": "Matrix", "year": "1999", "imdb_id": "tt0133093", "media_type": "movie", "poster_url": None}]
    with patch("backend.routers.jobs.arm_client.search_metadata", new_callable=AsyncMock, return_value=results):
        resp = await app_client.get("/api/metadata/search?q=matrix")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["title"] == "Matrix"


async def test_metadata_search_502_on_arm_unreachable(app_client):
    """GET /api/metadata/search returns 502 when ARM is unreachable."""
    import httpx as _httpx
    with patch(
        "backend.routers.jobs.arm_client.search_metadata",
        new_callable=AsyncMock, side_effect=_httpx.ConnectError("offline"),
    ):
        resp = await app_client.get("/api/metadata/search?q=test")
    assert resp.status_code == 502


# --- GET /api/jobs/{job_id}/progress ---


async def test_get_job_progress_with_track_counts(app_client):
    """GET /api/jobs/{id}/progress returns rip progress enriched with track counts."""
    job = make_job(job_id=5, title="Test Movie")
    with patch("backend.routers.jobs.arm_db.get_job", return_value=job), \
         patch("backend.routers.jobs.progress.get_rip_progress", return_value={"progress": 45, "stage": "rip"}), \
         patch("backend.routers.jobs.arm_db.get_job_track_counts", return_value={"tracks_total": 10, "tracks_ripped": 3}):
        resp = await app_client.get("/api/jobs/5/progress")
    assert resp.status_code == 200
    data = resp.json()
    assert data["progress"] == 45
    assert data["tracks_total"] == 10
    assert data["tracks_ripped"] == 3


async def test_get_job_progress_404(app_client):
    """GET /api/jobs/{id}/progress returns 404 when job not found."""
    with patch("backend.routers.jobs.arm_db.get_job", return_value=None):
        resp = await app_client.get("/api/jobs/999/progress")
    assert resp.status_code == 404


async def test_get_job_progress_music_branch(app_client):
    """GET /api/jobs/{id}/progress uses music progress parser for disctype=music."""
    job = make_job(job_id=7, title="Greatest Hits", disctype="music", logfile="job_7.log")
    with patch("backend.routers.jobs.arm_db.get_job", return_value=job), \
         patch("backend.routers.jobs.progress.get_music_progress", return_value={"progress": 66.7, "stage": "2/3 - encoding track 3"}) as mock_music, \
         patch("backend.routers.jobs.arm_db.get_job_track_counts", return_value={"tracks_total": 3, "tracks_ripped": 2}):
        resp = await app_client.get("/api/jobs/7/progress")
    assert resp.status_code == 200
    data = resp.json()
    assert data["progress"] == pytest.approx(66.7)
    assert "encoding" in data["stage"]
    mock_music.assert_called_once_with("job_7.log", 3)


async def test_get_job_progress_includes_no_of_titles(app_client):
    """GET /api/jobs/{id}/progress includes no_of_titles from the job."""
    job = make_job(job_id=8, title="Multi Title Disc", no_of_titles=12)
    with patch("backend.routers.jobs.arm_db.get_job", return_value=job), \
         patch("backend.routers.jobs.progress.get_rip_progress", return_value={"progress": None, "stage": None}), \
         patch("backend.routers.jobs.arm_db.get_job_track_counts", return_value={"tracks_total": 0, "tracks_ripped": 0}):
        resp = await app_client.get("/api/jobs/8/progress")
    assert resp.status_code == 200
    data = resp.json()
    assert data["no_of_titles"] == 12


# --- GET /api/jobs/{job_id}/naming-preview ---


async def test_naming_preview_success(app_client):
    """GET /api/jobs/{id}/naming-preview returns rendered filenames."""
    result = {
        "success": True,
        "job_title": "Show S01E01",
        "job_folder": "Show/Season 01",
        "tracks": [
            {"track_number": "0", "rendered_title": "Pilot S01E01", "rendered_folder": "Show/Season 01"},
        ],
    }
    with patch("backend.routers.jobs.arm_client.naming_preview_for_job", new_callable=AsyncMock, return_value=result):
        resp = await app_client.get("/api/jobs/1/naming-preview")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert len(data["tracks"]) == 1
    assert data["tracks"][0]["rendered_title"] == "Pilot S01E01"


async def test_naming_preview_job_not_found(app_client):
    """GET /api/jobs/{id}/naming-preview returns 404 for missing job."""
    result = {"success": False, "error": "Job not found"}
    with patch("backend.routers.jobs.arm_client.naming_preview_for_job", new_callable=AsyncMock, return_value=result):
        resp = await app_client.get("/api/jobs/999/naming-preview")
    assert resp.status_code == 404


async def test_naming_preview_arm_unreachable(app_client):
    """GET /api/jobs/{id}/naming-preview returns 502 when ARM is down."""
    with patch("backend.routers.jobs.arm_client.naming_preview_for_job", new_callable=AsyncMock, return_value=None):
        resp = await app_client.get("/api/jobs/1/naming-preview")
    assert resp.status_code == 502


# --- Per-job naming overrides ---


async def test_update_job_naming_success(app_client):
    """PATCH /api/jobs/{id}/naming saves pattern overrides."""
    result = {"success": True, "title_pattern_override": "{title} - E{episode}", "folder_pattern_override": None}
    with patch("backend.routers.jobs.arm_client.update_job_naming", new_callable=AsyncMock, return_value=result):
        resp = await app_client.patch("/api/jobs/1/naming", json={"title_pattern_override": "{title} - E{episode}"})
    assert resp.status_code == 200
    assert resp.json()["title_pattern_override"] == "{title} - E{episode}"


async def test_update_job_naming_invalid_pattern(app_client):
    """PATCH /api/jobs/{id}/naming returns 400 for invalid patterns."""
    result = {"success": False, "error": "Invalid variables in pattern: ['episde']", "invalid_vars": ["episde"], "suggestions": {"episde": "episode"}}
    with patch("backend.routers.jobs.arm_client.update_job_naming", new_callable=AsyncMock, return_value=result):
        resp = await app_client.patch("/api/jobs/1/naming", json={"title_pattern_override": "{title} S{episde}"})
    assert resp.status_code == 400


async def test_update_job_naming_arm_unreachable(app_client):
    """PATCH /api/jobs/{id}/naming returns 503 when ARM is down."""
    with patch("backend.routers.jobs.arm_client.update_job_naming", new_callable=AsyncMock, return_value=None):
        resp = await app_client.patch("/api/jobs/1/naming", json={"title_pattern_override": "{title}"})
    assert resp.status_code == 503


async def test_validate_naming_pattern(app_client):
    """POST /api/naming/validate returns validation result."""
    result = {"valid": False, "invalid_vars": ["episde"], "suggestions": {"episde": "episode"}}
    with patch("backend.routers.jobs.arm_client.validate_naming_pattern", new_callable=AsyncMock, return_value=result):
        resp = await app_client.post("/api/naming/validate", json={"pattern": "{title} {episde}"})
    assert resp.status_code == 200
    assert resp.json()["valid"] is False
    assert "episde" in resp.json()["invalid_vars"]


async def test_validate_naming_arm_unreachable(app_client):
    """POST /api/naming/validate returns 503 when ARM is down."""
    with patch("backend.routers.jobs.arm_client.validate_naming_pattern", new_callable=AsyncMock, return_value=None):
        resp = await app_client.post("/api/naming/validate", json={"pattern": "{title}"})
    assert resp.status_code == 503


async def test_get_naming_variables(app_client):
    """GET /api/naming/variables returns variable list."""
    result = {"variables": ["album", "artist", "episode", "label", "season", "title", "video_type", "year"], "descriptions": {}}
    with patch("backend.routers.jobs.arm_client.get_naming_variables", new_callable=AsyncMock, return_value=result):
        resp = await app_client.get("/api/naming/variables")
    assert resp.status_code == 200
    assert "title" in resp.json()["variables"]
    assert len(resp.json()["variables"]) == 8


async def test_get_naming_variables_arm_unreachable(app_client):
    """GET /api/naming/variables returns 503 when ARM is down."""
    with patch("backend.routers.jobs.arm_client.get_naming_variables", new_callable=AsyncMock, return_value=None):
        resp = await app_client.get("/api/naming/variables")
    assert resp.status_code == 503
