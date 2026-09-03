from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, model_validator
from app.models.enums import MedicationFrequency, TimingRelation, PrescriptionStatus


class ExtractedMedication(BaseModel):
    """Structured extraction of a single prescribed medication."""
    brand_name: Optional[str] = Field(
        default=None,
        description="Commercial or trade brand name, e.g. 'Lipitor', 'Augmentin'",
    )
    generic_molecule: Optional[str] = Field(
        default=None,
        description="Active pharmaceutical ingredient or molecule, e.g. 'Atorvastatin', 'Amoxicillin'",
    )
    dosage_form: str = Field(
        default="Tablet",
        description="Form factor, e.g. 'Tablet', 'Capsule', 'Syrup', 'Inhaler', 'Injection'",
    )
    strength: str = Field(
        ...,
        description="Dosage strength with unit, e.g. '500mg', '20mg', '10ml', '50mcg'",
    )
    frequency: MedicationFrequency = Field(
        default=MedicationFrequency.OD,
        description="Frequency code: OD (once daily), BD (twice daily), TID (thrice daily), QID (4 times), SOS (as needed)",
    )
    timing_relation: TimingRelation = Field(
        default=TimingRelation.PC,
        description="Timing relation: AC (before food), PC (after food), WITH_FOOD (with meals)",
    )
    duration_days: Optional[int] = Field(
        default=None,
        ge=1,
        description="Total duration prescribed in days, e.g. 5, 10, 30",
    )
    confidence_score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Model confidence rating for this line item (0.0 to 1.0)",
    )


class PrescriptionExtractionResult(BaseModel):
    """Complete multimodal prescription parsing payload."""
    doctor_name: Optional[str] = Field(
        default=None,
        description="Prescribing doctor's full name if legible",
    )
    doctor_specialty: Optional[str] = Field(
        default=None,
        description="Clinician specialty, e.g. 'Cardiology', 'General Medicine'",
    )
    medications: List[ExtractedMedication] = Field(
        default_factory=list,
        description="List of all detected medication items",
    )
    unreadable_notes: Optional[str] = Field(
        default=None,
        description="Any ambiguous, heavily cursive, or illegible sections detected",
    )
    requires_verification: bool = Field(
        default=False,
        description="Flag set to true if any medication confidence is below 0.85 or ambiguous notes are present",
    )

    @model_validator(mode="after")
    def compute_requires_verification(self) -> "PrescriptionExtractionResult":
        """Enforces clinical safety: triggers human verification if confidence is sub-threshold."""
        if self.requires_verification:
            return self

        # Flag if any medication item has confidence < 0.85
        has_low_confidence = any(m.confidence_score < 0.85 for m in self.medications)
        # Flag if ambiguous notes were detected
        has_unreadable = bool(self.unreadable_notes and self.unreadable_notes.strip())
        # Flag if no medications could be parsed
        is_empty = len(self.medications) == 0

        if has_low_confidence or has_unreadable or is_empty:
            self.requires_verification = True

        return self


class PrescriptionUploadResponse(BaseModel):
    """API response envelope for prescription uploads."""
    prescription_id: UUID
    user_id: UUID
    status: PrescriptionStatus
    raw_image_url: str
    extraction: PrescriptionExtractionResult
