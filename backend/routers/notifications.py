from fastapi import APIRouter

from backend.models.schemas import NotificationSchema
from backend.services import arm_db

router = APIRouter(prefix="/api", tags=["notifications"])


@router.get("/notifications", response_model=list[NotificationSchema])
def list_notifications():
    notifications = arm_db.get_notifications()
    return [NotificationSchema.model_validate(n) for n in notifications]
