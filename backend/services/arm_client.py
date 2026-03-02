"""Async httpx client for the ARM Flask JSON API."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from backend.config import settings

log = logging.getLogger(__name__)

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


def _parse_error_response(resp: httpx.Response) -> dict[str, Any]:
    """Extract an error dict from a non-2xx ARM response.

    Returns a dict with ``success=False`` and the best error detail
    we can extract so that ``_check_result`` in the router can surface
    the real message instead of "ARM web UI is unreachable".
    """
    try:
        body = resp.json()
        if isinstance(body, dict):
            # FastAPI error responses use "detail", ARM uses "error"
            detail = body.get("detail") or body.get("error") or body.get("Error")
            if detail:
                return {"success": False, "error": f"ARM error ({resp.status_code}): {detail}"}
            return {"success": False, "error": f"ARM error ({resp.status_code}): {body}"}
    except Exception:
        pass
    return {"success": False, "error": f"ARM returned HTTP {resp.status_code}"}


async def _request(
    method: str, url: str, **kwargs: Any
) -> dict[str, Any] | None:
    """Send a request to the ARM API.

    Returns the parsed JSON on success, an error dict on HTTP errors,
    or None only when ARM is genuinely unreachable (connection refused,
    DNS failure, timeout).
    """
    try:
        resp = await get_client().request(method, url, **kwargs)
        if resp.is_success:
            return resp.json()
        return _parse_error_response(resp)
    except (httpx.ConnectError, httpx.TimeoutException, RuntimeError, OSError) as exc:
        log.debug("ARM unreachable (%s %s): %s", method, url, exc)
        return None


async def abandon_job(job_id: int) -> dict[str, Any] | None:
    """Abandon a running job. Returns None if ARM is unreachable."""
    return await _request("POST", f"/api/v1/jobs/{job_id}/abandon")


async def cancel_waiting_job(job_id: int) -> dict[str, Any] | None:
    """Cancel a job in 'waiting' status. Returns None if ARM is unreachable."""
    return await _request("POST", f"/api/v1/jobs/{job_id}/cancel")


async def delete_job(job_id: int) -> dict[str, Any] | None:
    """Delete a completed/failed job. Returns None if ARM is unreachable."""
    return await _request("DELETE", f"/api/v1/jobs/{job_id}")


async def get_config() -> dict[str, Any] | None:
    """Fetch live ARM config (with comments metadata). Returns None if unreachable."""
    return await _request("GET", "/api/v1/settings/config")


async def update_config(config: dict[str, Any]) -> dict[str, Any] | None:
    """Write ARM config. Returns response dict or None if unreachable."""
    return await _request("PUT", "/api/v1/settings/config", json={"config": config})


async def get_system_info() -> dict[str, Any] | None:
    """Fetch static hardware info (CPU, RAM) from the ARM container."""
    return await _request("GET", "/api/v1/system/info")


async def get_system_stats() -> dict[str, Any] | None:
    """Fetch live system stats (CPU, memory, storage) from the ARM container."""
    return await _request("GET", "/api/v1/system/stats")


async def fix_permissions(job_id: int) -> dict[str, Any] | None:
    """Fix file permissions for a job. Returns None if ARM is unreachable."""
    return await _request("POST", f"/api/v1/jobs/{job_id}/fix-permissions")


async def update_title(job_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
    """Update a job's title metadata via ARM's REST API. Returns None if unreachable."""
    return await _request("PUT", f"/api/v1/jobs/{job_id}/title", json=data)


async def update_job_config(job_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
    """Update a job's rip parameters via ARM's REST API. Returns None if unreachable."""
    return await _request("PATCH", f"/api/v1/jobs/{job_id}/config", json=data)


async def start_waiting_job(job_id: int) -> dict[str, Any] | None:
    """Start a job in 'waiting' status. Returns None if ARM is unreachable."""
    return await _request("POST", f"/api/v1/jobs/{job_id}/start")


async def pause_waiting_job(job_id: int) -> dict[str, Any] | None:
    """Toggle per-job pause for a waiting job. Returns None if ARM is unreachable."""
    return await _request("POST", f"/api/v1/jobs/{job_id}/pause")


async def set_ripping_enabled(enabled: bool) -> dict[str, Any] | None:
    """Toggle global ripping pause. Returns None if ARM is unreachable."""
    return await _request("POST", "/api/v1/system/ripping-enabled", json={"enabled": enabled})


async def get_version() -> dict[str, str] | None:
    """Fetch ARM and MakeMKV version info."""
    return await _request("GET", "/api/v1/system/version")


async def get_paths() -> list[dict[str, Any]] | None:
    """Fetch path existence/writability checks from the ARM container."""
    try:
        resp = await get_client().get("/api/v1/system/paths")
        if resp.is_success:
            return resp.json()
        return None
    except (httpx.ConnectError, httpx.TimeoutException, RuntimeError, OSError):
        return None


async def send_to_crc_db(job_id: int) -> dict[str, Any] | None:
    """Submit a job's CRC data to the community database. Returns None if ARM is unreachable."""
    return await _request("POST", f"/api/v1/jobs/{job_id}/send")


