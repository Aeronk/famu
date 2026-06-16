from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, DbSession, TenantId, require_perm
from app.simulations.engine import run_simulation
from app.simulations.models import Simulation
from app.simulations.schemas import SimulationRequest, SimulationResult
from app.tenancy.repository import TenantRepository

router = APIRouter(prefix="/simulations", tags=["simulations"])


class _SimRepo(TenantRepository[Simulation]):
    model = Simulation


@router.post("/run", response_model=SimulationResult, dependencies=[Depends(require_perm("simulation:read"))])
async def run(payload: SimulationRequest, session: DbSession, tenant_id: TenantId, user: CurrentUser):
    result = run_simulation(payload)
    await _SimRepo(session, tenant_id).create(
        user_id=user.id,
        scenario=payload.model_dump(mode="json"),
        result=result.model_dump(mode="json"),
    )
    return result
