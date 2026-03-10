"""Read-only access to ARM's SQLite database."""

from __future__ import annotations

import logging
import math

from sqlalchemy import create_engine, func, or_, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool

from backend.config import settings
from backend.models.arm import (
    AppState,
    Config,
    HIDDEN_CONFIG_FIELDS,
    Job,
    Notifications,
    SystemDrives,
    SystemInfo,
    Track,
)

log = logging.getLogger(__name__)

_db_available: bool | None = None


def _engine():
    url = f"sqlite:///file:{settings.arm_db_path}?mode=ro&uri=true"
    return create_engine(
        url, connect_args={"check_same_thread": False}, poolclass=NullPool
    )


def _rw_engine():
    url = f"sqlite:///{settings.arm_db_path}"
    return create_engine(
        url, connect_args={"check_same_thread": False}, poolclass=NullPool
    )


_db_engine = None
_db_rw_engine = None


def get_engine():
    global _db_engine
    if _db_engine is None:
        _db_engine = _engine()
    return _db_engine


def get_rw_engine():
    global _db_rw_engine
    if _db_rw_engine is None:
        _db_rw_engine = _rw_engine()
    return _db_rw_engine


def get_session() -> Session:
    return Session(get_engine())


def get_rw_session() -> Session:
    return Session(get_rw_engine())


def is_available() -> bool:
    """Check if the ARM database is reachable. Caches negative result briefly."""
    global _db_available
    try:
        with get_session() as session:
            session.execute(select(1))
        if not _db_available:
            log.info("ARM database connection established")
        _db_available = True
        return True
    except Exception as e:
        if _db_available is not False:
            log.warning("ARM database unavailable: %s", e)
        _db_available = False
        return False


# --- Query helpers ---

ACTIVE_STATUSES = {"active", "ripping", "transcoding", "waiting", "info", "waiting_transcode"}


def get_active_jobs() -> list[dict]:
    """Return active jobs as dicts enriched with track progress counts."""
    try:
        with get_session() as session:
            stmt = select(Job).where(
                func.lower(Job.status).in_(ACTIVE_STATUSES)
            ).order_by(Job.start_time.desc())
            jobs = list(session.scalars(stmt).unique().all())
            result = []
            for job in jobs:
                job_dict = {col.name: getattr(job, col.name) for col in Job.__table__.columns}
                tracks = list(job.tracks) if job.tracks else []
                job_dict["tracks_total"] = len(tracks)
                job_dict["tracks_ripped"] = sum(1 for t in tracks if t.ripped)
                result.append(job_dict)
            return result
    except Exception:
        return []


def get_jobs_paginated(
    page: int = 1,
    per_page: int = 25,
    status: str | None = None,
    search: str | None = None,
    video_type: str | None = None,
) -> tuple[list[Job], int]:
    try:
        with get_session() as session:
            stmt = select(Job)

            if status:
                stmt = stmt.where(func.lower(Job.status) == status.lower())
            if video_type:
                stmt = stmt.where(func.lower(Job.video_type) == video_type.lower())
            if search:
                pattern = f"%{search}%"
                stmt = stmt.where(
                    or_(
                        Job.title.ilike(pattern),
                        Job.title_auto.ilike(pattern),
                        Job.title_manual.ilike(pattern),
                        Job.label.ilike(pattern),
                    )
                )

            count_stmt = select(func.count()).select_from(stmt.subquery())
            total = session.scalar(count_stmt) or 0

            stmt = stmt.order_by(Job.start_time.desc())
            stmt = stmt.offset((page - 1) * per_page).limit(per_page)
            jobs = list(session.scalars(stmt).unique().all())

            return jobs, total
    except Exception:
        return [], 0


def get_jobs_paginated_response(
    page: int = 1,
    per_page: int = 25,
    status: str | None = None,
    search: str | None = None,
    video_type: str | None = None,
) -> dict:
    jobs, total = get_jobs_paginated(page, per_page, status, search, video_type)
    return {
        "jobs": jobs,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": max(1, math.ceil(total / per_page)) if total else 1,
    }


def get_job_track_counts(job_id: int) -> dict:
    """Return track completion counts for a single job."""
    try:
        with get_session() as session:
            stmt = select(Job).where(Job.job_id == job_id)
            job = session.scalars(stmt).unique().first()
            if not job:
                return {"tracks_total": 0, "tracks_ripped": 0}
            tracks = list(job.tracks) if job.tracks else []
            return {
                "tracks_total": len(tracks),
                "tracks_ripped": sum(1 for t in tracks if t.ripped),
            }
    except Exception:
        return {"tracks_total": 0, "tracks_ripped": 0}


def get_job(job_id: int) -> Job | None:
    try:
        with get_session() as session:
            stmt = select(Job).where(Job.job_id == job_id)
            return session.scalars(stmt).unique().first()
    except Exception:
        return None


