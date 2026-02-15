"""Shared fixtures for the ARM UI backend test suite."""

from __future__ import annotations

import os

# --- Environment overrides (before any backend imports) ---
os.environ.setdefault("ARM_UI_ARM_DB_PATH", "/tmp/arm_test.db")
os.environ.setdefault("ARM_UI_ARM_LOG_PATH", "/tmp/arm_logs")
os.environ.setdefault("ARM_UI_ARM_CONFIG_PATH", "/tmp/arm.yaml")
os.environ.setdefault("ARM_UI_ARM_URL", "http://arm-test:8080")
os.environ.setdefault("ARM_UI_TRANSCODER_URL", "http://transcoder-test:5000")

from unittest.mock import AsyncMock, patch  # noqa: E402

import httpx  # noqa: E402
import pytest  # noqa: E402

from backend.services import arm_client, arm_db, metadata, system_cache, transcoder_client  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_singletons():
    """Reset all module-level singletons after each test."""
    yield
    # arm_db
    arm_db._db_engine = None
    arm_db._db_available = None
    # arm_client
    arm_client._client = None
    # transcoder_client
    transcoder_client._client = None
    # system_cache
    system_cache._arm_info = None
    system_cache._transcoder_info = None
    # metadata cached keys
    metadata._get_api_keys.cache_clear()


@pytest.fixture
async def app_client():
    """Async httpx client wired to the FastAPI app (no real network)."""
    with patch.object(system_cache, "refresh", new_callable=AsyncMock):
        from backend.main import app

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
