"""Read-only access to ARM's SQLite database."""

from __future__ import annotations

import logging
import math

from sqlalchemy import create_engine, func, or_, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool

from backend.config import settings
from backend.models.arm import (
    Config,
    HIDDEN_CONFIG_FIELDS,
    Job,
    Notifications,
    SystemDrives,
    SystemInfo,
)

log = logging.getLogger(__name__)

_db_available: bool | None = None


def _engine():
    url = f"sqlite:///file:{settings.arm_db_path}?mode=ro&uri=true"
    return create_engine(
        url, connect_args={"check_same_thread": False}, poolclass=NullPool
    )


_db_engine = None


def get_engine():
    global _db_engine
    if _db_engine is None:
        _db_engine = _engine()
    return _db_engine


def get_session() -> Session:
    return Session(get_engine())


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

ACTIVE_STATUSES = {"active", "ripping", "transcoding", "waiting"}


def get_active_jobs() -> list[Job]:
    try:
        with get_session() as session:
            stmt = select(Job).where(
                func.lower(Job.status).in_(ACTIVE_STATUSES)
            ).order_by(Job.start_time.desc())
            return list(session.scalars(stmt).unique().all())
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


def get_job(job_id: int) -> Job | None:
    try:
        with get_session() as session:
            return session.get(Job, job_id)
    except Exception:
        return None


def get_job_config_safe(job: Job) -> dict | None:
    """Return job config as dict with sensitive fields masked."""
    if not job.config:
        return None
    config = job.config
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
            else:
                config[key] = config[key]
        return config
    except Exception as e:
        log.warning("Failed to read arm.yaml: %s", e)
        return None
