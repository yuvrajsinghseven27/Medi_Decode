import uuid
from sqlalchemy import (
    Column,
    Text,
    DateTime,
    ForeignKey,
    Enum as SAEnum,
    func,
    JSON,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.enums import SafetyAlertType, AlertSeverity

JSONType = JSON().with_variant(JSONB, "postgresql")


class SafetyAlert(Base):
    __tablename__ = "safety_alerts"

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
        nullable=True,
        index=True,
    )
    alert_type = Column(
        SAEnum(SafetyAlertType, native_enum=False),
        nullable=False,
        index=True,
    )
    severity = Column(
        SAEnum(AlertSeverity, native_enum=False),
        nullable=False,
        default=AlertSeverity.MODERATE,
        index=True,
    )
    advisory_text = Column(Text, nullable=False)
    
    # Localized advisory map: e.g. {"hi": "...", "ta": "...", "te": "..."}
    localized_advisory = Column(JSONType, nullable=False, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="safety_alerts")
    medication = relationship("MedicationItem", back_populates="safety_alerts")

    def __repr__(self) -> str:
        return f"<SafetyAlert id={self.id} type={self.alert_type} severity={self.severity}>"
