"""Feature-flag discovery endpoint for the frontend."""

from fastapi import APIRouter

from backend.config import settings

router = APIRouter(prefix="/api", tags=["config"])


@router.get("/config")
async def get_config() -> dict[str, bool]:
    """Return feature flags that the frontend needs to render the right UI."""
    return {"transcoder_enabled": settings.transcoder_enabled}
