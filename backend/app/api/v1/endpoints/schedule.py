from typing import Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.schedule import (
    DailyScheduleView,
    DoseActionPayload,
    DoseActionResult,
)
from app.services.scheduler_service import scheduler_service

router = APIRouter()


@router.get(
    "/today",
    response_model=DailyScheduleView,
    status_code=status.HTTP_200_OK,
    summary="Fetch personalized daily dose schedule",
    description="Returns today's medication schedule categorized into Morning, Afternoon, Evening, and Bedtime slots with adherence metrics and low-stock indicators.",
)
async def get_today_schedule(
    user_id: UUID = Query(..., description="Target patient User UUID"),
    target_date: Optional[date] = Query(None, description="Optional target date, defaults to today"),
    session: AsyncSession = Depends(get_db),
):
    query_date = target_date or date.today()
    try:
        return await scheduler_service.get_daily_schedule(
            user_id=user_id,
            target_date=query_date,
            session=session,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate daily schedule: {str(e)}",
        )


@router.post(
    "/{item_id}/action",
    response_model=DoseActionResult,
    status_code=status.HTTP_200_OK,
    summary="Record action on scheduled dose",
    description="Logs intake (TAKEN - decrements inventory & checks refill threshold), SNOOZES dose by X minutes, or marks as SKIPPED.",
)
async def apply_schedule_item_action(
    item_id: UUID,
    payload: DoseActionPayload,
    session: AsyncSession = Depends(get_db),
):
    try:
        return await scheduler_service.apply_dose_action(
            item_id=item_id,
            payload=payload,
            session=session,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply dose action: {str(e)}",
        )
