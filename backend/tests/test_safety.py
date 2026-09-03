import pytest
import uuid
from datetime import date
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from app.main import app
from app.core.database import async_session_maker
from app.models import (
    User,
    Prescription,
    MedicationItem,
    SafetyAlert,
    PrescriptionStatus,
    MedicationFrequency,
    TimingRelation,
    SafetyAlertType,
    AlertSeverity,
)
from app.services.safety_service import safety_service, extract_strength_in_mg, normalize_molecule


def test_strength_extraction_and_normalization():
    assert normalize_molecule("Crocin 650", None) == "Paracetamol"
    assert normalize_molecule("Dolo-650", None) == "Paracetamol"
    assert normalize_molecule("Combiflam", None) == "Ibuprofen + Paracetamol"
    assert normalize_molecule("Glycomet GP", None) == "Metformin"
    assert normalize_molecule("Eltroxin", None) == "Levothyroxine"
    assert normalize_molecule("Ciplox 500", None) == "Ciprofloxacin"

    assert extract_strength_in_mg("650mg") == 650.0
    assert extract_strength_in_mg("1g") == 1000.0
    assert extract_strength_in_mg("50mcg") == 0.05
    assert extract_strength_in_mg("500") == 500.0


@pytest.mark.asyncio
async def test_duplicate_molecule_cross_doctor():
    """Verify detection of identical generic molecules under different brand names across prescriptions."""
    async with async_session_maker() as session:
        # Create Patient
        user = User(
            full_name="Aarav Sharma",
            phone=f"+9191{uuid.uuid4().hex[:8]}",
            preferred_language="hi",
            cultural_dietary_profile={"fasting_routines": []},
        )
        session.add(user)
        await session.flush()

        # Previous Prescription from Dr. A: Dolo 650mg BD (Paracetamol)
        rx1 = Prescription(
            user_id=user.id,
            raw_image_url="/uploads/rx1.jpg",
            doctor_name="Dr. Anil Gupta",
            doctor_specialty="General Physician",
            status=PrescriptionStatus.RECONCILED,
        )
        session.add(rx1)
        await session.flush()

        med1 = MedicationItem(
            prescription_id=rx1.id,
            raw_text="Tab Dolo 650mg BD",
            brand_name="Dolo",
            generic_molecule="Paracetamol",
            form="Tablet",
            strength="650mg",
            frequency=MedicationFrequency.BD,
            timing_relation=TimingRelation.PC,
            is_active=True,
        )
        session.add(med1)
        await session.flush()

        # New Prescription from Dr. B: Crocin 500mg TID (Paracetamol)
        rx2 = Prescription(
            user_id=user.id,
            raw_image_url="/uploads/rx2.jpg",
            doctor_name="Dr. Priya Rao",
            doctor_specialty="ENT Specialist",
            status=PrescriptionStatus.PARSED,
        )
        session.add(rx2)
        await session.flush()

        med2 = MedicationItem(
            prescription_id=rx2.id,
            raw_text="Tab Crocin 500mg TID",
            brand_name="Crocin",
            generic_molecule="Paracetamol",
            form="Tablet",
            strength="500mg",
            frequency=MedicationFrequency.TID,
            timing_relation=TimingRelation.PC,
            is_active=True,
        )
        session.add(med2)
        await session.commit()

        # Reconcile rx2
        result = await safety_service.reconcile_prescription(rx2.id, session)

        assert result.status == PrescriptionStatus.RECONCILED
        dup_alerts = [a for a in result.alerts if a.alert_type == SafetyAlertType.DUPLICATE_MOLECULE]
        assert len(dup_alerts) >= 1
        assert "Paracetamol" in dup_alerts[0].advisory_text
        assert "Dolo" in dup_alerts[0].advisory_text or "Crocin" in dup_alerts[0].advisory_text
        assert dup_alerts[0].severity == AlertSeverity.CRITICAL

        # Verify regional translation in Hindi
        assert "hi" in dup_alerts[0].localized_advisory
        assert "पेरासिटामोल" in dup_alerts[0].localized_advisory["hi"]


