import logging
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, CulturalDietaryProfile

logger = logging.getLogger(__name__)

router = APIRouter()


class LoginRequest(BaseModel):
    phone: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = "Patient"


class AuthResponse(BaseModel):
    status: str = "success"
    message: str
    user: UserRead
    token: str = "demo-session-token"


@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new patient or caregiver",
)
async def signup(
    payload: UserCreate,
    session: AsyncSession = Depends(get_db),
):
    """Creates a new patient profile and initializes chronological & dietary anchors."""
    # Check if phone already registered
    stmt = select(User).where(User.phone == payload.phone)
    result = await session.execute(stmt)
    existing_user = result.scalar_one_or_none()
    if existing_user:
        return AuthResponse(
            status="success",
            message="Welcome back! Account already exists.",
            user=UserRead.model_validate(existing_user),
            token=f"session_{existing_user.id}",
        )

    new_user = User(
        full_name=payload.full_name,
        phone=payload.phone,
        preferred_language=payload.preferred_language,
        cultural_dietary_profile=payload.cultural_dietary_profile.model_dump(),
        waking_time=payload.waking_time,
        breakfast_time=payload.breakfast_time,
        lunch_time=payload.lunch_time,
        dinner_time=payload.dinner_time,
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    logger.info(f"Registered new user: {new_user.full_name} ({new_user.phone})")
    return AuthResponse(
        status="success",
        message="Account created successfully!",
        user=UserRead.model_validate(new_user),
        token=f"session_{new_user.id}",
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Sign in via phone or email",
)
async def login(
    payload: LoginRequest,
    session: AsyncSession = Depends(get_db),
):
    """Finds user by phone or creates a demo patient session."""
    user = None
    if payload.phone:
        stmt = select(User).where(User.phone == payload.phone)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

    if not user:
        # Fallback to first available patient or create one
        stmt = select(User).limit(1)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

    if not user:
        user = User(
            full_name=payload.email.split("@")[0].title() if payload.email else "Ramesh Dadhaniya",
            phone=payload.phone or "+919876543210",
            preferred_language="en",
            cultural_dietary_profile={
                "dietary_type": "Vegetarian",
                "tea_dairy_intake": "High",
                "fasting_routines": ["Navratri"],
            },
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

    return AuthResponse(
        status="success",
        message="Login successful!",
        user=UserRead.model_validate(user),
        token=f"session_{user.id}",
    )


@router.get(
    "/me/{user_id}",
    response_model=UserRead,
    summary="Get user profile by UUID",
)
async def get_current_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_db),
):
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return UserRead.model_validate(user)
