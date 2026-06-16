"""Import-all registry so ``Base.metadata`` is fully populated.

Used by Alembic (autogenerate / initial create) and by ``create_all`` in tests.
Import order is irrelevant — SQLAlchemy resolves cross-table FKs lazily.
"""

from __future__ import annotations

from app.ai.models import AIConversation, AIMessage, ImageAnalysis  # noqa: F401
from app.ai.rag.models import KnowledgeChunk, KnowledgeDocument  # noqa: F401
from app.database.base import Base  # noqa: F401,E402
from app.modules.auth.models import RefreshToken, User  # noqa: F401
from app.modules.crops.models import Activity, CropCycle, CropInput, Harvest  # noqa: F401
from app.modules.farms.models import Farm  # noqa: F401
from app.modules.finance.models import Expense, Income, InputCredit, Loan  # noqa: F401
from app.modules.livestock.models import (  # noqa: F401
    BreedingRecord,
    DiseaseEvent,
    FeedRecord,
    Livestock,
    Vaccination,
    WeightRecord,
)
from app.modules.market.models import MarketPrice  # noqa: F401
from app.modules.tenants.models import Tenant  # noqa: F401
from app.modules.tobacco.models import (  # noqa: F401
    TobaccoCuring,
    TobaccoCycle,
    TobaccoDelivery,
    TobaccoGrading,
    TobaccoReaping,
)
from app.modules.weather.models import WeatherAlert, WeatherRecord  # noqa: F401
from app.notifications.models import Notification, NotificationPreference  # noqa: F401
from app.predictions.models import Prediction  # noqa: F401
from app.simulations.models import Simulation  # noqa: F401
from app.whatsapp.models import WhatsAppContact  # noqa: F401

__all__ = ["Base"]
