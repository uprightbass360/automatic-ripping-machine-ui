from fastapi import APIRouter, HTTPException, Query

from backend.models.schemas import LogContentResponse, LogFileSchema
from backend.services import log_reader

router = APIRouter(prefix="/api", tags=["logs"])


@router.get("/logs", response_model=list[LogFileSchema])
def list_logs():
    return log_reader.list_logs()


@router.get("/logs/{filename}", response_model=LogContentResponse)
def get_log(
    filename: str,
    mode: str = Query("tail", pattern="^(tail|full)$"),
    lines: int = Query(100, ge=1, le=10000),
):
    result = log_reader.read_log(filename, mode=mode, lines=lines)
    if result is None:
        raise HTTPException(status_code=404, detail="Log file not found")
    return result
