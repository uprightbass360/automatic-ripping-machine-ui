"""Pydantic response schemas for the API.

The Job/Track/JobSummary/TrackCounts/JobProgressState shapes are owned by
`arm_contracts` (Phase B/C of the shared-contracts rollout). This module
re-exports those types under their legacy `*Schema` names so call sites
in this repo don't need to change, and adds two arm-ui-only behaviors on
top of the contract:

- JobSchema.transcode_overrides field validator: strips legacy top-level
  keys (video_encoder, handbrake_preset*, etc.) with a WARN log and gates
  the post-strip dict against TranscodeJobConfig. Producer (arm-neu) emits
  clean shape going forward; this layer absorbs pre-v15 ARM data.
- JobDetailSchema: extends Job with tracks + config (the BFF builds these
  by composing two ripper endpoints).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from arm_contracts import (
    Job as _JobContract,
    JobSummary,
    Track as TrackSchema,
    TrackCounts as TrackCountsSchema,
)
from pydantic import BaseModel, field_validator

log = logging.getLogger(__name__)


# Top-level keys accepted in per-job transcode overrides. Mirrors the field
# names of arm_contracts.TranscodeJobConfig; kept in sync by hand.
TRANSCODE_OVERRIDES_ALLOWLIST: frozenset[str] = frozenset({
    "preset_slug",
    "overrides",
    "delete_source",
    "output_extension",
})


# --- ARM Job Schemas ---


class JobSchema(_JobContract):
    """arm-ui's view of a Job: the shared contract plus a transcode_overrides
    field validator that strips legacy keys before contract validation."""

    @field_validator("transcode_overrides", mode="before")
    @classmethod
    def _parse_transcode_overrides(cls, v: Any) -> dict | None:
        """Validate transcode_overrides via TranscodeJobConfig.

        Accepts a JSON string (from the arm-neu DB) or a dict (from the API
        body). Strips legacy top-level keys (video_encoder, handbrake_preset*,
        etc.) with a WARN log before validating so mixed legacy + new-shape
        rows still yield their valid subset. See arm_contracts.TranscodeJobConfig
        for the canonical shape.
        """
        from arm_contracts import TranscodeJobConfig
        from pydantic import ValidationError

        if v is None:
            return None
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return None
        elif isinstance(v, dict):
            parsed = v
        else:
            return None

        if not isinstance(parsed, dict):
            return None

        offending = set(parsed.keys()) - TRANSCODE_OVERRIDES_ALLOWLIST
        if offending:
            log.warning(
                "Stripping legacy transcode_overrides keys: %s",
                sorted(offending),
            )
            parsed = {k: v for k, v in parsed.items() if k in TRANSCODE_OVERRIDES_ALLOWLIST}

        # Validate-only: gate on contract shape but return the post-strip
        # dict so consumers see the exact keys the caller persisted, not
        # Pydantic's default-expanded envelope.
        try:
            TranscodeJobConfig.model_validate(parsed)
        except ValidationError as exc:
            log.warning(
                "transcode_overrides failed contract validation: %s",
                [{"loc": e["loc"], "msg": e["msg"]} for e in exc.errors()],
            )
            return None
        return parsed


class JobDetailSchema(JobSchema):
    tracks: list[TrackSchema] = []
    config: dict[str, Any] | None = None


class JobListResponse(BaseModel):
    jobs: list[JobSchema]
    total: int
    page: int
    per_page: int
    pages: int


__all__ = [
    "JobDetailSchema",
    "JobListResponse",
    "JobSchema",
    "JobSummary",
    "TRANSCODE_OVERRIDES_ALLOWLIST",
    "TrackCountsSchema",
    "TrackSchema",
]


# --- System Schemas ---


class SystemInfoSchema(BaseModel):
    id: int
    name: str | None = None
    cpu: str | None = None
    description: str | None = None
    mem_total: float | None = None

    model_config = {"from_attributes": True}


class HardwareInfoSchema(BaseModel):
    cpu: str | None = None
    memory_total_gb: float | None = None


class DriveSchema(BaseModel):
    drive_id: int
    name: str | None = None
    mount: str | None = None
    job_id_current: int | None = None
    job_id_previous: int | None = None
    description: str | None = None
    drive_mode: str | None = None
    maker: str | None = None
    model: str | None = None
    serial: str | None = None
    connection: str | None = None
    capabilities: list[str] | None = None
    firmware: str | None = None
    location: str | None = None
    stale: bool | None = None
    mdisc: int | None = None
    serial_id: str | None = None
    uhd_capable: bool | None = None
    rip_speed: int | None = None
    prescan_cache_mb: int | None = None
    prescan_timeout: int | None = None
    prescan_retries: int | None = None
    disc_enum_timeout: int | None = None
    current_job: JobSummary | None = None

    model_config = {"from_attributes": True}


class NotificationSchema(BaseModel):
    id: int
    title: str | None = None
    message: str | None = None
    trigger_time: datetime | None = None
    seen: bool = False
    cleared: bool = False

    model_config = {"from_attributes": True}


# --- System Stats Schemas ---


class MemoryInfoSchema(BaseModel):
    total_gb: float
    used_gb: float
    free_gb: float
    percent: float


class StoragePathSchema(BaseModel):
    name: str
    path: str
    total_gb: float
    used_gb: float
    free_gb: float
    percent: float


class GpuSnapshotSchema(BaseModel):
    vendor: str
    utilization_percent: float | None = None
    memory_used_mb: float | None = None
    memory_total_mb: float | None = None
    temperature_c: float | None = None
    encoder_percent: float | None = None
    power_draw_w: float | None = None
    power_limit_w: float | None = None
    clock_core_mhz: float | None = None
    clock_memory_mhz: float | None = None


class SystemStatsSchema(BaseModel):
    cpu_percent: float = 0
    cpu_temp: float = 0
    memory: MemoryInfoSchema | None = None
    storage: list[StoragePathSchema] = []
    gpu: GpuSnapshotSchema | None = None


# --- Dashboard Schema ---


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


# --- Transcoder Schemas ---


class TranscoderJobListResponse(BaseModel):
    jobs: list[dict[str, Any]]
    total: int


class TranscoderStatsResponse(BaseModel):
    online: bool
    stats: dict[str, Any] | None = None


# --- Logs Schemas ---


class LogFileSchema(BaseModel):
    filename: str
    size: int
    modified: datetime


class LogContentResponse(BaseModel):
    filename: str
    content: str
    lines: int


class LogEntrySchema(BaseModel):
    timestamp: str
    level: str
    logger: str
    event: str
    job_id: int | None = None
    label: str | None = None
    raw: str


class StructuredLogResponse(BaseModel):
    filename: str
    entries: list[LogEntrySchema]
    lines: int


# --- Settings Schema ---


class SettingsResponse(BaseModel):
    arm_config: dict[str, Any] | None = None
    arm_metadata: dict[str, Any] | None = None
    naming_variables: dict[str, str] | None = None
    transcoder_config: dict[str, Any] | None = None
    transcoder_gpu_support: dict[str, Any] | None = None
    transcoder_auth_status: dict[str, Any] | None = None
    # Deprecated — kept for backward compat; mirrors transcoder_gpu_support
    gpu_support: dict[str, Any] | None = None


# --- Metadata Search Schemas ---


class SearchResultSchema(BaseModel):
    title: str
    year: str
    imdb_id: str | None = None
    media_type: str
    poster_url: str | None = None


class MediaDetailSchema(SearchResultSchema):
    """Full detail for a single title (distinct from JobDetailSchema)."""
    plot: str | None = None
    background_url: str | None = None


class MusicSearchResultSchema(BaseModel):
    title: str
    artist: str
    year: str
    release_id: str
    media_type: str = "music"
    poster_url: str | None = None
    track_count: int | None = None
    country: str | None = None
    release_type: str | None = None
    format: str | None = None
    label: str | None = None


class MusicDetailSchema(MusicSearchResultSchema):
    catalog_number: str | None = None
    barcode: str | None = None
    status: str | None = None
    disc_count: int | None = None
    tracks: list[dict[str, Any]] = []


class TitleUpdateRequest(BaseModel):
    title: str | None = None
    year: str | None = None
    video_type: str | None = None
    imdb_id: str | None = None
    poster_url: str | None = None
    path: str | None = None
    disctype: str | None = None
    label: str | None = None
    artist: str | None = None
    album: str | None = None
    season: str | None = None
    episode: str | None = None


class JobConfigUpdateRequest(BaseModel):
    RIPMETHOD: str | None = None
    DISCTYPE: str | None = None
    MAINFEATURE: bool | None = None
    MINLENGTH: int | None = None
    MAXLENGTH: int | None = None
    AUDIO_FORMAT: str | None = None
    SKIP_TRANSCODE: bool | None = None


class DriveUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    uhd_capable: bool | None = None
    drive_mode: str | None = None
    rip_speed: int | None = None
    prescan_cache_mb: int | None = None
    prescan_timeout: int | None = None
    prescan_retries: int | None = None
    disc_enum_timeout: int | None = None


class NamingPreviewRequest(BaseModel):
    pattern: str
    variables: dict[str, str] = {}
