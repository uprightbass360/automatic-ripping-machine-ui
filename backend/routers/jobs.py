from fastapi import APIRouter, HTTPException, Query

from backend.models.schemas import (
    JobDetailSchema,
    JobListResponse,
    JobSchema,
    MediaDetailSchema,
    SearchResultSchema,
    TrackSchema,
)
from backend.services import arm_db, crc_lookup, metadata, progress, transcoder_client
from backend.services.metadata import MetadataConfigError

router = APIRouter(prefix="/api", tags=["jobs"])


@router.get("/jobs", response_model=JobListResponse)
def list_jobs(
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    status: str | None = None,
    search: str | None = None,
    video_type: str | None = None,
):
    data = arm_db.get_jobs_paginated_response(page, per_page, status, search, video_type)
    return JobListResponse(
        jobs=[JobSchema.model_validate(j) for j in data["jobs"]],
        total=data["total"],
        page=data["page"],
        per_page=data["per_page"],
        pages=data["pages"],
    )


@router.get("/jobs/{job_id}", response_model=JobDetailSchema)
def get_job(job_id: int):
    job, config = arm_db.get_job_with_config(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    tracks = [TrackSchema.model_validate(t) for t in (job.tracks or [])]

    job_data = JobSchema.model_validate(job).model_dump()
    return JobDetailSchema(**job_data, tracks=tracks, config=config)


@router.get("/jobs/{job_id}/progress")
def get_job_progress(job_id: int):
    job = arm_db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return progress.get_rip_progress(job.job_id)


@router.get("/jobs/{job_id}/crc-lookup")
async def crc_lookup_endpoint(job_id: int):
    """Look up a job's CRC64 hash in the community database."""
    job = arm_db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if not job.crc_id:
        return {"no_crc": True, "found": False, "results": [], "has_api_key": False}
    result = await crc_lookup.lookup_crc(job.crc_id)
    result["has_api_key"] = crc_lookup.has_api_key()
    return result


@router.get("/metadata/search", response_model=list[SearchResultSchema])
async def search_metadata(
    q: str = Query(..., min_length=1),
    year: str | None = None,
):
    """Search OMDb/TMDb for titles matching the query."""
    try:
        return await metadata.search(q, year)
    except MetadataConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/metadata/{imdb_id}", response_model=MediaDetailSchema)
async def get_media_detail(imdb_id: str):
    """Fetch full details for a title by IMDb ID."""
    try:
        result = await metadata.get_details(imdb_id)
    except MetadataConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    if not result:
        raise HTTPException(status_code=404, detail="Title not found")
    return result


@router.post("/jobs/{job_id}/retranscode")
async def retranscode_job(job_id: int):
    """Re-send a completed ARM job to the transcoder."""
    payload = arm_db.get_job_retranscode_info(job_id)
    if not payload:
        raise HTTPException(status_code=404, detail="Job not found or not a video disc")
    result = await transcoder_client.send_webhook(payload)
    if not result.get("success"):
        raise HTTPException(status_code=503, detail=result.get("error", "Transcoder unavailable"))
    return {"status": "ok", "message": "Transcode job queued"}
