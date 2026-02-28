"""Tests for backend.routers.arm_actions — _check_result + proxy endpoints."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from backend.routers.arm_actions import _check_result


# --- _check_result unit tests ---


def test_check_result_none_raises_503():
    """None result (ARM unreachable) raises 503."""
    with pytest.raises(HTTPException) as exc_info:
        _check_result(None)
    assert exc_info.value.status_code == 503
    assert "unreachable" in exc_info.value.detail.lower()


def test_check_result_success_false_raises_502():
    """Result with success=False raises 502 with error message."""
    with pytest.raises(HTTPException) as exc_info:
        _check_result({"success": False, "error": "Job not found"})
    assert exc_info.value.status_code == 502
    assert "Job not found" in exc_info.value.detail


def test_check_result_success_false_uses_Error_key():
    """Result with 'Error' key (capital E) is also used for detail."""
    with pytest.raises(HTTPException) as exc_info:
        _check_result({"success": False, "Error": "Something broke"})
    assert exc_info.value.status_code == 502
    assert "Something broke" in exc_info.value.detail


def test_check_result_success_false_fallback_message():
    """Result with success=False and no error keys uses 'Action failed' fallback."""
    with pytest.raises(HTTPException) as exc_info:
        _check_result({"success": False})
    assert exc_info.value.status_code == 502
    assert exc_info.value.detail == "Action failed"


def test_check_result_success_true_passthrough():
    """Successful result is returned unchanged."""
    result: dict[str, Any] = {"success": True, "data": "ok"}
    assert _check_result(result) is result


def test_check_result_dict_without_success_key():
    """A dict without 'success' key is passed through (not an error)."""
    result: dict[str, Any] = {"job_id": 1, "status": "abandoned"}
    assert _check_result(result) is result


# --- Endpoint tests via app_client ---


async def test_abandon_job_endpoint(app_client):
    """POST /api/jobs/{id}/abandon proxies to arm_client."""
    with patch(
        "backend.routers.arm_actions.arm_client.abandon_job",
        new_callable=AsyncMock, return_value={"success": True},
    ):
        resp = await app_client.post("/api/jobs/1/abandon")
    assert resp.status_code == 200
    assert resp.json()["success"] is True


async def test_abandon_job_503_when_unreachable(app_client):
    """POST /api/jobs/{id}/abandon returns 503 when ARM is down."""
    with patch(
        "backend.routers.arm_actions.arm_client.abandon_job",
        new_callable=AsyncMock, return_value=None,
    ):
        resp = await app_client.post("/api/jobs/1/abandon")
    assert resp.status_code == 503


async def test_delete_job_endpoint(app_client):
    """DELETE /api/jobs/{id} proxies to arm_client."""
    with patch(
        "backend.routers.arm_actions.arm_client.delete_job",
        new_callable=AsyncMock, return_value={"success": True},
    ):
        resp = await app_client.delete("/api/jobs/1")
    assert resp.status_code == 200


async def test_set_ripping_enabled_endpoint(app_client):
    """POST /api/system/ripping-enabled toggles ripping."""
    with patch(
        "backend.routers.arm_actions.arm_client.set_ripping_enabled",
        new_callable=AsyncMock, return_value={"success": True},
    ):
        resp = await app_client.post(
            "/api/system/ripping-enabled", json={"enabled": True},
        )
    assert resp.status_code == 200


async def test_start_waiting_job_endpoint(app_client):
    """POST /api/jobs/{id}/start proxies to arm_client."""
    with patch(
        "backend.routers.arm_actions.arm_client.start_waiting_job",
        new_callable=AsyncMock, return_value={"success": True},
    ):
        resp = await app_client.post("/api/jobs/1/start")
    assert resp.status_code == 200


async def test_pause_waiting_job_endpoint(app_client):
    """POST /api/jobs/{id}/pause proxies to arm_client."""
    with patch(
        "backend.routers.arm_actions.arm_client.pause_waiting_job",
        new_callable=AsyncMock, return_value={"success": True, "paused": True},
    ):
        resp = await app_client.post("/api/jobs/1/pause")
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    assert resp.json()["paused"] is True


async def test_pause_waiting_job_503_when_unreachable(app_client):
    """POST /api/jobs/{id}/pause returns 503 when ARM is down."""
    with patch(
        "backend.routers.arm_actions.arm_client.pause_waiting_job",
        new_callable=AsyncMock, return_value=None,
    ):
        resp = await app_client.post("/api/jobs/1/pause")
    assert resp.status_code == 503
