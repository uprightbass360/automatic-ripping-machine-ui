"""Settings response shape."""

from __future__ import annotations

from pydantic import BaseModel

from backend.models.transcoder import TranscoderAuthStatus, TranscoderConfig


class SettingsResponse(BaseModel):
    arm_config: dict[str, str | None] | None = None
    arm_metadata: dict[str, str] | None = None
    naming_variables: dict[str, str] | None = None
    transcoder_config: TranscoderConfig | None = None
    transcoder_gpu_support: dict[str, bool] | None = None
    transcoder_auth_status: TranscoderAuthStatus | None = None
    # Deprecated; mirrors transcoder_gpu_support
    gpu_support: dict[str, bool] | None = None
