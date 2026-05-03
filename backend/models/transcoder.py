"""Transcoder integration response shapes.

Models will be tightened in a follow-up commit (TranscoderJob,
TranscoderStatsSummary, etc.). For now this module re-exports the
existing list/stats response wrappers from the original schemas.py.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class TranscoderJobListResponse(BaseModel):
    jobs: list[dict[str, Any]]
    total: int


class TranscoderStatsResponse(BaseModel):
    online: bool
    stats: dict[str, Any] | None = None
