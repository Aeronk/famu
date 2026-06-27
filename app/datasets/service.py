"""Training-data service: capture, curate and export structured examples.

Every channel (web / mobile / WhatsApp / API) funnels labeled examples here so
the platform accumulates a clean, exportable dataset for model learning:

* ``yield``       features (crop, area, inputs, weather…) + label (actual yield)
* ``disease``     conditions + diagnosis label
* ``nlu_intent``  message text + extracted intent/entities (for NLU fine-tuning)
* ``vision``      image ref + findings label

Auto-captured rows start ``unverified``; human review promotes them to
``verified`` (gold) or ``rejected``.
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.datasets.models import TrainingExample
from app.datasets.repository import TrainingExampleRepo
from app.shared.enums import Channel, DatasetName, DatasetStatus

logger = get_logger(__name__)


class DatasetService:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.tid = str(tenant_id)
        self.repo = TrainingExampleRepo(session, tenant_id)

    # ------------------------------------------------------------------ #
    # Generic add / upsert
    # ------------------------------------------------------------------ #
    async def add(
        self,
        *,
        dataset: str,
        features: dict,
        label: dict,
        channel: str = Channel.API.value,
        source: str = "manual",
        ref_type: str | None = None,
        ref_id: str | None = None,
        status: DatasetStatus = DatasetStatus.UNVERIFIED,
        created_by: uuid.UUID | None = None,
        notes: str | None = None,
    ) -> TrainingExample:
        # Dedupe auto-captured rows by (dataset, ref) so re-captures update in place.
        existing = None
        if ref_id:
            existing = await self.repo.find_one(dataset=dataset, ref_type=ref_type, ref_id=ref_id)
        if existing:
            # Never overwrite a human-verified/rejected label.
            if existing.status == DatasetStatus.UNVERIFIED:
                existing.features = features
                existing.label = label
            return existing
        return await self.repo.create(
            dataset=dataset, features=features, label=label, channel=channel,
            source=source, ref_type=ref_type, ref_id=ref_id, status=status,
            created_by=created_by, notes=notes,
        )

    # ------------------------------------------------------------------ #
    # Channel-agnostic NLU capture (web / mobile / whatsapp)
    # ------------------------------------------------------------------ #
    async def record_nlu(
        self, *, text: str, intent: str, entities: dict, channel: str,
        created_by: uuid.UUID | None = None,
    ) -> None:
        if not text:
            return
        try:
            await self.add(
                dataset=DatasetName.NLU_INTENT.value,
                features={"text": text},
                label={"intent": intent, "entities": entities},
                channel=channel, source="auto", created_by=created_by,
            )
        except Exception as exc:  # noqa: BLE001 — capture must never break the flow
            logger.warning("nlu_capture_failed", error=str(exc))

    # ------------------------------------------------------------------ #
    # Yield capture (from a crop cycle once it has a harvest)
    # ------------------------------------------------------------------ #
    async def capture_yield(self, cycle_id: uuid.UUID, *, channel: str = Channel.SYSTEM.value) -> TrainingExample | None:
        from app.modules.crops.repository import CropCycleRepo, CropInputRepo, HarvestRepo
        from app.modules.farms.repository import FarmRepo
        from app.modules.weather.models import WeatherRecord

        cycle = await CropCycleRepo(self.session, self.tenant_id).get(cycle_id)
        if not cycle:
            return None
        harvests = await HarvestRepo(self.session, self.tenant_id).list(crop_cycle_id=cycle_id, limit=500)
        if not harvests:
            return None
        inputs = await CropInputRepo(self.session, self.tenant_id).list(crop_cycle_id=cycle_id, limit=500)
        farm = await FarmRepo(self.session, self.tenant_id).get(cycle.farm_id)

        total_kg = sum(_to_kg(h.quantity, h.unit) for h in harvests)
        fert_kg = sum((i.quantity or 0) for i in inputs if i.type.value == "fertilizer")
        input_cost = sum(float(i.cost or 0) for i in inputs)

        rainfall = None
        if farm:
            rw = (
                await self.session.execute(
                    select(WeatherRecord.rainfall_mm)
                    .where(WeatherRecord.tenant_id == self.tid, WeatherRecord.farm_id == farm.id)
                    .order_by(WeatherRecord.observed_at.desc())
                    .limit(1)
                )
            ).scalar_one_or_none()
            rainfall = float(rw) if rw is not None else None

        features = {
            "crop": cycle.crop_type.value,
            "area_ha": cycle.area_ha,
            "variety": cycle.variety,
            "has_variety": bool(cycle.variety),
            "planting_month": cycle.planting_date.month if cycle.planting_date else None,
            "province": farm.province if farm else None,
            "district": farm.district if farm else None,
            "farming_type": farm.farming_type.value if farm else None,
            "enterprise_type": farm.enterprise_type.value if farm else None,
            "soil_type": farm.soil_type if farm else None,
            "water_source": farm.water_source if farm else None,
            "irrigation_type": farm.irrigation_type if farm else None,
            "fertilizer_kg": fert_kg,
            "input_cost": round(input_cost, 2),
            "num_inputs": len(inputs),
            "rainfall_mm": rainfall,
        }
        label = {
            "yield_tonnes": round(total_kg / 1000, 3),
            "yield_per_ha_t": round((total_kg / 1000) / cycle.area_ha, 3) if cycle.area_ha else None,
        }
        return await self.add(
            dataset=DatasetName.YIELD.value, features=features, label=label,
            channel=channel, source="auto", ref_type="crop_cycle", ref_id=str(cycle_id),
        )

    async def capture_disease(self, event, *, channel: str = Channel.SYSTEM.value) -> None:
        try:
            await self.add(
                dataset=DatasetName.DISEASE.value,
                features={"head_count": event.head_count, "diagnosed_month": event.diagnosed_date.month if event.diagnosed_date else None},
                label={"disease": event.disease, "outcome": event.outcome},
                channel=channel, source="auto", ref_type="disease_event", ref_id=str(event.id),
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("disease_capture_failed", error=str(exc))

    async def capture_vision(self, analysis, *, channel: str = Channel.API.value) -> None:
        try:
            await self.add(
                dataset=DatasetName.VISION.value,
                features={"image_ref": analysis.image_ref, "analysis_type": analysis.analysis_type.value},
                label={"findings": analysis.result.get("findings", []), "confidence": analysis.confidence},
                channel=channel, source="auto", ref_type="image_analysis", ref_id=str(analysis.id),
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("vision_capture_failed", error=str(exc))

    # ------------------------------------------------------------------ #
    # Backfill + curation + export
    # ------------------------------------------------------------------ #
    async def build_yield_dataset(self) -> int:
        from app.modules.crops.models import CropCycle, Harvest

        cycle_ids = (
            await self.session.execute(
                select(CropCycle.id)
                .join(Harvest, Harvest.crop_cycle_id == CropCycle.id)
                .where(CropCycle.tenant_id == self.tid)
                .distinct()
            )
        ).scalars().all()
        count = 0
        for cid in cycle_ids:
            if await self.capture_yield(cid):
                count += 1
        return count

    async def list_examples(self, *, dataset: str | None, status: DatasetStatus | None, offset: int, limit: int):
        filters: dict = {}
        if dataset:
            filters["dataset"] = dataset
        if status:
            filters["status"] = status
        items = await self.repo.list(offset=offset, limit=limit, **filters)
        total = await self.repo.count(**filters)
        return items, total

    async def update_example(self, example_id: uuid.UUID, *, status=None, label=None, notes=None) -> TrainingExample:
        ex = await self.repo.get_or_404(example_id)
        if status is not None:
            ex.status = status
        if label is not None:
            ex.label = label
        if notes is not None:
            ex.notes = notes
        await self.session.flush()
        return ex

    async def stats(self) -> dict:
        rows = (
            await self.session.execute(
                select(TrainingExample.dataset, TrainingExample.status, func.count())
                .where(TrainingExample.tenant_id == self.tid)
                .group_by(TrainingExample.dataset, TrainingExample.status)
            )
        ).all()
        agg: dict[str, dict] = {}
        for dataset, status, n in rows:
            d = agg.setdefault(dataset, {"dataset": dataset, "total": 0, "verified": 0, "unverified": 0, "rejected": 0})
            d["total"] += int(n)
            d[status.value if hasattr(status, "value") else str(status)] += int(n)
        datasets = sorted(agg.values(), key=lambda x: x["dataset"])
        return {"datasets": datasets, "total_examples": sum(d["total"] for d in datasets)}

    @staticmethod
    def flatten(ex) -> dict:
        row = {"id": str(ex.id), "status": ex.status.value, "channel": ex.channel}
        row.update({f"feature.{k}": v for k, v in (ex.features or {}).items()})
        row.update({f"label.{k}": v for k, v in (ex.label or {}).items()})
        return row

    async def export_rows(
        self, *, dataset: str, status: DatasetStatus | None, anonymize: bool = True
    ) -> list[dict]:
        from app.datasets.anonymize import anonymize_row

        filters: dict = {"dataset": dataset}
        if status:
            filters["status"] = status
        examples = await self.repo.list(limit=100000, **filters)
        rows = [self.flatten(ex) for ex in examples]
        return [anonymize_row(r) for r in rows] if anonymize else rows

    async def feed_national(self, *, dataset: str, status: DatasetStatus | None) -> dict:
        """Anonymize and push examples to the national AI; mark them as shared."""
        from datetime import UTC, datetime

        from app.datasets.anonymize import anonymize_row
        from app.datasets.national import feed_national as send

        filters: dict = {"dataset": dataset}
        if status:
            filters["status"] = status
        examples = await self.repo.list(limit=100000, **filters)
        rows = [anonymize_row(self.flatten(ex)) for ex in examples]
        result = await send(dataset, rows)

        now = datetime.now(UTC)
        for ex in examples:
            ex.shared_national = True
            ex.shared_at = now
        await self.session.flush()
        return result


def _to_kg(quantity: float, unit: str | None) -> float:
    u = (unit or "kg").lower()
    if u in ("t", "tonne", "tonnes", "ton", "tons"):
        return float(quantity) * 1000
    if u in ("bag", "bags"):
        return float(quantity) * 50  # assume 50kg bags
    return float(quantity)
