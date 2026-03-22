"""Pydantic response schemas for the API."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, field_validator


# --- ARM Job Schemas ---


class TrackSchema(BaseModel):
    track_id: int
    job_id: int
    track_number: str | None = None
    length: int | None = None
    aspect_ratio: str | None = None
    fps: float | None = None
    enabled: bool | None = None
    basename: str | None = None
    filename: str | None = None
    orig_filename: str | None = None
    new_filename: str | None = None
    ripped: bool | None = None
    status: str | None = None
    error: str | None = None
    source: str | None = None
    # Per-track title metadata (null = inherits from job)
    title: str | None = None
    year: str | None = None
    imdb_id: str | None = None
    poster_url: str | None = None
    video_type: str | None = None
    # TVDB episode matching
    episode_number: str | None = None
    episode_name: str | None = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_compat(cls, track) -> "TrackSchema":
        """Build from a Track ORM object, falling back main_feature -> enabled."""
        schema = cls.model_validate(track)
        if schema.enabled is None:
            schema.enabled = getattr(track, "main_feature", None)
        return schema


class JobSchema(BaseModel):
    job_id: int
    arm_version: str | None = None
    crc_id: str | None = None
    logfile: str | None = None
    start_time: datetime | None = None
    stop_time: datetime | None = None
    job_length: str | None = None
    status: str | None = None
    stage: str | None = None
    no_of_titles: int | None = None
    title: str | None = None
    title_auto: str | None = None
    title_manual: str | None = None
    year: str | None = None
    year_auto: str | None = None
    year_manual: str | None = None
    video_type: str | None = None
    video_type_auto: str | None = None
    video_type_manual: str | None = None
    imdb_id: str | None = None
    imdb_id_auto: str | None = None
    imdb_id_manual: str | None = None
    poster_url: str | None = None
    poster_url_auto: str | None = None
    poster_url_manual: str | None = None
    devpath: str | None = None
    mountpoint: str | None = None
    hasnicetitle: bool | None = None
    errors: str | None = None
    disctype: str | None = None
    label: str | None = None
    path: str | None = None
    raw_path: str | None = None
    transcode_path: str | None = None
    source_type: str | None = None
    source_path: str | None = None
    transcode_overrides: dict | None = None
    multi_title: bool | None = None
    disc_number: int | None = None
    disc_total: int | None = None
    manual_pause: bool | None = None
    wait_start_time: datetime | None = None
    tvdb_id: int | None = None

    @field_validator("transcode_overrides", mode="before")
    @classmethod
    def _parse_transcode_overrides(cls, v: Any) -> dict | None:
        if v is None:
            return None
        if isinstance(v, dict):
            return v
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return None
        return None

    artist: str | None = None
    artist_auto: str | None = None
    artist_manual: str | None = None
    album: str | None = None
    album_auto: str | None = None
    album_manual: str | None = None
    season: str | None = None
    season_auto: str | None = None
    season_manual: str | None = None
    episode: str | None = None
    episode_auto: str | None = None
    episode_manual: str | None = None
    ejected: bool | None = None
    pid: int | None = None
    tracks_total: int | None = None
    tracks_ripped: int | None = None

    model_config = {"from_attributes": True}


class JobDetailSchema(JobSchema):
    tracks: list[TrackSchema] = []
    config: dict[str, Any] | None = None


class JobListResponse(BaseModel):
    jobs: list[JobSchema]
    total: int
    page: int
    per_page: int
    pages: int


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
    read_cd: bool | None = None
    read_dvd: bool | None = None
    read_bd: bool | None = None
    firmware: str | None = None
    location: str | None = None
    stale: bool | None = None
    mdisc: int | None = None
    serial_id: str | None = None
    uhd_capable: bool | None = None
    current_job: JobSchema | None = None

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


class SystemStatsSchema(BaseModel):
    cpu_percent: float = 0
    cpu_temp: float = 0
    memory: MemoryInfoSchema | None = None
    storage: list[StoragePathSchema] = []


# --- Dashboard Schema ---


class DashboardResponse(BaseModel):
    db_available: bool = True
    arm_online: bool = False
    active_jobs: list[JobSchema] = []
    system_info: HardwareInfoSchema | None = None
    drives_online: int = 0
    drive_names: dict[str, str] = {}
    notification_count: int = 0
    ripping_enabled: bool = True
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
    arm_handbrake_presets: list[str] | None = None
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


class DriveUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    uhd_capable: bool | None = None
    drive_mode: str | None = None


class NamingPreviewRequest(BaseModel):
    pattern: str
    variables: dict[str, str] = {}
