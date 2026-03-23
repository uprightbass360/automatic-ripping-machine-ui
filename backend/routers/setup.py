"""Setup wizard proxy endpoints."""
from typing import Any

from fastapi import APIRouter

from backend.routers.arm_actions import _check_result
from backend.services import arm_client, system_cache

router = APIRouter(prefix="/api", tags=["setup"])


@router.get("/setup/status")
async def get_setup_status() -> dict[str, Any]:
    """Return setup status, using cache to avoid blocking on slow ARM endpoint.

    On cold cache, falls back to a direct call with a short timeout.
    If that also fails, returns a safe default that won't redirect to
    setup — the background refresh will populate the real value.
    """
    cached = await system_cache.get_setup_status()
    if cached is not None:
        return cached
    # Cold cache — try a quick direct call (2s timeout)
    result = await arm_client.get_setup_status(timeout=2.0)
    if result is not None and "error" not in result:
        return result
    # ARM unreachable — assume not first run so UI loads normally.
    # Background refresh will correct this within 5 minutes.
    return {"first_run": False, "setup_complete": True}


@router.post("/setup/complete")
async def complete_setup() -> dict[str, Any]:
    """Mark setup as done (proxies to ARM backend)."""
    return _check_result(await arm_client.complete_setup())
