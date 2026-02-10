from fastapi import APIRouter

from backend.models.schemas import DashboardResponse, JobSchema, SystemInfoSchema
from backend.services import arm_db, transcoder_client

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard():
    db_available = arm_db.is_available()

    # Skip DB queries entirely when database is unavailable
    active_jobs: list = []
    system_info = None
    drives_online = 0
    notification_count = 0

    if db_available:
        active_jobs = arm_db.get_active_jobs()
        system_info = arm_db.get_system_info()
        drives = arm_db.get_drives()
        drives_online = len(drives)
        notification_count = arm_db.get_notification_count()

    # Transcoder data (graceful degradation)
    transcoder_online = False
    transcoder_stats = None
    active_transcodes: list = []

    health = await transcoder_client.health()
    if health:
        transcoder_online = True
        transcoder_stats = await transcoder_client.get_stats()
        jobs_data = await transcoder_client.get_jobs(status="processing")
        if jobs_data and "jobs" in jobs_data:
            active_transcodes = jobs_data["jobs"]

    return DashboardResponse(
        db_available=db_available,
        active_jobs=[JobSchema.model_validate(j) for j in active_jobs],
        system_info=SystemInfoSchema.model_validate(system_info) if system_info else None,
        drives_online=drives_online,
        notification_count=notification_count,
        transcoder_online=transcoder_online,
        transcoder_stats=transcoder_stats,
        active_transcodes=active_transcodes,
    )
