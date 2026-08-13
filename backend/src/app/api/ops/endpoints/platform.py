"""Ops platform — audit + seed preview (OPS-PLAT-02/03)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import DbSession
from app.api.ops.deps import CurrentOpsOperator
from app.schemas.ops_platform import AuditEventListOut, SeedPreviewIn, SeedPreviewOut
from app.services.ops_platform import OpsPlatformService

router = APIRouter(tags=["ops-platform"])


def get_ops_platform_service(db: DbSession) -> OpsPlatformService:
    return OpsPlatformService(session=db)


OpsPlatformServiceDep = Annotated[OpsPlatformService, Depends(get_ops_platform_service)]


@router.get(
    "/audit",
    response_model=AuditEventListOut,
    summary="Audit log (OPS-PLAT-02)",
)
async def list_audit(
    _ops: CurrentOpsOperator,
    svc: OpsPlatformServiceDep,
    action: Annotated[str | None, Query()] = None,
    resource_type: Annotated[str | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> AuditEventListOut:
    return await svc.list_audit(
        action=action,
        resource_type=resource_type,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/seed/preview",
    response_model=SeedPreviewOut,
    summary="Dry-run bulk seed (OPS-PLAT-03)",
)
async def seed_preview(
    body: SeedPreviewIn,
    ops: CurrentOpsOperator,
    svc: OpsPlatformServiceDep,
) -> SeedPreviewOut:
    result = await svc.seed_preview(body)
    await svc.record(
        operator=ops,
        action="seed.preview",
        resource_type="seed",
        summary=result.message,
        details={
            "would_create_cities": result.would_create_cities,
            "would_create_societies": result.would_create_societies,
        },
    )
    return result
