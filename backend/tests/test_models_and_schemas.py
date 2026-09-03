import pytest
import uuid
from datetime import datetime, date, time
from sqlalchemy import select
from app.core.database import async_session_maker
from app.models import (
    User,
    Prescription,
    MedicationItem,
    ScheduleItem,
    SafetyAlert,
    PrescriptionStatus,
    MedicationFrequency,
    TimingRelation,
    ScheduleStatus,
    SafetyAlertType,
    AlertSeverity,
)
from app.schemas import (
    UserCreate,
    UserRead,
    CulturalDietaryProfile,
    PrescriptionCreate,
    PrescriptionRead,
    PrescriptionWithConfidence,
    MedicationItemCreate,
    MedicationItemRead,
    MedicationItemWithConfidence,
    FieldWithConfidence,
    ScheduleItemCreate,
    ScheduleItemRead,
    SafetyAlertCreate,
    SafetyAlertRead,
)


@pytest.mark.asyncio
async def test_relational_models_persistence():
    """Verify that all 5 relational models persist, relate, and query cleanly."""
    async with async_session_maker() as session:
        # 1. Create User
        user = User(
            full_name="Dr. Rajesh Sharma",
            phone=f"+9198{uuid.uuid4().hex[:8]}",
            preferred_language="hi",
            cultural_dietary_profile={
                "fasting_routines": ["Ekadashi", "Navratri"],
                "tea_dairy_intake": "3 cups milk tea daily",
                "dietary_type": "Vegetarian",
            },
            waking_time=time(6, 0),
            breakfast_time=time(8, 0),
            lunch_time=time(13, 0),
            dinner_time=time(20, 30),
        )
        session.add(user)
        await session.flush()
        assert user.id is not None

        # 2. Create Prescription
        prescription = Prescription(
            user_id=user.id,
            raw_image_url="https://storage.medidecode.health/rx/scan_101.jpg",
            doctor_name="Dr. A. K. Verma",
            doctor_specialty="Endocrinologist",
            date_prescribed=date(2026, 9, 1),
            status=PrescriptionStatus.PARSED,
        )
        session.add(prescription)
        await session.flush()
        assert prescription.id is not None

        # 3. Create MedicationItem
        med = MedicationItem(
            prescription_id=prescription.id,
            raw_text="Tab Metformin 500mg BD PC x 30 days",
            brand_name="Glycomet",
            generic_molecule="Metformin HCl",
            form="Tablet",
            strength="500mg",
            frequency=MedicationFrequency.BD,
            timing_relation=TimingRelation.PC,
            duration_days=30,
            remaining_pills=60,
            is_active=True,
        )
        session.add(med)
        await session.flush()
        assert med.id is not None

        # 4. Create ScheduleItem
        schedule = ScheduleItem(
            user_id=user.id,
            medication_id=med.id,
            scheduled_timestamp=datetime(2026, 9, 3, 8, 30),
            status=ScheduleStatus.PENDING,
        )
        session.add(schedule)
        await session.flush()
        assert schedule.id is not None

        # 5. Create SafetyAlert
        alert = SafetyAlert(
            user_id=user.id,
            medication_id=med.id,
            alert_type=SafetyAlertType.FOOD_INTERACTION,
            severity=AlertSeverity.MODERATE,
            advisory_text="Do not take with heavy milk/dairy within 1 hour.",
            localized_advisory={
                "hi": "दवा लेने के 1 घंटे के भीतर दूध या चाय का सेवन न करें।",
                "ta": "பால் அல்லது தேநீருடன் இந்த மருந்தை உடனடியாக உட்கொள்ள வேண்டாம்.",
            },
        )
        session.add(alert)
        await session.commit()

        # Query back and verify relationships
        stmt = select(User).where(User.id == user.id)
        result = await session.execute(stmt)
        queried_user = result.scalar_one()

        assert queried_user.full_name == "Dr. Rajesh Sharma"
        assert queried_user.preferred_language == "hi"
        assert "Navratri" in queried_user.cultural_dietary_profile["fasting_routines"]

        # Verify cascades & relations
        stmt_rx = select(Prescription).where(Prescription.user_id == user.id)
        rx_result = await session.execute(stmt_rx)
        queried_rx = rx_result.scalar_one()
        assert queried_rx.doctor_name == "Dr. A. K. Verma"
        assert queried_rx.status == PrescriptionStatus.PARSED

        stmt_med = select(MedicationItem).where(MedicationItem.prescription_id == queried_rx.id)
        med_result = await session.execute(stmt_med)
        queried_med = med_result.scalar_one()
        assert queried_med.brand_name == "Glycomet"
        assert queried_med.frequency == MedicationFrequency.BD
        assert queried_med.timing_relation == TimingRelation.PC

        stmt_alert = select(SafetyAlert).where(SafetyAlert.user_id == user.id)
        alert_result = await session.execute(stmt_alert)
        queried_alert = alert_result.scalar_one()
        assert queried_alert.severity == AlertSeverity.MODERATE
        assert "दूध" in queried_alert.localized_advisory["hi"]


def test_pydantic_schemas_validation():
    """Verify Pydantic v2 schemas and OCR confidence models."""
    # Test User Schema
    user_data = {
        "full_name": "Priya Patel",
        "phone": "+919822334455",
        "preferred_language": "gu",
        "cultural_dietary_profile": {
            "fasting_routines": ["Paryushan"],
            "tea_dairy_intake": "Moderate",
            "dietary_type": "Jain",
        },
        "waking_time": "06:00:00",
        "breakfast_time": "08:00:00",
        "lunch_time": "12:30:00",
        "dinner_time": "18:30:00",
    }
    user_create = UserCreate(**user_data)
    assert user_create.cultural_dietary_profile.dietary_type == "Jain"

    # Test FieldWithConfidence and MedicationItemWithConfidence
    med_with_conf = MedicationItemWithConfidence(
        raw_text="Eltroxin 50mcg OD AC before breakfast",
        brand_name=FieldWithConfidence(value="Eltroxin", confidence=0.97, raw_snippet="Eltroxin"),
        generic_molecule=FieldWithConfidence(value="Levothyroxine", confidence=0.94),
        form=FieldWithConfidence(value="Tablet", confidence=0.99),
        strength=FieldWithConfidence(value="50mcg", confidence=0.98),
        frequency=FieldWithConfidence(value=MedicationFrequency.OD, confidence=0.95),
        timing_relation=FieldWithConfidence(value=TimingRelation.AC, confidence=0.96),
        duration_days=FieldWithConfidence(value=90, confidence=0.91),
        overall_confidence=0.96,
    )
    assert med_with_conf.brand_name.confidence == 0.97
    assert med_with_conf.timing_relation.value == TimingRelation.AC
    assert med_with_conf.overall_confidence == 0.96

    # Test PrescriptionWithConfidence
    rx_with_conf = PrescriptionWithConfidence(
        raw_image_url="https://s3.amazonaws.com/rx.png",
        doctor_name=FieldWithConfidence(value="Dr. Mehta", confidence=0.92),
        doctor_specialty=FieldWithConfidence(value="General Physician", confidence=0.89),
        date_prescribed=FieldWithConfidence(value=date(2026, 9, 2), confidence=0.95),
        medications=[med_with_conf],
        document_confidence=0.94,
    )
    assert len(rx_with_conf.medications) == 1
    assert rx_with_conf.doctor_name.value == "Dr. Mehta"
    assert rx_with_conf.document_confidence == 0.94
