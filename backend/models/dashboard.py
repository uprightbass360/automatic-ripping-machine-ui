"""Dashboard composite response shape."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from backend.models.job import JobSchema
from backend.models.system import HardwareInfoSchema, SystemStatsSchema


class DashboardResponse(BaseModel):
    db_available: bool = True
    arm_online: bool = False
    # Per-field optionality: None signals "this ARM endpoint blipped on
    # this poll, frontend should keep its prior value" rather than
    # overwriting with zero/empty and flickering badges to nothing.
    active_jobs: list[JobSchema] | None = None
    system_info: HardwareInfoSchema | None = None
    drives_online: int | None = None
    drive_names: dict[str, str] | None = None
    notification_count: int | None = None
    ripping_enabled: bool | None = None
    makemkv_key_valid: bool | None = None
    makemkv_key_checked_at: str | None = None
    transcoder_online: bool = False
    transcoder_stats: dict[str, Any] | None = None
    transcoder_system_stats: SystemStatsSchema | None = None
    active_transcodes: list[dict[str, Any]] = []
    system_stats: SystemStatsSchema | None = None
    transcoder_info: HardwareInfoSchema | None = None
