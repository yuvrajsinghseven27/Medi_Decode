import pytest
import uuid
from datetime import date, time, datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from app.main import app
from app.core.database import async_session_maker
from app.models import (
    User,
    Prescription,
    MedicationItem,
    ScheduleItem,
    PrescriptionStatus,
    MedicationFrequency,
    TimingRelation,
    ScheduleStatus,
)
from app.schemas.schedule import DoseActionPayload
from app.services.scheduler_service import scheduler_service


def test_chrono_scheduling_varied_meal_profiles():
    """Verify scheduler computes distinct 24-hour timestamps based on varied patient anchors."""
    # Profile A: Early Riser
    early_user = User(
        full_name="Early Bird",
        phone="+919000000001",
        waking_time=time(5, 30),
        breakfast_time=time(7, 0),
        lunch_time=time(12, 0),
        dinner_time=time(19, 30),
    )

    # Profile B: Late Riser
    late_user = User(
        full_name="Late Riser",
        phone="+919000000002",
        waking_time=time(8, 0),
        breakfast_time=time(9, 30),
        lunch_time=time(14, 0),
        dinner_time=time(21, 30),
    )

    # 1. AC Morning (e.g. Levothyroxine - 30 min before breakfast)
    early_ac = scheduler_service.compute_daily_dose_times(
        user=early_user,
        frequency=MedicationFrequency.OD,
        timing_relation=TimingRelation.AC,
    )
    late_ac = scheduler_service.compute_daily_dose_times(
        user=late_user,
        frequency=MedicationFrequency.OD,
        timing_relation=TimingRelation.AC,
    )
    assert early_ac == [time(6, 30)]  # 07:00 - 30m
    assert late_ac == [time(9, 0)]    # 09:30 - 30m

    # 2. PC Morning & Evening (BD - 30 min after meals)
    early_bd = scheduler_service.compute_daily_dose_times(
        user=early_user,
        frequency=MedicationFrequency.BD,
        timing_relation=TimingRelation.PC,
    )
    late_bd = scheduler_service.compute_daily_dose_times(
        user=late_user,
        frequency=MedicationFrequency.BD,
        timing_relation=TimingRelation.PC,
    )
    assert early_bd == [time(7, 30), time(20, 0)]   # 07:00 + 30m, 19:30 + 30m
    assert late_bd == [time(10, 0), time(22, 0)]   # 09:30 + 30m, 21:30 + 30m

    # 3. TID (Morning, Lunch, Dinner - With Food)
    early_tid = scheduler_service.compute_daily_dose_times(
        user=early_user,
        frequency=MedicationFrequency.TID,
        timing_relation=TimingRelation.WITH_FOOD,
    )
    assert early_tid == [time(7, 0), time(12, 0), time(19, 30)]

    # 4. Statin (Atorvastatin) OD defaults to bedtime
    statin_dose = scheduler_service.compute_daily_dose_times(
        user=early_user,
        frequency=MedicationFrequency.OD,
        timing_relation=TimingRelation.PC,
        generic_molecule="Atorvastatin Calcium",
    )
    assert statin_dose == [time(21, 0)]  # dinner 19:30 + 90m = 21:00


