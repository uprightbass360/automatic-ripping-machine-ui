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
    except (httpx.ConnectError, httpx.TimeoutException, httpx.RemoteProtocolError, httpx.ReadError, RuntimeError, OSError) as exc:
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


async def scan_folder(path: str) -> dict[str, Any] | None:
    """Scan a folder for disc structure. Returns None if ARM is unreachable."""
    return await _request("POST", "/api/v1/jobs/folder/scan", json={"path": path})


async def create_folder_job(data: dict[str, Any]) -> dict[str, Any] | None:
    """Create a folder import job. Returns None if ARM is unreachable."""
    return await _request("POST", "/api/v1/jobs/folder", json=data)


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


async def toggle_multi_title(job_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
    """Toggle the multi_title flag on a job. Returns None if ARM is unreachable."""
    return await _request("POST", f"/api/v1/jobs/{job_id}/multi-title", json=data)


async def update_track_title(job_id: int, track_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
    """Set per-track title metadata. Returns None if ARM is unreachable."""
    return await _request("PUT", f"/api/v1/jobs/{job_id}/tracks/{track_id}/title", json=data)


async def clear_track_title(job_id: int, track_id: int) -> dict[str, Any] | None:
    """Clear per-track title metadata. Returns None if ARM is unreachable."""
    return await _request("DELETE", f"/api/v1/jobs/{job_id}/tracks/{track_id}/title")


async def set_job_tracks(job_id: int, tracks: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Replace a job's tracks with MusicBrainz data. Returns None if ARM is unreachable."""
    return await _request("PUT", f"/api/v1/jobs/{job_id}/tracks", json={"tracks": tracks})


async def tvdb_match(job_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
    """Run TVDB episode matching for a job. Returns None if ARM is unreachable."""
    return await _request("POST", f"/api/v1/jobs/{job_id}/tvdb-match", json=data)


async def tvdb_episodes(job_id: int, season: int) -> dict[str, Any] | None:
    """Fetch TVDB episodes for a job's series. Returns None if ARM is unreachable."""
    return await _request("GET", f"/api/v1/jobs/{job_id}/tvdb-episodes", params={"season": str(season)})


async def update_drive(drive_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
    """Update a drive's name/description via ARM's REST API. Returns None if unreachable."""
    return await _request("PATCH", f"/api/v1/drives/{drive_id}", json=data)


async def scan_drive(drive_id: int) -> dict[str, Any] | None:
    """Trigger a disc scan on a drive. Returns None if ARM is unreachable."""
    return await _request("POST", f"/api/v1/drives/{drive_id}/scan")


async def drive_diagnostic() -> dict[str, Any] | None:
    """Run udev and device diagnostics. Returns None if ARM is unreachable."""
    return await _request("GET", "/api/v1/drives/diagnostic")


async def delete_drive(drive_id: int) -> dict[str, Any] | None:
    """Remove a stale drive from the database. Returns None if ARM is unreachable."""
    return await _request("DELETE", f"/api/v1/drives/{drive_id}")


async def dismiss_notification(notify_id: int) -> dict[str, Any] | None:
    """Mark a notification as read. Returns None if ARM is unreachable."""
    return await _request("PATCH", f"/api/v1/notifications/{notify_id}")


async def get_abcde_config() -> dict[str, Any] | None:
    """Fetch abcde.conf contents from ARM. Returns None if unreachable."""
    return await _request("GET", "/api/v1/settings/abcde")


async def update_abcde_config(content: str) -> dict[str, Any] | None:
    """Write abcde.conf contents via ARM. Returns None if unreachable."""
    return await _request("PUT", "/api/v1/settings/abcde", json={"content": content})


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


async def test_metadata_key(key: str | None = None, provider: str | None = None) -> dict[str, Any]:
    """Test a metadata API key via ARM. Uses saved config if overrides are omitted."""
    params: dict[str, str] = {}
    if key:
        params["key"] = key
    if provider:
        params["provider"] = provider
    resp = await get_client().get("/api/v1/metadata/test-key", params=params)
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# File browser proxy — ARM has direct filesystem access
# ---------------------------------------------------------------------------


async def get_file_roots() -> list[dict[str, Any]] | None:
    """Fetch configured media root directories. Returns None if ARM is unreachable."""
    return await _request("GET", "/api/v1/files/roots")


async def list_files(path: str) -> dict[str, Any] | None:
    """List directory contents. Returns None if ARM is unreachable."""
    return await _request("GET", "/api/v1/files/list", params={"path": path})


async def rename_file(path: str, new_name: str) -> dict[str, Any] | None:
    """Rename a file or directory. Returns None if ARM is unreachable."""
    return await _request("POST", "/api/v1/files/rename", json={"path": path, "new_name": new_name})


async def move_file(path: str, destination: str) -> dict[str, Any] | None:
    """Move a file or directory. Returns None if ARM is unreachable."""
    return await _request("POST", "/api/v1/files/move", json={"path": path, "destination": destination})


async def create_directory(path: str, name: str) -> dict[str, Any] | None:
    """Create a new directory. Returns None if ARM is unreachable."""
    return await _request("POST", "/api/v1/files/mkdir", json={"path": path, "name": name})


async def fix_file_permissions(path: str) -> dict[str, Any] | None:
    """Fix ownership and permissions for a file or directory. Returns None if ARM is unreachable."""
    return await _request("POST", "/api/v1/files/fix-permissions", json={"path": path})


async def delete_file(path: str) -> dict[str, Any] | None:
    """Delete a file or directory. Returns None if ARM is unreachable."""
    return await _request("DELETE", "/api/v1/files/delete", json={"path": path})


async def get_setup_status() -> dict[str, Any] | None:
    """Fetch setup wizard status. Returns None if ARM is unreachable."""
    return await _request("GET", "/api/v1/setup/status")


async def complete_setup() -> dict[str, Any] | None:
    """Mark first-run setup as complete. Returns None if ARM is unreachable."""
    return await _request("POST", "/api/v1/setup/complete")


async def eject_drive(drive_id: int, method: str = "toggle") -> dict[str, Any] | None:
    """Eject, close, or toggle a drive tray. Returns None if ARM is unreachable."""
    return await _request("POST", f"/api/v1/drives/{drive_id}/eject", json={"method": method})


async def get_job_stats() -> dict[str, Any] | None:
    """Fetch job counts by status and type. Returns None if ARM is unreachable."""
    return await _request("GET", "/api/v1/system/stats/jobs")


async def restart_arm() -> dict[str, Any] | None:
    """Restart the ARM service. Returns None if ARM is unreachable."""
    return await _request("POST", "/api/v1/system/restart")


# --- Maintenance ---


async def get_maintenance_counts() -> dict[str, Any] | None:
    """Get orphan counts from ARM."""
    return await _request("GET", "/api/v1/maintenance/counts")


async def get_orphan_logs() -> dict[str, Any] | None:
    """Get orphan log files from ARM."""
    return await _request("GET", "/api/v1/maintenance/orphan-logs")


async def get_orphan_folders() -> dict[str, Any] | None:
    """Get orphan folders from ARM."""
    return await _request("GET", "/api/v1/maintenance/orphan-folders")


async def delete_orphan_log(path: str) -> dict[str, Any] | None:
    """Delete a single orphan log file via ARM."""
    return await _request("POST", "/api/v1/maintenance/delete-log", json={"path": path})


async def delete_orphan_folder(path: str) -> dict[str, Any] | None:
    """Delete a single orphan folder via ARM."""
    return await _request("POST", "/api/v1/maintenance/delete-folder", json={"path": path})


async def bulk_delete_logs(paths: list[str]) -> dict[str, Any] | None:
    """Bulk delete orphan log files via ARM."""
    return await _request("POST", "/api/v1/maintenance/bulk-delete-logs", json={"paths": paths})


async def bulk_delete_folders(paths: list[str]) -> dict[str, Any] | None:
    """Bulk delete orphan folders via ARM."""
    return await _request("POST", "/api/v1/maintenance/bulk-delete-folders", json={"paths": paths})


# --- Architecture debt fix: proxy these through ARM ---


async def update_transcode_overrides(job_id: int, overrides: dict) -> dict[str, Any] | None:
    """Update per-job transcode overrides via ARM (existing endpoint)."""
    return await _request("PATCH", f"/api/v1/jobs/{job_id}/transcode-config", json=overrides)


async def update_track_fields(job_id: int, track_id: int, fields: dict) -> dict[str, Any] | None:
    """Update track fields via ARM."""
    return await _request("PATCH", f"/api/v1/jobs/{job_id}/tracks/{track_id}", json=fields)


# --- MakeMKV Key Check ---


async def get_ripping_enabled() -> dict[str, Any] | None:
    """Get ripping-enabled status and MakeMKV key validity from ARM."""
    return await _request("GET", "/api/v1/system/ripping-enabled")


async def check_makemkv_key() -> dict[str, Any] | None:
    """Trigger a MakeMKV key validity check on ARM.

    Uses a 30-second timeout since prep_mkv() may fetch the beta key
    from forum.makemkv.com over the network.
    """
    return await _request("POST", "/api/v1/system/makemkv-key-check", timeout=30.0)
