from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models import SafetyAlert, AlertSeverity, SafetyAlertType
from app.schemas.safety import SafetyAlertRead

router = APIRouter()


@router.get(
    "/advisories",
    response_model=List[SafetyAlertRead],
    status_code=status.HTTP_200_OK,
    summary="Retrieve safety and dietary advisories for a patient",
    description="Fetches all active safety alerts, cultural dietary conflicts, fasting adaptations, and cumulative toxicity warnings for the patient.",
)
async def get_patient_safety_advisories(
    user_id: UUID = Query(..., description="Target patient User UUID"),
    severity: Optional[AlertSeverity] = Query(None, description="Optional severity filter (INFO, MODERATE, CRITICAL)"),
    alert_type: Optional[SafetyAlertType] = Query(None, description="Optional alert type filter"),
    session: AsyncSession = Depends(get_db),
):
    stmt = select(SafetyAlert).where(SafetyAlert.user_id == user_id)

    if severity:
        stmt = stmt.where(SafetyAlert.severity == severity)
    if alert_type:
        stmt = stmt.where(SafetyAlert.alert_type == alert_type)

    stmt = stmt.order_by(SafetyAlert.created_at.desc())
    result = await session.execute(stmt)
    alerts = result.scalars().all()

    return alerts
