from typing import Optional, List, Literal
from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import ScheduleStatus, MedicationFrequency, TimingRelation


class ScheduleItemBase(BaseModel):
    scheduled_timestamp: datetime
    status: ScheduleStatus = Field(default=ScheduleStatus.PENDING)
    taken_at: Optional[datetime] = None


class ScheduleItemCreate(ScheduleItemBase):
    user_id: UUID
    medication_id: UUID


class ScheduleItemUpdate(BaseModel):
    scheduled_timestamp: Optional[datetime] = None
    status: Optional[ScheduleStatus] = None
    taken_at: Optional[datetime] = None


class ScheduleItemRead(ScheduleItemBase):
    id: UUID
    user_id: UUID
    medication_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DoseActionPayload(BaseModel):
    """Payload for user logging or adjusting a scheduled dose."""
    action: ScheduleStatus = Field(..., description="Target status: TAKEN, SNOOZED, SKIPPED")
    snooze_minutes: Optional[int] = Field(default=30, ge=5, le=240, description="Minutes to postpone if SNOOZED")
    skip_reason: Optional[str] = Field(default=None, description="Optional patient explanation if SKIPPED")


class DoseItemDetail(BaseModel):
    """Detailed view of a single scheduled dose for patient presentation."""
    id: UUID
    medication_id: UUID
    brand_name: str
    generic_molecule: Optional[str] = None
    form: str
    strength: str
    frequency: MedicationFrequency
    timing_relation: TimingRelation
    scheduled_timestamp: datetime
    time_str: str  # e.g. "08:00 AM"
    status: ScheduleStatus
    taken_at: Optional[datetime] = None
    remaining_pills: int
    is_low_stock: bool
    instructions: str


class DailyScheduleView(BaseModel):
    """Chronologically grouped view of daily doses across 4 standard slots."""
    date: date
    morning: List[DoseItemDetail] = Field(default_factory=list)      # 05:00 - 11:59
    afternoon: List[DoseItemDetail] = Field(default_factory=list)    # 12:00 - 16:59
    evening: List[DoseItemDetail] = Field(default_factory=list)      # 17:00 - 20:59
    bedtime: List[DoseItemDetail] = Field(default_factory=list)      # 21:00 - 04:59
    total_doses: int = 0
    taken_doses: int = 0
    adherence_percentage: int = 0


class DoseActionResult(BaseModel):
    """Response returned when an action (TAKEN/SNOOZED/SKIPPED) is applied to a dose."""
    schedule_item: ScheduleItemRead
    action_applied: ScheduleStatus
    remaining_pills: int
    days_of_supply_remaining: float
    is_low_stock: bool
    low_stock_warning: Optional[str] = None
