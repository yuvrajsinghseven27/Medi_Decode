import logging
from typing import List, Dict, Optional, Tuple
from uuid import UUID
from datetime import datetime, date, time, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.models import (
    User,
    Prescription,
    MedicationItem,
    ScheduleItem,
    SafetyAlert,
    ScheduleStatus,
    MedicationFrequency,
    TimingRelation,
    SafetyAlertType,
    AlertSeverity,
)
from app.schemas.schedule import (
    DoseActionPayload,
    DoseItemDetail,
    DailyScheduleView,
    DoseActionResult,
    ScheduleItemRead,
)

logger = logging.getLogger(__name__)

DAILY_CONSUMPTION_RATE: Dict[MedicationFrequency, int] = {
    MedicationFrequency.OD: 1,
    MedicationFrequency.BD: 2,
    MedicationFrequency.TID: 3,
    MedicationFrequency.QID: 4,
    MedicationFrequency.SOS: 1,
}


def offset_time(base_time: time, delta_minutes: int) -> time:
    """Adds or subtracts minutes from a time object cleanly."""
    dummy_dt = datetime.combine(date(2000, 1, 1), base_time) + timedelta(minutes=delta_minutes)
    return dummy_dt.time()


class SchedulerService:
    """Personalized Chrono-Scheduling and Smart Inventory Depletion Engine."""

    def compute_daily_dose_times(
        self,
        user: User,
        frequency: MedicationFrequency,
        timing_relation: TimingRelation,
        generic_molecule: Optional[str] = None,
    ) -> List[time]:
        """Maps frequency and food relations to exact clock times using personalized user anchors."""
        waking = user.waking_time or time(6, 30)
        breakfast = user.breakfast_time or time(8, 30)
        lunch = user.lunch_time or time(13, 0)
        dinner = user.dinner_time or time(20, 30)
        bedtime = offset_time(dinner, 90)  # ~22:00

        # Statins (Atorvastatin, Rosuvastatin) are clinically optimal at bedtime
        is_statin = bool(generic_molecule and "statin" in generic_molecule.lower())

        if is_statin and frequency == MedicationFrequency.OD:
            return [bedtime]

        # Calculate meal-anchored dose time
        if timing_relation == TimingRelation.AC:
            morning_time = offset_time(breakfast, -30)  # 30 mins before breakfast
            lunch_time = offset_time(lunch, -30)
            dinner_time = offset_time(dinner, -30)
        elif timing_relation == TimingRelation.PC:
            morning_time = offset_time(breakfast, 30)   # 30 mins after breakfast
            lunch_time = offset_time(lunch, 30)
            dinner_time = offset_time(dinner, 30)
        else:  # WITH_FOOD
            morning_time = breakfast
            lunch_time = lunch
            dinner_time = dinner

        if frequency == MedicationFrequency.OD:
            return [morning_time]
        elif frequency == MedicationFrequency.BD:
            return [morning_time, dinner_time]
        elif frequency == MedicationFrequency.TID:
            return [morning_time, lunch_time, dinner_time]
        elif frequency == MedicationFrequency.QID:
            return [morning_time, lunch_time, dinner_time, bedtime]
        elif frequency == MedicationFrequency.SOS:
            return [morning_time]

        return [morning_time]

    async def generate_schedule_for_prescription(
        self,
        prescription_id: UUID,
        session: AsyncSession,
        start_date: Optional[date] = None,
    ) -> List[ScheduleItem]:
        """Populates ScheduleItem records across the prescribed duration using patient anchors."""
        stmt = (
            select(Prescription)
            .where(Prescription.id == prescription_id)
            .options(
                selectinload(Prescription.medication_items),
                selectinload(Prescription.user),
            )
        )
        res = await session.execute(stmt)
        prescription = res.scalar_one_or_none()
        if not prescription:
            raise ValueError(f"Prescription '{prescription_id}' not found.")

        user = prescription.user
        created_items: List[ScheduleItem] = []
        anchor_date = start_date or date.today()

        for med in prescription.medication_items:
            if not med.is_active:
                continue

            # Prescribed duration (default to 7 days if open-ended)
            duration = med.duration_days if (med.duration_days and med.duration_days > 0) else 7
            daily_times = self.compute_daily_dose_times(
                user=user,
                frequency=med.frequency,
                timing_relation=med.timing_relation,
                generic_molecule=med.generic_molecule,
            )

            # Initialize remaining pills if currently zero
            total_prescribed_pills = duration * len(daily_times)
            if med.remaining_pills == 0:
                med.remaining_pills = total_prescribed_pills

            for day_offset in range(duration):
                current_day = anchor_date + timedelta(days=day_offset)
                for dose_time in daily_times:
                    # Construct tz-aware UTC timestamp
                    scheduled_dt = datetime.combine(
                        current_day, dose_time, tzinfo=timezone.utc
                    )
                    item = ScheduleItem(
                        user_id=user.id,
                        medication_id=med.id,
                        scheduled_timestamp=scheduled_dt,
                        status=ScheduleStatus.PENDING,
                    )
                    session.add(item)
                    created_items.append(item)

        await session.commit()
        return created_items

    async def get_daily_schedule(
        self,
        user_id: UUID,
        target_date: date,
        session: AsyncSession,
    ) -> DailyScheduleView:
        """Categorizes scheduled doses into Morning, Afternoon, Evening, and Bedtime slots."""
        start_of_day = datetime.combine(target_date, time.min, tzinfo=timezone.utc)
        end_of_day = datetime.combine(target_date, time.max, tzinfo=timezone.utc)

        stmt = (
            select(ScheduleItem)
            .where(
                ScheduleItem.user_id == user_id,
                ScheduleItem.scheduled_timestamp >= start_of_day,
                ScheduleItem.scheduled_timestamp <= end_of_day,
            )
            .options(selectinload(ScheduleItem.medication))
            .order_by(ScheduleItem.scheduled_timestamp.asc())
        )
        res = await session.execute(stmt)
        items = res.scalars().all()

        morning: List[DoseItemDetail] = []
        afternoon: List[DoseItemDetail] = []
        evening: List[DoseItemDetail] = []
        bedtime: List[DoseItemDetail] = []

        total_doses = len(items)
        taken_doses = 0

        for item in items:
            med = item.medication
            if item.status == ScheduleStatus.TAKEN:
                taken_doses += 1

            # Check low stock: supply <= 3 days
            rate = DAILY_CONSUMPTION_RATE.get(med.frequency, 1)
            days_supply = med.remaining_pills / rate if rate > 0 else 0
            is_low_stock = days_supply <= 3.0

            instructions = f"Take with water ({med.timing_relation.value})"
            if med.timing_relation == TimingRelation.AC:
                instructions = "Take 30 mins before food on an empty stomach"
            elif med.timing_relation == TimingRelation.PC:
                instructions = "Take 30 mins after food"
            elif med.timing_relation == TimingRelation.WITH_FOOD:
                instructions = "Take directly with meals"

            detail = DoseItemDetail(
                id=item.id,
                medication_id=med.id,
                brand_name=med.brand_name or "Medication",
                generic_molecule=med.generic_molecule,
                form=med.form,
                strength=med.strength,
                frequency=med.frequency,
                timing_relation=med.timing_relation,
                scheduled_timestamp=item.scheduled_timestamp,
                time_str=item.scheduled_timestamp.strftime("%I:%M %p"),
                status=item.status,
                taken_at=item.taken_at,
                remaining_pills=med.remaining_pills,
                is_low_stock=is_low_stock,
                instructions=instructions,
            )

            hour = item.scheduled_timestamp.hour
            if 5 <= hour < 12:
                morning.append(detail)
            elif 12 <= hour < 17:
                afternoon.append(detail)
            elif 17 <= hour < 21:
                evening.append(detail)
            else:
                bedtime.append(detail)

        adherence = int((taken_doses / total_doses) * 100) if total_doses > 0 else 0

        return DailyScheduleView(
            date=target_date,
            morning=morning,
            afternoon=afternoon,
            evening=evening,
            bedtime=bedtime,
            total_doses=total_doses,
            taken_doses=taken_doses,
            adherence_percentage=adherence,
        )

    async def apply_dose_action(
        self,
        item_id: UUID,
        payload: DoseActionPayload,
        session: AsyncSession,
    ) -> DoseActionResult:
        """Processes dose status updates, adjusts timestamps for snoozes, and decrements inventory."""
        stmt = (
            select(ScheduleItem)
            .where(ScheduleItem.id == item_id)
            .options(
                selectinload(ScheduleItem.medication),
                selectinload(ScheduleItem.user),
            )
        )
        res = await session.execute(stmt)
        item = res.scalar_one_or_none()
        if not item:
            raise ValueError(f"Schedule item '{item_id}' not found.")

        med = item.medication
        now_utc = datetime.now(timezone.utc)
        action = payload.action

        low_stock_warning: Optional[str] = None

        if action == ScheduleStatus.TAKEN:
            item.status = ScheduleStatus.TAKEN
            item.taken_at = now_utc
            # Decrement inventory
            med.remaining_pills = max(0, med.remaining_pills - 1)

            rate = DAILY_CONSUMPTION_RATE.get(med.frequency, 1)
            days_supply = med.remaining_pills / rate if rate > 0 else 0
            is_low_stock = days_supply <= 3.0

            if is_low_stock:
                low_stock_warning = (
                    f"Refill Needed: Only {med.remaining_pills} doses ({days_supply:.1f} days supply) "
                    f"of {med.brand_name or 'medication'} remaining."
                )
                # Record a safety notification
                alert = SafetyAlert(
                    user_id=item.user_id,
                    medication_id=med.id,
                    alert_type=SafetyAlertType.FOOD_INTERACTION,  # Reuse existing enum or general
                    severity=AlertSeverity.INFO,
                    advisory_text=low_stock_warning,
                    localized_advisory={"en": low_stock_warning},
                )
                session.add(alert)

        elif action == ScheduleStatus.SNOOZED:
            item.status = ScheduleStatus.SNOOZED
            snooze_delta = timedelta(minutes=payload.snooze_minutes or 30)
            item.scheduled_timestamp = item.scheduled_timestamp + snooze_delta

        elif action == ScheduleStatus.SKIPPED:
            item.status = ScheduleStatus.SKIPPED

        await session.commit()
        await session.refresh(item)

        rate = DAILY_CONSUMPTION_RATE.get(med.frequency, 1)
        days_supply = med.remaining_pills / rate if rate > 0 else 0

        return DoseActionResult(
            schedule_item=ScheduleItemRead.model_validate(item),
            action_applied=action,
            remaining_pills=med.remaining_pills,
            days_of_supply_remaining=round(days_supply, 1),
            is_low_stock=(days_supply <= 3.0),
            low_stock_warning=low_stock_warning,
        )


# Global scheduler service instance
scheduler_service = SchedulerService()
