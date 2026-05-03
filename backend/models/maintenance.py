"""BFF response shapes for the maintenance surface.

These wrap arm-neu's maintenance endpoints; the BFF currently passes
the dicts through. Per the spec, response_model annotations describe
the contract but no model_validate wrap is added on the BFF side.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class MaintenanceSummary(BaseModel):
    model_config = ConfigDict(extra="ignore")

    orphan_logs: int | None = None
    orphan_folders: int | None = None
    unseen_notifications: int | None = None
    cleared_notifications: int | None = None
    stale_transcoder_jobs: int | None = None


class OrphanLogList(BaseModel):
    """Orphan logs payload from arm-neu.

    Real upstream shape is a generic `{success, count, items?}` envelope
    rather than a typed list - typed permissively here so the BFF can
    pass it through, and the frontend reads `count` for the badge.
    """
    model_config = ConfigDict(extra="ignore")

    success: bool = True
    count: int | None = None
    logs: list[str] | None = None


class OrphanFolderList(BaseModel):
    model_config = ConfigDict(extra="ignore")

    success: bool = True
    count: int | None = None
    folders: list[str] | None = None


class BulkOperationResult(BaseModel):
    """Bulk delete result. Upstream returns `deleted: <int count>`."""
    model_config = ConfigDict(extra="ignore")

    success: bool = True
    deleted: int | None = None
    errors: list[str] | None = None


class ImageCacheStats(BaseModel):
    """Image cache snapshot. image_cache.stats() returns ``count`` and
    ``size_bytes``; image_cache.clear() returns ``cleared`` (the count
    of dropped entries). Both keys are surfaced so a single typed model
    serves both endpoints."""
    model_config = ConfigDict(extra="ignore")

    count: int | None = None
    size_bytes: int | None = None
    cleared: int | None = None


class CleanupTranscoderResult(BaseModel):
    """Cleanup-transcoder counts deleted jobs."""
    model_config = ConfigDict(extra="ignore")

    success: bool = True
    deleted: int = 0
    errors: list[str] = []


class ClearRawResult(BaseModel):
    """Clear-raw cleared count, bytes freed, and any errors."""
    model_config = ConfigDict(extra="ignore")

    success: bool = True
    cleared: int = 0
    freed_bytes: int = 0
    errors: list[str] = []
    path: str | None = None
