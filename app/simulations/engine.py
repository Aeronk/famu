"""Scenario simulation engine.

Reuses the heuristic yield + revenue models to compare a baseline plan against a
"what-if" scenario (crop swap, rainfall change, price change, input change).
"""

from __future__ import annotations

from app.predictions.revenue_model import RevenueModel
from app.predictions.yield_model import YieldModel
from app.simulations.schemas import Outcome, SimulationRequest, SimulationResult

_yield = YieldModel()
_revenue = RevenueModel()


def _outcome(*, crop: str, area: float, rainfall: float, fert: float, price, costs: float) -> Outcome:
    y = _yield.predict(
        {"crop": crop, "area": area, "rainfall_mm": rainfall, "fertilizer_factor": fert}
    )
    r = _revenue.predict(
        {"crop": crop, "expected_yield": y["expected_yield"], "price_per_tonne": price, "costs": costs}
    )
    return Outcome(
        crop=crop,
        area_ha=area,
        expected_yield=y["expected_yield"],
        revenue=r["revenue"],
        costs=r["expenses"],
        profit=r["profit"],
    )


def run_simulation(req: SimulationRequest) -> SimulationResult:
    baseline = _outcome(
        crop=req.crop.value,
        area=req.area,
        rainfall=req.rainfall_mm,
        fert=req.fertilizer_factor,
        price=req.price_per_tonne,
        costs=req.costs,
    )

    sc = req.scenario
    new_crop = (sc.new_crop.value if sc.new_crop else req.crop.value)
    new_area = sc.area if sc.area is not None else req.area
    new_rain = req.rainfall_mm * (1 + sc.rainfall_delta_pct / 100)
    new_fert = sc.fertilizer_factor if sc.fertilizer_factor is not None else req.fertilizer_factor
    new_costs = sc.costs if sc.costs is not None else req.costs
    new_price = None
    if req.price_per_tonne is not None:
        new_price = req.price_per_tonne * (1 + sc.price_delta_pct / 100)

    scenario = _outcome(
        crop=new_crop,
        area=new_area,
        rainfall=new_rain,
        fert=new_fert,
        price=new_price,
        costs=new_costs,
    )

    def delta(a: float, b: float) -> dict:
        return {"absolute": round(b - a, 2), "pct": round(((b - a) / a * 100) if a else 0.0, 2)}

    deltas = {
        "expected_yield": delta(baseline.expected_yield, scenario.expected_yield),
        "revenue": delta(baseline.revenue, scenario.revenue),
        "profit": delta(baseline.profit, scenario.profit),
    }
    return SimulationResult(baseline=baseline, scenario=scenario, deltas=deltas)
