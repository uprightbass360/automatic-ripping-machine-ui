from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from backend.models.schemas import LogContentResponse, LogFileSchema, StructuredLogResponse
from backend.services import log_reader

router = APIRouter(prefix="/api", tags=["logs"])


@router.get("/logs", response_model=list[LogFileSchema])
def list_logs():
    return log_reader.list_logs()


@router.get("/logs/{filename}/download", responses={404: {"description": "Log file not found"}})
def download_log(filename: str):
    """Download a log file."""
    log_path = log_reader.resolve_log_path(filename)
    if log_path is None:
        raise HTTPException(status_code=404, detail="Log file not found")
    return FileResponse(
        path=str(log_path),
        filename=log_path.name,
        media_type="text/plain",
    )


@router.delete("/logs/{filename}", responses={404: {"description": "Log file not found"}})
def delete_log(filename: str):
    """Delete a log file."""
    if not log_reader.delete_log(filename):
        raise HTTPException(status_code=404, detail="Log file not found")
    return {"success": True, "filename": filename}


@router.get("/logs/{filename}/structured", response_model=StructuredLogResponse, responses={404: {"description": "Log file not found"}})
def get_structured_log(
    filename: str,
    mode: str = Query("tail", pattern="^(tail|full)$"),
    lines: int = Query(100, ge=1, le=10000),
    level: str | None = Query(None),
    search: str | None = Query(None),
):
    result = log_reader.read_structured_log(
        filename, mode=mode, lines=lines, level=level, search=search
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Log file not found")
    return result


@router.get("/logs/{filename}", response_model=LogContentResponse, responses={404: {"description": "Log file not found"}})
def get_log(
    filename: str,
    mode: str = Query("tail", pattern="^(tail|full)$"),
    lines: int = Query(100, ge=1, le=10000),
):
    result = log_reader.read_log(filename, mode=mode, lines=lines)
    if result is None:
        raise HTTPException(status_code=404, detail="Log file not found")
    return result
