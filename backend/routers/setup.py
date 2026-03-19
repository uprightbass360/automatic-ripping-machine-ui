"""Setup wizard proxy endpoints."""
from typing import Any

from fastapi import APIRouter, HTTPException

from backend.services import arm_client

router = APIRouter(prefix="/api", tags=["setup"])


@router.get("/setup/status")
async def get_setup_status() -> dict[str, Any]:
    """Proxy setup status from ARM backend."""
    result = await arm_client.get_setup_status()
    if result is None:
        raise HTTPException(status_code=503, detail="ARM web UI is unreachable")
    return result


@router.post("/setup/complete")
async def complete_setup() -> dict[str, Any]:
    """Mark setup as done (proxies to ARM backend)."""
    result = await arm_client.complete_setup()
    if result is None:
        raise HTTPException(status_code=503, detail="ARM web UI is unreachable")
    if isinstance(result, dict) and result.get("success") is False:
        raise HTTPException(status_code=502, detail=result.get("error", "Failed to complete setup"))
    return result
