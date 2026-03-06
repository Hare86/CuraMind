import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_role
from app.db.models.document import Document
from app.db.models.feedback import Feedback
from app.db.models.knowledge_base import KnowledgeBase
from app.db.models.research_article import ResearchArticle
from app.db.models.role import Role
from app.db.models.source_submission import SourceSubmission
from app.db.models.user import User
from app.schemas.admin import CreateRoleRequest, DashboardStats, RoleResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["admin"])


@router.post("/admin-create-role", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    payload: CreateRoleRequest,
    _: Annotated[User, Depends(require_role("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    existing = await db.execute(select(Role).where(Role.name == payload.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Role already exists")

    role = Role(
        name=payload.name,
        description=payload.description,
        permissions=payload.permissions,
    )
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return role


@router.get("/admin/roles", response_model=list[RoleResponse])
async def list_roles(
    _: Annotated[User, Depends(require_role("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(Role))
    return result.scalars().all()


@router.get("/admin/dashboard", response_model=DashboardStats)
async def dashboard_stats(
    _: Annotated[User, Depends(require_role("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    pending_research = await db.scalar(
        select(func.count(ResearchArticle.id)).where(ResearchArticle.status == "pending_review")
    )
    pending_submissions = await db.scalar(
        select(func.count(SourceSubmission.id)).where(SourceSubmission.status == "pending_review")
    )
    total_kbs = await db.scalar(select(func.count(KnowledgeBase.id)))
    total_docs = await db.scalar(select(func.count(Document.id)))
    total_users = await db.scalar(select(func.count(User.id)))
    low_rated = await db.scalar(
        select(func.count(Feedback.id)).where(
            Feedback.rating.in_(["incorrect", "needs_review"])
        )
    )
    pending_user_approvals = await db.scalar(
        select(func.count(User.id)).where(
            User.is_approved == False,  # noqa: E712
            User.pending_role_name.isnot(None),
        )
    )

    return DashboardStats(
        pending_research_articles=pending_research or 0,
        pending_submissions=pending_submissions or 0,
        total_knowledge_bases=total_kbs or 0,
        total_documents=total_docs or 0,
        total_users=total_users or 0,
        low_rated_responses=low_rated or 0,
        pending_user_approvals=pending_user_approvals or 0,
    )


@router.get("/admin/users", response_model=list[dict])
async def list_users(
    _: Annotated[User, Depends(require_role("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 100,
    offset: int = 0,
):
    result = await db.execute(
        select(User).order_by(User.created_at.desc()).limit(limit).offset(offset)
    )
    users = result.scalars().all()
    return [
        {
            "id": str(u.id),
            "email": u.email,
            "username": u.username,
            "full_name": u.full_name,
            "salutation": u.salutation,
            "is_active": u.is_active,
            "is_approved": u.is_approved,
            "pending_role_name": u.pending_role_name,
            "role": u.role.name if u.role else None,
            "created_at": u.created_at.isoformat(),
        }
        for u in users
    ]


@router.get("/admin/users/pending-approval", response_model=list[dict])
async def list_pending_approvals(
    _: Annotated[User, Depends(require_role("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List users with pending role approval requests."""
    result = await db.execute(
        select(User)
        .where(
            User.is_approved == False,  # noqa: E712
            User.pending_role_name.isnot(None),
        )
        .order_by(User.created_at.asc())
    )
    users = result.scalars().all()
    return [
        {
            "id": str(u.id),
            "email": u.email,
            "username": u.username,
            "full_name": u.full_name,
            "salutation": u.salutation,
            "pending_role_name": u.pending_role_name,
            "created_at": u.created_at.isoformat(),
        }
        for u in users
    ]


@router.post("/admin/users/{user_id}/approve")
async def approve_user(
    user_id: str,
    background_tasks: BackgroundTasks,
    _admin: Annotated[User, Depends(require_role("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Approve a pending user's role request, activate account, notify user."""
    from uuid import UUID

    user = await db.get(User, UUID(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_approved:
        raise HTTPException(status_code=400, detail="User is already approved")

    requested_role = user.pending_role_name
    if not requested_role:
        raise HTTPException(status_code=400, detail="No pending role request")

    role_result = await db.execute(select(Role).where(Role.name == requested_role))
    role = role_result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail=f"Role '{requested_role}' not found")

    user.role_id = role.id
    user.is_active = True
    user.is_approved = True
    user.pending_role_name = None
    await db.commit()

    background_tasks.add_task(_notify_approved, user.email, user.username or user.email, requested_role)
    return {"user_id": user_id, "role": requested_role, "status": "approved"}


@router.post("/admin/users/{user_id}/reject")
async def reject_user(
    user_id: str,
    background_tasks: BackgroundTasks,
    _admin: Annotated[User, Depends(require_role("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Reject a pending user's role request."""
    from uuid import UUID

    user = await db.get(User, UUID(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    rejected_role = user.pending_role_name or "unknown"
    user.pending_role_name = None
    await db.commit()

    background_tasks.add_task(_notify_rejected, user.email, user.username or user.email, rejected_role)
    return {"user_id": user_id, "status": "rejected"}


@router.patch("/admin/users/{user_id}/role")
async def assign_role(
    user_id: str,
    payload: dict = Body(...),
    _: Annotated[User, Depends(require_role("admin"))] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    from uuid import UUID

    role_name = payload.get("role_name")
    if not role_name:
        raise HTTPException(status_code=422, detail="role_name is required")

    user = await db.get(User, UUID(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    role_result = await db.execute(select(Role).where(Role.name == role_name))
    role = role_result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    user.role_id = role.id
    user.is_active = True
    user.is_approved = True
    await db.commit()
    return {"user_id": user_id, "role": role_name}


async def _notify_approved(email: str, username: str, role: str) -> None:
    try:
        from app.services.email_service import send_role_approved_notification
        await send_role_approved_notification(email, username, role)
    except Exception as exc:
        logger.warning("Failed to send approval email: %s", exc)


async def _notify_rejected(email: str, username: str, role: str) -> None:
    try:
        from app.services.email_service import send_role_rejected_notification
        await send_role_rejected_notification(email, username, role)
    except Exception as exc:
        logger.warning("Failed to send rejection email: %s", exc)
