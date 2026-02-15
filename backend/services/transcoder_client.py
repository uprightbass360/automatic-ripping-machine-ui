"""Async httpx client for the arm-transcoder REST API."""

from __future__ import annotations

from typing import Any

import httpx

from backend.config import settings

_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        headers = {}
        if settings.transcoder_api_key:
            headers["X-API-Key"] = settings.transcoder_api_key
        _client = httpx.AsyncClient(
            base_url=settings.transcoder_url,
            headers=headers,
            timeout=httpx.Timeout(10.0, connect=3.0),
        )
    return _client


async def close_client() -> None:
    global _client
    if _client and not _client.is_closed:
        await _client.aclose()
        _client = None


async def health() -> dict[str, Any] | None:
    """Check transcoder health. Returns None if offline."""
    try:
        resp = await get_client().get("/health")
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, httpx.ConnectError):
        return None


async def get_system_info() -> dict[str, Any] | None:
    """Fetch static hardware info (CPU, RAM, GPU) from the transcoder."""
    try:
        resp = await get_client().get("/system/info")
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, httpx.ConnectError):
        return None


async def get_config() -> dict[str, Any] | None:
    """Fetch transcoder config with valid option lists. Returns None if offline."""
    try:
        resp = await get_client().get("/config")
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, httpx.ConnectError):
        return None


async def update_config(config: dict[str, Any]) -> dict[str, Any] | None:
    """Patch transcoder config. Returns response dict or None if offline."""
    try:
        resp = await get_client().patch("/config", json=config)
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, httpx.ConnectError):
        return None


async def get_jobs(
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any] | None:
    try:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        resp = await get_client().get("/jobs", params=params)
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, httpx.ConnectError):
        return None


async def get_stats() -> dict[str, Any] | None:
    try:
        resp = await get_client().get("/stats")
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, httpx.ConnectError):
        return None


async def retry_job(job_id: int) -> dict[str, Any] | None:
    try:
        resp = await get_client().post(f"/jobs/{job_id}/retry")
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, httpx.ConnectError):
        return None


async def delete_job(job_id: int) -> bool:
    try:
        resp = await get_client().delete(f"/jobs/{job_id}")
        resp.raise_for_status()
        return True
    except (httpx.HTTPError, httpx.ConnectError):
        return False


async def list_logs() -> list[dict[str, Any]] | None:
    """List transcoder log files. Returns None if offline."""
    try:
        resp = await get_client().get("/logs")
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, httpx.ConnectError):
        return None


async def read_log(
    filename: str, mode: str = "tail", lines: int = 100
) -> dict[str, Any] | None:
    """Read a transcoder log file. Returns None if offline."""
    try:
        resp = await get_client().get(
            f"/logs/{filename}", params={"mode": mode, "lines": lines}
        )
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, httpx.ConnectError):
        return None
