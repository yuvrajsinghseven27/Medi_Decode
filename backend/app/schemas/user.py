from typing import Optional, Dict, Any, List
from datetime import time, datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class CulturalDietaryProfile(BaseModel):
    """Structured cultural and dietary behavior profile."""
    model_config = ConfigDict(extra="allow")

    fasting_routines: Optional[List[str]] = Field(
        default_factory=list,
        description="Active fasting commitments, e.g. ['Navratri', 'Ramadan', 'Ekadashi', 'Intermittent']",
    )
    tea_dairy_intake: Optional[str] = Field(
        default="High",
        description="Daily consumption pattern of chai/milk/dairy (influences tetracycline/thyroxine absorption)",
    )
    dietary_type: Optional[str] = Field(
        default="Vegetarian",
        description="Dietary lifestyle: Vegetarian, Vegan, Non-Vegetarian, Jain",
    )
    custom_notes: Optional[str] = None


class UserBase(BaseModel):
    full_name: str = Field(..., max_length=255)
    phone: str = Field(..., max_length=32, description="E.164 phone number, e.g. +919876543210")
    preferred_language: str = Field(default="en", max_length=10, description="'hi', 'ta', 'te', 'en'")
    cultural_dietary_profile: CulturalDietaryProfile = Field(default_factory=CulturalDietaryProfile)
    waking_time: time = Field(default=time(6, 30))
    breakfast_time: time = Field(default=time(8, 30))
    lunch_time: time = Field(default=time(13, 0))
    dinner_time: time = Field(default=time(20, 30))


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    preferred_language: Optional[str] = None
    cultural_dietary_profile: Optional[CulturalDietaryProfile] = None
    waking_time: Optional[time] = None
    breakfast_time: Optional[time] = None
    lunch_time: Optional[time] = None
    dinner_time: Optional[time] = None


class UserRead(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
