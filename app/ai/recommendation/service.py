"""Rule-based recommendation agent (ML-ready interface).

Encodes agronomic best-practice for Zimbabwean conditions. Swap individual
methods for model-backed logic later without changing the API surface.
"""

from __future__ import annotations

PLANTING_WINDOWS = {
    "maize": {"window": "Mid-November to mid-December (onset of rains)", "plant_population": "44,000–53,000 plants/ha"},
    "tobacco": {"window": "Seedbeds June–July; transplant September–October", "plant_population": "~16,000–20,000 plants/ha"},
    "soybeans": {"window": "Late November to December", "plant_population": "~330,000 plants/ha"},
    "wheat": {"window": "May (winter, irrigated)", "plant_population": "250–300 plants/m²"},
    "cotton": {"window": "November to early December", "plant_population": "~50,000–60,000 plants/ha"},
    "groundnuts": {"window": "November to December", "plant_population": "~180,000 plants/ha"},
    "vegetables": {"window": "Year-round under irrigation", "plant_population": "crop-dependent"},
}

FERTILIZER = {
    "maize": [
        {"stage": "Planting", "product": "Compound D (7:14:7)", "rate": "250–350 kg/ha"},
        {"stage": "Knee-height (4–6 weeks)", "product": "Ammonium Nitrate", "rate": "200–250 kg/ha"},
    ],
    "tobacco": [
        {"stage": "Planting", "product": "Compound C / S", "rate": "as per soil test"},
        {"stage": "Top-dress", "product": "Ammonium Nitrate", "rate": "split applications"},
    ],
    "soybeans": [
        {"stage": "Planting", "product": "Single Super Phosphate + inoculant", "rate": "200–300 kg/ha"},
    ],
    "wheat": [
        {"stage": "Planting", "product": "Compound D", "rate": "300 kg/ha"},
        {"stage": "Tillering", "product": "Ammonium Nitrate", "rate": "200–300 kg/ha"},
    ],
}

IRRIGATION = {
    "default": [
        {"stage": "Establishment", "frequency": "Every 2–3 days", "amount": "Light, frequent"},
        {"stage": "Vegetative", "frequency": "Every 5–7 days", "amount": "Moderate"},
        {"stage": "Reproductive (critical)", "frequency": "Every 4–5 days", "amount": "High — avoid stress"},
        {"stage": "Maturity", "frequency": "Reduce / stop", "amount": "Low"},
    ]
}

VACCINATION = {
    "cattle": [
        {"vaccine": "Blackleg (clostridial)", "schedule": "Calves 2–3 months + booster, then annually"},
        {"vaccine": "Anthrax", "schedule": "Annually in endemic areas"},
        {"vaccine": "Lumpy Skin Disease", "schedule": "Annually before the wet season"},
    ],
    "goats": [
        {"vaccine": "Pulpy kidney (enterotoxaemia)", "schedule": "Annually + booster for kids"},
        {"vaccine": "Pasteurellosis", "schedule": "As advised before wet season"},
    ],
    "sheep": [
        {"vaccine": "Pulpy kidney", "schedule": "Annually + booster for lambs"},
    ],
    "pigs": [
        {"vaccine": "Erysipelas", "schedule": "Breeding stock twice yearly"},
    ],
    "poultry": [
        {"vaccine": "Newcastle Disease", "schedule": "Day-old, repeat every 3 months"},
        {"vaccine": "Gumboro (IBD)", "schedule": "Weeks 2 and 3"},
    ],
}


class RecommendationService:
    def planting(self, crop: str) -> dict:
        info = PLANTING_WINDOWS.get(crop.lower(), {"window": "Plant at the onset of reliable rains", "plant_population": "n/a"})
        return {"crop": crop, **info}

    def fertilizer(self, crop: str) -> dict:
        return {"crop": crop, "schedule": FERTILIZER.get(crop.lower(), [])}

    def irrigation(self, crop: str) -> dict:
        return {"crop": crop, "schedule": IRRIGATION["default"]}

    def vaccination(self, species: str) -> dict:
        return {"species": species, "schedule": VACCINATION.get(species.lower(), [])}
