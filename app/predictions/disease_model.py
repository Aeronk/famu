from __future__ import annotations

from typing import Any

from app.predictions.base import ModelService, clamp

# Relative disease susceptibility weighting per crop.
CROP_SUSCEPTIBILITY = {
    "maize": 0.6,
    "tobacco": 0.8,
    "soybeans": 0.5,
    "wheat": 0.5,
    "cotton": 0.7,
    "groundnuts": 0.5,
    "vegetables": 0.85,
}


class DiseaseModel(ModelService):
    name = "disease"

    def predict(self, features: dict[str, Any]) -> dict[str, Any]:
        crop = str(features.get("crop", "maize")).lower()
        humidity = float(features.get("humidity", 60))
        rainfall = float(features.get("rainfall_mm", 5))
        temp = float(features.get("temp_c", 24))

        susceptibility = CROP_SUSCEPTIBILITY.get(crop, 0.6)

        # Warm + humid + wet conditions favour fungal/bacterial disease.
        humidity_score = clamp((humidity - 50) / 50, 0, 1)         # 50->0, 100->1
        rainfall_score = clamp(rainfall / 30, 0, 1)                # 30mm+ -> 1
        temp_score = clamp(1 - abs(temp - 26) / 20, 0, 1)          # peak ~26C

        probability = clamp(
            0.15 + susceptibility * (0.45 * humidity_score + 0.3 * rainfall_score + 0.25 * temp_score),
            0.0,
            0.98,
        )
        risk = "HIGH" if probability >= 0.66 else "MEDIUM" if probability >= 0.4 else "LOW"

        return {
            "crop": crop,
            "risk": risk,
            "probability": round(probability, 2),
            "confidence": 0.7,
            "factors": {
                "humidity": humidity,
                "rainfall_mm": rainfall,
                "temp_c": temp,
                "susceptibility": susceptibility,
            },
        }
