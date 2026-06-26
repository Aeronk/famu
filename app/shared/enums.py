"""Central domain enumerations.

Stored as portable VARCHAR (``native_enum=False``) with the lowercase value, so
migrations stay simple and the same models work against any backend in tests.
"""

from __future__ import annotations

from enum import Enum

import sqlalchemy as sa


class StrEnum(str, Enum):
    def __str__(self) -> str:  # nicer logging / serialization
        return self.value


def enum_type(enum_cls: type[Enum]) -> sa.Enum:
    """SQLAlchemy column type that persists an enum's *value* as VARCHAR."""
    return sa.Enum(
        enum_cls,
        native_enum=False,
        length=40,
        validate_strings=True,
        values_callable=lambda e: [m.value for m in e],
    )


# ---- Identity / tenancy ----
class Role(StrEnum):
    SUPER_ADMIN = "super_admin"
    TENANT_ADMIN = "tenant_admin"
    FARM_MANAGER = "farm_manager"
    FARMER = "farmer"
    EXTENSION_OFFICER = "extension_officer"
    VIEWER = "viewer"


class Language(StrEnum):
    EN = "en"
    SN = "sn"  # Shona
    ND = "nd"  # Ndebele


class TenantType(StrEnum):
    SMALLHOLDER = "smallholder"
    COMMERCIAL = "commercial"
    FARMER_GROUP = "farmer_group"
    COOPERATIVE = "cooperative"
    NGO = "ngo"
    EXTENSION = "extension"


class TenantStatus(StrEnum):
    TRIAL = "trial"
    ACTIVE = "active"
    SUSPENDED = "suspended"


# ---- Crops ----
class CropType(StrEnum):
    MAIZE = "maize"
    TOBACCO = "tobacco"
    SOYBEANS = "soybeans"
    WHEAT = "wheat"
    COTTON = "cotton"
    GROUNDNUTS = "groundnuts"
    VEGETABLES = "vegetables"


class CropCycleStatus(StrEnum):
    PLANNED = "planned"
    PLANTED = "planted"
    GROWING = "growing"
    HARVESTED = "harvested"
    FAILED = "failed"


class InputType(StrEnum):
    SEED = "seed"
    FERTILIZER = "fertilizer"
    CHEMICAL = "chemical"
    LABOUR = "labour"
    OTHER = "other"


class ActivitySource(StrEnum):
    MANUAL = "manual"
    WHATSAPP = "whatsapp"
    SYSTEM = "system"


# ---- Livestock ----
class LivestockSpecies(StrEnum):
    CATTLE = "cattle"
    GOATS = "goats"
    SHEEP = "sheep"
    PIGS = "pigs"
    POULTRY = "poultry"


class Sex(StrEnum):
    MALE = "male"
    FEMALE = "female"


class LivestockStatus(StrEnum):
    ACTIVE = "active"
    SOLD = "sold"
    DECEASED = "deceased"


# ---- Finance ----
class TxnType(StrEnum):
    EXPENSE = "expense"
    INCOME = "income"


class LoanStatus(StrEnum):
    ACTIVE = "active"
    REPAID = "repaid"
    DEFAULTED = "defaulted"


class CreditStatus(StrEnum):
    ISSUED = "issued"
    REPAID = "repaid"
    OVERDUE = "overdue"


# ---- Weather / alerts ----
class AlertSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ---- Notifications ----
class NotificationChannel(StrEnum):
    WHATSAPP = "whatsapp"
    SMS = "sms"
    EMAIL = "email"


class NotificationStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class NotificationType(StrEnum):
    WEATHER_ALERT = "weather_alert"
    DISEASE_RISK = "disease_risk"
    VACCINATION_REMINDER = "vaccination_reminder"
    IRRIGATION_REMINDER = "irrigation_reminder"
    GENERAL = "general"


# ---- AI / predictions ----
class PredictionType(StrEnum):
    YIELD = "yield"
    DISEASE = "disease"
    REVENUE = "revenue"


class ImageAnalysisType(StrEnum):
    CROP_DISEASE = "crop_disease"
    NUTRIENT_DEFICIENCY = "nutrient_deficiency"
    PEST = "pest"
    LIVESTOCK_CONDITION = "livestock_condition"
    AUTO = "auto"


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


# ---- Channels & ML training data ----
class Channel(StrEnum):
    WEB = "web"
    MOBILE = "mobile"
    WHATSAPP = "whatsapp"
    API = "api"
    SYSTEM = "system"


class DatasetStatus(StrEnum):
    UNVERIFIED = "unverified"   # captured automatically, awaiting review
    VERIFIED = "verified"       # human-confirmed label (gold for training)
    REJECTED = "rejected"       # excluded from training


class DatasetName(StrEnum):
    YIELD = "yield"
    DISEASE = "disease"
    NLU_INTENT = "nlu_intent"
    VISION = "vision"
