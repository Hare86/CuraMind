"""
Hybrid search combining dense (BGE-large) and sparse (BM25 keyword) vectors in Qdrant.

Final score = 0.7 * vector_similarity + 0.3 * sparse_score

Uses Qdrant's Query API with Reciprocal Rank Fusion (RRF) for combining results,
weighted to match the 0.7/0.3 split.
"""
from dataclasses import dataclass

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    NamedSparseVector,
    NamedVector,
    QueryRequest,
    SparseVector,
)

from app.core.config import settings


@dataclass
class RetrievedChunk:
    chunk_id: str
    content: str
    document_title: str
    document_id: str
    kb_id: str
    page_number: int | None
    score: float
    source_url: str | None = None
    kb_name: str | None = None


class HybridSearchEngine:
    """
    Combines dense and sparse vector retrieval from Qdrant.

    Implements the Interface Segregation Principle — callers depend on
    search(query_vector, sparse_vector, collection, top_k) only.
    """

    DENSE_VECTOR_NAME = "dense"
    SPARSE_VECTOR_NAME = "sparse"

    def __init__(self, client: AsyncQdrantClient):
        self._client = client

    async def search(
        self,
        collection_name: str,
        dense_vector: list[float],
        sparse_indices: list[int],
        sparse_values: list[float],
        top_k: int = 10,
        score_threshold: float = 0.0,
    ) -> list[RetrievedChunk]:
        """
        Performs hybrid search and returns deduplicated, ranked chunks.
        """
        # Run dense and sparse searches in parallel
        dense_results, sparse_results = await self._run_parallel_searches(
            collection_name=collection_name,
            dense_vector=dense_vector,
            sparse_indices=sparse_indices,
            sparse_values=sparse_values,
            top_k=top_k * 2,  # Over-fetch for fusion
        )

        fused = self._reciprocal_rank_fusion(
            dense_results=dense_results,
            sparse_results=sparse_results,
            dense_weight=settings.HYBRID_VECTOR_WEIGHT,
            sparse_weight=settings.HYBRID_SPARSE_WEIGHT,
        )

        return [c for c in fused[:top_k] if c.score >= score_threshold]

    async def _run_parallel_searches(
        self,
        collection_name: str,
        dense_vector: list[float],
        sparse_indices: list[int],
        sparse_values: list[float],
        top_k: int,
    ) -> tuple[list, list]:
        import asyncio

        dense_task = self._client.search(
            collection_name=collection_name,
            query_vector=NamedVector(name=self.DENSE_VECTOR_NAME, vector=dense_vector),
            limit=top_k,
            with_payload=True,
        )
        sparse_task = self._client.search(
            collection_name=collection_name,
            query_vector=NamedSparseVector(
                name=self.SPARSE_VECTOR_NAME,
                vector=SparseVector(indices=sparse_indices, values=sparse_values),
            ),
            limit=top_k,
            with_payload=True,
        )

        results = await asyncio.gather(dense_task, sparse_task, return_exceptions=True)

        dense_results = results[0] if not isinstance(results[0], Exception) else []
        sparse_results = results[1] if not isinstance(results[1], Exception) else []

        return dense_results, sparse_results

    def _reciprocal_rank_fusion(
        self,
        dense_results: list,
        sparse_results: list,
        dense_weight: float,
        sparse_weight: float,
        k: int = 60,
    ) -> list[RetrievedChunk]:
        """
        Weighted RRF — higher weight on dense results to match 0.7/0.3 formula.
        """
        scores: dict[str, float] = {}
        payloads: dict[str, dict] = {}

        for rank, hit in enumerate(dense_results):
            point_id = str(hit.id)
            scores[point_id] = scores.get(point_id, 0.0) + dense_weight * (1.0 / (k + rank + 1))
            payloads[point_id] = hit.payload or {}

        for rank, hit in enumerate(sparse_results):
            point_id = str(hit.id)
            scores[point_id] = scores.get(point_id, 0.0) + sparse_weight * (1.0 / (k + rank + 1))
            if point_id not in payloads:
                payloads[point_id] = hit.payload or {}

        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

        chunks = []
        for point_id in sorted_ids:
            payload = payloads[point_id]
            chunks.append(
                RetrievedChunk(
                    chunk_id=point_id,
                    content=payload.get("content", ""),
                    document_title=payload.get("document_title", "Unknown"),
                    document_id=payload.get("document_id", ""),
                    kb_id=payload.get("kb_id", ""),
                    page_number=payload.get("page_number"),
                    score=scores[point_id],
                    source_url=payload.get("source_url"),
                    kb_name=payload.get("kb_name"),
                )
            )

        return chunks
