import uuid
from datetime import datetime, time
from sqlalchemy import Column, String, Time, DateTime, func, JSON, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base

JSONType = JSON().with_variant(JSONB, "postgresql")


class User(Base):
    __tablename__ = "users"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(32), unique=True, index=True, nullable=False)
    preferred_language = Column(String(10), default="en", nullable=False)  # 'hi', 'ta', 'te', 'en'
    
    # Cultural & dietary profile: fasting routines, tea/dairy intake, religious restrictions
    cultural_dietary_profile = Column(JSONType, nullable=False, default=dict)
    
    # Daily chronological anchors for dose timing calculations
    waking_time = Column(Time, nullable=False, default=time(6, 30))
    breakfast_time = Column(Time, nullable=False, default=time(8, 30))
    lunch_time = Column(Time, nullable=False, default=time(13, 0))
    dinner_time = Column(Time, nullable=False, default=time(20, 30))

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    prescriptions = relationship("Prescription", back_populates="user", cascade="all, delete-orphan")
    schedule_items = relationship("ScheduleItem", back_populates="user", cascade="all, delete-orphan")
    safety_alerts = relationship("SafetyAlert", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User id={self.id} full_name='{self.full_name}' phone='{self.phone}'>"
