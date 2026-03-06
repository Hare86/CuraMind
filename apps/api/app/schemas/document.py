from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: UUID
    kb_id: UUID
    filename: str
    file_type: str
    status: str
    page_count: int | None
    chunk_count: int | None
    error_message: str | None
    created_at: datetime
    processed_at: datetime | None

    model_config = {"from_attributes": True}