@pytest.mark.asyncio
async def test_cumulative_toxicity_and_markdown_summary():
    """Verify cumulative dose overage (>4000mg/day Paracetamol) triggers CRITICAL alert and markdown sheet."""
    async with async_session_maker() as session:
        user = User(
            full_name="Meera Sen",
            phone=f"+9192{uuid.uuid4().hex[:8]}",
            preferred_language="bn",
            cultural_dietary_profile={},
        )
        session.add(user)
        await session.flush()

        # Prescription 1: Dolo 650mg TID = 1950mg
        rx1 = Prescription(
            user_id=user.id,
            raw_image_url="/uploads/rx1.jpg",
            doctor_name="Dr. Sen",
            status=PrescriptionStatus.RECONCILED,
        )
        session.add(rx1)
        await session.flush()

        session.add(
            MedicationItem(
                prescription_id=rx1.id,
                raw_text="Dolo 650 TID",
                brand_name="Dolo",
                generic_molecule="Paracetamol",
                strength="650mg",
                frequency=MedicationFrequency.TID,
                is_active=True,
            )
        )

        # Prescription 2: Calpol 1000mg TID = 3000mg (Combined = 4950mg > 4000mg)
        rx2 = Prescription(
            user_id=user.id,
            raw_image_url="/uploads/rx2.jpg",
            doctor_name="Dr. Mukherjee",
            status=PrescriptionStatus.PARSED,
        )
        session.add(rx2)
        await session.flush()

        session.add(
            MedicationItem(
                prescription_id=rx2.id,
                raw_text="Calpol 1000mg TID",
                brand_name="Calpol",
                generic_molecule="Paracetamol",
                strength="1000mg",
                frequency=MedicationFrequency.TID,
                is_active=True,
            )
        )
        await session.commit()

        result = await safety_service.reconcile_prescription(rx2.id, session)

        # Verify cumulative toxicity detected
        assert len(result.cumulative_toxicities) == 1
        cum = result.cumulative_toxicities[0]
        assert cum.generic_molecule == "Paracetamol"
        assert cum.cumulative_daily_dose_mg == 4950.0
        assert cum.max_safe_daily_dose_mg == 4000.0
        assert cum.is_toxic is True

        # Verify Doctor Query Summary markdown sheet generated
        assert result.doctor_query_summary is not None
        assert "MediDecode Clinical Safety & Multi-Script Reconciliation Report" in result.doctor_query_summary
        assert "4950 mg/day" in result.doctor_query_summary
        assert "Dr. Sen" in result.doctor_query_summary or "Dr. Mukherjee" in result.doctor_query_summary


@pytest.mark.asyncio
async def test_cultural_dietary_chai_and_dairy_rules():
    """Verify cultural rules: Chai blunting Levothyroxine and Dairy chelating Doxycycline."""
    async with async_session_maker() as session:
        user = User(
            full_name="Kavita Iyer",
            phone=f"+9193{uuid.uuid4().hex[:8]}",
            preferred_language="ta",
            cultural_dietary_profile={
                "tea_dairy_intake": "High: 4 cups milk tea daily, dahi with lunch",
            },
        )
        session.add(user)
        await session.flush()

        rx = Prescription(
            user_id=user.id,
            raw_image_url="/uploads/thyroid.jpg",
            doctor_name="Dr. Ramanathan",
            status=PrescriptionStatus.PARSED,
        )
        session.add(rx)
        await session.flush()

        # Med 1: Levothyroxine (Chai conflict)
        session.add(
            MedicationItem(
                prescription_id=rx.id,
                raw_text="Thyronorm 50mcg OD AC",
                brand_name="Thyronorm",
                generic_molecule="Levothyroxine",
                strength="50mcg",
                frequency=MedicationFrequency.OD,
                timing_relation=TimingRelation.AC,
                is_active=True,
            )
        )
        # Med 2: Doxycycline (Dairy chelation conflict)
        session.add(
            MedicationItem(
                prescription_id=rx.id,
                raw_text="Doxy-1 100mg BD PC",
                brand_name="Doxy-1",
                generic_molecule="Doxycycline",
                strength="100mg",
                frequency=MedicationFrequency.BD,
                timing_relation=TimingRelation.PC,
                is_active=True,
            )
        )
        await session.commit()

        result = await safety_service.reconcile_prescription(rx.id, session)

        food_alerts = [a for a in result.alerts if a.alert_type == SafetyAlertType.FOOD_INTERACTION]
        assert len(food_alerts) >= 2

        # Chai alert
        chai_alert = next(a for a in food_alerts if "tea" in a.advisory_text.lower() or "chai" in a.advisory_text.lower())
        assert chai_alert.severity == AlertSeverity.MODERATE
        assert "ta" in chai_alert.localized_advisory
        assert "தேநீர்" in chai_alert.localized_advisory["ta"]

        # Dairy alert
        dairy_alert = next(a for a in food_alerts if "dairy" in a.advisory_text.lower() or "chelate" in a.advisory_text.lower())
        assert dairy_alert.severity == AlertSeverity.MODERATE
        assert "ta" in dairy_alert.localized_advisory
        assert "பால்" in dairy_alert.localized_advisory["ta"]


