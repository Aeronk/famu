"""Role-based access control: permission matrix and helpers.

Framework-agnostic. FastAPI dependency factories (`require_role`, `require_perm`)
live in ``app.api.deps`` and consume the helpers here.
"""

from __future__ import annotations

from app.shared.enums import Role

# Coarse-grained permissions. Use "<resource>:<action>" or "<resource>:*".
ALL = "*"

PERMISSIONS: dict[Role, set[str]] = {
    Role.SUPER_ADMIN: {ALL},
    Role.TENANT_ADMIN: {
        "tenant:read",
        "tenant:update",
        "user:*",
        "farm:*",
        "crop:*",
        "tobacco:*",
        "livestock:*",
        "finance:*",
        "weather:*",
        "market:*",
        "ai:*",
        "prediction:*",
        "simulation:*",
        "analytics:*",
        "notification:*",
        "dataset:*",
        "media:*",
    },
    Role.FARM_MANAGER: {
        "farm:*",
        "crop:*",
        "tobacco:*",
        "livestock:*",
        "finance:*",
        "weather:read",
        "market:read",
        "ai:*",
        "prediction:*",
        "simulation:*",
        "analytics:read",
        "notification:read",
        "dataset:*",
        "media:*",
    },
    Role.FARMER: {
        "farm:read",
        "crop:read",
        "crop:create",
        "tobacco:read",
        "livestock:read",
        "livestock:create",
        "finance:read",
        "finance:create",
        "weather:read",
        "market:read",
        "ai:*",
        "prediction:read",
        "simulation:read",
        "analytics:read",
        "media:*",
    },
    Role.EXTENSION_OFFICER: {
        "farm:read",
        "crop:read",
        "tobacco:read",
        "livestock:read",
        "finance:read",
        "weather:read",
        "market:read",
        "ai:*",
        "prediction:*",
        "simulation:*",
        "analytics:read",
        "notification:create",
        "dataset:*",
        "media:*",
    },
    Role.VIEWER: {
        "farm:read",
        "crop:read",
        "tobacco:read",
        "livestock:read",
        "finance:read",
        "weather:read",
        "market:read",
        "analytics:read",
        "media:read",
    },
}


def has_permission(role: Role, permission: str) -> bool:
    """Check whether ``role`` satisfies ``permission`` (supports wildcards)."""
    grants = PERMISSIONS.get(role, set())
    if ALL in grants or permission in grants:
        return True
    resource, _, _action = permission.partition(":")
    return f"{resource}:*" in grants


def is_super_admin(role: Role) -> bool:
    return role == Role.SUPER_ADMIN
