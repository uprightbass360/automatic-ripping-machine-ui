import logging

from fastapi import APIRouter, HTTPException, Query, Request

from backend.models.schemas import (
    JobDetailSchema,
    JobListResponse,
    JobSchema,
    MediaDetailSchema,
    MusicDetailSchema,
    MusicSearchResultSchema,
    SearchResultSchema,
    TrackSchema,
)
import httpx

from backend.services import arm_client, arm_db, progress, transcoder_client

log = logging.getLogger(__name__)

_JOB_NOT_FOUND = "Job not found"
_ARM_UNREACHABLE = "ARM service unreachable"

_404_JOB = {404: {"description": _JOB_NOT_FOUND}}
_502_ARM = {502: {"description": _ARM_UNREACHABLE}}
_404_502_ARM = {404: {"description": _JOB_NOT_FOUND}, 502: {"description": _ARM_UNREACHABLE}}

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


@router.get("/jobs/{job_id}", response_model=JobDetailSchema, responses=_404_JOB)
def get_job(job_id: int):
    job, config = arm_db.get_job_with_config(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=_JOB_NOT_FOUND)

    tracks = [TrackSchema.from_orm_compat(t) for t in (job.tracks or [])]

    job_data = JobSchema.model_validate(job).model_dump()
    return JobDetailSchema(**job_data, tracks=tracks, config=config)


@router.get("/jobs/{job_id}/progress", responses=_404_JOB)
def get_job_progress(job_id: int):
    job = arm_db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=_JOB_NOT_FOUND)
    counts = arm_db.get_job_track_counts(job_id)
    if getattr(job, "disctype", None) == "music":
        result = progress.get_music_progress(
            getattr(job, "logfile", None),
            counts.get("tracks_total", 0),
        )
    else:
        result = progress.get_rip_progress(job.job_id)
    result.update(counts)
    # Include no_of_titles so the frontend can show title count even before
    # Track rows are created in the DB (early scan/decrypt phase).
    result["no_of_titles"] = getattr(job, "no_of_titles", None)
    return result


@router.get("/jobs/{job_id}/crc-lookup", responses=_404_502_ARM)
async def crc_lookup_endpoint(job_id: int):
    """Look up a job's CRC64 hash in the community database."""
    job = arm_db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=_JOB_NOT_FOUND)
    if not job.crc_id:
        return {"no_crc": True, "found": False, "results": [], "has_api_key": False}
    try:
        return await arm_client.lookup_crc(job.crc_id)
    except httpx.HTTPStatusError as exc:
        log.warning("CRC lookup for job %d failed: %d", job_id, exc.response.status_code)
        raise HTTPException(status_code=exc.response.status_code, detail="CRC lookup failed")
    except (httpx.HTTPError, httpx.ConnectError, RuntimeError, OSError) as exc:
        log.error("CRC lookup for job %d unreachable: %s", job_id, exc)
        raise HTTPException(status_code=502, detail=_ARM_UNREACHABLE)


@router.get("/metadata/search", response_model=list[SearchResultSchema], responses=_502_ARM)
async def search_metadata(
    q: str = Query(..., min_length=1),
    year: str | None = None,
):
    """Search OMDb/TMDb for titles matching the query (proxied through ARM)."""
    try:
        return await arm_client.search_metadata(q, year)
    except httpx.HTTPStatusError as exc:
        log.warning("Metadata search failed for q=%r: %d", q, exc.response.status_code)
        raise HTTPException(status_code=exc.response.status_code, detail="Metadata search failed")
    except (httpx.HTTPError, httpx.ConnectError, RuntimeError, OSError) as exc:
        log.error("Metadata search unreachable for q=%r: %s", q, exc)
        raise HTTPException(status_code=502, detail=_ARM_UNREACHABLE)


@router.get("/metadata/{imdb_id}", response_model=MediaDetailSchema, responses={404: {"description": "Title not found"}, 502: {"description": _ARM_UNREACHABLE}})
async def get_media_detail(imdb_id: str):
    """Fetch full details for a title by IMDb ID (proxied through ARM)."""
    try:
        result = await arm_client.get_media_detail(imdb_id)
    except httpx.HTTPStatusError as exc:
        log.warning("Metadata detail failed: %d", exc.response.status_code)
        raise HTTPException(status_code=exc.response.status_code, detail="Metadata detail failed")
    except (httpx.HTTPError, httpx.ConnectError, RuntimeError, OSError):
        log.error("Metadata detail unreachable")
        raise HTTPException(status_code=502, detail=_ARM_UNREACHABLE)
    if not result:
        raise HTTPException(status_code=404, detail="Title not found")
    return result


