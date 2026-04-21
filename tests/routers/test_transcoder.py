"""Tests for backend.routers.transcoder — stats, jobs, logs, retranscode."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch


# --- GET /api/transcoder/stats ---


async def test_get_stats_online(app_client):
    """GET /api/transcoder/stats returns online=True with stats."""
    stats = {"queue_size": 3, "active_jobs": 1}
    with patch(
        "backend.routers.transcoder.transcoder_client.get_stats",
        new_callable=AsyncMock,
        return_value=stats,
    ):
        resp = await app_client.get("/api/transcoder/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["online"] is True
    assert data["stats"] == stats


async def test_get_stats_offline(app_client):
    """GET /api/transcoder/stats returns online=False when transcoder is down."""
    with patch(
        "backend.routers.transcoder.transcoder_client.get_stats",
        new_callable=AsyncMock,
        return_value=None,
    ):
        resp = await app_client.get("/api/transcoder/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["online"] is False
    assert data["stats"] is None


# --- GET /api/transcoder/jobs ---


async def test_list_jobs_success(app_client):
    """GET /api/transcoder/jobs returns jobs list."""
    data = {"jobs": [{"id": 1, "status": "completed"}], "total": 1}
    with patch(
        "backend.routers.transcoder.transcoder_client.get_jobs",
        new_callable=AsyncMock,
        return_value=data,
    ):
        resp = await app_client.get("/api/transcoder/jobs")
    assert resp.status_code == 200
    result = resp.json()
    assert result["total"] == 1
    assert len(result["jobs"]) == 1


async def test_list_jobs_offline(app_client):
    """GET /api/transcoder/jobs returns empty list when offline."""
    with patch(
        "backend.routers.transcoder.transcoder_client.get_jobs",
        new_callable=AsyncMock,
        return_value=None,
    ):
        resp = await app_client.get("/api/transcoder/jobs")
    assert resp.status_code == 200
    result = resp.json()
    assert result["jobs"] == []
    assert result["total"] == 0


async def test_list_jobs_with_filters(app_client):
    """GET /api/transcoder/jobs passes status/limit/offset to client."""
    with patch(
        "backend.routers.transcoder.transcoder_client.get_jobs",
        new_callable=AsyncMock,
        return_value={"jobs": [], "total": 0},
    ) as mock_fn:
        resp = await app_client.get("/api/transcoder/jobs?status=failed&limit=10&offset=5")
    assert resp.status_code == 200
    mock_fn.assert_awaited_once_with(status="failed", limit=10, offset=5)


# --- POST /api/transcoder/jobs/{job_id}/retry ---


async def test_retry_job_success(app_client):
    """POST retry returns result from transcoder."""
    with patch(
        "backend.routers.transcoder.transcoder_client.retry_job",
        new_callable=AsyncMock,
        return_value={"status": "queued"},
    ):
        resp = await app_client.post("/api/transcoder/jobs/1/retry")
    assert resp.status_code == 200
    assert resp.json()["status"] == "queued"


async def test_retry_job_offline(app_client):
    """POST retry returns 503 when transcoder is offline."""
    with patch(
        "backend.routers.transcoder.transcoder_client.retry_job",
        new_callable=AsyncMock,
        return_value=None,
    ):
        resp = await app_client.post("/api/transcoder/jobs/1/retry")
    assert resp.status_code == 503


# --- DELETE /api/transcoder/jobs/{job_id} ---


async def test_delete_job_success(app_client):
    """DELETE job returns status=deleted."""
    with patch(
        "backend.routers.transcoder.transcoder_client.delete_job",
        new_callable=AsyncMock,
        return_value=True,
    ):
        resp = await app_client.delete("/api/transcoder/jobs/1")
    assert resp.status_code == 200
    assert resp.json()["status"] == "deleted"


async def test_delete_job_failure(app_client):
    """DELETE job returns 503 when transcoder offline or job not found."""
    with patch(
        "backend.routers.transcoder.transcoder_client.delete_job",
        new_callable=AsyncMock,
        return_value=False,
    ):
        resp = await app_client.delete("/api/transcoder/jobs/1")
    assert resp.status_code == 503


# --- GET /api/transcoder/logs ---


async def test_list_logs_success(app_client):
    """GET /api/transcoder/logs returns log file list."""
    logs = [{"filename": "transcoder.log", "size": 1024, "modified": "2026-03-14T10:00:00"}]
    with patch(
        "backend.routers.transcoder.transcoder_client.list_logs",
        new_callable=AsyncMock,
        return_value=logs,
    ):
        resp = await app_client.get("/api/transcoder/logs")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


async def test_list_logs_offline(app_client):
    """GET /api/transcoder/logs returns empty list when offline."""
    with patch(
        "backend.routers.transcoder.transcoder_client.list_logs",
        new_callable=AsyncMock,
        return_value=None,
    ):
        resp = await app_client.get("/api/transcoder/logs")
    assert resp.status_code == 200
    assert resp.json() == []


# --- GET /api/transcoder/logs/{filename}/structured ---


async def test_get_structured_log_success(app_client):
    """GET structured log returns parsed log data."""
    log_data = {"filename": "transcoder.log", "entries": [{"timestamp": "2026-03-14T10:00:00", "level": "INFO", "logger": "root", "event": "Started", "raw": "2026-03-14 10:00:00 INFO Started"}], "lines": 1}
    with patch(
        "backend.routers.transcoder.transcoder_client.read_structured_log",
        new_callable=AsyncMock,
        return_value=log_data,
    ):
        resp = await app_client.get("/api/transcoder/logs/transcoder.log/structured")
    assert resp.status_code == 200
    assert resp.json()["lines"] == 1


async def test_get_structured_log_not_found(app_client):
    """GET structured log returns 404 when log missing or offline."""
    with patch(
        "backend.routers.transcoder.transcoder_client.read_structured_log",
        new_callable=AsyncMock,
        return_value=None,
    ):
        resp = await app_client.get("/api/transcoder/logs/missing.log/structured")
    assert resp.status_code == 404


# --- GET /api/transcoder/logs/{filename} ---


async def test_get_log_success(app_client):
    """GET log returns raw log content."""
    log_data = {"filename": "transcoder.log", "content": "line 1\nline 2", "lines": 2}
    with patch(
        "backend.routers.transcoder.transcoder_client.read_log",
        new_callable=AsyncMock,
        return_value=log_data,
    ):
        resp = await app_client.get("/api/transcoder/logs/transcoder.log")
    assert resp.status_code == 200
    assert "line 1" in resp.json()["content"]


async def test_get_log_not_found(app_client):
    """GET log returns 404 when log missing or offline."""
    with patch(
        "backend.routers.transcoder.transcoder_client.read_log",
        new_callable=AsyncMock,
        return_value=None,
    ):
        resp = await app_client.get("/api/transcoder/logs/missing.log")
    assert resp.status_code == 404


# --- POST /api/transcoder/jobs/{job_id}/retranscode ---


async def test_retranscode_success(app_client):
    """POST retranscode re-queues a completed job."""
    job = {
        "id": 5,
        "status": "completed",
        "title": "My Movie",
        "source_path": "/media/raw/movie",
        "arm_job_id": 42,
        "video_type": "movie",
        "year": "2024",
        "disctype": "bluray",
    }
    with (
        patch(
            "backend.routers.transcoder.transcoder_client.get_job",
            new_callable=AsyncMock,
            return_value=job,
        ),
        patch(
            "backend.routers.transcoder.transcoder_client.send_webhook",
            new_callable=AsyncMock,
            return_value={"success": True},
        ),
    ):
        resp = await app_client.post("/api/transcoder/jobs/5/retranscode")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


async def test_retranscode_job_not_found(app_client):
    """POST retranscode returns 404 when job not found."""
    with patch(
        "backend.routers.transcoder.transcoder_client.get_job",
        new_callable=AsyncMock,
        return_value=None,
    ):
        resp = await app_client.post("/api/transcoder/jobs/999/retranscode")
    assert resp.status_code == 404


async def test_retranscode_invalid_status(app_client):
    """POST retranscode returns 400 for in-progress job."""
    job = {"id": 5, "status": "processing", "title": "Movie"}
    with patch(
        "backend.routers.transcoder.transcoder_client.get_job",
        new_callable=AsyncMock,
        return_value=job,
    ):
        resp = await app_client.post("/api/transcoder/jobs/5/retranscode")
    assert resp.status_code == 400
    assert "processing" in resp.json()["detail"]


async def test_retranscode_webhook_failure(app_client):
    """POST retranscode returns 503 when webhook send fails."""
    job = {
        "id": 5,
        "status": "failed",
        "title": "Movie",
        "source_path": "/media/raw/movie",
        "arm_job_id": 42,
        "video_type": "movie",
        "year": "2024",
        "disctype": "bluray",
    }
    with (
        patch(
            "backend.routers.transcoder.transcoder_client.get_job",
            new_callable=AsyncMock,
            return_value=job,
        ),
        patch(
            "backend.routers.transcoder.transcoder_client.send_webhook",
            new_callable=AsyncMock,
            return_value={"success": False, "error": "Connection refused"},
        ),
    ):
        resp = await app_client.post("/api/transcoder/jobs/5/retranscode")
    assert resp.status_code == 503


# --- GET /api/transcoder/job-for-arm/{arm_job_id} ---


async def test_get_job_for_arm_found(app_client):
    """GET job-for-arm returns found=True with job details."""
    data = {"jobs": [{"id": 10, "logfile": "job_10.log", "status": "completed"}]}
    with patch(
        "backend.routers.transcoder.transcoder_client.get_jobs",
        new_callable=AsyncMock,
        return_value=data,
    ):
        resp = await app_client.get("/api/transcoder/job-for-arm/42")
    assert resp.status_code == 200
    result = resp.json()
    assert result["found"] is True
    assert result["transcoder_job_id"] == 10
    assert result["logfile"] == "job_10.log"


async def test_get_job_for_arm_not_found(app_client):
    """GET job-for-arm returns found=False when no matching jobs."""
    with patch(
        "backend.routers.transcoder.transcoder_client.get_jobs",
        new_callable=AsyncMock,
        return_value={"jobs": []},
    ):
        resp = await app_client.get("/api/transcoder/job-for-arm/42")
    assert resp.status_code == 200
    assert resp.json()["found"] is False


async def test_get_job_for_arm_offline(app_client):
    """GET job-for-arm returns found=False when transcoder offline."""
    with patch(
        "backend.routers.transcoder.transcoder_client.get_jobs",
        new_callable=AsyncMock,
        return_value=None,
    ):
        resp = await app_client.get("/api/transcoder/job-for-arm/42")
    assert resp.status_code == 200
    assert resp.json()["found"] is False


async def test_get_job_for_arm_filters_by_job_id_not_most_recent(app_client):
    """GET job-for-arm must filter by job_id so it never returns an unrelated older job.

    Regression: the previous implementation passed arm_job_id as an unknown
    param, which FastAPI silently dropped, causing the transcoder to return
    its most recent job regardless of ARM id.
    """
    mock_get = AsyncMock(return_value={"jobs": [{"id": 42, "logfile": "JOB_42_Transcode.log"}]})
    with patch(
        "backend.routers.transcoder.transcoder_client.get_jobs",
        new=mock_get,
    ):
        await app_client.get("/api/transcoder/job-for-arm/42")

    mock_get.assert_called_once()
    _, kwargs = mock_get.call_args
    assert kwargs.get("job_id") == 42, (
        f"Expected get_jobs to be called with job_id=42 (unified ID) "
        f"to avoid stale-correlation; got kwargs={kwargs!r}"
    )
    assert "arm_job_id" not in kwargs
