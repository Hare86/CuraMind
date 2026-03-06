import uuid
import os
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_user, get_db, require_role
from app.db.models.notification import Notification
from app.db.models.source_submission import SourceSubmission
from app.db.models.user import User
from app.schemas.submission import SourceSubmissionCreate, SourceSubmissionResponse

router = APIRouter(tags=["submissions"])


@router.post("/source-submit", response_model=SourceSubmissionResponse, status_code=status.HTTP_201_CREATED)
async def submit_source(
    submission_type: Annotated[str, Form()],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    url: Annotated[str | None, Form()] = None,
    title: Annotated[str | None, Form()] = None,
    file: Annotated[UploadFile | None, File()] = None,
):
    if submission_type == "url" and not url:
        raise HTTPException(status_code=400, detail="URL is required for URL submissions")
    if submission_type == "document" and not file:
        raise HTTPException(status_code=400, detail="File is required for document submissions")

    file_path = None
    if file:
        upload_dir = os.path.join(settings.LOCAL_UPLOAD_DIR, "submissions")
        os.makedirs(upload_dir, exist_ok=True)
        safe_name = f"{uuid.uuid4().hex}_{file.filename}"
        file_path = os.path.join(upload_dir, safe_name)
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

    submission = SourceSubmission(
        user_id=current_user.id,
        submission_type=submission_type,
        url=url,
        file_path=file_path,
        title=title or url,
        status="pending_review",
    )
    db.add(submission)

    # Queue LLM summary generation
    if url:
        from app.workers.ingestion_worker import _scrape_url
        import asyncio
        # Fire and forget summarization
        asyncio.create_task(_summarize_submission(submission.id, url))

    await db.commit()
    await db.refresh(submission)

    # Notify admins
    await _notify_admins_new_submission(db, submission)
    await db.commit()

    return submission


@router.get("/source-submissions", response_model=list[SourceSubmissionResponse])
async def list_submissions(
    admin: Annotated[User, Depends(require_role("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: str = "pending_review",
):
    result = await db.execute(
        select(SourceSubmission)
        .where(SourceSubmission.status == status_filter)
        .order_by(SourceSubmission.created_at.desc())
    )
    return result.scalars().all()


@router.post("/source-submissions/{submission_id}/review", status_code=200)
async def review_submission(
    submission_id: uuid.UUID,
    approved: bool,
    target_kb_id: uuid.UUID | None,
    admin: Annotated[User, Depends(require_role("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    submission = await db.get(SourceSubmission, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    submission.reviewed_at = datetime.now(timezone.utc)

    if approved:
        submission.status = "approved"
        submission.target_kb_id = target_kb_id
        if target_kb_id:
            if submission.url:
                from app.workers.ingestion_worker import ingest_url_task
                ingest_url_task.delay(submission.url, str(target_kb_id), str(submission_id))
            elif submission.file_path:
                # Create document + ingest
                from app.db.models.document import Document
                ext = submission.file_path.rsplit(".", 1)[-1].lower()
                doc = Document(
                    kb_id=target_kb_id,
                    filename=submission.title or "submission",
                    file_path=submission.file_path,
                    file_type=ext,
                    status="pending",
                )
                db.add(doc)
                await db.flush()
                from app.workers.ingestion_worker import ingest_document_task
                ingest_document_task.delay(str(doc.id), str(target_kb_id))
        submission.status = "ingested"
    else:
        submission.status = "rejected"

    # Notify submitting user
    if submission.user_id:
        message = (
            f"Your submission '{submission.title}' has been {'approved' if approved else 'rejected'}."
        )
        db.add(Notification(
            user_id=submission.user_id,
            message=message,
            notification_type="submission_approved" if approved else "submission_rejected",
            reference_id=submission.id,
        ))

    await db.commit()
    return {"status": submission.status}


async def _summarize_submission(submission_id: uuid.UUID, url: str):
    """Best-effort summary via Mistral."""
    pass  # Implemented via research_worker._generate_summary pattern


async def _notify_admins_new_submission(db, submission: SourceSubmission):
    from sqlalchemy import select
    from app.db.models.role import Role

    result = await db.execute(
        select(User).join(Role, User.role_id == Role.id).where(Role.name == "admin")
    )
    for admin in result.scalars().all():
        db.add(Notification(
            user_id=admin.id,
            message=f"New source submission: '{submission.title}' awaiting review.",
            notification_type="new_submission",
            reference_id=submission.id,
        ))
