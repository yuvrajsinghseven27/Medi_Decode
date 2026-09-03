from typing import Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import MedicationFrequency, TimingRelation
from app.schemas.confidence import FieldWithConfidence


class MedicationItemBase(BaseModel):
    raw_text: str = Field(..., description="Original raw prescription line extracted via OCR")
    brand_name: Optional[str] = Field(None, max_length=255)
    generic_molecule: Optional[str] = Field(None, max_length=255)
    form: str = Field(default="Tablet", max_length=64, description="Tablet, Capsule, Syrup, etc.")
    strength: str = Field(..., max_length=64, description="e.g. 500mg, 10ml, 50mcg")
    frequency: MedicationFrequency = Field(default=MedicationFrequency.OD)
    timing_relation: TimingRelation = Field(default=TimingRelation.PC)
    duration_days: Optional[int] = Field(None, ge=1)
    remaining_pills: int = Field(default=0, ge=0)
    is_active: bool = Field(default=True)


class MedicationItemCreate(MedicationItemBase):
    prescription_id: UUID


class MedicationItemUpdate(BaseModel):
    raw_text: Optional[str] = None
    brand_name: Optional[str] = None
    generic_molecule: Optional[str] = None
    form: Optional[str] = None
    strength: Optional[str] = None
    frequency: Optional[MedicationFrequency] = None
    timing_relation: Optional[TimingRelation] = None
    duration_days: Optional[int] = None
    remaining_pills: Optional[int] = None
    is_active: Optional[bool] = None


class MedicationItemRead(MedicationItemBase):
    id: UUID
    prescription_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MedicationItemWithConfidence(BaseModel):
    """Medication item schema containing field-level OCR confidence scores."""
    raw_text: str
    brand_name: FieldWithConfidence[str] = Field(default_factory=FieldWithConfidence)
    generic_molecule: FieldWithConfidence[str] = Field(default_factory=FieldWithConfidence)
    form: FieldWithConfidence[str] = Field(default_factory=lambda: FieldWithConfidence(value="Tablet"))
    strength: FieldWithConfidence[str] = Field(default_factory=FieldWithConfidence)
    frequency: FieldWithConfidence[MedicationFrequency] = Field(
        default_factory=lambda: FieldWithConfidence(value=MedicationFrequency.OD)
    )
    timing_relation: FieldWithConfidence[TimingRelation] = Field(
        default_factory=lambda: FieldWithConfidence(value=TimingRelation.PC)
    )
    duration_days: FieldWithConfidence[int] = Field(default_factory=FieldWithConfidence)
    overall_confidence: float = Field(default=1.0, ge=0.0, le=1.0)
