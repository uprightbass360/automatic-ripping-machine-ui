"""Theme management API endpoints."""

import json

from fastapi import APIRouter, Form, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse, PlainTextResponse

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
    """Download theme JSON (without CSS — CSS is a separate file)."""
    theme = theme_service.get_theme(theme_id)
    if not theme:
        raise HTTPException(status_code=404, detail=f"Theme '{theme_id}' not found")
    download = {k: v for k, v in theme.items() if k not in ("builtin", "css")}
    return JSONResponse(
        content=download,
        headers={"Content-Disposition": f'attachment; filename="{theme_id}.json"'},
    )


@router.get("/{theme_id}/css")
async def download_theme_css(theme_id: str):
    """Download theme CSS file. Returns 404 if theme has no custom CSS."""
    theme = theme_service.get_theme(theme_id)
    if not theme:
        raise HTTPException(status_code=404, detail=f"Theme '{theme_id}' not found")
    css = theme.get("css", "")
    if not css.strip():
        raise HTTPException(status_code=404, detail=f"Theme '{theme_id}' has no custom CSS")
    return PlainTextResponse(
        content=css,
        headers={"Content-Disposition": f'attachment; filename="{theme_id}.css"'},
    )


@router.post("", status_code=201)
async def upload_theme(
    theme_json: UploadFile = File(..., description="Theme JSON file"),
    theme_css: str = Form("", description="Optional custom CSS"),
):
    """Upload a user theme (JSON file + optional CSS text)."""
    try:
        content = await theme_json.read()
        data = json.loads(content)
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(status_code=400, detail="Invalid JSON file")

    try:
        saved = theme_service.save_user_theme(data, css=theme_css)
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
