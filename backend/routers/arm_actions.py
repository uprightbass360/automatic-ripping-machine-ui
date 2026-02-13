from typing import Any

from fastapi import APIRouter, HTTPException

from backend.models.schemas import TitleUpdateRequest
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


@router.put("/{job_id}/title")
async def update_title(job_id: int, body: TitleUpdateRequest) -> dict[str, Any]:
    """Update a job's title metadata (proxies to ARM)."""
    result = await arm_client.update_title(job_id, body.model_dump(exclude_none=True))
    if result is None:
        raise HTTPException(status_code=503, detail="ARM web UI is unreachable")
    return result
