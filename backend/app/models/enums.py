import enum


class PrescriptionStatus(str, enum.Enum):
    PENDING = "PENDING"
    PARSED = "PARSED"
    VERIFIED = "VERIFIED"
    RECONCILED = "RECONCILED"


class MedicationFrequency(str, enum.Enum):
    OD = "OD"      # Once daily
    BD = "BD"      # Twice daily
    TID = "TID"    # Three times daily
    QID = "QID"    # Four times daily
    SOS = "SOS"    # As needed / Emergency


class TimingRelation(str, enum.Enum):
    AC = "AC"              # Ante Cibum (Before Food)
    PC = "PC"              # Post Cibum (After Food)
    WITH_FOOD = "WITH_FOOD"  # Concurrently with food


class ScheduleStatus(str, enum.Enum):
    PENDING = "PENDING"
    TAKEN = "TAKEN"
    SNOOZED = "SNOOZED"
    SKIPPED = "SKIPPED"


class SafetyAlertType(str, enum.Enum):
    FOOD_INTERACTION = "FOOD_INTERACTION"
    CUMULATIVE_TOXICITY = "CUMULATIVE_TOXICITY"
    FASTING_CONFLICT = "FASTING_CONFLICT"
    DUPLICATE_MOLECULE = "DUPLICATE_MOLECULE"


class AlertSeverity(str, enum.Enum):
    INFO = "INFO"
    MODERATE = "MODERATE"
    CRITICAL = "CRITICAL"
