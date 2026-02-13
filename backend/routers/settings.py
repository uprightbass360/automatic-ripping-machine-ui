import json
import logging
import os

from fastapi import APIRouter, HTTPException
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
    arm_resp = await arm_client.get_config()
    if arm_resp:
        arm_config = arm_resp.get("config")
        arm_metadata = arm_resp.get("comments")
    if not arm_config:
        arm_config = arm_db.get_all_config_safe()

    # HandBrake presets from init container
    arm_handbrake_presets = _read_hb_presets()

    # ARM GPU support
    arm_gpu_support = await arm_client.get_gpu_support()

    # Transcoder config + GPU support
    transcoder_config = None
    transcoder_gpu_support = None

    tc_config_resp = await transcoder_client.get_config()
    if tc_config_resp:
        transcoder_config = tc_config_resp

    health = await transcoder_client.health()
    if health:
        transcoder_gpu_support = health.get("gpu_support")
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
        transcoder_config=transcoder_config,
        arm_gpu_support=arm_gpu_support,
        transcoder_gpu_support=transcoder_gpu_support,
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


@router.patch("/settings/transcoder")
async def update_transcoder_config(body: dict):
    result = await transcoder_client.update_config(body)
    if result is None:
        raise HTTPException(status_code=502, detail="Transcoder service unreachable")
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("detail", "Unknown error"))
    return result
