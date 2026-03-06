from pydantic import BaseModel


class Citation(BaseModel):
    index: int
    document_title: str
    page_number: int | None = None
    source_url: str | None = None
    kb_name: str | None = None
    chunk_excerpt: str | None = None
    relevance_score: float | None = None