async def set_job_tracks(job_id: int, tracks: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Replace a job's tracks with MusicBrainz data. Returns None if ARM is unreachable."""
    return await _request("PUT", f"/api/v1/jobs/{job_id}/tracks", json={"tracks": tracks})


async def update_drive(drive_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
    """Update a drive's name/description via ARM's REST API. Returns None if unreachable."""
    return await _request("PATCH", f"/api/v1/drives/{drive_id}", json=data)


async def dismiss_notification(notify_id: int) -> dict[str, Any] | None:
    """Mark a notification as read. Returns None if ARM is unreachable."""
    return await _request("PATCH", f"/api/v1/notifications/{notify_id}")


async def naming_preview(pattern: str, variables: dict[str, str]) -> dict[str, Any] | None:
    """Preview a naming pattern with given variables. Returns None if ARM is unreachable."""
    return await _request(
        "POST", "/api/v1/naming/preview",
        json={"pattern": pattern, "variables": variables},
    )


# ---------------------------------------------------------------------------
# Metadata proxy — ARM is the single source of truth
# ---------------------------------------------------------------------------


async def search_metadata(query: str, year: str | None = None) -> list[dict[str, Any]]:
    """Search OMDb/TMDb via ARM. Raises httpx.HTTPStatusError on 4xx/5xx."""
    params: dict[str, str] = {"q": query}
    if year:
        params["year"] = year
    resp = await get_client().get("/api/v1/metadata/search", params=params)
    resp.raise_for_status()
    return resp.json()


async def get_media_detail(imdb_id: str) -> dict[str, Any] | None:
    """Fetch full details for a title by IMDb ID via ARM."""
    resp = await get_client().get(f"/api/v1/metadata/{imdb_id}")
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


async def search_music_metadata(
    query: str, **kwargs: Any
) -> dict[str, Any]:
    """Search MusicBrainz via ARM."""
    params: dict[str, str] = {"q": query}
    for key, val in kwargs.items():
        if val is not None:
            params[key] = str(val)
    resp = await get_client().get("/api/v1/metadata/music/search", params=params)
    resp.raise_for_status()
    return resp.json()


async def get_music_detail(release_id: str) -> dict[str, Any] | None:
    """Fetch full release details from MusicBrainz via ARM."""
    resp = await get_client().get(f"/api/v1/metadata/music/{release_id}")
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


async def lookup_crc(crc64: str) -> dict[str, Any]:
    """Look up a CRC64 hash via ARM."""
    resp = await get_client().get(f"/api/v1/metadata/crc/{crc64}")
    resp.raise_for_status()
    return resp.json()


async def test_metadata_key() -> dict[str, Any]:
    """Test the configured metadata API key via ARM."""
    resp = await get_client().get("/api/v1/metadata/test-key")
    resp.raise_for_status()
    return resp.json()