@router.get("/metadata/music/search", responses=_502_ARM)
async def search_music_metadata(
    q: str = Query(..., min_length=1),
    artist: str | None = None,
    release_type: str | None = None,
    format: str | None = None,
    country: str | None = None,
    status: str | None = None,
    tracks: int | None = None,
    offset: int = Query(0, ge=0),
):
    """Search MusicBrainz for releases (proxied through ARM)."""
    try:
        return await arm_client.search_music_metadata(
            q, artist=artist, release_type=release_type, format=format,
            country=country, status=status, tracks=tracks, offset=offset,
        )
    except httpx.HTTPStatusError as exc:
        log.warning("Music search failed: %d", exc.response.status_code)
        raise HTTPException(status_code=exc.response.status_code, detail="Music search failed")
    except (httpx.HTTPError, httpx.ConnectError, RuntimeError, OSError):
        log.error("Music search unreachable")
        raise HTTPException(status_code=502, detail=_ARM_UNREACHABLE)


@router.get("/metadata/music/{release_id}", response_model=MusicDetailSchema, responses={404: {"description": "Release not found"}, 502: {"description": _ARM_UNREACHABLE}})
async def get_music_detail(release_id: str):
    """Fetch full release details from MusicBrainz (proxied through ARM)."""
    try:
        result = await arm_client.get_music_detail(release_id)
    except httpx.HTTPStatusError as exc:
        log.warning("Music detail failed: %d", exc.response.status_code)
        raise HTTPException(status_code=exc.response.status_code, detail="Music detail failed")
    except (httpx.HTTPError, httpx.ConnectError, RuntimeError, OSError):
        log.error("Music detail unreachable")
        raise HTTPException(status_code=502, detail=_ARM_UNREACHABLE)
    if not result:
        raise HTTPException(status_code=404, detail="Release not found")
    return result


@router.post("/jobs/{job_id}/multi-title", responses=_404_502_ARM)
async def toggle_multi_title(job_id: int, request: Request):
    """Toggle the multi_title flag on a job."""
    body = await request.json()
    result = await arm_client.toggle_multi_title(job_id, body)
    if result is None:
        raise HTTPException(status_code=502, detail=_ARM_UNREACHABLE)
    if not result.get("success"):
        status = 404 if "not found" in result.get("error", "").lower() else 400
        raise HTTPException(status_code=status, detail=result.get("error", "Failed"))
    return result


@router.put("/jobs/{job_id}/tracks/{track_id}/title", responses=_404_502_ARM)
async def update_track_title(job_id: int, track_id: int, request: Request):
    """Set per-track title metadata for a multi-title disc."""
    body = await request.json()
    result = await arm_client.update_track_title(job_id, track_id, body)
    if result is None:
        raise HTTPException(status_code=502, detail=_ARM_UNREACHABLE)
    if not result.get("success"):
        status = 404 if "not found" in result.get("error", "").lower() else 400
        raise HTTPException(status_code=status, detail=result.get("error", "Failed"))
    return result


@router.delete("/jobs/{job_id}/tracks/{track_id}/title", responses=_404_502_ARM)
async def clear_track_title(job_id: int, track_id: int):
    """Clear per-track title metadata (revert to job-level inheritance)."""
    result = await arm_client.clear_track_title(job_id, track_id)
    if result is None:
        raise HTTPException(status_code=502, detail=_ARM_UNREACHABLE)
    if not result.get("success"):
        status = 404 if "not found" in result.get("error", "").lower() else 400
        raise HTTPException(status_code=status, detail=result.get("error", "Failed"))
    return result


@router.patch("/jobs/{job_id}/transcode-config", responses={400: {"description": "Invalid request"}, 404: {"description": _JOB_NOT_FOUND}})
async def update_transcode_config(job_id: int, request: Request):
    """Set per-job transcode override settings."""
    body = await request.json()
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Request body must be a JSON object")
    try:
        result = arm_db.update_job_transcode_overrides(job_id, body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if result is None:
        raise HTTPException(status_code=404, detail=_JOB_NOT_FOUND)
    return {"success": True, "overrides": result}


@router.patch("/jobs/{job_id}/tracks/{track_id}", responses={400: {"description": "Invalid request"}, 404: {"description": "Track not found"}})
async def update_track_fields(job_id: int, track_id: int, request: Request):
    """Update editable fields (enabled, filename, ripped) on a track."""
    body = await request.json()
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Request body must be a JSON object")
    try:
        result = arm_db.update_track_fields(job_id, track_id, body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if result is None:
        raise HTTPException(status_code=404, detail="Track not found")
    return {"success": True, "updated": result}


@router.post("/jobs/{job_id}/retranscode", responses={404: {"description": "Job not found or not a video disc"}, 503: {"description": "Transcoder unavailable"}})
async def retranscode_job(job_id: int):
    """Re-send a completed ARM job to the transcoder."""
    payload = arm_db.get_job_retranscode_info(job_id)
    if not payload:
        raise HTTPException(status_code=404, detail="Job not found or not a video disc")
    result = await transcoder_client.send_webhook(payload)
    if not result.get("success"):
        raise HTTPException(status_code=503, detail=result.get("error", "Transcoder unavailable"))
    return {"status": "ok", "message": "Transcode job queued"}
