"""Backwards-compat re-exports from backend.models per-domain modules.

This module preserves the existing `from backend.models.schemas import X`
import path used throughout the codebase. New imports should target the
per-domain module directly (e.g. `from backend.models.job import JobSchema`).

Scheduled for removal once all callers migrate to per-domain imports.
"""

from arm_contracts import (
    JobSummary,
)
from arm_contracts import (
    Track as TrackSchema,
)
from arm_contracts import (
    TrackCounts as TrackCountsSchema,
)

from backend.models.dashboard import DashboardResponse
from backend.models.drive import DriveSchema, DriveUpdateRequest
from backend.models.folder import FolderCreateRequest, FolderScanRequest
from backend.models.job import (
    TRANSCODE_OVERRIDES_ALLOWLIST,
    JobDetailSchema,
    JobListResponse,
    JobSchema,
)
from backend.models.logs import (
    LogContentResponse,
    LogEntrySchema,
    LogFileSchema,
    StructuredLogResponse,
)
from backend.models.metadata import (
    JobConfigUpdateRequest,
    MediaDetailSchema,
    MusicDetailSchema,
    MusicSearchResultSchema,
    NamingPreviewRequest,
    SearchResultSchema,
    TitleUpdateRequest,
)
from backend.models.notification import NotificationSchema
from backend.models.settings import SettingsResponse
from backend.models.system import (
    GpuSnapshotSchema,
    HardwareInfoSchema,
    MemoryInfoSchema,
    StoragePathSchema,
    SystemInfoSchema,
    SystemStatsSchema,
)
from backend.models.transcoder import (
    TranscoderJobListResponse,
    TranscoderStatsResponse,
)

__all__ = [
    "TRANSCODE_OVERRIDES_ALLOWLIST",
    "DashboardResponse",
    "DriveSchema",
    "DriveUpdateRequest",
    "FolderCreateRequest",
    "FolderScanRequest",
    "GpuSnapshotSchema",
    "HardwareInfoSchema",
    "JobConfigUpdateRequest",
    "JobDetailSchema",
    "JobListResponse",
    "JobSchema",
    "JobSummary",
    "LogContentResponse",
    "LogEntrySchema",
    "LogFileSchema",
    "MediaDetailSchema",
    "MemoryInfoSchema",
    "MusicDetailSchema",
    "MusicSearchResultSchema",
    "NamingPreviewRequest",
    "NotificationSchema",
    "SearchResultSchema",
    "SettingsResponse",
    "StoragePathSchema",
    "StructuredLogResponse",
    "SystemInfoSchema",
    "SystemStatsSchema",
    "TitleUpdateRequest",
    "TrackCountsSchema",
    "TrackSchema",
    "TranscoderJobListResponse",
    "TranscoderStatsResponse",
]
