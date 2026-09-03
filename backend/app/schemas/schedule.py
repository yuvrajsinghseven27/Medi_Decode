from typing import Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import ScheduleStatus


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


class DoseActionRequest(BaseModel):
    """User action payload for logging, snoozing, or skipping scheduled doses."""
    status: ScheduleStatus
    action_timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None