def get_job_with_config(job_id: int) -> tuple[Job | None, dict | None]:
    """Load job and its config in a single session to avoid detached access."""
    try:
        with get_session() as session:
            stmt = select(Job).where(Job.job_id == job_id)
            job = session.scalars(stmt).unique().first()
            if not job:
                return None, None
            config = _extract_config_safe(job.config)
            return job, config
    except Exception:
        return None, None


def _extract_config_safe(config: Config | None) -> dict | None:
    """Extract config as dict with sensitive fields masked. Must be called inside a session."""
    if not config:
        return None
    result = {}
    for col in Config.__table__.columns:
        name = col.name
        if name in ("CONFIG_ID", "job_id"):
            continue
        value = getattr(config, name, None)
        if name in HIDDEN_CONFIG_FIELDS:
            result[name] = "***" if value else None
        else:
            result[name] = value
    return result


def get_job_config_safe(job: Job) -> dict | None:
    """Return job config as dict with sensitive fields masked.

    NOTE: This only works if the job's config relationship was loaded
    while the session was still open. Prefer get_job_with_config() instead.
    """
    return _extract_config_safe(job.config)


def get_drives() -> list[SystemDrives]:
    try:
        with get_session() as session:
            stmt = select(SystemDrives)
            return list(session.scalars(stmt).all())
    except Exception:
        return []


def get_drives_with_jobs() -> list[dict]:
    """Return drives with their current job info attached."""
    try:
        with get_session() as session:
            drives = list(session.scalars(select(SystemDrives)).all())
            result = []
            for drive in drives:
                drive_dict = {
                    col.name: getattr(drive, col.name)
                    for col in SystemDrives.__table__.columns
                }
                current_job = None
                if drive.job_id_current:
                    job = session.get(Job, drive.job_id_current)
                    if job:
                        current_job = {
                            col.name: getattr(job, col.name)
                            for col in Job.__table__.columns
                        }
                drive_dict["current_job"] = current_job
                result.append(drive_dict)
            return result
    except Exception:
        return []


def get_system_info() -> SystemInfo | None:
    try:
        with get_session() as session:
            return session.scalars(select(SystemInfo)).first()
    except Exception:
        return None


def get_notifications(include_cleared: bool = False) -> list[Notifications]:
    try:
        with get_session() as session:
            stmt = select(Notifications)
            if not include_cleared:
                stmt = stmt.where(Notifications.cleared == False)  # noqa: E712
            stmt = stmt.order_by(Notifications.trigger_time.desc())
            return list(session.scalars(stmt).all())
    except Exception:
        return []


def get_notification_count() -> int:
    try:
        with get_session() as session:
            stmt = select(func.count()).select_from(Notifications).where(
                Notifications.seen == False  # noqa: E712
            )
            return session.scalar(stmt) or 0
    except Exception:
        return 0


def get_all_config_safe() -> dict | None:
    """Return the most recent config with sensitive fields masked.

    Falls back to reading arm.yaml directly if the DB has no config rows
    (e.g. fresh install with no jobs yet).
    """
    # Try DB first
    try:
        with get_session() as session:
            stmt = select(Config).order_by(Config.CONFIG_ID.desc()).limit(1)
            config = session.scalars(stmt).first()
            if config:
                result = {}
                for col in Config.__table__.columns:
                    name = col.name
                    if name in ("CONFIG_ID", "job_id"):
                        continue
                    value = getattr(config, name, None)
                    if name in HIDDEN_CONFIG_FIELDS:
                        result[name] = "***" if value else None
                    else:
                        result[name] = value
                return result
    except Exception:
        pass

    # Fallback: read arm.yaml directly
    return _read_arm_yaml()


def _read_arm_yaml() -> dict | None:
    """Read arm.yaml from the mounted config volume."""
    import os
    yaml_path = settings.arm_config_path
    if not yaml_path or not os.path.isfile(yaml_path):
        return None
    try:
        import yaml
        with open(yaml_path, "r") as f:
            config = yaml.safe_load(f)
        if not isinstance(config, dict):
            return None
        # Mask sensitive fields
        for key in list(config.keys()):
            if key in HIDDEN_CONFIG_FIELDS and config[key]:
                config[key] = "***"
        return config
    except Exception as e:
        log.warning("Failed to read arm.yaml: %s", e)
        return None


def get_ripping_paused() -> bool:
    """Read global ripping-paused flag directly from the ARM database."""
    try:
        with get_session() as session:
            state = session.get(AppState, 1)
            return bool(state.ripping_paused) if state else False
    except Exception:
        return False


