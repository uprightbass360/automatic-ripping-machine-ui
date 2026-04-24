"""FastAPI dependency injection utilities."""

from fastapi import HTTPException

from backend.config import settings
from backend.services.arm_db import get_session


def require_transcoder_enabled() -> None:
    """Raise 503 when the transcoder feature is disabled for this deployment."""
    if not settings.transcoder_enabled:
        raise HTTPException(
            status_code=503,
            detail="Transcoder disabled on this deployment",
        )


def get_db():
    """Yield a read-only database session."""
    session = get_session()
    try:
        yield session
    finally:
        session.close()
