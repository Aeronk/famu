"""Middleware that resolves the tenant from the JWT and populates the context.

Best-effort: a missing/invalid token simply leaves the context empty — the auth
dependencies in ``app.api.deps`` perform the authoritative check. WhatsApp
requests resolve their tenant per-message (phone -> contact) in the pipeline.
"""

from __future__ import annotations

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.security import decode_access_token
from app.tenancy.context import (
    TenantContext,
    reset_tenant_context,
    set_tenant_context,
)


class TenantContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        ctx = TenantContext()
        auth = request.headers.get("authorization", "")
        if auth.startswith("Bearer "):
            try:
                payload = decode_access_token(auth[7:])
                ctx = TenantContext(
                    tenant_id=payload.get("tenant_id"),
                    user_id=payload.get("sub"),
                    role=payload.get("role"),
                )
            except Exception:  # noqa: BLE001 — invalid token handled later by deps
                ctx = TenantContext()

        token = set_tenant_context(ctx)
        structlog.contextvars.bind_contextvars(
            tenant_id=ctx.tenant_id, user_id=ctx.user_id
        )
        try:
            return await call_next(request)
        finally:
            reset_tenant_context(token)
            structlog.contextvars.clear_contextvars()