@pytest.mark.asyncio
async def test_ramadan_fasting_adaptations():
    """Verify Ramadan fasting adaptation alters AC to Suhoor and PC to Iftar."""
    async with async_session_maker() as session:
        user = User(
            full_name="Farhan Ahmed",
            phone=f"+9194{uuid.uuid4().hex[:8]}",
            preferred_language="hi",
            cultural_dietary_profile={
                "fasting_routines": ["RAMADAN"],
                "tea_dairy_intake": "Low",
            },
        )
        session.add(user)
        await session.flush()

        rx = Prescription(
            user_id=user.id,
            raw_image_url="/uploads/rx_fasting.jpg",
            doctor_name="Dr. Khan",
            status=PrescriptionStatus.PARSED,
        )
        session.add(rx)
        await session.flush()

        # Morning AC med
        session.add(
            MedicationItem(
                prescription_id=rx.id,
                raw_text="Eltroxin 50mcg OD AC",
                brand_name="Eltroxin",
                generic_molecule="Levothyroxine",
                strength="50mcg",
                frequency=MedicationFrequency.OD,
                timing_relation=TimingRelation.AC,
                is_active=True,
            )
        )
        # Evening PC med
        session.add(
            MedicationItem(
                prescription_id=rx.id,
                raw_text="Glycomet 500mg BD PC",
                brand_name="Glycomet",
                generic_molecule="Metformin",
                strength="500mg",
                frequency=MedicationFrequency.BD,
                timing_relation=TimingRelation.PC,
                is_active=True,
            )
        )
        await session.commit()

        result = await safety_service.reconcile_prescription(rx.id, session)

        assert len(result.fasting_adjustments) >= 2
        suhoor_adj = next(a for a in result.fasting_adjustments if "Suhoor" in a.adapted_timing)
        assert "Pre-dawn" in suhoor_adj.adapted_timing

        iftar_adj = next(a for a in result.fasting_adjustments if "Iftar" in a.adapted_timing)
        assert "Post-sunset" in iftar_adj.adapted_timing

        fasting_alerts = [a for a in result.alerts if a.alert_type == SafetyAlertType.FASTING_CONFLICT]
        assert len(fasting_alerts) >= 1
        assert "Ramadan" in fasting_alerts[0].advisory_text


@pytest.mark.asyncio
async def test_reconcile_and_safety_advisories_api_endpoints():
    """Verify POST /prescriptions/{id}/verify-and-reconcile and GET /safety/advisories."""
    async with async_session_maker() as session:
        user = User(
            full_name="Sunita Rao",
            phone=f"+9195{uuid.uuid4().hex[:8]}",
            preferred_language="te",
            cultural_dietary_profile={"tea_dairy_intake": "High chai"},
        )
        session.add(user)
        await session.flush()

        rx = Prescription(
            user_id=user.id,
            raw_image_url="/uploads/rx_test.jpg",
            doctor_name="Dr. Srinivas",
            status=PrescriptionStatus.PARSED,
        )
        session.add(rx)
        await session.flush()

        session.add(
            MedicationItem(
                prescription_id=rx.id,
                raw_text="Thyronorm 50mcg OD AC",
                brand_name="Thyronorm",
                generic_molecule="Levothyroxine",
                strength="50mcg",
                frequency=MedicationFrequency.OD,
                timing_relation=TimingRelation.AC,
                is_active=True,
            )
        )
        await session.commit()
        rx_id = rx.id
        user_id = user.id

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Test POST /verify-and-reconcile
        rec_resp = await client.post(f"/api/v1/prescriptions/{rx_id}/verify-and-reconcile")
        assert rec_resp.status_code == 200
        rec_data = rec_resp.json()
        assert rec_data["status"] == "RECONCILED"
        assert len(rec_data["alerts"]) >= 1

        # 2. Test GET /safety/advisories
        adv_resp = await client.get(f"/api/v1/safety/advisories?user_id={user_id}")
        assert adv_resp.status_code == 200
        adv_data = adv_resp.json()
        assert len(adv_data) >= 1
        assert adv_data[0]["user_id"] == str(user_id)
