import os
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_user, get_db
from app.db.models.document import Document
from app.db.models.knowledge_base import KnowledgeBase
from app.db.models.user import User
from app.schemas.document import DocumentResponse
from app.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseResponse

router = APIRouter(tags=["knowledge-base"])

ALLOWED_EXTENSIONS = {"pdf", "docx", "pptx", "txt", "csv", "md"}


@router.get("/kb-list", response_model=list[KnowledgeBaseResponse])
async def list_knowledge_bases(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from sqlalchemy import or_
    result = await db.execute(
        select(KnowledgeBase).where(
            or_(
                KnowledgeBase.is_public.is_(True),
                KnowledgeBase.owner_id == current_user.id,
            )
        )
    )
    return result.scalars().all()


@router.post("/kb-create", response_model=KnowledgeBaseResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge_base(
    payload: KnowledgeBaseCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    collection_name = f"{settings.QDRANT_COLLECTION_PREFIX}_{uuid.uuid4().hex[:12]}"
    kb = KnowledgeBase(
        name=payload.name,
        description=payload.description,
        category=payload.category,
        owner_id=current_user.id,
        is_public=payload.is_public,
        qdrant_collection=collection_name,
    )
    db.add(kb)
    await db.commit()
    await db.refresh(kb)
    return kb


@router.post("/kb-upload", response_model=DocumentResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    kb_id: Annotated[uuid.UUID, Form()],
    file: Annotated[UploadFile, File()],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Validate KB ownership/access
    kb = await db.get(KnowledgeBase, kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    if kb.owner_id != current_user.id and not _is_admin(current_user):
        raise HTTPException(status_code=403, detail="Not authorized for this knowledge base")

    # Validate file type
    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' not supported. Allowed: {ALLOWED_EXTENSIONS}",
        )

    # Save file
    upload_dir = os.path.join(settings.LOCAL_UPLOAD_DIR, str(kb_id))
    os.makedirs(upload_dir, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(upload_dir, safe_name)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # Create document record
    doc = Document(
        kb_id=kb_id,
        filename=file.filename or safe_name,
        file_path=file_path,
        file_type=ext,
        file_size_bytes=len(content),
        status="pending",
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # Dispatch ingestion task
    from app.workers.ingestion_worker import ingest_document_task
    ingest_document_task.delay(str(doc.id), str(kb_id))

    return doc


@router.get("/kb/{kb_id}/documents", response_model=list[DocumentResponse])
async def list_documents(
    kb_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Document).where(Document.kb_id == kb_id).order_by(Document.created_at.desc())
    )
    return result.scalars().all()


def _is_admin(user: User) -> bool:
    return user.role and user.role.name == "admin"
