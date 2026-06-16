"""Pure-logic unit tests (no database required)."""

from __future__ import annotations

from app.ai.agents.extraction import rule_based
from app.core.rbac import has_permission
from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.predictions.disease_model import DiseaseModel
from app.predictions.revenue_model import RevenueModel
from app.predictions.yield_model import YieldModel
from app.shared.enums import Language, Role
from app.shared.i18n import detect_language, translate
from app.simulations.engine import run_simulation
from app.simulations.schemas import ScenarioChange, SimulationRequest


def test_password_hash_roundtrip():
    h = hash_password("secret-pw")
    assert h != "secret-pw"
    assert verify_password("secret-pw", h)
    assert not verify_password("wrong", h)


def test_jwt_roundtrip():
    token = create_access_token(subject="u1", role="farmer", tenant_id="t1")
    payload = decode_access_token(token)
    assert payload["sub"] == "u1"
    assert payload["role"] == "farmer"
    assert payload["tenant_id"] == "t1"


def test_refresh_token_hash_is_deterministic():
    raw, h = generate_refresh_token()
    assert hash_token(raw) == h


def test_rbac_matrix():
    assert has_permission(Role.SUPER_ADMIN, "anything:weird")
    assert has_permission(Role.TENANT_ADMIN, "farm:create")
    assert has_permission(Role.FARMER, "crop:create")
    assert not has_permission(Role.VIEWER, "farm:create")
    assert has_permission(Role.VIEWER, "farm:read")


def test_language_detection():
    assert detect_language("I planted maize today") == Language.EN
    assert detect_language("ndakadyara chibage munda") == Language.SN
    assert detect_language("ngilime ummbila namuhla insimu") == Language.ND


def test_translate_fallback():
    assert "ha" in translate("planting_recorded", Language.EN, area=2, crop="maize")
    # Unknown key falls back to the key itself.
    assert translate("nope_missing", Language.EN) == "nope_missing"


def test_extraction_planting():
    res = rule_based("I planted 2 hectares of maize")
    assert res.intent == "record_planting"
    assert res.entities["crop"] == "maize"
    assert res.entities["area"] == 2


def test_extraction_vaccination():
    res = rule_based("I vaccinated 20 cattle today")
    assert res.intent == "record_vaccination"
    assert res.entities["count"] == 20


def test_extraction_question():
    res = rule_based("When should I plant tobacco?")
    assert res.intent in ("ask_question", "record_planting")  # contains 'plant'
    # Pure question without a verb keyword:
    assert rule_based("What is the best fertilizer?").intent == "ask_question"


def test_yield_model():
    out = YieldModel().predict({"crop": "maize", "area": 2, "rainfall_mm": 650})
    assert out["expected_yield"] > 0
    assert 0.5 <= out["confidence"] <= 0.9


def test_disease_model_levels():
    high = DiseaseModel().predict({"crop": "tobacco", "humidity": 95, "rainfall_mm": 30, "temp_c": 26})
    low = DiseaseModel().predict({"crop": "maize", "humidity": 40, "rainfall_mm": 0, "temp_c": 15})
    assert high["probability"] > low["probability"]
    assert high["risk"] in ("MEDIUM", "HIGH")


def test_revenue_model():
    out = RevenueModel().predict({"crop": "maize", "expected_yield": 10, "costs": 500})
    assert out["revenue"] == 3000.0
    assert out["profit"] == 2500.0


def test_simulation_crop_swap():
    req = SimulationRequest(
        crop="maize", area=2, rainfall_mm=600, fertilizer_factor=0.9, price_per_tonne=300, costs=400,
        scenario=ScenarioChange(new_crop="vegetables", rainfall_delta_pct=-20),
    )
    result = run_simulation(req)
    assert result.baseline.crop == "maize"
    assert result.scenario.crop == "vegetables"
    assert "profit" in result.deltas
