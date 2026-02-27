import asyncio

from fastapi import APIRouter

from backend.models.schemas import DashboardResponse, HardwareInfoSchema, JobSchema, SystemStatsSchema
from backend.services import arm_client, arm_db, transcoder_client, system_cache

router = APIRouter(prefix="/api", tags=["dashboard"])


async def _fetch_transcoder() -> tuple[bool, dict | None, list]:
    """Fetch transcoder health, stats, and active jobs concurrently."""
    health = await transcoder_client.health()
    if not health:
        return False, None, []

    stats, jobs_data = await asyncio.gather(
        transcoder_client.get_stats(),
        transcoder_client.get_jobs(status="processing"),
    )
    active = jobs_data["jobs"] if jobs_data and "jobs" in jobs_data else []
    return True, stats, active


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard():
    db_available = arm_db.is_available()

    # Skip DB queries entirely when database is unavailable
    active_jobs: list = []
    drives_online = 0
    drive_names: dict[str, str] = {}
    notification_count = 0

    ripping_paused = False

    if db_available:
        active_jobs = arm_db.get_active_jobs()
        drives = arm_db.get_drives()
        drives_online = len(drives)
        # Normalize mount paths — drives store /mnt/dev/sr0, jobs store /dev/sr0
        drive_names = {}
        for d in drives:
            if d.mount and d.name:
                drive_names[d.mount] = d.name
                # Also map the bare /dev/srX form
                basename = d.mount.rsplit("/", 1)[-1]
                drive_names[f"/dev/{basename}"] = d.name
        notification_count = arm_db.get_notification_count()
        ripping_paused = arm_db.get_ripping_paused()

    # Transcoder + ARM system stats in parallel
    transcoder_task = asyncio.create_task(_fetch_transcoder())
    stats_task = asyncio.create_task(arm_client.get_system_stats())
    transcoder_stats_task = asyncio.create_task(transcoder_client.get_system_stats())

    transcoder_online, transcoder_stats, active_transcodes = await transcoder_task

    system_stats: SystemStatsSchema | None = None
    stats_data = await stats_task
    if stats_data:
        system_stats = SystemStatsSchema(**stats_data)

    transcoder_system_stats: SystemStatsSchema | None = None
    transcoder_stats_data = await transcoder_stats_task
    if transcoder_stats_data:
        transcoder_system_stats = SystemStatsSchema(**transcoder_stats_data)

    arm_hw = system_cache.get_arm_info()
    transcoder_hw = system_cache.get_transcoder_info()

    arm_online = stats_data is not None

    return DashboardResponse(
        db_available=db_available,
        arm_online=arm_online,
        active_jobs=[JobSchema(**j) for j in active_jobs],
        system_info=HardwareInfoSchema(**arm_hw) if arm_hw else None,
        drives_online=drives_online,
        drive_names=drive_names,
        notification_count=notification_count,
        ripping_enabled=not ripping_paused,
        transcoder_online=transcoder_online,
        transcoder_stats=transcoder_stats,
        transcoder_system_stats=transcoder_system_stats,
        active_transcodes=active_transcodes,
        system_stats=system_stats,
        transcoder_info=HardwareInfoSchema(**transcoder_hw) if transcoder_hw else None,
    )
