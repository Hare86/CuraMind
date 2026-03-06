from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: UUID
    message: str
    notification_type: str
    is_read: bool
    reference_id: UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}
