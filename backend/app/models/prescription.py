import uuid
from sqlalchemy import Column, String, Date, DateTime, ForeignKey, Enum as SAEnum, func, Uuid
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.enums import PrescriptionStatus


class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    raw_image_url = Column(String(1024), nullable=False)
    doctor_name = Column(String(255), nullable=True)
    doctor_specialty = Column(String(255), nullable=True)
    date_prescribed = Column(Date, nullable=True)
    status = Column(
        SAEnum(PrescriptionStatus, native_enum=False),
        default=PrescriptionStatus.PENDING,
        nullable=False,
        index=True,
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="prescriptions")
    medication_items = relationship(
        "MedicationItem",
        back_populates="prescription",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Prescription id={self.id} doctor='{self.doctor_name}' status={self.status}>"
