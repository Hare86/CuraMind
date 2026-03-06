from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_role
from app.db.models.research_article import ResearchArticle
from app.db.models.user import User
from app.schemas.research import ResearchApproveRequest, ResearchArticleResponse

router = APIRouter(tags=["research"])


@router.get("/research-queue", response_model=list[ResearchArticleResponse])
async def get_research_queue(
    _: Annotated[User, Depends(require_role("admin", "researcher"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(ResearchArticle)
        .where(ResearchArticle.status == "pending_review")
        .order_by(ResearchArticle.created_at.desc())
    )
    return result.scalars().all()


@router.post("/research-approve", status_code=status.HTTP_200_OK)
async def approve_research_article(
    payload: ResearchApproveRequest,
    admin: Annotated[User, Depends(require_role("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    article = await db.get(ResearchArticle, payload.article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    if payload.approved:
        article.status = "approved"
        article.kb_id = payload.target_kb_id
        article.reviewed_at = datetime.now(timezone.utc)

        # Trigger ingestion
        if payload.target_kb_id:
            from app.workers.ingestion_worker import ingest_url_task
            ingest_url_task.delay(article.url, str(payload.target_kb_id))
            article.status = "ingested"
    else:
        article.status = "rejected"
        article.reviewed_at = datetime.now(timezone.utc)

    await db.commit()
    return {"status": article.status, "article_id": str(article.id)}


@router.post("/research-search", status_code=status.HTTP_202_ACCEPTED)
async def trigger_research_search(
    _: Annotated[User, Depends(require_role("admin", "researcher"))],
):
    """Manually trigger the research agent."""
    from app.workers.research_worker import run_research_agent
    run_research_agent.delay()
    return {"message": "Research agent triggered. Results will appear in the review queue."}
