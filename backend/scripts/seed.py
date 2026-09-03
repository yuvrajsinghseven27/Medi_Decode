import asyncio
import sys
import logging
from datetime import date, time, datetime, timezone
from pathlib import Path

# Ensure backend root is on Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import async_session_maker, engine, Base
from app.models import (
    User,
    Prescription,
    MedicationItem,
    PrescriptionStatus,
    MedicationFrequency,
    TimingRelation,
)
from app.services.safety_service import safety_service
from app.services.scheduler_service import scheduler_service

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("seed")


async def seed_database():
    """Seeds a realistic clinical multi-doctor polypharmacy conflict scenario."""
    logger.info("Initializing database schema...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as session:
        logger.info("Seeding patient profile: Ramesh Patel (62 y/o)...")
        # 1. Create Patient Profile
        patient = User(
            full_name="Ramesh Patel",
            phone="+919876543210",
            preferred_language="hi",
            cultural_dietary_profile={
                "dietary_type": "Vegetarian",
                "tea_dairy_intake": "High: 4 cups milk tea (chai) daily, curd with lunch",
                "fasting_routines": ["EKADASHI", "RAMADAN"],
                "notes": "Prefers medication reminders in Hindi.",
            },
            waking_time=time(6, 0),
            breakfast_time=time(8, 0),
            lunch_time=time(13, 0),
            dinner_time=time(20, 30),
        )
        session.add(patient)
        await session.flush()
        logger.info(f"Created Patient User: {patient.full_name} [ID: {patient.id}]")

        # 2. Prescription 1 (Cardiologist - Dr. S. K. Gupta)
        # Active baseline medications for hypertension, diabetes, and knee osteoarthritis
        logger.info("Seeding Baseline Prescription 1 from Dr. S. K. Gupta (Cardiology)...")
        rx1 = Prescription(
            user_id=patient.id,
            raw_image_url="/uploads/rx_gupta_cardio.jpg",
            doctor_name="Dr. S. K. Gupta",
            doctor_specialty="Cardiologist",
            date_prescribed=date(2026, 8, 15),
            status=PrescriptionStatus.RECONCILED,
        )
        session.add(rx1)
        await session.flush()

        med1_1 = MedicationItem(
            prescription_id=rx1.id,
            raw_text="Tab Amlong 5mg OD PC",
            brand_name="Amlong",
            generic_molecule="Amlodipine",
            form="Tablet",
            strength="5mg",
            frequency=MedicationFrequency.OD,
            timing_relation=TimingRelation.PC,
            duration_days=30,
            remaining_pills=26,
            is_active=True,
        )
        med1_2 = MedicationItem(
            prescription_id=rx1.id,
            raw_text="Tab Glycomet 500mg BD PC",
            brand_name="Glycomet",
            generic_molecule="Metformin",
            form="Tablet",
            strength="500mg",
            frequency=MedicationFrequency.BD,
            timing_relation=TimingRelation.PC,
            duration_days=30,
            remaining_pills=18,
            is_active=True,
        )
        med1_3 = MedicationItem(
            prescription_id=rx1.id,
            raw_text="Tab Dolo 650 TID PC",
            brand_name="Dolo 650",
            generic_molecule="Paracetamol",
            form="Tablet",
            strength="650mg",
            frequency=MedicationFrequency.TID,
            timing_relation=TimingRelation.PC,
            duration_days=10,
            remaining_pills=12,
            is_active=True,
        )
        session.add_all([med1_1, med1_2, med1_3])
        await session.flush()

        # 3. Prescription 2 (Orthopedic Surgeon - Dr. Ananya Sharma)
        # New consultation for acute shoulder injury. Doctor prescribes Crocin 500mg BD
        # without knowing patient is already taking Dolo 650 TID!
        logger.info("Seeding New Prescription 2 from Dr. Ananya Sharma (Orthopedics)...")
        rx2 = Prescription(
            user_id=patient.id,
            raw_image_url="/uploads/rx_sharma_ortho.jpg",
            doctor_name="Dr. Ananya Sharma",
            doctor_specialty="Orthopedic Surgeon",
            date_prescribed=date(2026, 9, 2),
            status=PrescriptionStatus.PARSED,
        )
        session.add(rx2)
        await session.flush()

        med2_1 = MedicationItem(
            prescription_id=rx2.id,
            raw_text="Tab Crocin 500mg BD PC",
            brand_name="Crocin",
            generic_molecule="Paracetamol",
            form="Tablet",
            strength="500mg",
            frequency=MedicationFrequency.BD,
            timing_relation=TimingRelation.PC,
            duration_days=7,
            remaining_pills=14,
            is_active=True,
        )
        med2_2 = MedicationItem(
            prescription_id=rx2.id,
            raw_text="Tab Thyronorm 50mcg OD AC",
            brand_name="Thyronorm",
            generic_molecule="Levothyroxine",
            form="Tablet",
            strength="50mcg",
            frequency=MedicationFrequency.OD,
            timing_relation=TimingRelation.AC,
            duration_days=30,
            remaining_pills=30,
            is_active=True,
        )
        session.add_all([med2_1, med2_2])
        await session.commit()

        # 4. Trigger Core Multi-Script Reconciliation Audit
        logger.info("\n" + "=" * 70)
        logger.info("RUNNING MULTI-SCRIPT SAFETY & RECONCILIATION AUDIT...")
        logger.info("=" * 70)

        reconciliation = await safety_service.reconcile_prescription(
            prescription_id=rx2.id,
            session=session,
        )

        logger.info(f"Prescription Status: {reconciliation.status.value}")
        logger.info(f"Total Safety Alerts Triggered: {len(reconciliation.alerts)}")

        for idx, alert in enumerate(reconciliation.alerts, 1):
            logger.info(f"\n[Alert #{idx}] [{alert.severity.value}] - {alert.alert_type.value}")
            logger.info(f"  English: {alert.advisory_text}")
            if "hi" in alert.localized_advisory:
                logger.info(f"  Hindi Localization: {alert.localized_advisory['hi']}")

        if reconciliation.cumulative_toxicities:
            logger.info("\n" + "-" * 70)
            logger.info("CUMULATIVE DOSAGE OVERAGES:")
            for tox in reconciliation.cumulative_toxicities:
                logger.info(
                    f"  Molecule: {tox.generic_molecule} | Cumulative Dose: {tox.cumulative_daily_dose_mg}mg/day | Safe Limit: {tox.max_safe_daily_dose_mg}mg/day"
                )

        # 5. Populate Chrono-Schedule
        logger.info("\n" + "=" * 70)
        logger.info("GENERATING PERSONALIZED CHRONO-SCHEDULE FOR PATIENT...")
        logger.info("=" * 70)

        schedule_items = await scheduler_service.generate_schedule_for_prescription(
            prescription_id=rx2.id,
            session=session,
            start_date=date.today(),
        )
        logger.info(f"Generated {len(schedule_items)} ScheduleItem records across duration.")

        # Fetch today's view
        today_view = await scheduler_service.get_daily_schedule(
            user_id=patient.id,
            target_date=date.today(),
            session=session,
        )
        logger.info(f"Today's Morning Doses: {len(today_view.morning)}")
        for item in today_view.morning:
            logger.info(f"  - {item.time_str}: {item.brand_name} ({item.strength}) -> {item.instructions}")

        logger.info(f"Today's Afternoon Doses: {len(today_view.afternoon)}")
        logger.info(f"Today's Evening Doses: {len(today_view.evening)}")

        logger.info("\n" + "=" * 70)
        logger.info("DATABASE SEEDING AND CLINICAL VALIDATION COMPLETED SUCCESSFULLY!")
        logger.info("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(seed_database())
