"""
Query service — dispatches different query modes to the RAG pipeline.
"""
import json
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.rag.pipeline import RAGPipeline
from app.schemas.query import (
    CaseRequest,
    CaseResponse,
    MCQRequest,
    MCQResponse,
    QueryRequest,
    QueryResponse,
)
from app.services.retrieval_service import RetrievalService


class QueryService:
    """
    Routes query requests to the RAG pipeline and handles mode-specific post-processing.
    Follows Open/Closed Principle: new modes added via the QueryMode enum, not conditionals.
    """

    def __init__(self, pipeline: RAGPipeline, retrieval_service: RetrievalService):
        self._pipeline = pipeline
        self._retrieval_service = retrieval_service

    async def answer_question(
        self, request: QueryRequest, user_id: str | None = None
    ) -> QueryResponse:
        collection_names = await self._resolve_collections(request.kb_ids, user_id)

        return await self._pipeline.run(
            query=request.query,
            mode=request.mode,
            collection_names=collection_names,
        )

    async def generate_mcq(
        self, request: MCQRequest, user_id: str | None = None
    ) -> MCQResponse:
        collection_names = await self._resolve_collections(request.kb_ids, user_id)

        query = (
            f"Generate {request.count} {request.difficulty} multiple choice questions "
            f"about: {request.topic}"
        )
        response = await self._pipeline.run(
            query=query,
            mode="mcq",
            collection_names=collection_names,
        )

        items = _parse_mcq_response(response.answer, response.citations)
        return MCQResponse(
            topic=request.topic,
            items=items,
            kb_ids_searched=response.kb_ids_searched,
        )

    async def generate_case(
        self, request: CaseRequest, user_id: str | None = None
    ) -> CaseResponse:
        collection_names = await self._resolve_collections(request.kb_ids, user_id)

        if request.disorder:
            query = f"Generate a case study for: {request.disorder}"
        elif request.symptoms:
            query = f"Generate a case study presenting these symptoms: {', '.join(request.symptoms)}"
        else:
            query = f"Generate a psychology case study. Context: {request.scenario_context or 'general'}"

        response = await self._pipeline.run(
            query=query,
            mode="case_study",
            collection_names=collection_names,
        )

        return CaseResponse(
            case_description=response.answer,
            presenting_symptoms=request.symptoms or [],
            differential_diagnosis="See case description above.",
            treatment_considerations="Refer to source citations.",
            citations=response.citations,
        )

    async def _resolve_collections(
        self, kb_ids: list[UUID] | None, user_id: str | None
    ) -> list[str]:
        chunks, collections = await self._retrieval_service.retrieve(
            query="",
            kb_ids=kb_ids,
            user_id=user_id,
            top_k=0,  # We only want collection names here
        )
        return collections


def _parse_mcq_response(answer: str, citations) -> list:
    """Best-effort parser for LLM-generated MCQ text."""
    from app.schemas.query import MCQItem, MCQOption

    items = []
    # Try JSON block extraction first
    json_match = __import__("re").search(r"\[.*\]", answer, __import__("re").DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group())
            for q in data:
                options = [
                    MCQOption(
                        label=chr(65 + i),
                        text=opt.get("text", ""),
                        is_correct=opt.get("correct", False),
                    )
                    for i, opt in enumerate(q.get("options", []))
                ]
                items.append(
                    MCQItem(
                        question=q.get("question", ""),
                        options=options,
                        explanation=q.get("explanation", ""),
                        citations=citations,
                    )
                )
            return items
        except Exception:
            pass

    # Fallback: return raw text as single item
    return [
        __import__("app.schemas.query", fromlist=["MCQItem"]).MCQItem(
            question="See generated content below",
            options=[],
            explanation=answer,
            citations=citations,
        )
    ]
