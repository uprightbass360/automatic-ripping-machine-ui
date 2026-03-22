"""Maintenance endpoints — orchestrates ARM proxy, notifications, and transcoder cleanup."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services import arm_client, arm_db, transcoder_client

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["maintenance"])

_ARM_UNREACHABLE = "ARM web UI is unreachable"


class PathRequest(BaseModel):
    path: str


class BulkPathRequest(BaseModel):
    paths: list[str]


def _check_arm(result: dict[str, Any] | None) -> dict[str, Any]:
    if result is None:
        raise HTTPException(status_code=503, detail=_ARM_UNREACHABLE)
    if result.get("success") is False:
        raise HTTPException(status_code=502, detail=result.get("error", "ARM request failed"))
    return result


@router.get("/maintenance/summary")
async def get_summary():
    """Aggregate counts from ARM, notifications DB, and transcoder."""

    async def _arm_counts():
        return await arm_client.get_maintenance_counts()

    async def _transcoder_counts():
        completed = await transcoder_client.get_jobs(status="completed", limit=1)
        failed = await transcoder_client.get_jobs(status="failed", limit=1)
        if completed is None and failed is None:
            return None
        total = 0
        if completed and "total" in completed:
            total += completed["total"]
        if failed and "total" in failed:
            total += failed["total"]
        return total

    arm_task = asyncio.create_task(_arm_counts())
    tc_task = asyncio.create_task(_transcoder_counts())

    arm_counts = await arm_task
    tc_count = await tc_task

    return {
        "orphan_logs": arm_counts.get("orphan_logs") if arm_counts else None,
        "orphan_folders": arm_counts.get("orphan_folders") if arm_counts else None,
        "unseen_notifications": arm_db.get_notification_count(),
        "cleared_notifications": arm_db.get_cleared_notification_count(),
        "stale_transcoder_jobs": tc_count,
    }


@router.get("/maintenance/orphan-logs")
async def get_orphan_logs():
    return _check_arm(await arm_client.get_orphan_logs())


@router.get("/maintenance/orphan-folders")
async def get_orphan_folders():
    return _check_arm(await arm_client.get_orphan_folders())


@router.post("/maintenance/delete-log")
async def delete_log(req: PathRequest):
    return _check_arm(await arm_client.delete_orphan_log(req.path))


@router.post("/maintenance/delete-folder")
async def delete_folder(req: PathRequest):
    return _check_arm(await arm_client.delete_orphan_folder(req.path))


@router.post("/maintenance/bulk-delete-logs")
async def bulk_delete_logs(req: BulkPathRequest):
    return _check_arm(await arm_client.bulk_delete_logs(req.paths))


@router.post("/maintenance/bulk-delete-folders")
async def bulk_delete_folders(req: BulkPathRequest):
    return _check_arm(await arm_client.bulk_delete_folders(req.paths))


@router.post("/maintenance/dismiss-all-notifications")
async def dismiss_all_notifications():
    count = arm_db.dismiss_all_notifications()
    return {"success": True, "count": count}


@router.post("/maintenance/purge-notifications")
async def purge_notifications():
    count = arm_db.purge_cleared_notifications()
    return {"success": True, "count": count}


@router.post("/maintenance/cleanup-transcoder")
async def cleanup_transcoder():
    """Delete completed and failed transcoder jobs. Paginates through all results."""
    deleted = 0
    errors: list[str] = []

    for status in ("completed", "failed"):
        offset = 0
        while True:
            page = await transcoder_client.get_jobs(status=status, limit=50, offset=offset)
            if page is None:
                errors.append(f"Transcoder unreachable while fetching {status} jobs")
                break
            jobs = page.get("jobs", [])
            if not jobs:
                break
            for job in jobs:
                job_id = job.get("id") or job.get("job_id")
                if job_id and await transcoder_client.delete_job(job_id):
                    deleted += 1
                else:
                    errors.append(f"Failed to delete transcoder job {job_id}")
            offset += len(jobs)
            if offset >= page.get("total", 0):
                break

    return {"success": True, "deleted": deleted, "errors": errors}
