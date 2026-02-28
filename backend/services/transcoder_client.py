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
    except (httpx.HTTPError, httpx.ConnectError, RuntimeError, OSError):
        return None


async def test_connection() -> dict[str, Any]:
    """Two-step probe: check reachability via /health, then auth via /config."""
    result: dict[str, Any] = {
        "reachable": False,
        "auth_ok": False,
        "auth_required": False,
        "gpu_support": None,
        "worker_running": False,
        "queue_size": 0,
        "error": None,
    }
    try:
        resp = await get_client().get("/health")
        resp.raise_for_status()
        data = resp.json()
        result["reachable"] = True
        result["gpu_support"] = data.get("gpu_support")
        result["worker_running"] = data.get("worker_running", False)
        result["queue_size"] = data.get("queue_size", 0)
        result["auth_required"] = data.get("require_api_auth", False)
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        result["error"] = f"Connection failed: {e}"
        return result
    except httpx.HTTPError as e:
        result["error"] = f"Health check failed: {e}"
        return result

    # Step 2: verify API key by hitting an authenticated endpoint
    try:
        config_resp = await get_client().get("/config")
        if config_resp.status_code in (401, 403):
            result["auth_ok"] = False
        else:
            config_resp.raise_for_status()
            result["auth_ok"] = True
    except httpx.HTTPStatusError as e:
        if e.response.status_code in (401, 403):
            result["auth_ok"] = False
        else:
            result["error"] = f"Config check failed: {e}"
    except (httpx.ConnectError, httpx.TimeoutException):
        # Reachability already confirmed via /health; this is unexpected
        result["error"] = "Lost connection during auth check"

    return result


async def test_webhook(webhook_secret: str) -> dict[str, Any]:
    """Send a test webhook payload to verify the webhook secret."""
    result: dict[str, Any] = {
        "reachable": False,
        "secret_ok": False,
        "secret_required": False,
        "error": None,
    }
    headers: dict[str, str] = {}
    if webhook_secret:
        headers["X-Webhook-Secret"] = webhook_secret

    try:
        # Use a fresh client without the shared X-API-Key header
        async with httpx.AsyncClient(
            base_url=settings.transcoder_url,
            timeout=httpx.Timeout(10.0, connect=3.0),
        ) as client:
            resp = await client.post(
                "/webhook/arm",
                json={"title": "ARM UI connection test", "body": "test", "type": "info"},
                headers=headers,
            )
        result["reachable"] = True
        if resp.status_code in (401, 403):
            result["secret_ok"] = False
            result["secret_required"] = True
        else:
            # Any non-auth error (400, 200 "ignored") means the secret was accepted
            result["secret_ok"] = True
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        result["error"] = f"Connection failed: {e}"
    except httpx.HTTPError as e:
        result["reachable"] = True
        result["error"] = f"Webhook test failed: {e}"

    return result


async def send_webhook(payload: dict) -> dict[str, Any]:
    """Send a webhook payload to the transcoder to trigger a transcode job.

    Returns {"success": True} or {"success": False, "error": "..."}.
    """
    import os
    import yaml

    # Read webhook secret directly from arm.yaml (API masks secrets)
    webhook_secret = ""
    yaml_path = settings.arm_config_path
    if yaml_path and os.path.isfile(yaml_path):
        try:
            with open(yaml_path, "r") as f:
                arm_cfg = yaml.safe_load(f) or {}
            webhook_secret = arm_cfg.get("TRANSCODER_WEBHOOK_SECRET", "") or ""
        except Exception:
            pass

    headers: dict[str, str] = {}
    if webhook_secret:
        headers["X-Webhook-Secret"] = webhook_secret

    try:
        async with httpx.AsyncClient(
            base_url=settings.transcoder_url,
            timeout=httpx.Timeout(10.0, connect=3.0),
        ) as client:
            resp = await client.post("/webhook/arm", json=payload, headers=headers)
        if resp.status_code in (401, 403):
            return {"success": False, "error": "Webhook secret rejected"}
        resp.raise_for_status()
        return {"success": True}
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        return {"success": False, "error": f"Transcoder offline: {e}"}
    except httpx.HTTPError as e:
        return {"success": False, "error": f"Webhook failed: {e}"}


async def get_job(job_id: int) -> dict[str, Any] | None:
    """Fetch a single transcoder job by ID."""
    try:
        resp = await get_client().get(f"/jobs/{job_id}")
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, httpx.ConnectError, RuntimeError, OSError):
        return None


async def get_system_info() -> dict[str, Any] | None:
    """Fetch static hardware info (CPU, RAM, GPU) from the transcoder."""
    try:
        resp = await get_client().get("/system/info")
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, httpx.ConnectError, RuntimeError, OSError):
        return None


async def get_system_stats() -> dict[str, Any] | None:
    """Fetch live system metrics (CPU%, temp, memory) from the transcoder."""
    try:
        resp = await get_client().get("/system/stats")
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, httpx.ConnectError, RuntimeError, OSError):
        return None


async def get_config() -> dict[str, Any] | None:
    """Fetch transcoder config with valid option lists. Returns None if offline."""
    try:
        resp = await get_client().get("/config")
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, httpx.ConnectError, RuntimeError, OSError):
        return None


async def update_config(config: dict[str, Any]) -> dict[str, Any] | None:
    """Patch transcoder config. Returns response dict or None if offline."""
    try:
        resp = await get_client().patch("/config", json=config)
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, httpx.ConnectError, RuntimeError, OSError):
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
    except (httpx.HTTPError, httpx.ConnectError, RuntimeError, OSError):
        return None


async def get_stats() -> dict[str, Any] | None:
    try:
        resp = await get_client().get("/stats")
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, httpx.ConnectError, RuntimeError, OSError):
        return None


async def retry_job(job_id: int) -> dict[str, Any] | None:
    try:
        resp = await get_client().post(f"/jobs/{job_id}/retry")
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, httpx.ConnectError, RuntimeError, OSError):
        return None


async def delete_job(job_id: int) -> bool:
    try:
        resp = await get_client().delete(f"/jobs/{job_id}")
        resp.raise_for_status()
        return True
    except (httpx.HTTPError, httpx.ConnectError, RuntimeError, OSError):
        return False


async def list_logs() -> list[dict[str, Any]] | None:
    """List transcoder log files. Returns None if offline."""
    try:
        resp = await get_client().get("/logs")
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, httpx.ConnectError, RuntimeError, OSError):
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
    except (httpx.HTTPError, httpx.ConnectError, RuntimeError, OSError):
        return None


async def read_structured_log(
    filename: str,
    mode: str = "tail",
    lines: int = 100,
    level: str | None = None,
    search: str | None = None,
) -> dict[str, Any] | None:
    """Read a structured transcoder log file. Returns None if offline."""
    try:
        params: dict[str, Any] = {"mode": mode, "lines": lines}
        if level:
            params["level"] = level
        if search:
            params["search"] = search
        resp = await get_client().get(
            f"/logs/{filename}/structured", params=params
        )
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, httpx.ConnectError, RuntimeError, OSError):
        return None
