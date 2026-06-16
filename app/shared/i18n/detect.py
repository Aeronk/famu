"""Lightweight language detection for English / Shona / Ndebele.

Keyword-frequency heuristic — dependency-free and good enough to route the AI
agent. The LLM layer can refine detection when an OpenAI key is configured.
"""

from __future__ import annotations

import re

from app.shared.enums import Language

# Indicative tokens (lemmas / common words & affixes).
SHONA_MARKERS = {
    "ndakadyara", "ndiri", "mvura", "chibage", "fodya", "mombe", "huku", "mbudzi",
    "ndakadya", "kudyara", "munda", "goho", "ndinoda", "maticha", "zvirimwa",
    "ndinokumbira", "tatenda", "mhoro", "ndave", "ndakapa", "mishonga",
}
NDEBELE_MARKERS = {
    "ngilime", "ngi", "inkomo", "izimvu", "imbuzi", "inkukhu", "amabele",
    "ummbila", "ugwayi", "insimu", "ngifuna", "ngicela", "sawubona", "ngiyabonga",
    "ngifake", "umlimi", "izulu", "amanzi",
}


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z']+", text.lower())


def detect_language(text: str, default: Language = Language.EN) -> Language:
    tokens = set(_tokens(text))
    if not tokens:
        return default
    sn = len(tokens & SHONA_MARKERS)
    nd = len(tokens & NDEBELE_MARKERS)
    if sn == 0 and nd == 0:
        return default
    return Language.SN if sn >= nd else Language.ND
