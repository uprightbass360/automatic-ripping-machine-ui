from fastapi import APIRouter

from backend.services import arm_db

router = APIRouter(prefix="/api", tags=["drives"])


@router.get("/drives")
def list_drives():
    return arm_db.get_drives_with_jobs()
