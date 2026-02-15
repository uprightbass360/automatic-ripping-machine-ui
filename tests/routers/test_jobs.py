"""Tests for backend.routers.jobs — list/detail/metadata endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from tests.factories import make_config, make_job, make_track


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
    mock_fn.assert_called_once_with(3, 10, "active", None, None)


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
    """GET /api/metadata/search returns search results."""
    results = [{"title": "Matrix", "year": "1999", "imdb_id": "tt0133093", "media_type": "movie", "poster_url": None}]
    with patch("backend.routers.jobs.metadata.search", new_callable=AsyncMock, return_value=results):
        resp = await app_client.get("/api/metadata/search?q=matrix")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["title"] == "Matrix"


async def test_metadata_search_503_on_config_error(app_client):
    """GET /api/metadata/search returns 503 when no API key configured."""
    from backend.services.metadata import MetadataConfigError

    with patch("backend.routers.jobs.metadata.search", new_callable=AsyncMock, side_effect=MetadataConfigError("No key")):
        resp = await app_client.get("/api/metadata/search?q=test")
    assert resp.status_code == 503
