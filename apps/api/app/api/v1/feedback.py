from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_role
from app.db.models.feedback import Feedback
from app.db.models.user import User
from app.schemas.feedback import FeedbackCreate, FeedbackResponse

router = APIRouter(tags=["feedback"])


@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    payload: FeedbackCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    feedback = Feedback(
        user_id=current_user.id,
        query_text=payload.query_text,
        response_text=payload.response_text,
        kb_id=payload.kb_id,
        rating=payload.rating,
        comment=payload.comment,
        query_mode=payload.query_mode,
    )
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)
    return feedback


@router.get("/feedback/low-rated", response_model=list[FeedbackResponse])
async def get_low_rated_responses(
    _: Annotated[User, Depends(require_role("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 50,
):
    result = await db.execute(
        select(Feedback)
        .where(Feedback.rating.in_(["incorrect", "needs_review"]))
        .order_by(Feedback.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()
