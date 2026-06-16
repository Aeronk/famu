"""Data-capture tools: turn extracted intents into real domain records.

Each tool calls the proper domain service (so tenant scoping, events and
validation all apply) and returns a localized reply key for the responder.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from app.ai.agents.schemas import AgentDeps
from app.modules.crops.repository import CropCycleRepo
from app.modules.crops.schemas import CropCycleCreate, HarvestCreate
from app.modules.crops.service import CropService
from app.modules.farms.repository import FarmRepo
from app.modules.finance.schemas import ExpenseCreate
from app.modules.finance.service import FinanceService
from app.modules.livestock.schemas import DiseaseEventCreate, VaccinationCreate
from app.modules.livestock.service import LivestockService
from app.shared.enums import CropCycleStatus, CropType


@dataclass
class ToolResult:
    success: bool
    reply_key: str
    reply_kwargs: dict = field(default_factory=dict)
    record_id: str | None = None
    follow_up_key: str | None = None


async def _default_farm(deps: AgentDeps):
    repo = FarmRepo(deps.session, deps.tenant_id)
    if deps.user_id:
        owned = await repo.find_one(owner_user_id=deps.user_id)
        if owned:
            return owned
    existing = await repo.list(limit=1)
    if existing:
        return existing[0]
    return await repo.create(name="Home Farm", owner_user_id=deps.user_id)


async def record_planting(deps: AgentDeps, entities: dict) -> ToolResult:
    farm = await _default_farm(deps)
    try:
        crop = CropType(entities.get("crop", "maize"))
    except ValueError:
        crop = CropType.MAIZE
    area = float(entities.get("area") or 0)
    cycle = await CropService(deps.session, deps.tenant_id).create_cycle(
        CropCycleCreate(
            farm_id=farm.id,
            crop_type=crop,
            area_ha=area,
            planting_date=date.today(),
            status=CropCycleStatus.PLANTED,
        )
    )
    return ToolResult(
        success=True,
        reply_key="planting_recorded",
        reply_kwargs={"area": area, "crop": crop.value},
        record_id=str(cycle.id),
    )


async def record_vaccination(deps: AgentDeps, entities: dict) -> ToolResult:
    count = int(entities.get("count") or 1)
    vac = await LivestockService(deps.session, deps.tenant_id).add_vaccination(
        VaccinationCreate(head_count=count, vaccination_date=date.today())
    )
    return ToolResult(
        success=True,
        reply_key="vaccination_recorded",
        reply_kwargs={"count": count},
        record_id=str(vac.id),
        follow_up_key="ask_vaccine",
    )


async def record_harvest(deps: AgentDeps, entities: dict) -> ToolResult:
    repo = CropCycleRepo(deps.session, deps.tenant_id)
    cycles = await repo.list(limit=1)
    if not cycles:
        return ToolResult(success=False, reply_key="not_understood")
    quantity = float(entities.get("quantity") or 0)
    unit = entities.get("unit") or "kg"
    harvest = await CropService(deps.session, deps.tenant_id).add_harvest(
        cycles[0].id, HarvestCreate(quantity=quantity, unit=unit, harvest_date=date.today())
    )
    return ToolResult(
        success=True,
        reply_key="harvest_recorded",
        reply_kwargs={"quantity": quantity, "unit": unit},
        record_id=str(harvest.id),
    )


async def record_expense(deps: AgentDeps, entities: dict) -> ToolResult:
    amount = float(entities.get("amount") or 0)
    if amount <= 0:
        return ToolResult(success=False, reply_key="not_understood")
    expense = await FinanceService(deps.session, deps.tenant_id).add_expense(
        ExpenseCreate(amount=amount, currency=entities.get("currency", "USD"), txn_date=date.today())
    )
    return ToolResult(
        success=True,
        reply_key="expense_recorded",
        reply_kwargs={"amount": amount},
        record_id=str(expense.id),
    )


async def record_disease(deps: AgentDeps, entities: dict) -> ToolResult:
    event = await LivestockService(deps.session, deps.tenant_id).add_disease(
        DiseaseEventCreate(
            head_count=int(entities.get("count") or 1),
            disease=entities.get("disease") or "unspecified",
            diagnosed_date=date.today(),
        )
    )
    return ToolResult(
        success=True,
        reply_key="disease_recorded",
        reply_kwargs={"disease": event.disease},
        record_id=str(event.id),
    )


TOOL_MAP = {
    "record_planting": record_planting,
    "record_vaccination": record_vaccination,
    "record_harvest": record_harvest,
    "record_expense": record_expense,
    "record_disease": record_disease,
}


async def dispatch(intent: str, entities: dict, deps: AgentDeps) -> ToolResult | None:
    tool = TOOL_MAP.get(intent)
    if not tool:
        return None
    return await tool(deps, entities)
