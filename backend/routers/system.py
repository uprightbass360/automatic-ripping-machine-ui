"""System management proxy endpoints."""
from typing import Any

from fastapi import APIRouter, HTTPException

from backend.services import arm_client, transcoder_client

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/system/job-stats")
async def get_job_stats() -> dict[str, Any]:
    """Proxy job statistics from ARM backend."""
    result = await arm_client.get_job_stats()
    if result is None:
        raise HTTPException(status_code=503, detail="ARM web UI is unreachable")
    return result


@router.post("/system/restart")
async def restart_arm() -> dict[str, Any]:
    """Restart the ARM service (proxies to ARM backend)."""
    result = await arm_client.restart_arm()
    if result is None:
        raise HTTPException(status_code=503, detail="ARM web UI is unreachable")
    return result


@router.post("/system/restart-transcoder", responses={503: {"description": "Transcoder unreachable"}})
async def restart_transcoder() -> dict[str, Any]:
    """Restart the transcoder service."""
    result = await transcoder_client.restart_transcoder()
    if result is None:
        raise HTTPException(status_code=503, detail="Transcoder is unreachable")
    return result