def get_job_retranscode_info(job_id: int) -> dict | None:
    """Build a webhook-shaped payload for re-transcoding an ARM job.

    Returns None if the job doesn't exist or isn't a video disc.
    """
    try:
        with get_session() as session:
            stmt = select(Job).where(Job.job_id == job_id)
            job = session.scalars(stmt).unique().first()
            if not job:
                return None
            if job.disctype not in ("dvd", "bluray", "bluray4k"):
                return None

            title = job.title or job.title_auto or job.label or "Unknown"
            year = job.year or job.year_auto or ""

            # Parse transcode overrides if present
            config_overrides = None
            if getattr(job, 'transcode_overrides', None):
                import json as _json
                try:
                    config_overrides = _json.loads(job.transcode_overrides)
                except (ValueError, TypeError):
                    pass

            payload = {
                "title": title,
                "body": f"{title} ({year})" if year else title,
                "path": job.raw_path or job.path or "",
                "job_id": job.job_id,
                "status": "success",
                "video_type": job.video_type or job.video_type_auto or "movie",
                "year": year,
                "disctype": job.disctype,
                "poster_url": job.poster_url or job.poster_url_auto or "",
                "config_overrides": config_overrides,
            }

            # Include per-track metadata for multi-title discs
            if getattr(job, 'multi_title', False):
                payload["multi_title"] = True
                tracks_meta = []
                for track in (job.tracks or []):
                    if getattr(track, 'title', None):
                        tracks_meta.append({
                            "track_number": str(track.track_number or ''),
                            "title": str(track.title),
                            "year": str(getattr(track, 'year', '') or ''),
                            "video_type": str(getattr(track, 'video_type', '') or ''),
                            "filename": str(track.filename or ''),
                        })
                if tracks_meta:
                    payload["tracks"] = tracks_meta

            return payload
    except Exception:
        log.exception("Failed to get retranscode info for job %s", job_id)
        return None


TRANSCODE_OVERRIDE_KEYS = {
    "video_encoder", "video_quality", "audio_encoder", "subtitle_mode",
    "handbrake_preset", "handbrake_preset_4k", "handbrake_preset_dvd",
    "handbrake_preset_file", "delete_source", "output_extension",
}


def _coerce_override(key: str, value) -> tuple[str, object] | None:
    """Coerce a single transcode override value. Returns None to skip."""
    if value is None or value == "":
        return None
    if key == "video_quality":
        return key, int(value)
    if key == "delete_source":
        if isinstance(value, bool):
            return key, value
        if isinstance(value, str):
            return key, value.lower() in ("true", "1", "yes")
        return key, bool(value)
    return key, str(value)


def update_job_transcode_overrides(job_id: int, overrides: dict) -> dict | None:
    """Validate and store per-job transcode overrides.

    Returns the validated overrides dict, or None if the job doesn't exist.
    """
    import json as _json

    # Validate keys
    invalid = set(overrides.keys()) - TRANSCODE_OVERRIDE_KEYS
    if invalid:
        raise ValueError(f"Unknown keys: {', '.join(sorted(invalid))}")

    clean = {}
    for key, value in overrides.items():
        pair = _coerce_override(key, value)
        if pair:
            clean[pair[0]] = pair[1]

    try:
        with get_rw_session() as session:
            stmt = select(Job).where(Job.job_id == job_id)
            job = session.scalars(stmt).unique().first()
            if not job:
                return None
            job.transcode_overrides = _json.dumps(clean) if clean else None
            session.commit()
            return clean
    except Exception:
        log.exception("Failed to update transcode overrides for job %s", job_id)
        raise


TRACK_EDITABLE_FIELDS: dict[str, type] = {
    "enabled": bool,
    "filename": str,
    "ripped": bool,
}


def update_track_fields(job_id: int, track_id: int, fields: dict) -> dict | None:
    """Update editable fields on a single track.

    Returns the updated field values, or None if the track doesn't exist
    or doesn't belong to the given job.
    """
    invalid = set(fields.keys()) - TRACK_EDITABLE_FIELDS.keys()
    if invalid:
        raise ValueError(f"Unknown fields: {', '.join(sorted(invalid))}")
    if not fields:
        raise ValueError("No fields to update")

    clean: dict = {}
    for key, value in fields.items():
        expected = TRACK_EDITABLE_FIELDS[key]
        if expected is bool:
            if isinstance(value, bool):
                clean[key] = value
            elif isinstance(value, str):
                clean[key] = value.lower() in ("true", "1", "yes")
            else:
                clean[key] = bool(value)
        else:
            clean[key] = str(value)

    try:
        with get_rw_session() as session:
            stmt = select(Track).where(
                Track.track_id == track_id, Track.job_id == job_id
            )
            track = session.scalars(stmt).first()
            if not track:
                return None
            for key, value in clean.items():
                if key == "enabled":
                    # API exposes "enabled"; DB column is still "main_feature"
                    # until the arm-neu migration runs.
                    setattr(track, "main_feature", value)
                else:
                    setattr(track, key, value)
            session.commit()
            return clean
    except Exception:
        log.exception("Failed to update track %s for job %s", track_id, job_id)
        raise
