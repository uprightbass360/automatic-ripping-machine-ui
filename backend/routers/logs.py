"""Logs BFF - thin pass-through to the arm-neu logs API.

Keeps the public BFF route shape unchanged so the frontend doesn't need
to be touched. Filesystem reads moved to arm-neu in v17.3.0; this
container no longer needs the LOGPATH bind mount.
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from backend.models.schemas import LogContentResponse, LogFileSchema, StructuredLogResponse
from backend.services import arm_client

router = APIRouter(prefix="/api", tags=["logs"])

_ARM_UNREACHABLE = "ARM service unreachable"
_NOT_FOUND = "Log file not found"


def _check_or_404(result):
    """Raise 502 if upstream is unreachable, 404 if it returned an error."""
    if result is None:
        raise HTTPException(status_code=502, detail=_ARM_UNREACHABLE)
    if isinstance(result, dict) and result.get("success") is False:
        raise HTTPException(status_code=404, detail=_NOT_FOUND)
    return result


@router.get("/logs", response_model=list[LogFileSchema])
async def list_logs():
    result = await arm_client.list_logs()
    if result is None:
        raise HTTPException(status_code=502, detail=_ARM_UNREACHABLE)
    return result


@router.get("/logs/{filename}/download", responses={404: {"description": _NOT_FOUND}})
async def download_log(filename: str):
    """Stream the upstream raw log download to the client."""
    resp = await arm_client.stream_log_download(filename)
    if resp is None:
        raise HTTPException(status_code=502, detail=_ARM_UNREACHABLE)
    if resp.status_code == 404:
        await resp.aclose()
        raise HTTPException(status_code=404, detail=_NOT_FOUND)
    if resp.status_code != 200:
        await resp.aclose()
        raise HTTPException(status_code=502, detail=_ARM_UNREACHABLE)

    async def body():
        try:
            async for chunk in resp.aiter_bytes():
                yield chunk
        finally:
            await resp.aclose()

    headers = {}
    if "content-disposition" in resp.headers:
        headers["content-disposition"] = resp.headers["content-disposition"]
    return StreamingResponse(
        body(),
        media_type=resp.headers.get("content-type", "text/plain"),
        headers=headers,
    )


@router.delete("/logs/{filename}", responses={404: {"description": _NOT_FOUND}})
async def delete_log(filename: str):
    result = await arm_client.delete_log(filename)
    return _check_or_404(result)


@router.get(
    "/logs/{filename}/structured",
    response_model=StructuredLogResponse,
    responses={404: {"description": _NOT_FOUND}},
)
async def get_structured_log(
    filename: str,
    mode: str = Query("tail", pattern="^(tail|full)$"),
    lines: int = Query(100, ge=1, le=10000),
    level: str | None = Query(None),
    search: str | None = Query(None),
):
    result = await arm_client.read_log_structured(
        filename, mode=mode, lines=lines, level=level, search=search,
    )
    return _check_or_404(result)


@router.get(
    "/logs/{filename}",
    response_model=LogContentResponse,
    responses={404: {"description": _NOT_FOUND}},
)
async def get_log(
    filename: str,
    mode: str = Query("tail", pattern="^(tail|full)$"),
    lines: int = Query(100, ge=1, le=10000),
):
    result = await arm_client.read_log(filename, mode=mode, lines=lines)
    return _check_or_404(result)
