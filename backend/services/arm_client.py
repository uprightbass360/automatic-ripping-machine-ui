"""Async httpx client for the ARM Flask JSON API."""

from __future__ import annotations

from typing import Any

import httpx

from backend.config import settings

_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            base_url=settings.arm_url,
            timeout=10.0,
        )
    return _client


async def close_client() -> None:
    global _client
    if _client and not _client.is_closed:
        await _client.aclose()
        _client = None


async def abandon_job(job_id: int) -> dict[str, Any] | None:
    """Abandon a running job. Returns None if ARM is unreachable."""
    try:
        resp = await get_client().post(f"/api/v1/jobs/{job_id}/abandon")
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, httpx.ConnectError):
        return None


async def cancel_waiting_job(job_id: int) -> dict[str, Any] | None:
    """Cancel a job in 'waiting' status. Returns None if ARM is unreachable."""
    try:
        resp = await get_client().post(f"/api/v1/jobs/{job_id}/cancel")
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, httpx.ConnectError):
        return None


async def delete_job(job_id: int) -> dict[str, Any] | None:
    """Delete a completed/failed job. Returns None if ARM is unreachable."""
    try:
        resp = await get_client().delete(f"/api/v1/jobs/{job_id}")
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, httpx.ConnectError):
        return None


async def get_config() -> dict[str, Any] | None:
    """Fetch live ARM config (with comments metadata). Returns None if unreachable."""
    try:
        resp = await get_client().get("/api/v1/settings/config")
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, httpx.ConnectError):
        return None


async def update_config(config: dict[str, Any]) -> dict[str, Any] | None:
    """Write ARM config. Returns response dict or None if unreachable."""
    try:
        resp = await get_client().put(
            "/api/v1/settings/config",
            json={"config": config},
        )
        return resp.json()
    except (httpx.ConnectError, httpx.TimeoutException):
        return None


async def get_system_info() -> dict[str, Any] | None:
    """Fetch static hardware info (CPU, RAM) from the ARM container."""
    try:
        resp = await get_client().get("/api/v1/system/info")
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, httpx.ConnectError):
        return None


async def get_system_stats() -> dict[str, Any] | None:
    """Fetch live system stats (CPU, memory, storage) from the ARM container."""
    try:
        resp = await get_client().get("/api/v1/system/stats")
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, httpx.ConnectError):
        return None


async def fix_permissions(job_id: int) -> dict[str, Any] | None:
    """Fix file permissions for a job. Returns None if ARM is unreachable."""
    try:
        resp = await get_client().post(f"/api/v1/jobs/{job_id}/fix-permissions")
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, httpx.ConnectError):
        return None


async def update_title(job_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
    """Update a job's title metadata via ARM's REST API. Returns None if unreachable."""
    try:
        resp = await get_client().put(f"/api/v1/jobs/{job_id}/title", json=data)
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, httpx.ConnectError):
        return None


async def update_job_config(job_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
    """Update a job's rip parameters via ARM's REST API. Returns None if unreachable."""
    try:
        resp = await get_client().patch(f"/api/v1/jobs/{job_id}/config", json=data)
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, httpx.ConnectError):
        return None


async def start_waiting_job(job_id: int) -> dict[str, Any] | None:
    """Start a job in 'waiting' status. Returns None if ARM is unreachable."""
    try:
        resp = await get_client().post(f"/api/v1/jobs/{job_id}/start")
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, httpx.ConnectError):
        return None


async def set_ripping_enabled(enabled: bool) -> dict[str, Any] | None:
    """Toggle global ripping pause. Returns None if ARM is unreachable."""
    try:
        resp = await get_client().post(
            "/api/v1/system/ripping-enabled",
            json={"enabled": enabled},
        )
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, httpx.ConnectError):
        return None


async def get_version() -> dict[str, str] | None:
    """Fetch ARM and MakeMKV version info."""
    try:
        resp = await get_client().get("/api/v1/system/version")
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, httpx.ConnectError):
        return None


async def get_paths() -> list[dict[str, Any]] | None:
    """Fetch path existence/writability checks from the ARM container."""
    try:
        resp = await get_client().get("/api/v1/system/paths")
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, httpx.ConnectError):
        return None


async def update_drive(drive_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
    """Update a drive's name/description via ARM's REST API. Returns None if unreachable."""
    try:
        resp = await get_client().patch(f"/api/v1/drives/{drive_id}", json=data)
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, httpx.ConnectError):
        return None
