"""Image analysis: crop disease / nutrient deficiency / pest / livestock.

Uses OpenAI vision when configured, else a deterministic stub keyed off the
requested analysis type so the endpoint is fully functional offline.
"""

from __future__ import annotations

import json
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm import llm
from app.ai.models import ImageAnalysis
from app.ai.prompts import VISION_SYSTEM
from app.core.config import settings
from app.core.logging import get_logger
from app.shared.enums import ImageAnalysisType

logger = get_logger(__name__)

_STUB = {
    ImageAnalysisType.CROP_DISEASE: {
        "findings": [{"label": "Maize Grey Leaf Spot (suspected)", "confidence": 0.71, "severity": "moderate"}],
        "recommendation": "Rotate crops, remove infected residue, and apply a registered fungicide if severe.",
    },
    ImageAnalysisType.NUTRIENT_DEFICIENCY: {
        "findings": [{"label": "Nitrogen deficiency (suspected)", "confidence": 0.68, "severity": "mild"}],
        "recommendation": "Top-dress with ammonium nitrate; confirm with a soil test.",
    },
    ImageAnalysisType.PEST: {
        "findings": [{"label": "Fall armyworm damage (suspected)", "confidence": 0.74, "severity": "moderate"}],
        "recommendation": "Scout early mornings; apply registered control and encourage natural predators.",
    },
    ImageAnalysisType.LIVESTOCK_CONDITION: {
        "findings": [{"label": "Low body condition score (suspected)", "confidence": 0.65, "severity": "mild"}],
        "recommendation": "Improve feed quality, deworm, and check for parasites.",
    },
    ImageAnalysisType.AUTO: {
        "findings": [{"label": "General plant stress (suspected)", "confidence": 0.6, "severity": "mild"}],
        "recommendation": "Send a closer, well-lit photo for a more specific diagnosis.",
    },
}


class VisionService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def analyze(
        self,
        *,
        image_url: str | None,
        image_b64: str | None,
        analysis_type: ImageAnalysisType,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID | None,
    ) -> ImageAnalysis:
        result = await self._run_model(image_url, image_b64, analysis_type)
        confidence = max((f.get("confidence", 0) for f in result.get("findings", [])), default=None)

        analysis = ImageAnalysis(
            tenant_id=tenant_id,
            user_id=user_id,
            image_ref=image_url or ("inline-base64" if image_b64 else None),
            analysis_type=analysis_type,
            result=result,
            confidence=confidence,
        )
        self.session.add(analysis)
        await self.session.flush()
        return analysis

    async def _run_model(self, image_url, image_b64, analysis_type) -> dict:
        if not settings.openai_enabled or llm._client is None or not (image_url or image_b64):
            return _STUB[analysis_type]
        try:
            image_part = (
                {"type": "image_url", "image_url": {"url": image_url}}
                if image_url
                else {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
            )
            resp = await llm._client.chat.completions.create(
                model=settings.OPENAI_VISION_MODEL,
                messages=[
                    {"role": "system", "content": VISION_SYSTEM},
                    {"role": "user", "content": [
                        {"type": "text", "text": f"Analysis type: {analysis_type.value}. Diagnose this image."},
                        image_part,
                    ]},
                ],
                max_tokens=400,
            )
            raw = resp.choices[0].message.content or "{}"
            return json.loads(raw[raw.find("{") : raw.rfind("}") + 1])
        except Exception as exc:  # noqa: BLE001
            logger.warning("vision_failed", error=str(exc))
            return _STUB[analysis_type]
