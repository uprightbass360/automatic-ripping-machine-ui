from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.models.schemas import JobConfigUpdateRequest, TitleUpdateRequest
from backend.services import arm_client

router = APIRouter(prefix="/api/jobs", tags=["arm-actions"])


def _check_result(result: dict[str, Any] | None) -> dict[str, Any]:
    """Raise HTTPException if the ARM proxy result is None or reports failure."""
    if result is None:
        raise HTTPException(status_code=503, detail="ARM web UI is unreachable")
    if isinstance(result, dict) and result.get("success") is False:
        detail = result.get("error") or result.get("Error") or "Action failed"
        raise HTTPException(status_code=502, detail=detail)
    return result


@router.post("/{job_id}/abandon")
async def abandon_job(job_id: int) -> dict[str, Any]:
    return _check_result(await arm_client.abandon_job(job_id))


@router.post("/{job_id}/cancel")
async def cancel_waiting_job(job_id: int) -> dict[str, Any]:
    """Cancel a job in 'waiting' status (proxies to ARM)."""
    return _check_result(await arm_client.cancel_waiting_job(job_id))


@router.delete("/{job_id}")
async def delete_job(job_id: int) -> dict[str, Any]:
    return _check_result(await arm_client.delete_job(job_id))


@router.post("/{job_id}/fix-permissions")
async def fix_permissions(job_id: int) -> dict[str, Any]:
    return _check_result(await arm_client.fix_permissions(job_id))


@router.put("/{job_id}/title")
async def update_title(job_id: int, body: TitleUpdateRequest) -> dict[str, Any]:
    """Update a job's title metadata (proxies to ARM)."""
    return _check_result(await arm_client.update_title(job_id, body.model_dump(exclude_none=True)))


@router.patch("/{job_id}/config")
async def update_job_config(job_id: int, body: JobConfigUpdateRequest) -> dict[str, Any]:
    """Update a job's rip parameters (proxies to ARM)."""
    return _check_result(await arm_client.update_job_config(job_id, body.model_dump(exclude_none=True)))


@router.post("/{job_id}/start")
async def start_waiting_job(job_id: int) -> dict[str, Any]:
    """Start a job in 'waiting' status (proxies to ARM)."""
    return _check_result(await arm_client.start_waiting_job(job_id))


@router.post("/{job_id}/crc-submit")
async def crc_submit(job_id: int) -> dict[str, Any]:
    """Submit a job's CRC data to the community database (proxies to ARM)."""
    return _check_result(await arm_client.send_to_crc_db(job_id))


# --- System-level actions (separate prefix) ---

class RippingEnabledRequest(BaseModel):
    enabled: bool


system_router = APIRouter(prefix="/api/system", tags=["arm-system-actions"])


@system_router.post("/ripping-enabled")
async def set_ripping_enabled(body: RippingEnabledRequest) -> dict[str, Any]:
    """Toggle global ripping pause (proxies to ARM)."""
    return _check_result(await arm_client.set_ripping_enabled(body.enabled))
