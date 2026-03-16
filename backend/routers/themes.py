"""Theme management API endpoints."""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from backend.services import themes as theme_service

router = APIRouter(prefix="/api/themes", tags=["themes"])


@router.get("")
async def list_themes():
    """List all available themes (metadata only, no CSS)."""
    return theme_service.get_all_themes()


@router.get("/{theme_id}")
async def get_theme(theme_id: str):
    """Get full theme data including CSS."""
    theme = theme_service.get_theme(theme_id)
    if not theme:
        raise HTTPException(status_code=404, detail=f"Theme '{theme_id}' not found")
    return theme


@router.get("/{theme_id}/download")
async def download_theme(theme_id: str):
    """Download a theme as a JSON file."""
    theme = theme_service.get_theme(theme_id)
    if not theme:
        raise HTTPException(status_code=404, detail=f"Theme '{theme_id}' not found")
    # Remove runtime-only fields
    download = {k: v for k, v in theme.items() if k != "builtin"}
    return JSONResponse(
        content=download,
        headers={"Content-Disposition": f'attachment; filename="{theme_id}.json"'},
    )


@router.post("", status_code=201)
async def upload_theme(request: Request):
    """Upload a user theme."""
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    try:
        saved = theme_service.save_user_theme(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return saved


@router.delete("/{theme_id}")
async def delete_theme(theme_id: str):
    """Delete a user theme. Built-in themes cannot be deleted."""
    deleted = theme_service.delete_user_theme(theme_id)
    if not deleted:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete '{theme_id}': built-in theme or not found",
        )
    return {"detail": f"Theme '{theme_id}' deleted"}
