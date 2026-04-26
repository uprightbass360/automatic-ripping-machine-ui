"""Test data factories for ripper-API-shaped dicts.

The UI no longer touches the ripper DB directly, so the ORM-spec mocks that
used to live here have been retired alongside `backend/services/arm_db.py`.
What remains is the shared `make_job_dict()` helper that produces a Job
columns dict matching what `/api/v1/jobs/active` and `/jobs/paginated`
return.
"""

from __future__ import annotations

from datetime import datetime, timezone


_JOB_DEFAULTS: dict = {
    "job_id": 1,
    "arm_version": "2.8.0",
    "crc_id": "abc123",
    "logfile": "job_1.log",
    "start_time": datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
    "stop_time": None,
    "job_length": "01:30:00",
    "status": "active",
    "stage": "rip",
    "no_of_titles": 5,
    "title": "Test Movie",
    "title_auto": "Test Movie",
    "title_manual": None,
    "year": "2024",
    "year_auto": "2024",
    "year_manual": None,
    "video_type": "movie",
    "video_type_auto": "movie",
    "video_type_manual": None,
    "imdb_id": "tt1234567",
    "poster_url": "https://example.com/poster.jpg",
    "devpath": "/dev/sr0",
    "mountpoint": "/mnt/dev/sr0",
    "hasnicetitle": True,
    "errors": None,
    "disctype": "dvd",
    "label": "TEST_MOVIE",
    "path": "/home/arm/media/Test Movie (2024)",
    "raw_path": "/home/arm/raw/Test Movie (2024)",
    "transcode_path": "/home/arm/transcode",
    "source_type": None,
    "source_path": None,
    "ejected": False,
    "disc_number": None,
    "disc_total": None,
    "pid": 12345,
    "artist": None,
    "artist_auto": None,
    "artist_manual": None,
    "album": None,
    "album_auto": None,
    "album_manual": None,
    "season": None,
    "season_auto": None,
    "season_manual": None,
    "episode": None,
    "episode_auto": None,
    "episode_manual": None,
}


def make_job_dict(**overrides) -> dict:
    """Return a plain dict matching the Job-columns dict the ripper API returns.

    Used by router tests that mock ``arm_client.get_jobs_paginated`` /
    ``get_active_jobs`` / ``get_job_detail``. Includes a default
    ``track_counts`` so JobSchema's nested-counts field is populated.
    """
    defaults = {
        **_JOB_DEFAULTS,
        "track_counts": {"total": 5, "ripped": 0},
    }
    defaults.update(overrides)
    return defaults
