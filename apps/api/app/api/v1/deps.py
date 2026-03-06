"""
FastAPI dependency factories for services that require DB + external clients.
Using factories instead of global singletons enables proper async lifecycle management.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.rag.pipeline import RAGPipeline
from app.services.embedding_service import get_embedding_service
from app.services.query_service import QueryService
from app.services.retrieval_service import RetrievalService
from app.services.safety_service import SafetyService


def get_qdrant_client():
    from qdrant_client import AsyncQdrantClient
    return AsyncQdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)


def get_retrieval_service(db: AsyncSession) -> RetrievalService:
    return RetrievalService(
        db=db,
        qdrant_client=get_qdrant_client(),
        embedding_service=get_embedding_service(),
    )


def get_rag_pipeline(db: AsyncSession) -> RAGPipeline:
    from app.rag.hybrid_search import HybridSearchEngine
    return RAGPipeline(
        embedding_service=get_embedding_service(),
        search_engine=HybridSearchEngine(get_qdrant_client()),
        safety_service=SafetyService(),
        reranker_enabled=False,
    )


def get_query_service(db: AsyncSession) -> QueryService:
    return QueryService(
        pipeline=get_rag_pipeline(db),
        retrieval_service=get_retrieval_service(db),
    )