@pytest.mark.asyncio
async def test_schedule_population_and_inventory_depletion():
    """Verify schedule generation across duration and smart inventory depletion with low-stock alerts."""
    async with async_session_maker() as session:
        user = User(
            full_name="Raj Malhotra",
            phone=f"+9198{uuid.uuid4().hex[:8]}",
            breakfast_time=time(8, 0),
            dinner_time=time(20, 0),
        )
        session.add(user)
        await session.flush()

        rx = Prescription(
            user_id=user.id,
            raw_image_url="/uploads/rx_sched.jpg",
            doctor_name="Dr. Mehta",
            status=PrescriptionStatus.PARSED,
        )
        session.add(rx)
        await session.flush()

        # Med 1: OD for 5 days with 4 initial pills (already near low-stock)
        med1 = MedicationItem(
            prescription_id=rx.id,
            raw_text="Thyronorm 50mcg OD AC",
            brand_name="Thyronorm",
            generic_molecule="Levothyroxine",
            strength="50mcg",
            frequency=MedicationFrequency.OD,
            timing_relation=TimingRelation.AC,
            duration_days=5,
            remaining_pills=4,
            is_active=True,
        )
        # Med 2: BD for 3 days
        med2 = MedicationItem(
            prescription_id=rx.id,
            raw_text="Glycomet 500mg BD PC",
            brand_name="Glycomet",
            generic_molecule="Metformin",
            strength="500mg",
            frequency=MedicationFrequency.BD,
            timing_relation=TimingRelation.PC,
            duration_days=3,
            remaining_pills=6,
            is_active=True,
        )
        session.add_all([med1, med2])
        await session.commit()

        # Generate schedule starting today
        today = date.today()
        created_items = await scheduler_service.generate_schedule_for_prescription(
            prescription_id=rx.id,
            session=session,
            start_date=today,
        )

        # Med1 (OD x 5 = 5 items) + Med2 (BD x 3 = 6 items) = 11 items
        assert len(created_items) == 11

        # Test TAKEN action on Med 1: pills decrement from 4 -> 3
        # Supply for OD: 3 pills / 1 = 3 days supply -> triggers is_low_stock = True!
        first_item = next(i for i in created_items if i.medication_id == med1.id)
        action_payload = DoseActionPayload(action=ScheduleStatus.TAKEN)
        result = await scheduler_service.apply_dose_action(
            item_id=first_item.id,
            payload=action_payload,
            session=session,
        )

        assert result.action_applied == ScheduleStatus.TAKEN
        assert result.remaining_pills == 3
        assert result.days_of_supply_remaining == 3.0
        assert result.is_low_stock is True
        assert result.low_stock_warning is not None
        assert "Refill Needed" in result.low_stock_warning

        # Test SNOOZE action on Med 2: advances scheduled time by 45 minutes
        med2_item = next(i for i in created_items if i.medication_id == med2.id)
        original_time = med2_item.scheduled_timestamp
        snooze_payload = DoseActionPayload(
            action=ScheduleStatus.SNOOZED,
            snooze_minutes=45,
        )
        snooze_result = await scheduler_service.apply_dose_action(
            item_id=med2_item.id,
            payload=snooze_payload,
            session=session,
        )
        assert snooze_result.action_applied == ScheduleStatus.SNOOZED
        expected_snooze_time = original_time + timedelta(minutes=45)
        assert (
            snooze_result.schedule_item.scheduled_timestamp.replace(tzinfo=timezone.utc)
            == expected_snooze_time.replace(tzinfo=timezone.utc)
        )

        # Test SKIP action: status marked SKIPPED without decrementing inventory
        med2_item_2 = [i for i in created_items if i.medication_id == med2.id][1]
        skip_payload = DoseActionPayload(
            action=ScheduleStatus.SKIPPED,
            skip_reason="Patient was fasting",
        )
        skip_result = await scheduler_service.apply_dose_action(
            item_id=med2_item_2.id,
            payload=skip_payload,
            session=session,
        )
        assert skip_result.action_applied == ScheduleStatus.SKIPPED
        assert skip_result.remaining_pills == 6  # unchanged


@pytest.mark.asyncio
async def test_schedule_api_endpoints():
    """Verify GET /api/v1/schedule/today and POST /api/v1/schedule/{id}/action."""
    async with async_session_maker() as session:
        user = User(
            full_name="Nisha Kapoor",
            phone=f"+9199{uuid.uuid4().hex[:8]}",
            breakfast_time=time(8, 30),
            lunch_time=time(13, 0),
            dinner_time=time(20, 30),
        )
        session.add(user)
        await session.flush()

        rx = Prescription(
            user_id=user.id,
            raw_image_url="/uploads/rx_nisha.jpg",
            status=PrescriptionStatus.PARSED,
        )
        session.add(rx)
        await session.flush()

        med = MedicationItem(
            prescription_id=rx.id,
            raw_text="Pantocid 40mg OD AC",
            brand_name="Pantocid",
            generic_molecule="Pantoprazole",
            strength="40mg",
            frequency=MedicationFrequency.OD,
            timing_relation=TimingRelation.AC,
            duration_days=1,
            remaining_pills=10,
            is_active=True,
        )
        session.add(med)
        await session.commit()

        # Generate schedule for today
        items = await scheduler_service.generate_schedule_for_prescription(
            prescription_id=rx.id,
            session=session,
            start_date=date.today(),
        )
        target_item_id = items[0].id
        user_id = user.id

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. GET /api/v1/schedule/today
        get_res = await client.get(f"/api/v1/schedule/today?user_id={user_id}")
        assert get_res.status_code == 200
        data = get_res.json()
        assert data["total_doses"] == 1
        assert len(data["morning"]) == 1
        assert data["morning"][0]["brand_name"] == "Pantocid"
        assert data["morning"][0]["time_str"] == "08:00 AM"

        # 2. POST /api/v1/schedule/{item_id}/action
        post_res = await client.post(
            f"/api/v1/schedule/{target_item_id}/action",
            json={"action": "TAKEN"},
        )
        assert post_res.status_code == 200
        action_data = post_res.json()
        assert action_data["action_applied"] == "TAKEN"
        assert action_data["remaining_pills"] == 9
        assert action_data["is_low_stock"] is False

        # 3. GET /today again to verify adherence gauge updated
        get_res2 = await client.get(f"/api/v1/schedule/today?user_id={user_id}")
        data2 = get_res2.json()
        assert data2["taken_doses"] == 1
        assert data2["adherence_percentage"] == 100
