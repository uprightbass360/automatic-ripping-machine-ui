"""Tests for backend.main.lifespan - the FastAPI startup/shutdown context."""

from __future__ import annotations

import logging

import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_lifespan_runs_themes_migration():
    """Lifespan calls migrate_legacy_themes with the configured themes_path."""
    from backend.main import app, lifespan
    from backend.config import settings as app_settings
    from backend.services import arm_client, image_cache, system_cache, transcoder_client

    with patch("backend.main.migrate_legacy_themes") as mock_migrate, \
         patch.object(system_cache, "refresh", new_callable=AsyncMock), \
         patch.object(image_cache, "startup_scan"), \
         patch.object(arm_client, "close_client", new_callable=AsyncMock), \
         patch.object(transcoder_client, "close_client", new_callable=AsyncMock):
        async with lifespan(app):
            pass

    mock_migrate.assert_called_once_with(app_settings.themes_path)


@pytest.mark.asyncio
async def test_lifespan_swallows_migration_errors(caplog):
    """If migrate_legacy_themes raises, startup continues and the error is logged."""
    from backend.main import app, lifespan
    from backend.services import arm_client, image_cache, system_cache, transcoder_client

    with patch("backend.main.migrate_legacy_themes", side_effect=OSError("simulated EROFS")), \
         patch.object(system_cache, "refresh", new_callable=AsyncMock) as mock_refresh, \
         patch.object(image_cache, "startup_scan"), \
         patch.object(arm_client, "close_client", new_callable=AsyncMock), \
         patch.object(transcoder_client, "close_client", new_callable=AsyncMock), \
         caplog.at_level(logging.ERROR, logger="backend.main"):
        async with lifespan(app):
            pass

    # Startup did not abort: refresh was still called after the failed migrator.
    mock_refresh.assert_awaited_once()
    assert any(
        "Theme migration failed" in rec.message and rec.levelno == logging.ERROR
        for rec in caplog.records
    ), "Expected an ERROR log from main.py for the failed migration"
