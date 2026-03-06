import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    verify_refresh_token,
)
from app.db.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

STUDENT_ROLE = "student"
APPROVAL_REQUIRED_ROLES = {"psychologist", "rehab_staff", "hospital_admin", "researcher", "doctor"}


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account inactive")

    extra = {"role": user.role.name if user.role else None}
    return TokenResponse(
        access_token=create_access_token(str(user.id), extra_claims=extra),
        refresh_token=create_refresh_token(str(user.id)),
        user_id=str(user.id),
        username=user.username,
        full_name=user.full_name,
        role=user.role.name if user.role else None,
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Check email uniqueness
    existing_email = await db.execute(select(User).where(User.email == payload.email))
    if existing_email.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    # Check username uniqueness
    existing_username = await db.execute(select(User).where(User.username == payload.username))
    if existing_username.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")

    # Validate salutation if provided
    if payload.salutation:
        from app.schemas.auth import SALUTATION_CHOICES
        if payload.salutation not in SALUTATION_CHOICES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid salutation",
            )

    from app.db.models.role import Role

    requested_role = (payload.role_request or STUDENT_ROLE).lower().strip()
    if requested_role not in {STUDENT_ROLE} | APPROVAL_REQUIRED_ROLES:
        requested_role = STUDENT_ROLE

    is_student = requested_role == STUDENT_ROLE

    role_result = await db.execute(select(Role).where(Role.name == STUDENT_ROLE))
    student_role = role_result.scalar_one_or_none()

    if is_student:
        user = User(
            email=payload.email,
            hashed_password=hash_password(payload.password),
            username=payload.username,
            full_name=payload.full_name,
            salutation=payload.salutation,
            is_active=True,
            is_approved=True,
            role_id=student_role.id if student_role else None,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        background_tasks.add_task(_send_student_confirmation, payload.email, payload.username)

        return TokenResponse(
            access_token="",
            refresh_token="",
            user_id=str(user.id),
            username=user.username,
            full_name=user.full_name,
            role=STUDENT_ROLE,
            requires_login=True,
        )

    else:
        user = User(
            email=payload.email,
            hashed_password=hash_password(payload.password),
            username=payload.username,
            full_name=payload.full_name,
            salutation=payload.salutation,
            is_active=False,
            is_approved=False,
            pending_role_name=requested_role,
            role_id=student_role.id if student_role else None,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        background_tasks.add_task(
            _send_pending_notifications, payload.email, payload.username, requested_role
        )

        return TokenResponse(
            access_token="",
            refresh_token="",
            user_id=str(user.id),
            username=user.username,
            full_name=user.full_name,
            role=None,
            pending_approval=True,
        )


async def _send_student_confirmation(email: str, username: str) -> None:
    try:
        from app.services.email_service import send_student_registration_confirmation
        await send_student_registration_confirmation(email, username)
    except Exception as exc:
        logger.warning("Failed to send student confirmation email: %s", exc)


async def _send_pending_notifications(email: str, username: str, role: str) -> None:
    try:
        from app.services.email_service import (
            send_pending_approval_notification,
            send_admin_new_user_notification,
        )
        await send_pending_approval_notification(email, username, role)
        if settings.ADMIN_NOTIFICATION_EMAIL:
            await send_admin_new_user_notification(
                settings.ADMIN_NOTIFICATION_EMAIL, username, email, role
            )
    except Exception as exc:
        logger.warning("Failed to send pending approval notifications: %s", exc)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    payload: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        user_id = verify_refresh_token(payload.refresh_token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    from uuid import UUID
    user = await db.get(User, UUID(user_id))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    extra = {"role": user.role.name if user.role else None}
    return TokenResponse(
        access_token=create_access_token(str(user.id), extra_claims=extra),
        refresh_token=create_refresh_token(str(user.id)),
        user_id=str(user.id),
        username=user.username,
        full_name=user.full_name,
        role=user.role.name if user.role else None,
    )


@router.post("/create-admin", status_code=status.HTTP_201_CREATED)
async def create_admin(
    payload: RegisterRequest,
    setup_secret: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Bootstrap endpoint to create the first admin account.
    Protected by ADMIN_SETUP_SECRET env variable.
    """
    if setup_secret != settings.ADMIN_SETUP_SECRET:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid setup secret")

    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    from app.db.models.role import Role
    role_result = await db.execute(select(Role).where(Role.name == "admin"))
    admin_role = role_result.scalar_one_or_none()
    if not admin_role:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin role not found — ensure migrations have been applied",
        )

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        username=payload.username,
        full_name=payload.full_name,
        salutation=payload.salutation,
        is_active=True,
        is_approved=True,
        role_id=admin_role.id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    extra = {"role": "admin"}
    return TokenResponse(
        access_token=create_access_token(str(user.id), extra_claims=extra),
        refresh_token=create_refresh_token(str(user.id)),
        user_id=str(user.id),
        username=user.username,
        full_name=user.full_name,
        role="admin",
    )
