import asyncio
import json
import logging
import os
import shutil
from pathlib import Path

from fastapi import APIRouter, HTTPException
import httpx
from pydantic import BaseModel
from sqlalchemy import or_, select

from backend.config import settings as app_settings
from backend.models.arm import Config, Job, SystemDrives, Track
from backend.models.schemas import SettingsResponse
from backend.services import arm_client, arm_db, transcoder_client

router = APIRouter(prefix="/api", tags=["settings"])
log = logging.getLogger(__name__)


def _read_hb_presets() -> list[str] | None:
    """Read HandBrake presets from the JSON file written by the init container."""
    path = app_settings.arm_hb_presets_path
    if not path or not os.path.isfile(path):
        return None
    try:
        with open(path) as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
    except (json.JSONDecodeError, OSError) as e:
        log.warning("Failed to read HandBrake presets: %s", e)
    return None


@router.get("/settings", response_model=SettingsResponse)
async def get_settings():
    # ARM config: prefer live API, fall back to DB snapshot
    arm_config = None
    arm_metadata = None
    naming_variables = None
    arm_resp = await arm_client.get_config()
    if arm_resp:
        arm_config = arm_resp.get("config")
        arm_metadata = arm_resp.get("comments")
        naming_variables = arm_resp.get("naming_variables")
    if not arm_config:
        arm_config = arm_db.get_all_config_safe()

    # HandBrake presets from init container
    arm_handbrake_presets = _read_hb_presets()

    # Transcoder config + GPU support
    transcoder_config = None
    transcoder_gpu_support = None

    tc_config_resp = await transcoder_client.get_config()
    if tc_config_resp:
        transcoder_config = tc_config_resp

    health = await transcoder_client.health()
    transcoder_auth_status = None
    if health:
        transcoder_gpu_support = health.get("gpu_support")
        transcoder_auth_status = {
            "require_api_auth": health.get("require_api_auth", False),
            "webhook_secret_configured": health.get("webhook_secret_configured", False),
        }
        # If the dedicated /config endpoint was offline, use health fallback
        if not transcoder_config:
            transcoder_config = {
                "config": health.get("config"),
                "updatable_keys": list(health.get("config", {}).keys()),
            }

    return SettingsResponse(
        arm_config=arm_config,
        arm_metadata=arm_metadata,
        arm_handbrake_presets=arm_handbrake_presets,
        naming_variables=naming_variables,
        transcoder_config=transcoder_config,
        transcoder_gpu_support=transcoder_gpu_support,
        transcoder_auth_status=transcoder_auth_status,
        gpu_support=transcoder_gpu_support,
    )


class ArmConfigUpdate(BaseModel):
    config: dict


@router.put("/settings/arm", responses={400: {"description": "Invalid config"}, 502: {"description": "ARM service unreachable"}})
async def update_arm_config(body: ArmConfigUpdate):
    result = await arm_client.update_config(body.config)
    if result is None:
        raise HTTPException(status_code=502, detail="ARM service unreachable")
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
    return result


@router.get("/settings/test-metadata")
async def test_metadata_key():
    """Test the currently saved metadata API key (proxied through ARM)."""
    try:
        return await arm_client.test_metadata_key()
    except httpx.HTTPStatusError as exc:
        log.warning("Metadata key test failed: %d", exc.response.status_code)
        return {"success": False, "message": "Metadata key test failed", "provider": "unknown"}
    except (httpx.HTTPError, httpx.ConnectError, RuntimeError, OSError) as exc:
        log.error("Metadata key test unreachable: %s", exc)
        return {"success": False, "message": "ARM service unreachable", "provider": "unknown"}


@router.patch("/settings/transcoder", responses={400: {"description": "Invalid config"}, 502: {"description": "Transcoder service unreachable"}})
async def update_transcoder_config(body: dict):
    result = await transcoder_client.update_config(body)
    if result is None:
        raise HTTPException(status_code=502, detail="Transcoder service unreachable")
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("detail", "Unknown error"))
    return result


@router.post("/settings/transcoder/test-connection")
async def test_transcoder_connection():
    return await transcoder_client.test_connection()


class WebhookTestRequest(BaseModel):
    webhook_secret: str = ""


@router.post("/settings/transcoder/test-webhook")
async def test_transcoder_webhook(body: WebhookTestRequest):
    return await transcoder_client.test_webhook(body.webhook_secret)


def _drive_capabilities(d) -> list[str]:
    """Extract capability labels from a drive object."""
    caps = []
    for attr, label in (("read_cd", "CD"), ("read_dvd", "DVD"), ("read_bd", "BD"), ("uhd_capable", "UHD")):
        if getattr(d, attr, False):
            caps.append(label)
    return caps


@router.get("/settings/system-info")
async def get_system_info():
    """Gather system info: versions, paths, database, drives."""
    arm_versions = await arm_client.get_version()
    tc_health = await transcoder_client.health()

    # UI version from local VERSION file
    ui_version_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "VERSION")

    def _read_version() -> str:
        try:
            with open(ui_version_file) as f:
                return f.read().strip()
        except OSError:
            return "unknown"

    ui_version = await asyncio.to_thread(_read_version)
    tc_version = tc_health.get("version") if tc_health else None

    versions = {
        "arm": arm_versions.get("arm_version", "unknown") if arm_versions else "offline",
        "makemkv": arm_versions.get("makemkv_version", "unknown") if arm_versions else "offline",
        "transcoder": tc_version or ("offline" if not tc_health else "unknown"),
        "ui": ui_version,
    }

    db_path = app_settings.arm_db_path
    drive_list = [
        {
            "name": d.name, "mount": d.mount, "maker": d.maker,
            "model": d.model, "capabilities": _drive_capabilities(d),
            "firmware": d.firmware,
        }
        for d in arm_db.get_drives()
    ]

    return {
        "versions": versions,
        "endpoints": {
            "arm": {"url": app_settings.arm_url, "reachable": arm_versions is not None},
            "transcoder": {"url": app_settings.transcoder_url, "reachable": tc_health is not None},
        },
        "paths": await arm_client.get_paths() or [],
        "database": {
            "path": db_path,
            "size_bytes": os.path.getsize(db_path) if os.path.isfile(db_path) else None,
            "available": arm_db.is_available(),
        },
        "drives": drive_list,
    }


