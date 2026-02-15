from fastapi import APIRouter, HTTPException

from backend.models.schemas import DriveUpdateRequest
from backend.services import arm_db, arm_client

router = APIRouter(prefix="/api", tags=["drives"])


@router.get("/drives")
def list_drives():
    return arm_db.get_drives_with_jobs()


@router.patch("/drives/{drive_id}")
async def update_drive(drive_id: int, body: DriveUpdateRequest):
    data = body.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = await arm_client.update_drive(drive_id, data)
    if result is None:
        raise HTTPException(status_code=502, detail="ARM unreachable")
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Update failed"))
    return result
