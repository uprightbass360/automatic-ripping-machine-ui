"""Tests for enhanced job listing — sort, disc type filter, time range."""
from __future__ import annotations
from unittest.mock import patch
from tests.factories import make_job

_EMPTY = {"jobs": [], "total": 0, "page": 1, "per_page": 25, "pages": 1}


async def test_sort_by_title_asc(app_client):
    with patch("backend.routers.jobs.arm_db.get_jobs_paginated_response", return_value=_EMPTY) as mock_fn:
        resp = await app_client.get("/api/jobs?sort_by=title&sort_dir=asc")
    assert resp.status_code == 200
    mock_fn.assert_called_once_with(1, 25, None, None, None, None, None, "title", "asc")


async def test_sort_by_start_time_desc_is_default(app_client):
    with patch("backend.routers.jobs.arm_db.get_jobs_paginated_response", return_value=_EMPTY) as mock_fn:
        resp = await app_client.get("/api/jobs")
    assert resp.status_code == 200
    mock_fn.assert_called_once_with(1, 25, None, None, None, None, None, None, None)


async def test_filter_by_disctype(app_client):
    with patch("backend.routers.jobs.arm_db.get_jobs_paginated_response", return_value=_EMPTY) as mock_fn:
        resp = await app_client.get("/api/jobs?disctype=dvd")
    assert resp.status_code == 200
    mock_fn.assert_called_once_with(1, 25, None, None, None, "dvd", None, None, None)


async def test_filter_by_days(app_client):
    with patch("backend.routers.jobs.arm_db.get_jobs_paginated_response", return_value=_EMPTY) as mock_fn:
        resp = await app_client.get("/api/jobs?days=7")
    assert resp.status_code == 200
    mock_fn.assert_called_once_with(1, 25, None, None, None, None, 7, None, None)


async def test_invalid_sort_dir_rejected(app_client):
    resp = await app_client.get("/api/jobs?sort_dir=invalid")
    assert resp.status_code == 422
