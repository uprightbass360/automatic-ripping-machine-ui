"""BFF response shapes for the file browser surface."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class FileRoot(BaseModel):
    model_config = ConfigDict(extra="ignore")

    label: str
    path: str
    key: str | None = None
    host_path: str | None = None
    readonly: bool = False


class FileEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    type: Literal["directory", "file"]
    size: int = 0
    modified: str | None = None
    extension: str = ""
    category: str = ""
    permissions: str | None = None
    owner: str | None = None
    group: str | None = None


class DirectoryListing(BaseModel):
    model_config = ConfigDict(extra="ignore")

    path: str | None
    parent: str | None
    entries: list[FileEntry]
    readonly: bool = False


class OperationResult(BaseModel):
    """Generic result for action / passthrough endpoints.

    Designed permissively because upstream arm-neu actions return a
    family of envelopes (``{success}``, ``{success, paused}``,
    ``{success, count}``, ``{success, deleted, ...}``, etc). Common
    keys are surfaced for type help; ``extra='allow'`` keeps unknown
    keys (e.g. ``updated``, ``overrides``) flowing through so callers
    can read upstream-specific fields. Passthrough hardening into
    dedicated models is tracked separately.
    """
    model_config = ConfigDict(extra="allow")

    success: bool = True
    path: str | None = None
    error: str | None = None
    paused: bool | None = None
    count: int | None = None
    cleared: int | None = None
    # `deleted` may be either a path string (single-target delete) or
    # an int count (bulk delete) depending on the upstream endpoint.
    # Permissive str|int union keeps a single model usable across both.
    deleted: str | int | None = None
