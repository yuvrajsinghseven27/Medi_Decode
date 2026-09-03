from typing import Optional, Dict
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import SafetyAlertType, AlertSeverity


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
