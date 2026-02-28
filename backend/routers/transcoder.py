from typing import Any

from fastapi import APIRouter, HTTPException, Query

from backend.models.schemas import LogContentResponse, LogFileSchema, StructuredLogResponse, TranscoderJobListResponse, TranscoderStatsResponse
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


@router.get("/logs", response_model=list[LogFileSchema])
async def list_logs():
    data = await transcoder_client.list_logs()
    if data is None:
        return []
    return data


@router.get("/logs/{filename}/structured", response_model=StructuredLogResponse)
async def get_structured_log(
    filename: str,
    mode: str = Query("tail", pattern="^(tail|full)$"),
    lines: int = Query(100, ge=1, le=10000),
    level: str | None = Query(None),
    search: str | None = Query(None),
):
    data = await transcoder_client.read_structured_log(
        filename, mode=mode, lines=lines, level=level, search=search
    )
    if data is None:
        raise HTTPException(status_code=404, detail="Log not found or transcoder offline")
    return data


@router.get("/logs/{filename}", response_model=LogContentResponse)
async def get_log(
    filename: str,
    mode: str = Query("tail", pattern="^(tail|full)$"),
    lines: int = Query(100, ge=1, le=10000),
):
    data = await transcoder_client.read_log(filename, mode=mode, lines=lines)
    if data is None:
        raise HTTPException(status_code=404, detail="Log not found or transcoder offline")
    return data


@router.post("/jobs/{job_id}/retranscode")
async def retranscode_transcoder_job(job_id: int):
    """Re-queue a completed or failed transcoder job for re-transcoding."""
    job = await transcoder_client.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Transcoder job not found or transcoder offline")

    status = job.get("status", "")
    if status not in ("completed", "failed"):
        raise HTTPException(status_code=400, detail=f"Cannot re-transcode job with status '{status}'")

    payload = {
        "title": job.get("title", "Unknown"),
        "body": job.get("title", "Unknown"),
        "path": job.get("source_path", ""),
        "job_id": job.get("arm_job_id"),
        "status": "success",
        "video_type": job.get("video_type", "movie"),
        "year": job.get("year", ""),
        "disctype": job.get("disctype", "bluray"),
    }
    result = await transcoder_client.send_webhook(payload)
    if not result.get("success"):
        raise HTTPException(status_code=503, detail=result.get("error", "Transcoder unavailable"))
    return {"status": "ok", "message": "Transcode job re-queued"}
