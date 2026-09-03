from typing import Optional, Dict, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import SafetyAlertType, AlertSeverity, PrescriptionStatus


class SafetyAlertBase(BaseModel):
    alert_type: SafetyAlertType
    severity: AlertSeverity = Field(default=AlertSeverity.MODERATE)
    advisory_text: str = Field(..., description="English/Default clinical guidance text")
    localized_advisory: Dict[str, str] = Field(
        default_factory=dict,
        description="Keyed by language code, e.g. {'hi': '...', 'ta': '...', 'te': '...'}",
    )


class SafetyAlertCreate(SafetyAlertBase):
    user_id: UUID
    medication_id: Optional[UUID] = None


class SafetyAlertRead(SafetyAlertBase):
    id: UUID
    user_id: UUID
    medication_id: Optional[UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CumulativeToxicityAlert(BaseModel):
    """Details regarding cumulative active ingredient overage across multiple scripts."""
    generic_molecule: str
    cumulative_daily_dose_mg: float
    max_safe_daily_dose_mg: float
    is_toxic: bool
    contributing_brands: List[str]
    prescribing_doctors: List[str]
    clinical_risk: str


class FastingAdjustment(BaseModel):
    """Suggested timing adaptation for active religious fasting."""
    routine_name: str
    original_timing: str
    adapted_timing: str
    rationale: str


class ReconciliationResponse(BaseModel):
    """Complete reconciliation and safety audit response envelope."""
    prescription_id: UUID
    user_id: UUID
    status: PrescriptionStatus
    alerts: List[SafetyAlertRead]
    cumulative_toxicities: List[CumulativeToxicityAlert]
    fasting_adjustments: List[FastingAdjustment]
    doctor_query_summary: Optional[str] = Field(
        default=None,
        description="Exportable doctor consultation sheet in formatted Markdown",
    )
