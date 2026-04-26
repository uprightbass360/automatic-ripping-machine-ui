from typing import Any

from fastapi import APIRouter, HTTPException

from backend.models.schemas import NotificationSchema
from backend.services import arm_client

router = APIRouter(prefix="/api", tags=["notifications"])


@router.get("/notifications", response_model=list[NotificationSchema])
async def list_notifications():
    resp = await arm_client.get_notifications()
    if resp is None:
        raise HTTPException(status_code=503, detail="ARM web UI is unreachable")
    notifications = resp.get("notifications") or []
    return [NotificationSchema.model_validate(n) for n in notifications]


@router.patch("/notifications/{notify_id}", responses={502: {"description": "Failed to dismiss notification"}, 503: {"description": "ARM web UI is unreachable"}})
async def dismiss_notification(notify_id: int) -> dict[str, Any]:
    """Mark a notification as read (proxies to ARM)."""
    result = await arm_client.dismiss_notification(notify_id)
    if result is None:
        raise HTTPException(status_code=503, detail="ARM web UI is unreachable")
    if isinstance(result, dict) and result.get("success") is False:
        detail = result.get("message") or "Failed to dismiss notification"
        raise HTTPException(status_code=502, detail=detail)
    return result