class MaintenanceJobRequest(BaseModel):
    job_id: int


def _path_is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _resolve_raw_root() -> Path:
    cfg = arm_db.get_all_config_safe() or {}
    raw = cfg.get("RAW_PATH") or "/home/arm/media/raw"
    return Path(str(raw)).resolve()


@router.get("/settings/maintenance/failed-jobs")
async def list_failed_jobs():
    failed_statuses = {"failed", "error", "cancelled", "abandoned"}
    rows = []
    try:
        with arm_db.get_session() as session:
            stmt = (
                select(Job)
                .where(Job.status.is_not(None))
                .order_by(Job.start_time.desc())
                .limit(100)
            )
            for job in session.scalars(stmt).all():
                status = (job.status or "").lower()
                if status not in failed_statuses:
                    continue
                rows.append(
                    {
                        "job_id": job.job_id,
                        "status": job.status,
                        "title": job.title or job.title_manual or job.title_auto or job.label,
                        "label": job.label,
                        "raw_path": job.raw_path,
                        "logfile": job.logfile,
                        "start_time": job.start_time.isoformat() if job.start_time else None,
                    }
                )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to query failed jobs: {exc}") from exc
    return {"jobs": rows}


@router.post("/settings/maintenance/rescan-drives")
async def maintenance_rescan_drives():
    result = await arm_client.rescan_drives()
    if result is None:
        raise HTTPException(status_code=502, detail="ARM service unreachable")
    if not result.get("success", True):
        raise HTTPException(status_code=400, detail=result.get("error", "Drive rescan failed"))
    return result


@router.post("/settings/maintenance/clear-job")
async def maintenance_clear_job(body: MaintenanceJobRequest):
    try:
        with arm_db.get_rw_session() as session:
            job = session.get(Job, body.job_id)
            if not job:
                raise HTTPException(status_code=404, detail=f"Job {body.job_id} not found")

            title = job.title or job.title_manual or job.title_auto or job.label

            # Clear drive references to this job before delete.
            for drive in session.scalars(
                select(SystemDrives).where(
                    or_(
                        SystemDrives.job_id_current == body.job_id,
                        SystemDrives.job_id_previous == body.job_id,
                    )
                )
            ).all():
                if drive.job_id_current == body.job_id:
                    drive.job_id_current = None
                if drive.job_id_previous == body.job_id:
                    drive.job_id_previous = None

            session.query(Track).filter(Track.job_id == body.job_id).delete(synchronize_session=False)
            session.query(Config).filter(Config.job_id == body.job_id).delete(synchronize_session=False)
            session.delete(job)
            session.commit()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to clear job: {exc}") from exc

    return {"success": True, "job_id": body.job_id, "title": title}


@router.post("/settings/maintenance/delete-job-logs")
async def maintenance_delete_job_logs(body: MaintenanceJobRequest):
    removed: list[str] = []
    missing: list[str] = []
    try:
        with arm_db.get_session() as session:
            job = session.get(Job, body.job_id)
            if not job:
                raise HTTPException(status_code=404, detail=f"Job {body.job_id} not found")
            logfile = job.logfile

        root = Path(app_settings.arm_log_path).resolve()
        progress = (root / "progress").resolve()
        candidates: list[Path] = []

        if logfile:
            lf = Path(logfile)
            if lf.is_absolute():
                candidates.append(lf)
            else:
                candidates.append(root / lf)
                candidates.append(progress / lf)
        candidates.append(progress / f"{body.job_id}.log")

        seen = set()
        for candidate in candidates:
            resolved = candidate.resolve()
            if str(resolved) in seen:
                continue
            seen.add(str(resolved))

            if not (_path_is_within(resolved, root) or _path_is_within(resolved, progress)):
                continue
            if resolved.exists() and resolved.is_file():
                resolved.unlink()
                removed.append(str(resolved))
            else:
                missing.append(str(resolved))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to delete logs: {exc}") from exc

    return {"success": True, "job_id": body.job_id, "removed": removed, "missing": missing}


@router.post("/settings/maintenance/delete-job-raw")
async def maintenance_delete_job_raw(body: MaintenanceJobRequest):
    try:
        with arm_db.get_session() as session:
            job = session.get(Job, body.job_id)
            if not job:
                raise HTTPException(status_code=404, detail=f"Job {body.job_id} not found")
            raw_path = job.raw_path
            title = job.title or job.title_manual or job.title_auto or job.label

        if not raw_path:
            return {"success": True, "job_id": body.job_id, "deleted": False, "reason": "No raw path recorded"}

        root = _resolve_raw_root()
        target = Path(raw_path).resolve()
        if not _path_is_within(target, root):
            raise HTTPException(
                status_code=400,
                detail=f"Raw path is outside RAW_PATH root (raw={target}, root={root})",
            )

        if target.exists():
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
            return {"success": True, "job_id": body.job_id, "deleted": True, "path": str(target), "title": title}
        return {"success": True, "job_id": body.job_id, "deleted": False, "path": str(target), "reason": "Path not found"}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to delete raw output: {exc}") from exc
