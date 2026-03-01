from typing import Any

from fastapi import APIRouter, HTTPException

from backend.models.schemas import NotificationSchema
from backend.services import arm_client, arm_db

router = APIRouter(prefix="/api", tags=["notifications"])


@router.get("/notifications", response_model=list[NotificationSchema])
def list_notifications():
    notifications = arm_db.get_notifications()
    return [NotificationSchema.model_validate(n) for n in notifications]


@router.patch("/notifications/{notify_id}")
async def dismiss_notification(notify_id: int) -> dict[str, Any]:
    """Mark a notification as read (proxies to ARM)."""
    result = await arm_client.dismiss_notification(notify_id)
    if result is None:
        raise HTTPException(status_code=503, detail="ARM web UI is unreachable")
    if isinstance(result, dict) and result.get("success") is False:
        detail = result.get("message") or "Failed to dismiss notification"
        raise HTTPException(status_code=502, detail=detail)
    return result
