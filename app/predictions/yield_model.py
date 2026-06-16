from __future__ import annotations

from typing import Any

from app.predictions.base import ModelService, clamp

# Attainable yield potential (tonnes/ha) under good management in Zimbabwe.
BASE_YIELD_T_HA = {
    "maize": 5.0,
    "tobacco": 2.5,
    "soybeans": 2.8,
    "wheat": 5.5,
    "cotton": 2.0,
    "groundnuts": 1.6,
    "vegetables": 20.0,
}


class YieldModel(ModelService):
    name = "yield"

    def predict(self, features: dict[str, Any]) -> dict[str, Any]:
        crop = str(features.get("crop", "maize")).lower()
        area = float(features.get("area", 1) or 0)
        base = BASE_YIELD_T_HA.get(crop, 3.0)

        # Factors default to neutral; supplying them increases confidence.
        rainfall = features.get("rainfall_mm")
        weather_factor = self._rainfall_factor(rainfall) if rainfall is not None else 0.85
        input_factor = float(features.get("fertilizer_factor", 0.85))
        variety_factor = 1.1 if features.get("variety") else 1.0
        history_factor = float(features.get("history_factor", 1.0))

        per_ha = base * weather_factor * input_factor * variety_factor * history_factor
        expected = round(per_ha * area, 2)

        provided = sum(
            1 for k in ("rainfall_mm", "fertilizer_factor", "variety", "history_factor")
            if features.get(k) is not None
        )
        confidence = round(clamp(0.55 + provided * 0.1, 0.5, 0.9), 2)

        return {
            "crop": crop,
            "area_ha": area,
            "expected_yield": expected,
            "expected_yield_per_ha": round(per_ha, 2),
            "unit": "tonnes",
            "confidence": confidence,
            "drivers": {
                "base_yield_t_ha": base,
                "weather_factor": round(weather_factor, 2),
                "input_factor": round(input_factor, 2),
                "variety_factor": variety_factor,
            },
        }

    @staticmethod
    def _rainfall_factor(rainfall_mm: float) -> float:
        # Seasonal rainfall adequacy curve (very rough): ~650mm ideal for maize.
        r = float(rainfall_mm)
        if r <= 0:
            return 0.4
        return clamp(0.4 + (r / 650.0) * 0.6, 0.4, 1.1)
