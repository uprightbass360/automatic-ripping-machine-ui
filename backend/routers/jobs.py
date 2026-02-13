from fastapi import APIRouter, HTTPException, Query

from backend.models.schemas import (
    JobDetailSchema,
    JobListResponse,
    JobSchema,
    MediaDetailSchema,
    SearchResultSchema,
    TrackSchema,
)
from backend.services import arm_db, metadata

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
    job = arm_db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    config = arm_db.get_job_config_safe(job)
    tracks = [TrackSchema.model_validate(t) for t in (job.tracks or [])]

    job_data = JobSchema.model_validate(job).model_dump()
    return JobDetailSchema(**job_data, tracks=tracks, config=config)


@router.get("/metadata/search", response_model=list[SearchResultSchema])
async def search_metadata(
    q: str = Query(..., min_length=1),
    year: str | None = None,
):
    """Search OMDb/TMDb for titles matching the query."""
    return await metadata.search(q, year)


@router.get("/metadata/{imdb_id}", response_model=MediaDetailSchema)
async def get_media_detail(imdb_id: str):
    """Fetch full details for a title by IMDb ID."""
    result = await metadata.get_details(imdb_id)
    if not result:
        raise HTTPException(status_code=404, detail="Title not found")
    return result
