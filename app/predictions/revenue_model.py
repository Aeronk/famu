from __future__ import annotations

from typing import Any

from app.predictions.base import ModelService

# Indicative farmgate prices (USD per tonne) — overridden by live market data.
DEFAULT_PRICE_PER_TONNE = {
    "maize": 300.0,
    "tobacco": 3000.0,
    "soybeans": 600.0,
    "wheat": 450.0,
    "cotton": 700.0,
    "groundnuts": 800.0,
    "vegetables": 500.0,
}


class RevenueModel(ModelService):
    name = "revenue"

    def predict(self, features: dict[str, Any]) -> dict[str, Any]:
        crop = str(features.get("crop", "maize")).lower()
        expected_yield = float(features.get("expected_yield", 0) or 0)  # tonnes
        price = features.get("price_per_tonne")
        if price is None:
            price = DEFAULT_PRICE_PER_TONNE.get(crop, 400.0)
        price = float(price)
        costs = float(features.get("costs", 0) or 0)

        revenue = round(expected_yield * price, 2)
        profit = round(revenue - costs, 2)
        return {
            "crop": crop,
            "expected_yield": expected_yield,
            "price_per_tonne": price,
            "revenue": revenue,
            "expenses": round(costs, 2),
            "profit": profit,
            "margin_pct": round((profit / revenue * 100) if revenue else 0.0, 2),
            "confidence": 0.65,
        }
