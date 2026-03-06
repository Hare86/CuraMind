from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class FeedbackCreate(BaseModel):
    query_text: str
    response_text: str
    kb_id: UUID | None = None
    rating: Literal["useful", "incorrect", "needs_review"]
    comment: str | None = None
    query_mode: str | None = None


class FeedbackResponse(BaseModel):
    id: UUID
    rating: str
    comment: str | None
    query_mode: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
