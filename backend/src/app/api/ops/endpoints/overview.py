"""Ops overview — Module 9 (OPS-DASH-01)."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import DbSession
from app.api.ops.deps import CurrentOpsOperator
from app.schemas.ops_dashboard import OpsOverviewOut
from app.services.ops_dashboard import OpsDashboardService

router = APIRouter(tags=["ops-dashboard"])


def get_ops_dashboard_service(db: DbSession) -> OpsDashboardService:
    return OpsDashboardService(session=db)


OpsDashboardServiceDep = Annotated[OpsDashboardService, Depends(get_ops_dashboard_service)]


@router.get(
    "/overview",
    response_model=OpsOverviewOut,
    summary="Ops overview counts (OPS-DASH-01)",
)
async def overview(
    _ops: CurrentOpsOperator,
    svc: OpsDashboardServiceDep,
) -> OpsOverviewOut:
    return await svc.overview()
