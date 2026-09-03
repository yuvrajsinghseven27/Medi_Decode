import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models import User
from app.schemas.user import UserRead, UserCreate

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/default",
    response_model=UserRead,
    summary="Get active/default patient profile",
    description="Returns the primary patient (e.g. Ramesh Patel) or creates a default patient if database is empty.",
)
async def get_default_user(session: AsyncSession = Depends(get_db)):
    # Prioritize seeded patient "Ramesh Patel" if present
    stmt = select(User).where(User.full_name.ilike("%Ramesh%")).limit(1)
    res = await session.execute(stmt)
    user = res.scalar_one_or_none()

    if not user:
        stmt = select(User).order_by(User.created_at.asc()).limit(1)
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()

    if not user:
        # Create baseline patient
        user = User(
            full_name="Ramesh Patel",
            phone="+919876543210",
            preferred_language="hi",
            cultural_dietary_profile={
                "dietary_type": "Vegetarian",
                "tea_dairy_intake": "High: 4 cups milk tea daily, curd with lunch",
                "fasting_routines": ["EKADASHI", "RAMADAN"],
                "notes": "Prefers Hindi reminders",
            },
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

    return user


@router.get(
    "/{user_id}",
    response_model=UserRead,
    summary="Get user profile by ID",
)
async def get_user_by_id(user_id: UUID, session: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.id == user_id)
    res = await session.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.get(
    "/",
    response_model=List[UserRead],
    summary="List all patients",
)
async def list_users(session: AsyncSession = Depends(get_db)):
    stmt = select(User).order_by(User.created_at.asc())
    res = await session.execute(stmt)
    return res.scalars().all()
