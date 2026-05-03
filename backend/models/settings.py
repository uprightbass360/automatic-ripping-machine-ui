"""Settings response shape."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class SettingsResponse(BaseModel):
    arm_config: dict[str, Any] | None = None
    arm_metadata: dict[str, Any] | None = None
    naming_variables: dict[str, str] | None = None
    transcoder_config: dict[str, Any] | None = None
    transcoder_gpu_support: dict[str, Any] | None = None
    transcoder_auth_status: dict[str, Any] | None = None
    # Deprecated - kept for backward compat; mirrors transcoder_gpu_support
    gpu_support: dict[str, Any] | None = None
