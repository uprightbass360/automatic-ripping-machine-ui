from fastapi import APIRouter

from backend.models.schemas import SettingsResponse
from backend.services import arm_db, transcoder_client

router = APIRouter(prefix="/api", tags=["settings"])


@router.get("/settings", response_model=SettingsResponse)
async def get_settings():
    arm_config = arm_db.get_all_config_safe()

    transcoder_config = None
    stats = await transcoder_client.get_stats()
    if stats:
        transcoder_config = stats

    return SettingsResponse(
        arm_config=arm_config,
        transcoder_config=transcoder_config,
    )
