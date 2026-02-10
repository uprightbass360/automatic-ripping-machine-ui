from typing import Any

from fastapi import APIRouter, HTTPException, Query

from backend.models.schemas import TranscoderJobListResponse, TranscoderStatsResponse
from backend.services import transcoder_client

router = APIRouter(prefix="/api/transcoder", tags=["transcoder"])


@router.get("/stats", response_model=TranscoderStatsResponse)
async def get_stats():
    stats = await transcoder_client.get_stats()
    return TranscoderStatsResponse(
        online=stats is not None,
        stats=stats,
    )


@router.get("/jobs", response_model=TranscoderJobListResponse)
async def list_jobs(
    status: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    data = await transcoder_client.get_jobs(status=status, limit=limit, offset=offset)
    if data is None:
        return TranscoderJobListResponse(jobs=[], total=0)
    return TranscoderJobListResponse(
        jobs=data.get("jobs", []),
        total=data.get("total", 0),
    )


@router.post("/jobs/{job_id}/retry")
async def retry_job(job_id: int) -> dict[str, Any]:
    result = await transcoder_client.retry_job(job_id)
    if result is None:
        raise HTTPException(status_code=503, detail="Transcoder offline")
    return result


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: int) -> dict[str, str]:
    success = await transcoder_client.delete_job(job_id)
    if not success:
        raise HTTPException(status_code=503, detail="Transcoder offline or job not found")
    return {"status": "deleted"}
