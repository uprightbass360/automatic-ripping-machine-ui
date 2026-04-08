from fastapi import APIRouter, HTTPException

from backend.models.schemas import DriveUpdateRequest
from backend.services import arm_db, arm_client

router = APIRouter(prefix="/api", tags=["drives"])


@router.get("/drives")
def list_drives():
    return arm_db.get_drives_with_jobs()


@router.post("/drives/rescan", responses={502: {"description": "ARM unreachable"}})
async def rescan_drives():
    """Re-detect optical drives and update the database."""
    result = await arm_client.rescan_drives()
    if result is None:
        raise HTTPException(status_code=502, detail="ARM unreachable")
    return result


@router.get("/drives/diagnostic", responses={502: {"description": "ARM unreachable"}})
async def drive_diagnostic():
    result = await arm_client.drive_diagnostic()
    if result is None:
        raise HTTPException(status_code=502, detail="ARM unreachable")
    return result


@router.delete("/drives/{drive_id}", responses={404: {"description": "Drive not found"}, 409: {"description": "Drive has active job"}, 502: {"description": "ARM unreachable"}})
async def delete_drive(drive_id: int):
    result = await arm_client.delete_drive(drive_id)
    if result is None:
        raise HTTPException(status_code=502, detail="ARM unreachable")
    if not result.get("success"):
        error = result.get("error", "Delete failed")
        status = 409 if "active" in error.lower() else 404
        raise HTTPException(status_code=status, detail=error)
    return result


@router.post("/drives/{drive_id}/scan", responses={404: {"description": "Drive not found"}, 502: {"description": "ARM unreachable"}})
async def scan_drive(drive_id: int):
    result = await arm_client.scan_drive(drive_id)
    if result is None:
        raise HTTPException(status_code=502, detail="ARM unreachable")
    if not result.get("success"):
        status = 404 if "not found" in result.get("error", "").lower() else 400
        raise HTTPException(status_code=status, detail=result.get("error", "Scan failed"))
    return result


@router.post("/drives/{drive_id}/eject", responses={404: {"description": "Drive not found"}, 502: {"description": "ARM unreachable"}})
async def eject_drive(drive_id: int, method: str = "toggle"):
    """Eject, close, or toggle the drive tray."""
    result = await arm_client.eject_drive(drive_id, method)
    if result is None:
        raise HTTPException(status_code=502, detail="ARM unreachable")
    if not result.get("success"):
        status = 404 if "not found" in result.get("error", "").lower() else 500
        raise HTTPException(status_code=status, detail=result.get("error", "Eject failed"))
    return result


@router.patch("/drives/{drive_id}", responses={400: {"description": "No fields to update"}, 404: {"description": "Update failed"}, 502: {"description": "ARM unreachable"}})
async def update_drive(drive_id: int, body: DriveUpdateRequest):
    data = body.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = await arm_client.update_drive(drive_id, data)
    if result is None:
        raise HTTPException(status_code=502, detail="ARM unreachable")
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Update failed"))
    return result
