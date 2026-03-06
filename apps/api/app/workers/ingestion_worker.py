"""
Celery tasks for document ingestion pipeline.
Tasks are fire-and-forget from the API, tracked via document status in DB.
"""
import uuid

from app.workers.celery_app import celery_app


@celery_app.task(
    name="app.workers.ingestion_worker.ingest_document_task",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def ingest_document_task(self, document_id: str, kb_id: str) -> dict:
    """
    Triggered after a document is uploaded.
    Runs the full ingestion pipeline synchronously within the worker.
    """
    import asyncio
    from qdrant_client import AsyncQdrantClient

    from app.core.config import settings
    from app.db.base import AsyncSessionLocal
    from app.services.embedding_service import get_embedding_service
    from app.services.ingestion_service import IngestionService

    async def _run():
        qdrant_client = AsyncQdrantClient(
            host=settings.QDRANT_HOST, port=settings.QDRANT_PORT
        )
        embedding_service = get_embedding_service()

        async with AsyncSessionLocal() as db:
            service = IngestionService(
                db=db,
                qdrant_client=qdrant_client,
                embedding_service=embedding_service,
            )
            await service.ingest_document(uuid.UUID(document_id))

        await qdrant_client.close()
        return {"status": "completed", "document_id": document_id}

    try:
        return asyncio.get_event_loop().run_until_complete(_run())
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(
    name="app.workers.ingestion_worker.ingest_url_task",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def ingest_url_task(self, url: str, kb_id: str, submission_id: str | None = None) -> dict:
    """
    Scrape a URL using Firecrawl, then ingest the extracted text.
    """
    import asyncio
    import tempfile
    import os
    from pathlib import Path

    async def _run():
        from app.core.config import settings

        # Scrape with Firecrawl
        scraped_text = await _scrape_url(url)
        if not scraped_text:
            return {"status": "failed", "reason": "No content scraped"}

        # Save to temp file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write(scraped_text)
            temp_path = f.name

        # Create document record and ingest
        from qdrant_client import AsyncQdrantClient
        from app.db.base import AsyncSessionLocal
        from app.db.models.document import Document
        from app.services.embedding_service import get_embedding_service
        from app.services.ingestion_service import IngestionService

        qdrant_client = AsyncQdrantClient(
            host=settings.QDRANT_HOST, port=settings.QDRANT_PORT
        )

        async with AsyncSessionLocal() as db:
            doc = Document(
                kb_id=uuid.UUID(kb_id),
                filename=url,
                file_path=temp_path,
                file_type="txt",
                status="pending",
                doc_metadata={"source_url": url, "submission_id": submission_id},
            )
            db.add(doc)
            await db.flush()

            service = IngestionService(
                db=db,
                qdrant_client=qdrant_client,
                embedding_service=get_embedding_service(),
            )
            await service.ingest_document(doc.id)

        await qdrant_client.close()
        os.unlink(temp_path)
        return {"status": "completed", "url": url}

    try:
        return asyncio.get_event_loop().run_until_complete(_run())
    except Exception as exc:
        raise self.retry(exc=exc)


async def _scrape_url(url: str) -> str | None:
    """Scrape URL content using Firecrawl API."""
    import httpx
    from app.core.config import settings

    if not settings.FIRECRAWL_API_KEY:
        # Fallback: plain HTTP scrape
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            return response.text

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://api.firecrawl.dev/v1/scrape",
            headers={"Authorization": f"Bearer {settings.FIRECRAWL_API_KEY}"},
            json={"url": url, "formats": ["markdown"]},
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("data", {}).get("markdown", "")
    return None
