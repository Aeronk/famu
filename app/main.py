"""FastAPI application factory for Famu / Murimi OS."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.core.rate_limit import RateLimitMiddleware
from app.core.redis import close_redis
from app.shared.exceptions import register_exception_handlers
from app.tenancy.middleware import TenantContextMiddleware
from app.whatsapp.webhook import router as whatsapp_router

logger = get_logger(__name__)

DESCRIPTION = """
**Murimi OS** — an AI-powered, WhatsApp-first Farm Operating System for African farmers.

Multi-tenant SaaS covering farm management, AI advisory, data capture, yield &
disease prediction, simulations, weather and market intelligence.
""".strip()


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger.info(
        "startup",
        env=settings.ENV,
        openai=settings.openai_enabled,
        whatsapp=settings.whatsapp_enabled,
        weather=settings.weather_enabled,
    )
    yield
    await close_redis()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description=DESCRIPTION,
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(TenantContextMiddleware)

    register_exception_handlers(app)

    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    app.include_router(whatsapp_router)  # /webhooks/whatsapp (root, per Meta spec)

    @app.get("/health", tags=["system"])
    async def health():
        return {"status": "ok", "app": settings.APP_NAME, "env": settings.ENV}

    @app.get("/", tags=["system"])
    async def root():
        return {
            "name": settings.APP_NAME,
            "docs": "/docs",
            "health": "/health",
            "api": settings.API_V1_PREFIX,
        }

    return app


app = create_app()
