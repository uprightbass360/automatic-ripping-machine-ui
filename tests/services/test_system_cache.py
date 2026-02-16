"""Tests for backend.services.system_cache — refresh + getters."""

from __future__ import annotations

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
