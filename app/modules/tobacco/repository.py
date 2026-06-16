from __future__ import annotations

from app.modules.tobacco.models import (
    TobaccoCuring,
    TobaccoCycle,
    TobaccoDelivery,
    TobaccoGrading,
    TobaccoReaping,
)
from app.tenancy.repository import TenantRepository


class TobaccoCycleRepo(TenantRepository[TobaccoCycle]):
    model = TobaccoCycle


class ReapingRepo(TenantRepository[TobaccoReaping]):
    model = TobaccoReaping


class CuringRepo(TenantRepository[TobaccoCuring]):
    model = TobaccoCuring


class GradingRepo(TenantRepository[TobaccoGrading]):
    model = TobaccoGrading


class DeliveryRepo(TenantRepository[TobaccoDelivery]):
    model = TobaccoDelivery
