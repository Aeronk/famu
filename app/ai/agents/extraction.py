"""Intent classification + entity extraction.

Uses the LLM when configured; otherwise a robust rule-based extractor that works
fully offline (the default path for demos). Handles English, Shona and Ndebele
keywords for the common data-capture intents.
"""

from __future__ import annotations

import json
import re

from app.ai.agents.schemas import ExtractionResult
from app.ai.llm import llm
from app.ai.prompts import EXTRACTION_SYSTEM
from app.shared.enums import CropType, Language

# ---- lexicons (multilingual) ---------------------------------------------- #
CROP_SYNONYMS = {
    "maize": CropType.MAIZE, "mealies": CropType.MAIZE, "corn": CropType.MAIZE,
    "chibage": CropType.MAIZE, "ummbila": CropType.MAIZE,
    "tobacco": CropType.TOBACCO, "fodya": CropType.TOBACCO, "ugwayi": CropType.TOBACCO,
    "soybeans": CropType.SOYBEANS, "soya": CropType.SOYBEANS, "soybean": CropType.SOYBEANS,
    "wheat": CropType.WHEAT, "gorosi": CropType.WHEAT,
    "cotton": CropType.COTTON, "donje": CropType.COTTON,
    "groundnuts": CropType.GROUNDNUTS, "nyimo": CropType.GROUNDNUTS, "nzungu": CropType.GROUNDNUTS,
    "vegetables": CropType.VEGETABLES, "muriwo": CropType.VEGETABLES,
}
ANIMAL_SYNONYMS = {
    "cattle": "cattle", "cow": "cattle", "cows": "cattle", "mombe": "cattle", "inkomo": "cattle",
    "goat": "goats", "goats": "goats", "mbudzi": "goats", "imbuzi": "goats",
    "sheep": "sheep", "hwai": "sheep", "izimvu": "sheep",
    "pig": "pigs", "pigs": "pigs", "nguruve": "pigs",
    "poultry": "poultry", "chicken": "poultry", "chickens": "poultry", "huku": "poultry", "inkukhu": "poultry",
}

PLANT_KW = ("plant", "planted", "dyara", "kudyara", "tshala", "ngilime", "sown", "sow")
VAX_KW = ("vaccinat", "baiwa", "gonyel", "injection", "immuni")
HARVEST_KW = ("harvest", "reap", "goho", "vun", "kohwa")
EXPENSE_KW = ("spent", "bought", "paid", "purchas", "cost", "tenga")
DISEASE_KW = ("sick", "disease", "chirwere", "infected", "dying", "ill")
GREETING_KW = ("hello", "hi", "hey", "mhoro", "sawubona", "makadii", "good morning")
QUESTION_KW = ("how", "when", "what", "why", "which", "recommend", "should i", "advice", "best")


def _first_number(text: str) -> float | None:
    m = re.search(r"(\d+(?:[.,]\d+)?)", text)
    return float(m.group(1).replace(",", ".")) if m else None


def _unit(text: str) -> str | None:
    t = text.lower()
    for u in ("hectare", "hectares", "ha", "acre", "acres", "kg", "kgs", "kilograms", "bags", "tonnes", "tons"):
        if re.search(rf"\b{u}\b", t):
            return {"hectares": "ha", "hectare": "ha", "kgs": "kg", "kilograms": "kg"}.get(u, u)
    return None


def _match(text: str, mapping: dict):
    t = text.lower()
    for word, value in mapping.items():
        if re.search(rf"\b{re.escape(word)}\b", t):
            return value
    return None


def _has(text: str, keywords) -> bool:
    t = text.lower()
    return any(k in t for k in keywords)


def rule_based(text: str) -> ExtractionResult:
    crop = _match(text, CROP_SYNONYMS)
    animal = _match(text, ANIMAL_SYNONYMS)
    number = _first_number(text)
    unit = _unit(text)
    amount_match = re.search(r"(?:\$|usd\s*)(\d+(?:[.,]\d+)?)", text.lower())

    if _has(text, GREETING_KW) and not (crop or animal):
        return ExtractionResult(intent="greeting", entities={}, confidence=0.9)

    if _has(text, VAX_KW) or (animal and "vaccin" in text.lower()):
        return ExtractionResult(
            intent="record_vaccination",
            entities={"count": int(number) if number else 1, "animal": animal or "cattle"},
            confidence=0.85,
        )
    if _has(text, PLANT_KW) and crop:
        return ExtractionResult(
            intent="record_planting",
            entities={"crop": crop.value, "area": number or 0, "unit": unit or "ha"},
            confidence=0.9,
        )
    if _has(text, HARVEST_KW):
        return ExtractionResult(
            intent="record_harvest",
            entities={"crop": crop.value if crop else None, "quantity": number or 0, "unit": unit or "kg"},
            confidence=0.8,
        )
    if _has(text, EXPENSE_KW) or amount_match:
        amount = float(amount_match.group(1).replace(",", ".")) if amount_match else number
        return ExtractionResult(
            intent="record_expense",
            entities={"amount": amount or 0, "currency": "USD"},
            confidence=0.75,
        )
    if _has(text, DISEASE_KW):
        return ExtractionResult(
            intent="record_disease",
            entities={"animal": animal, "crop": crop.value if crop else None, "count": int(number) if number else 1},
            confidence=0.7,
        )
    if "?" in text or _has(text, QUESTION_KW):
        return ExtractionResult(intent="ask_question", entities={"query": text}, confidence=0.7)

    return ExtractionResult(intent="unknown", entities={}, confidence=0.3)


async def extract(text: str, *, lang: Language = Language.EN) -> ExtractionResult:
    if not llm.enabled:
        return rule_based(text)
    try:
        raw = await llm.chat(
            system=EXTRACTION_SYSTEM,
            user=text,
            temperature=0.0,
            max_tokens=200,
        )
        data = json.loads(raw[raw.find("{") : raw.rfind("}") + 1])
        return ExtractionResult(
            intent=data.get("intent", "unknown"),
            entities=data.get("entities", {}) or {},
            confidence=0.9,
        )
    except Exception:  # noqa: BLE001 — never fail extraction; fall back to rules
        return rule_based(text)
