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


from pydantic import BaseModel, Field
from typing import Dict, Any
from app.services.safety_service import safety_service


class GeminiAskRequest(BaseModel):
    question: str = Field(..., description="Patient question about medicines, foods to avoid, or timings")
    user_id: Optional[UUID] = None
    medications: Optional[List[Dict[str, Any]]] = None
    language: Optional[str] = "en"


@router.post(
    "/ask-gemini",
    summary="Ask Google Gemini AI about medications, consumed details, and foods to avoid",
    description="Invokes Gemini Clinical AI to analyze active prescriptions, foods to avoid, danger mechanisms, and safe dietary alternatives.",
)
async def ask_gemini_endpoint(
    payload: GeminiAskRequest,
    session: AsyncSession = Depends(get_db),
):
    meds = payload.medications
    # If meds not provided in request but user_id is given, load from DB
    if not meds and payload.user_id:
        from app.models.medication import MedicationItem
        from app.models.prescription import Prescription
        stmt = (
            select(MedicationItem)
            .join(Prescription, MedicationItem.prescription_id == Prescription.id)
            .where(Prescription.user_id == payload.user_id)
        )
        res = await session.execute(stmt)
        db_items = res.scalars().all()
        if db_items:
            meds = [
                {
                    "name": m.brand_name or m.generic_molecule,
                    "brand": m.brand_name,
                    "dosage": m.strength,
                    "frequency": m.frequency.value if m.frequency else "OD",
                    "timing_relation": m.timing_relation.value if m.timing_relation else "PC",
                }
                for m in db_items
            ]

    result = await safety_service.ask_gemini_about_medications(
        question=payload.question,
        medications=meds,
        language=payload.language or "en",
    )
    return result

