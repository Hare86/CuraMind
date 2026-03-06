from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class KnowledgeBaseCreate(BaseModel):
    name: str = Field(min_length=2, max_length=256)
    description: str | None = None
    category: str | None = None
    is_public: bool = False


class KnowledgeBaseResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    category: str | None
    is_public: bool
    document_count: int
    chunk_count: int
    owner_id: UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}
