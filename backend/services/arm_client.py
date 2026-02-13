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
        resp = await get_client().get("/json", params={"mode": "abandon", "job": job_id})
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, httpx.ConnectError):
        return None


async def delete_job(job_id: int) -> dict[str, Any] | None:
    """Delete a completed/failed job. Returns None if ARM is unreachable."""
    try:
        resp = await get_client().get("/json", params={"mode": "delete", "job": job_id})
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
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, httpx.ConnectError):
        return None


async def get_gpu_support() -> dict[str, Any] | None:
    """Fetch GPU encoder support from the ARM container."""
    try:
        resp = await get_client().get("/api/v1/system/gpu")
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, httpx.ConnectError):
        return None


async def fix_permissions(job_id: int) -> dict[str, Any] | None:
    """Fix file permissions for a job. Returns None if ARM is unreachable."""
    try:
        resp = await get_client().get("/json", params={"mode": "fixperms", "job": job_id})
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
