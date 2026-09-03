from typing import List, Optional
from pydantic import BaseModel, Field


class BiomarkerItem(BaseModel):
    name: str = Field(..., description="Name of the test or biomarker, e.g. HbA1c, LDL Cholesterol, TSH")
    value: str = Field(..., description="Observed result with units, e.g. 7.8 % or 165 mg/dL")
    normal_range: str = Field(..., description="Reference normal clinical range, e.g. 4.0 - 5.6 %")
    status: str = Field(..., description="HIGH, LOW, NORMAL, or BORDERLINE")
    explanation: str = Field(..., description="Plain-language explanation of what this marker indicates")


class ReportSummaryResponse(BaseModel):
    report_title: str = Field(..., description="Title of the diagnostic or pathology report")
    patient_name: Optional[str] = Field(None, description="Patient name found on report")
    test_date: Optional[str] = Field(None, description="Date when sample was collected or reported")
    lab_name: Optional[str] = Field(None, description="Diagnostic lab, clinic or hospital name")
    overall_status: str = Field(..., description="NORMAL, ATTENTION, or ACTION_REQUIRED")
    plain_language_summary: str = Field(..., description="Patient-friendly plain-language explanation of all findings")
    biomarkers: List[BiomarkerItem] = Field(default_factory=list, description="Extracted individual lab test parameters")
    lifestyle_and_diet_recommendations: List[str] = Field(default_factory=list, description="Actionable dietary or lifestyle changes")
    questions_for_doctor: List[str] = Field(default_factory=list, description="Questions for the patient to ask their physician")
    urgency: str = Field("ROUTINE", description="ROUTINE, FOLLOW_UP_SOON, or URGENT")
    model_used: str = Field("gemini-2.5-flash", description="AI Model used for summarization")
