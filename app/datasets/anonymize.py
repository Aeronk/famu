"""Privacy-preserving anonymization for shared training data.

Individual farmers must not be identifiable in exported / nationally-shared
datasets — not even by tenant admins. We:

* replace the row id with a **stable salted pseudonym** (HMAC) so records can
  still be linked for learning, but not traced back to a person;
* drop overly-granular location (village, GPS) — keep region (province/district)
  which is useful and non-identifying at scale;
* redact phone-number-like PII from free text (e.g. NLU messages).
"""

from __future__ import annotations

import hashlib
import hmac
import re

from app.core.config import settings

# Feature keys too granular to share (could re-identify a farmer).
_DROP_KEYS = {"feature.village", "feature.gps_lat", "feature.gps_lng"}
_PHONE_RE = re.compile(r"\+?\d[\d\s\-]{7,}\d")


def _salt() -> bytes:
    return (settings.ANON_SALT or settings.SECRET_KEY).encode()


def pseudonym(value: str) -> str:
    return hmac.new(_salt(), str(value).encode(), hashlib.sha256).hexdigest()[:16]


def _redact(text: str) -> str:
    return _PHONE_RE.sub("[redacted]", text)


def anonymize_row(row: dict) -> dict:
    out: dict = {}
    if "id" in row:
        out["subject"] = pseudonym(row["id"])  # stable, non-reversible
    for k, v in row.items():
        if k == "id" or k in _DROP_KEYS:
            continue
        if k == "feature.text" and isinstance(v, str):
            v = _redact(v)
        out[k] = v
    return out
