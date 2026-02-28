import json
import logging
import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.config import settings as app_settings
from backend.models.schemas import SettingsResponse
from backend.services import arm_client, arm_db, metadata, transcoder_client

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


@router.put("/settings/arm")
async def update_arm_config(body: ArmConfigUpdate):
    result = await arm_client.update_config(body.config)
    if result is None:
        raise HTTPException(status_code=502, detail="ARM service unreachable")
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
    return result


@router.get("/settings/test-metadata")
async def test_metadata_key():
    """Test the currently saved metadata API key by making a real API call."""
    return await metadata.test_configured_key()


@router.patch("/settings/transcoder")
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


@router.get("/settings/system-info")
async def get_system_info():
    """Gather system info: versions, paths, database, drives."""
    # Versions
    arm_versions = await arm_client.get_version()

    tc_health = await transcoder_client.health()
    transcoder_version = None
    if tc_health:
        transcoder_version = tc_health.get("version")

    # UI version from local VERSION file
    ui_version = "unknown"
    ui_version_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "VERSION")
    try:
        with open(ui_version_file) as f:
            ui_version = f.read().strip()
    except OSError:
        pass

    versions = {
        "arm": arm_versions.get("arm_version", "unknown") if arm_versions else "offline",
        "makemkv": arm_versions.get("makemkv_version", "unknown") if arm_versions else "offline",
        "transcoder": transcoder_version or ("offline" if not tc_health else "unknown"),
        "ui": ui_version,
    }

    # Paths — delegate to ARM container (paths only exist there)
    paths = await arm_client.get_paths() or []

    # Database
    db_path = app_settings.arm_db_path
    db_info = {
        "path": db_path,
        "size_bytes": os.path.getsize(db_path) if os.path.isfile(db_path) else None,
        "available": arm_db.is_available(),
    }

    # Drives
    drives = arm_db.get_drives()
    drive_list = []
    for d in drives:
        caps = []
        if getattr(d, 'read_cd', False): caps.append('CD')
        if getattr(d, 'read_dvd', False): caps.append('DVD')
        if getattr(d, 'read_bd', False): caps.append('BD')
        if getattr(d, 'uhd_capable', False): caps.append('UHD')
        drive_list.append({
            "name": d.name,
            "mount": d.mount,
            "maker": d.maker,
            "model": d.model,
            "capabilities": caps,
            "firmware": d.firmware,
        })

    endpoints = {
        "arm": {"url": app_settings.arm_url, "reachable": arm_versions is not None},
        "transcoder": {"url": app_settings.transcoder_url, "reachable": tc_health is not None},
    }

    return {
        "versions": versions,
        "endpoints": endpoints,
        "paths": paths,
        "database": db_info,
        "drives": drive_list,
    }
