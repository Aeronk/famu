"""Field-level encryption helper (Fernet / AES-128-CBC + HMAC).

Use for encrypting sensitive values at rest (e.g. external provider tokens).
The key comes from ``FERNET_KEY`` or is derived deterministically from
``SECRET_KEY`` so the platform works without extra configuration.
"""

from __future__ import annotations

import base64
import hashlib
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


@lru_cache
def _fernet() -> Fernet:
    if settings.FERNET_KEY:
        key = settings.FERNET_KEY.encode()
    else:
        digest = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def decrypt(token: str) -> str:
    try:
        return _fernet().decrypt(token.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("Could not decrypt value") from exc
