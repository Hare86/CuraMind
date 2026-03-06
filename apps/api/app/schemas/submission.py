from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, HttpUrl


class SourceSubmissionCreate(BaseModel):
    submission_type: str  # url | document
    url: str | None = None
    title: str | None = None


class SourceSubmissionResponse(BaseModel):
    id: UUID
    submission_type: str
    url: str | None
    title: str | None
    summary: str | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
