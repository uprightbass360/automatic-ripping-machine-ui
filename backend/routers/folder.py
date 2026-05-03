"""Folder import proxy - routes folder scan/create through the ARM backend."""
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse

from backend.models.folder import FolderCreateRequest, FolderScanRequest
from backend.services import arm_client

router = APIRouter(prefix="/api/jobs/folder", tags=["folder"])

_ARM_UI_UNREACHABLE = "ARM web UI is unreachable"


def _check_result(result: dict[str, Any] | None) -> dict[str, Any]:
    if result is None:
        raise HTTPException(status_code=503, detail=_ARM_UI_UNREACHABLE)
    if isinstance(result, dict) and result.get("success") is False:
        detail = result.get("error") or "Action failed"
        raise HTTPException(status_code=502, detail=detail)
    return result


@router.post("/scan")
async def scan_folder(req: FolderScanRequest) -> dict[str, Any]:
    """Scan a folder for disc structure and metadata."""
    return _check_result(await arm_client.scan_folder(req.path))


@router.post("", status_code=201)
async def create_folder_job(req: FolderCreateRequest) -> dict[str, Any]:
    """Create a folder import job."""
    return _check_result(await arm_client.create_folder_job(req.model_dump()))


@router.get("/poster-proxy")
async def poster_proxy_redirect(url: str = Query(..., description="Poster image URL")):
    """Redirect to new image proxy endpoint (backward compatibility)."""
    return RedirectResponse(f"/api/images/proxy?url={url}", status_code=301)
