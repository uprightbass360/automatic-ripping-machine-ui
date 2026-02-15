"""Startup cache for static hardware info from ARM and transcoder."""

from __future__ import annotations

import logging
from typing import Any

from backend.services import arm_client, transcoder_client

logger = logging.getLogger(__name__)

_arm_info: dict[str, Any] | None = None
_transcoder_info: dict[str, Any] | None = None


async def refresh() -> None:
    """Fetch system info from ARM and transcoder, cache in memory."""
    global _arm_info, _transcoder_info
    _arm_info = await arm_client.get_system_info()
    _transcoder_info = await transcoder_client.get_system_info()
    logger.info(
        "System cache refreshed: arm=%s, transcoder=%s",
        "ok" if _arm_info else "unavailable",
        "ok" if _transcoder_info else "unavailable",
    )


def get_arm_info() -> dict[str, Any] | None:
    return _arm_info


def get_transcoder_info() -> dict[str, Any] | None:
    return _transcoder_info
