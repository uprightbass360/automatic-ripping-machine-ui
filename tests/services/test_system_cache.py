"""Tests for backend.services.system_cache — refresh + getters + ripping cache."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

from backend.services import system_cache


async def test_refresh_populates_cache():
    """refresh() stores info from both ARM and transcoder clients."""
    arm_info = {"cpu": "AMD Ryzen 7", "memory_total_gb": 32.0}
    transcoder_info = {"cpu": "Intel i7", "memory_total_gb": 16.0}
    with (
        patch(
            "backend.services.system_cache.arm_client.get_system_info",
            new_callable=AsyncMock, return_value=arm_info,
        ),
        patch(
            "backend.services.system_cache.transcoder_client.get_system_info",
            new_callable=AsyncMock, return_value=transcoder_info,
        ),
    ):
        await system_cache.refresh()
    assert system_cache.get_arm_info() == arm_info
    assert system_cache.get_transcoder_info() == transcoder_info


async def test_refresh_handles_none_from_services():
    """refresh() stores None when services are unreachable."""
    with (
        patch(
            "backend.services.system_cache.arm_client.get_system_info",
            new_callable=AsyncMock, return_value=None,
        ),
        patch(
            "backend.services.system_cache.transcoder_client.get_system_info",
            new_callable=AsyncMock, return_value=None,
        ),
    ):
        await system_cache.refresh()
    assert system_cache.get_arm_info() is None
    assert system_cache.get_transcoder_info() is None


# --- Ripping data cache tests ---


def _reset_ripping_cache():
    """Reset ripping cache globals for test isolation."""
    system_cache._ripping_data = None
    system_cache._ripping_fetched_at = 0.0
    system_cache._ripping_lock = None


async def test_get_ripping_data_returns_none_on_cold_cache():
    """Cold cache returns None immediately without blocking."""
    _reset_ripping_cache()
    with patch(
        "backend.services.system_cache.arm_client.get_ripping_enabled",
        new_callable=AsyncMock, return_value={"ripping_enabled": True},
    ):
        result = await system_cache.get_ripping_data()
    assert result is None  # background task kicked off, not awaited


async def test_get_ripping_data_returns_cached_after_refresh():
    """After background refresh completes, cache returns the data."""
    _reset_ripping_cache()
    ripping_info = {"ripping_enabled": True, "makemkv_key_valid": True}
    with patch(
        "backend.services.system_cache.arm_client.get_ripping_enabled",
        new_callable=AsyncMock, return_value=ripping_info,
    ):
        await system_cache.get_ripping_data()  # triggers background refresh
        await asyncio.sleep(0.05)  # let background task complete
        result = await system_cache.get_ripping_data()
    assert result == ripping_info


async def test_get_ripping_data_uses_ttl():
    """Within TTL, returns cached data without calling ARM again."""
    _reset_ripping_cache()
    ripping_info = {"ripping_enabled": True}
    mock = AsyncMock(return_value=ripping_info)
    with patch("backend.services.system_cache.arm_client.get_ripping_enabled", mock):
        await system_cache.get_ripping_data()
        await asyncio.sleep(0.05)
        # Second call within TTL should not trigger another refresh
        await system_cache.get_ripping_data()
        await asyncio.sleep(0.05)
    assert mock.call_count == 1


async def test_refresh_ripping_skips_on_none_result():
    """If ARM returns None, cache is not updated (stays at previous value)."""
    _reset_ripping_cache()
    # First: populate cache with real data
    ripping_info = {"ripping_enabled": True}
    with patch(
        "backend.services.system_cache.arm_client.get_ripping_enabled",
        new_callable=AsyncMock, return_value=ripping_info,
    ):
        await system_cache.get_ripping_data()
        await asyncio.sleep(0.05)

    # Force TTL expiry
    system_cache._ripping_fetched_at = 0.0

    # Second: ARM returns None (unreachable)
    with patch(
        "backend.services.system_cache.arm_client.get_ripping_enabled",
        new_callable=AsyncMock, return_value=None,
    ):
        await system_cache.get_ripping_data()
        await asyncio.sleep(0.05)
        result = await system_cache.get_ripping_data()
    # Should still have the previous data
    assert result == ripping_info
