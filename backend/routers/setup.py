"""Setup wizard proxy endpoints."""
from typing import Any

from fastapi import APIRouter

from backend.routers.arm_actions import _check_result
from backend.services import arm_client, system_cache

router = APIRouter(prefix="/api", tags=["setup"])


@router.get("/setup/status")
async def get_setup_status() -> dict[str, Any]:
    """Return setup status, using cache to avoid blocking on slow ARM endpoint."""
    cached = await system_cache.get_setup_status()
    if cached is not None:
        return cached
    # Cold cache — return safe default (not first_run) so the UI doesn't
    # redirect to /setup. Background refresh will populate the real value.
    return {"first_run": False, "setup_complete": True}


@router.post("/setup/complete")
async def complete_setup() -> dict[str, Any]:
    """Mark setup as done (proxies to ARM backend)."""
    return _check_result(await arm_client.complete_setup())
