from typing import Any

from fastapi import APIRouter, HTTPException

from backend.services import arm_client

router = APIRouter(prefix="/api/jobs", tags=["arm-actions"])


@router.post("/{job_id}/abandon")
async def abandon_job(job_id: int) -> dict[str, Any]:
    result = await arm_client.abandon_job(job_id)
    if result is None:
        raise HTTPException(status_code=503, detail="ARM web UI is unreachable")
    return result


@router.delete("/{job_id}")
async def delete_job(job_id: int) -> dict[str, Any]:
    result = await arm_client.delete_job(job_id)
    if result is None:
        raise HTTPException(status_code=503, detail="ARM web UI is unreachable")
    return result


@router.post("/{job_id}/fix-permissions")
async def fix_permissions(job_id: int) -> dict[str, Any]:
    result = await arm_client.fix_permissions(job_id)
    if result is None:
        raise HTTPException(status_code=503, detail="ARM web UI is unreachable")
    return result
