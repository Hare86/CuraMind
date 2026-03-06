from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.db.models.user import User
from app.schemas.query import CaseRequest, CaseResponse, MCQRequest, MCQResponse, QueryRequest, QueryResponse
from app.api.v1.deps import get_rag_pipeline, get_query_service, get_retrieval_service

router = APIRouter(tags=["query"])


@router.post("/query", response_model=QueryResponse)
async def query(
    payload: QueryRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if payload.stream:
        pipeline = get_rag_pipeline(db)
        retrieval_service = get_retrieval_service(db)
        collection_names, _ = await retrieval_service.retrieve(
            query=payload.query,
            kb_ids=payload.kb_ids,
            user_id=str(current_user.id),
            top_k=0,
        )

        async def token_stream():
            async for token in pipeline.stream(
                query=payload.query,
                mode=payload.mode,
                collection_names=collection_names,
            ):
                yield token

        return StreamingResponse(token_stream(), media_type="text/event-stream")

    query_service = get_query_service(db)
    return await query_service.answer_question(payload, user_id=str(current_user.id))


@router.post("/generate-mcq", response_model=MCQResponse)
async def generate_mcq(
    payload: MCQRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    query_service = get_query_service(db)
    return await query_service.generate_mcq(payload, user_id=str(current_user.id))


@router.post("/generate-case", response_model=CaseResponse)
async def generate_case(
    payload: CaseRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    query_service = get_query_service(db)
    return await query_service.generate_case(payload, user_id=str(current_user.id))
