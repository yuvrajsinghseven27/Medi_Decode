from typing import Optional, List
from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import PrescriptionStatus
from app.schemas.confidence import FieldWithConfidence
from app.schemas.medication import MedicationItemRead, MedicationItemWithConfidence


class PrescriptionBase(BaseModel):
    raw_image_url: str = Field(..., max_length=1024)
    doctor_name: Optional[str] = Field(None, max_length=255)
    doctor_specialty: Optional[str] = Field(None, max_length=255)
    date_prescribed: Optional[date] = None
    status: PrescriptionStatus = Field(default=PrescriptionStatus.PENDING)


class PrescriptionCreate(PrescriptionBase):
    user_id: UUID


class PrescriptionUpdate(BaseModel):
    doctor_name: Optional[str] = None
    doctor_specialty: Optional[str] = None
    date_prescribed: Optional[date] = None
    status: Optional[PrescriptionStatus] = None


class PrescriptionRead(PrescriptionBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    medication_items: List[MedicationItemRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class PrescriptionWithConfidence(BaseModel):
    """Full AI-extracted prescription document with per-field OCR confidence scores."""
    raw_image_url: str
    doctor_name: FieldWithConfidence[str] = Field(default_factory=FieldWithConfidence)
    doctor_specialty: FieldWithConfidence[str] = Field(default_factory=FieldWithConfidence)
    date_prescribed: FieldWithConfidence[date] = Field(default_factory=FieldWithConfidence)
    medications: List[MedicationItemWithConfidence] = Field(default_factory=list)
    document_confidence: float = Field(default=1.0, ge=0.0, le=1.0)
