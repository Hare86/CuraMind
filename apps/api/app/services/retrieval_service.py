"""
Retrieval service — resolves knowledge base collections and coordinates hybrid search.
"""
from uuid import UUID

from qdrant_client import AsyncQdrantClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.db.models.knowledge_base import KnowledgeBase
from app.rag.hybrid_search import HybridSearchEngine, RetrievedChunk
from app.services.embedding_service import EmbeddingService


class RetrievalService:
    """
    Resolves which Qdrant collections to query, then delegates to HybridSearchEngine.
    Supports multi-KB search and automatic KB recommendation.
    """

    def __init__(
        self,
        db: AsyncSession,
        qdrant_client: AsyncQdrantClient,
        embedding_service: EmbeddingService,
    ):
        self._db = db
        self._search_engine = HybridSearchEngine(qdrant_client)
        self._embedding_service = embedding_service

    async def retrieve(
        self,
        query: str,
        kb_ids: list[UUID] | None,
        user_id: str | None,
        top_k: int = None,
    ) -> tuple[list[RetrievedChunk], list[str]]:
        """
        Returns (chunks, collection_names_searched).
        If kb_ids is None, searches all accessible KBs.
        """
        top_k = top_k or settings.RETRIEVAL_TOP_K

        collection_names = await self._resolve_collections(kb_ids, user_id)
        if not collection_names:
            return [], []

        dense_vector = await self._embedding_service.embed_query(query)
        sparse_indices, sparse_values = self._embedding_service.compute_sparse_vector(query)

        all_chunks: list[RetrievedChunk] = []
        for collection in collection_names:
            try:
                chunks = await self._search_engine.search(
                    collection_name=collection,
                    dense_vector=dense_vector,
                    sparse_indices=sparse_indices,
                    sparse_values=sparse_values,
                    top_k=top_k,
                )
                all_chunks.extend(chunks)
            except Exception:
                continue

        # Global re-sort by score across collections
        all_chunks.sort(key=lambda c: c.score, reverse=True)
        return all_chunks[:top_k], collection_names

    async def _resolve_collections(
        self, kb_ids: list[UUID] | None, user_id: str | None
    ) -> list[str]:
        if kb_ids:
            result = await self._db.execute(
                select(KnowledgeBase.qdrant_collection).where(
                    KnowledgeBase.id.in_(kb_ids)
                )
            )
            return [row[0] for row in result.fetchall()]

        # No specific KBs — return all public + user's own
        stmt = select(KnowledgeBase.qdrant_collection).where(KnowledgeBase.is_public.is_(True))
        if user_id:
            from sqlalchemy import or_
            stmt = select(KnowledgeBase.qdrant_collection).where(
                or_(
                    KnowledgeBase.is_public.is_(True),
                    KnowledgeBase.owner_id == UUID(user_id),
                )
            )

        result = await self._db.execute(stmt)
        return [row[0] for row in result.fetchall()]
