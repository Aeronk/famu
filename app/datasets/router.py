from __future__ import annotations

import csv
import io
import json
import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from app.api.deps import CurrentUser, DbSession, Pagination, TenantId, require_perm
from app.datasets.schemas import (
    DatasetStats,
    TrainingExampleCreate,
    TrainingExampleOut,
    TrainingExampleUpdate,
)
from app.datasets.service import DatasetService
from app.shared.enums import DatasetStatus, Role
from app.shared.exceptions import PermissionDeniedError
from app.shared.schemas import Page

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("", response_model=DatasetStats, dependencies=[Depends(require_perm("dataset:read"))])
async def dataset_stats(session: DbSession, tenant_id: TenantId):
    return await DatasetService(session, tenant_id).stats()


@router.get("/examples", response_model=Page[TrainingExampleOut], dependencies=[Depends(require_perm("dataset:read"))])
async def list_examples(
    session: DbSession,
    tenant_id: TenantId,
    pagination: Pagination,
    dataset: str | None = Query(None),
    status: DatasetStatus | None = Query(None),
):
    items, total = await DatasetService(session, tenant_id).list_examples(
        dataset=dataset, status=status, offset=pagination.offset, limit=pagination.limit
    )
    return Page(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


@router.post("/examples", response_model=TrainingExampleOut, dependencies=[Depends(require_perm("dataset:create"))])
async def add_example(payload: TrainingExampleCreate, session: DbSession, tenant_id: TenantId, user: CurrentUser):
    return await DatasetService(session, tenant_id).add(
        dataset=payload.dataset, features=payload.features, label=payload.label,
        channel=payload.channel.value, source=payload.source, ref_type=payload.ref_type,
        ref_id=payload.ref_id, created_by=user.id, notes=payload.notes,
    )


@router.patch("/examples/{example_id}", response_model=TrainingExampleOut, dependencies=[Depends(require_perm("dataset:update"))])
async def update_example(example_id: uuid.UUID, payload: TrainingExampleUpdate, session: DbSession, tenant_id: TenantId):
    return await DatasetService(session, tenant_id).update_example(
        example_id, status=payload.status, label=payload.label, notes=payload.notes
    )


@router.post("/build/yield", dependencies=[Depends(require_perm("dataset:update"))])
async def build_yield(session: DbSession, tenant_id: TenantId):
    count = await DatasetService(session, tenant_id).build_yield_dataset()
    return {"dataset": "yield", "examples_built": count}


@router.post("/feed-national", dependencies=[Depends(require_perm("dataset:export"))])
async def feed_national(
    session: DbSession,
    tenant_id: TenantId,
    dataset: str = Query(...),
    status: DatasetStatus | None = Query(DatasetStatus.VERIFIED, description="Default: only verified (gold) examples"),
):
    """Anonymize and feed examples to the national AI service (always anonymized)."""
    return await DatasetService(session, tenant_id).feed_national(dataset=dataset, status=status)


@router.get("/export", dependencies=[Depends(require_perm("dataset:export"))])
async def export_dataset(
    session: DbSession,
    tenant_id: TenantId,
    user: CurrentUser,
    dataset: str = Query(...),
    format: str = Query("jsonl", pattern="^(jsonl|csv)$"),
    status: DatasetStatus | None = Query(None),
    anonymize: bool = Query(True, description="Strip identifiers (default). Raw export needs Super Admin."),
):
    # Privacy: only Super Admin may export raw (de-anonymized) data.
    if not anonymize and user.role != Role.SUPER_ADMIN:
        raise PermissionDeniedError("Raw export requires Super Admin; use anonymize=true")
    rows = await DatasetService(session, tenant_id).export_rows(
        dataset=dataset, status=status, anonymize=anonymize
    )

    if format == "csv":
        buf = io.StringIO()
        fieldnames: list[str] = []
        for r in rows:
            for k in r:
                if k not in fieldnames:
                    fieldnames.append(k)
        writer = csv.DictWriter(buf, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: _flat(v) for k, v in r.items()})
        content, media = buf.getvalue(), "text/csv"
        ext = "csv"
    else:
        content = "\n".join(json.dumps(r, default=str) for r in rows)
        media, ext = "application/x-ndjson", "jsonl"

    return Response(
        content=content,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{dataset}.{ext}"'},
    )


def _flat(v):
    return json.dumps(v, default=str) if isinstance(v, dict | list) else v
