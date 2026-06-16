"""Request-scoped tenant context stored in a ``contextvar``.

Lets any layer (repositories, RLS GUC, logging) read the active tenant without
threading it through every call signature.
"""

from __future__ import annotations

import contextvars
from dataclasses import dataclass


@dataclass
class TenantContext:
    tenant_id: str | None = None
    user_id: str | None = None
    role: str | None = None


# Default None (not a mutable instance); callers get an empty context.
_ctx: contextvars.ContextVar[TenantContext | None] = contextvars.ContextVar(
    "tenant_context", default=None
)


def set_tenant_context(ctx: TenantContext) -> contextvars.Token:
    return _ctx.set(ctx)


def reset_tenant_context(token: contextvars.Token) -> None:
    _ctx.reset(token)


def get_tenant_context() -> TenantContext:
    return _ctx.get() or TenantContext()


def current_tenant_id() -> str | None:
    ctx = _ctx.get()
    return ctx.tenant_id if ctx else None
