import uuid
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Enum as SAEnum,
    func,
    Uuid,
)
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.enums import ScheduleStatus


class ScheduleItem(Base):
    __tablename__ = "schedule_items"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    medication_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("medication_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scheduled_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(
        SAEnum(ScheduleStatus, native_enum=False),
        nullable=False,
        default=ScheduleStatus.PENDING,
        index=True,
    )
    taken_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="schedule_items")
    medication = relationship("MedicationItem", back_populates="schedule_items")

    def __repr__(self) -> str:
        return f"<ScheduleItem id={self.id} time={self.scheduled_timestamp} status={self.status}>"
