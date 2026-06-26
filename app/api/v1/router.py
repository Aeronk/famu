"""Aggregate all module routers under the versioned API prefix."""

from __future__ import annotations

from fastapi import APIRouter

from app.ai.router import router as ai_router
from app.analytics.router import router as analytics_router
from app.datasets.router import router as datasets_router
from app.modules.auth.router import router as auth_router
from app.modules.crops.router import router as crops_router
from app.modules.farms.router import router as farms_router
from app.modules.finance.router import router as finance_router
from app.modules.livestock.router import router as livestock_router
from app.modules.market.router import router as market_router
from app.modules.tenants.router import router as tenants_router
from app.modules.tobacco.router import router as tobacco_router
from app.modules.weather.router import router as weather_router
from app.notifications.router import router as notifications_router
from app.predictions.router import router as predictions_router
from app.simulations.router import router as simulations_router

api_router = APIRouter()

for r in (
    auth_router,
    tenants_router,
    farms_router,
    crops_router,
    tobacco_router,
    livestock_router,
    finance_router,
    weather_router,
    market_router,
    ai_router,
    predictions_router,
    simulations_router,
    analytics_router,
    notifications_router,
    datasets_router,
):
    api_router.include_router(r)
