from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.ai.advisory.service import AdvisoryService
from app.ai.agents.graph import run_agent
from app.ai.agents.schemas import AgentDeps
from app.ai.recommendation.service import RecommendationService
from app.ai.schemas import (
    AskRequest,
    AskResponse,
    ChatRequest,
    ChatResponse,
    ImageAnalysisOut,
    ImageAnalyzeRequest,
)
from app.ai.vision.service import VisionService
from app.api.deps import CurrentUser, DbSession, TenantId, require_perm
from app.shared.enums import Language
from app.shared.exceptions import ValidationAppError

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/ask", response_model=AskResponse, dependencies=[Depends(require_perm("ai:read"))])
async def ask(payload: AskRequest, session: DbSession, user: CurrentUser):
    language = payload.language or user.language or Language.EN
    result = await AdvisoryService(session).ask(
        payload.question, tenant_id=user.tenant_id, language=language
    )
    return result


@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(require_perm("ai:read"))])
async def chat(payload: ChatRequest, session: DbSession, user: CurrentUser, tenant_id: TenantId):
    """Run the full data-capture agent on free text (web / mobile / API)."""
    deps = AgentDeps(session=session, tenant_id=tenant_id, user_id=user.id)
    reply = await run_agent(payload.text, deps)
    # Capture the NLU example so the intent/entity extractor can be fine-tuned.
    from app.datasets.service import DatasetService

    await DatasetService(session, tenant_id).record_nlu(
        text=payload.text, intent=reply.intent, entities=reply.entities,
        channel=payload.channel.value, created_by=user.id,
    )
    return ChatResponse(**reply.model_dump())


@router.post("/analyze-image", response_model=ImageAnalysisOut, dependencies=[Depends(require_perm("ai:read"))])
async def analyze_image(payload: ImageAnalyzeRequest, session: DbSession, user: CurrentUser, tenant_id: TenantId):
    if not payload.image_url and not payload.image_b64:
        raise ValidationAppError("Provide image_url or image_b64")
    return await VisionService(session).analyze(
        image_url=payload.image_url,
        image_b64=payload.image_b64,
        analysis_type=payload.analysis_type,
        tenant_id=tenant_id,
        user_id=user.id,
    )


# ---- Recommendation agent ----
_rec = RecommendationService()


@router.get("/recommendations/planting", dependencies=[Depends(require_perm("ai:read"))])
async def rec_planting(crop: str = Query(...)):
    return _rec.planting(crop)


@router.get("/recommendations/fertilizer", dependencies=[Depends(require_perm("ai:read"))])
async def rec_fertilizer(crop: str = Query(...)):
    return _rec.fertilizer(crop)


@router.get("/recommendations/irrigation", dependencies=[Depends(require_perm("ai:read"))])
async def rec_irrigation(crop: str = Query(...)):
    return _rec.irrigation(crop)


@router.get("/recommendations/vaccination", dependencies=[Depends(require_perm("ai:read"))])
async def rec_vaccination(species: str = Query(...)):
    return _rec.vaccination(species)
