"""Folder scan / create request shapes."""

from __future__ import annotations

from pydantic import BaseModel


class FolderScanRequest(BaseModel):
    path: str


class FolderCreateRequest(BaseModel):
    source_path: str
    title: str
    year: str | None = None
    video_type: str
    disctype: str
    imdb_id: str | None = None
    poster_url: str | None = None
    multi_title: bool = False
    season: int | None = None
    disc_number: int | None = None
    disc_total: int | None = None
