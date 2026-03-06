from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ResearchArticleResponse(BaseModel):
    id: UUID
    title: str
    url: str
    source: str
    authors: str | None
    abstract: str | None
    summary: str | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ResearchApproveRequest(BaseModel):
    article_id: UUID
    approved: bool
    target_kb_id: UUID | None = None
    admin_notes: str | None = None
