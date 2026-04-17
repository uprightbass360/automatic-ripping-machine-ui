import asyncio
import json
import logging
import os
from typing import NoReturn

from fastapi import APIRouter, HTTPException
import httpx
from pydantic import BaseModel

from backend.config import settings as app_settings
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


class AbcdeConfigUpdate(BaseModel):
    content: str


@router.get("/settings/abcde")
async def get_abcde_config():
    result = await arm_client.get_abcde_config()
    if result is None:
        raise HTTPException(status_code=502, detail="ARM service unreachable")
    return result


@router.put("/settings/abcde", responses={400: {"description": "Invalid request"}, 502: {"description": "ARM service unreachable"}})
async def update_abcde_config(body: AbcdeConfigUpdate):
    result = await arm_client.update_abcde_config(body.content)
    if result is None:
        raise HTTPException(status_code=502, detail="ARM service unreachable")
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
    return result


@router.get("/settings/test-metadata")
async def test_metadata_key(key: str | None = None, provider: str | None = None):
    """Test a metadata API key (proxied through ARM). Tests the field value if provided, else saved config."""
    try:
        return await arm_client.test_metadata_key(key=key, provider=provider)
    except httpx.HTTPStatusError as exc:
        log.warning("Metadata key test failed: %d", exc.response.status_code)
        upstream_msg = "Metadata key test failed"
        try:
            body = exc.response.json()
            if body.get("detail"):
                upstream_msg = body["detail"]
        except Exception:
            pass
        return {"success": False, "message": upstream_msg, "provider": "unknown"}
    except (httpx.HTTPError, httpx.ConnectError, RuntimeError, OSError) as exc:
        log.error("Metadata key test unreachable: %s", exc)
        return {"success": False, "message": "ARM service unreachable", "provider": "unknown"}


@router.get("/settings/transcoder/scheme")
async def get_transcoder_scheme():
    result = await transcoder_client.get_scheme()
    if result is None:
        raise HTTPException(status_code=502, detail="Transcoder service unreachable")
    return result


@router.get("/settings/transcoder/presets")
async def get_transcoder_presets():
    result = await transcoder_client.get_presets()
    if result is None:
        raise HTTPException(status_code=502, detail="Transcoder service unreachable")
    return result


def _raise_from_http_status_error(exc: httpx.HTTPStatusError) -> NoReturn:
    """Re-raise an httpx HTTPStatusError as a FastAPI HTTPException, forwarding detail."""
    detail = "Preset operation failed"
    try:
        detail = exc.response.json().get("detail", detail)
    except Exception:
        pass
    raise HTTPException(status_code=exc.response.status_code, detail=detail)


@router.post("/settings/transcoder/presets", status_code=201,
             responses={409: {"description": "Slug conflict"}, 502: {"description": "Transcoder unreachable"}})
async def create_transcoder_preset(body: dict):
    try:
        result = await transcoder_client.create_preset(body)
    except httpx.HTTPStatusError as exc:
        _raise_from_http_status_error(exc)
    if result is None:
        raise HTTPException(status_code=502, detail="Transcoder service unreachable")
    return result


@router.patch("/settings/transcoder/presets/{slug}",
              responses={404: {"description": "Preset not found"}, 502: {"description": "Transcoder unreachable"}})
async def update_transcoder_preset(slug: str, body: dict):
    try:
        result = await transcoder_client.update_preset(slug, body)
    except httpx.HTTPStatusError as exc:
        _raise_from_http_status_error(exc)
    if result is None:
        raise HTTPException(status_code=502, detail="Transcoder service unreachable")
    return result


@router.delete("/settings/transcoder/presets/{slug}",
               responses={404: {"description": "Preset not found"}, 502: {"description": "Transcoder unreachable"}})
async def delete_transcoder_preset(slug: str):
    try:
        result = await transcoder_client.delete_preset(slug)
    except httpx.HTTPStatusError as exc:
        _raise_from_http_status_error(exc)
    if result is None:
        raise HTTPException(status_code=502, detail="Transcoder service unreachable")
    return result


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

    # DB migration info from ARM
    db_version = arm_versions.get("db_version", "unknown") if arm_versions else "offline"
    db_head = arm_versions.get("db_head", "unknown") if arm_versions else "offline"
    db_up_to_date = db_version == db_head if (db_version not in ("unknown", "offline") and db_head not in ("unknown", "offline")) else None

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
            "migration_current": db_version,
            "migration_head": db_head,
            "up_to_date": db_up_to_date,
        },
        "drives": drive_list,
    }
