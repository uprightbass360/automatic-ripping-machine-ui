"""FastAPI dependency injection utilities."""

from backend.services.arm_db import get_session


def get_db():
    """Yield a read-only database session."""
    session = get_session()
    try:
        yield session
    finally:
        session.close()
