"""
RAG Pipeline Orchestrator.

Flow:
  Query → Safety Check → Query Rewriting → Hybrid Retrieval
        → Reranking → Prompt Construction → Claude Generation
        → Citation Extraction → Response
"""
import uuid
from typing import AsyncGenerator

from app.core.config import settings
from app.rag.hybrid_search import HybridSearchEngine, RetrievedChunk
from app.rag.prompt_builder import build_rag_prompt
from app.rag.reranker import get_reranker
from app.schemas.citation import Citation
from app.schemas.query import QueryMode, QueryResponse
from app.services.embedding_service import EmbeddingService
from app.services.safety_service import SafetyService


class RAGPipeline:
    """
    Orchestrates the full RAG flow from user query to cited response.
    Follows Single Responsibility: each step is delegated to a focused service.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        search_engine: HybridSearchEngine,
        safety_service: SafetyService,
        reranker_enabled: bool = False,
    ):
        self._embedding_service = embedding_service
        self._search_engine = search_engine
        self._safety_service = safety_service
        self._reranker = get_reranker(reranker_enabled)

    async def run(
        self,
        query: str,
        mode: QueryMode,
        collection_names: list[str],
        top_k: int = None,
    ) -> QueryResponse:
        top_k = top_k or settings.RETRIEVAL_TOP_K

        # 1. Safety classification
        safety_result = await self._safety_service.classify(query)
        if not safety_result.is_allowed:
            return QueryResponse(
                answer=settings.SAFETY_BLOCKED_MESSAGE,
                citations=[],
                query_mode=mode,
                kb_ids_searched=[],
                was_blocked=True,
                query_id=str(uuid.uuid4()),
            )

        # 2. Query rewriting
        rewritten_query = await self._safety_service.rewrite_query(query)

        # 3. Embedding
        dense_vector = await self._embedding_service.embed_query(rewritten_query)
        sparse_indices, sparse_values = self._embedding_service.compute_sparse_vector(
            rewritten_query
        )

        # 4. Hybrid retrieval across all selected collections
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

        if not all_chunks:
            return QueryResponse(
                answer=settings.NO_RESULTS_MESSAGE,
                citations=[],
                query_mode=mode,
                kb_ids_searched=collection_names,
                retrieval_count=0,
                query_id=str(uuid.uuid4()),
            )

        # 5. Reranking
        reranked = self._reranker.rerank(
            query=rewritten_query,
            chunks=all_chunks,
            top_k=settings.RERANK_TOP_K,
        )

        # 6. Build context with citation indices
        context_chunks = [
            {
                "citation_index": idx + 1,
                "content": chunk.content,
                "document_title": chunk.document_title,
                "page_number": chunk.page_number,
                "source_url": chunk.source_url,
                "kb_name": chunk.kb_name,
                "chunk_id": chunk.chunk_id,
            }
            for idx, chunk in enumerate(reranked)
        ]

        # 7. Prompt construction + LLM generation
        system_prompt, user_prompt = build_rag_prompt(
            query=query,
            mode=mode,
            context_chunks=context_chunks,
        )
        answer = await self._generate_answer(system_prompt, user_prompt)

        # 8. Citation extraction
        citations = _extract_citations(context_chunks)

        return QueryResponse(
            answer=answer,
            citations=citations,
            query_mode=mode,
            kb_ids_searched=collection_names,
            retrieval_count=len(reranked),
            query_id=str(uuid.uuid4()),
        )

    async def stream(
        self,
        query: str,
        mode: QueryMode,
        collection_names: list[str],
    ) -> AsyncGenerator[str, None]:
        """Streaming variant — yields answer tokens as they arrive from Claude."""
        safety_result = await self._safety_service.classify(query)
        if not safety_result.is_allowed:
            yield settings.SAFETY_BLOCKED_MESSAGE
            return

        rewritten_query = await self._safety_service.rewrite_query(query)
        dense_vector = await self._embedding_service.embed_query(rewritten_query)
        sparse_indices, sparse_values = self._embedding_service.compute_sparse_vector(
            rewritten_query
        )

        all_chunks: list[RetrievedChunk] = []
        for collection in collection_names:
            try:
                chunks = await self._search_engine.search(
                    collection_name=collection,
                    dense_vector=dense_vector,
                    sparse_indices=sparse_indices,
                    sparse_values=sparse_values,
                    top_k=settings.RETRIEVAL_TOP_K,
                )
                all_chunks.extend(chunks)
            except Exception:
                continue

        if not all_chunks:
            yield settings.NO_RESULTS_MESSAGE
            return

        reranked = self._reranker.rerank(query=rewritten_query, chunks=all_chunks)
        context_chunks = [
            {
                "citation_index": idx + 1,
                "content": chunk.content,
                "document_title": chunk.document_title,
                "page_number": chunk.page_number,
                "source_url": chunk.source_url,
            }
            for idx, chunk in enumerate(reranked)
        ]

        system_prompt, user_prompt = build_rag_prompt(query=query, mode=mode, context_chunks=context_chunks)

        async for token in self._stream_answer(system_prompt, user_prompt):
            yield token

    async def _generate_answer(self, system_prompt: str, user_prompt: str) -> str:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        message = await client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=settings.CLAUDE_MAX_TOKENS,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return message.content[0].text

    async def _stream_answer(
        self, system_prompt: str, user_prompt: str
    ) -> AsyncGenerator[str, None]:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        async with client.messages.stream(
            model=settings.CLAUDE_MODEL,
            max_tokens=settings.CLAUDE_MAX_TOKENS,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        ) as stream:
            async for text in stream.text_stream:
                yield text


def _extract_citations(context_chunks: list[dict]) -> list[Citation]:
    return [
        Citation(
            index=chunk["citation_index"],
            document_title=chunk["document_title"],
            page_number=chunk.get("page_number"),
            source_url=chunk.get("source_url"),
            kb_name=chunk.get("kb_name"),
            chunk_excerpt=chunk["content"][:200] + "..." if len(chunk["content"]) > 200 else chunk["content"],
        )
        for chunk in context_chunks
    ]
