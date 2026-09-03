import uuid
from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Enum as SAEnum,
    func,
    Uuid,
)
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.enums import MedicationFrequency, TimingRelation


class MedicationItem(Base):
    __tablename__ = "medication_items"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    prescription_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("prescriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    raw_text = Column(Text, nullable=False)  # Raw unnormalized OCR line
    brand_name = Column(String(255), nullable=True, index=True)
    generic_molecule = Column(String(255), nullable=True, index=True)
    form = Column(String(64), nullable=False, default="Tablet")  # Tablet, Capsule, Syrup, Inhaler, etc.
    strength = Column(String(64), nullable=False)  # 500mg, 10ml, etc.
    
    frequency = Column(
        SAEnum(MedicationFrequency, native_enum=False),
        nullable=False,
        default=MedicationFrequency.OD,
    )
    timing_relation = Column(
        SAEnum(TimingRelation, native_enum=False),
        nullable=False,
        default=TimingRelation.PC,
    )
    
    duration_days = Column(Integer, nullable=True)
    remaining_pills = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    prescription = relationship("Prescription", back_populates="medication_items")
    schedule_items = relationship(
        "ScheduleItem",
        back_populates="medication",
        cascade="all, delete-orphan",
    )
    safety_alerts = relationship(
        "SafetyAlert",
        back_populates="medication",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<MedicationItem id={self.id} brand='{self.brand_name}' freq={self.frequency}>"
