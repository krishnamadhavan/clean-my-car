"""Ops app config — Module 13 (OPS-APP-01/02)."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import DbSession
from app.api.ops.deps import CurrentOpsOperator
from app.schemas.app_meta import AppConfigOut, OpsAppConfigUpdateIn
from app.services.app_meta import AppMetaService
from app.services.ops_platform import OpsPlatformService

router = APIRouter(prefix="/app/config", tags=["ops-app"])


def get_app_meta_service(db: DbSession) -> AppMetaService:
    return AppMetaService(session=db)


AppMetaServiceDep = Annotated[AppMetaService, Depends(get_app_meta_service)]


@router.get(
    "",
    response_model=AppConfigOut,
    summary="Read app config (OPS-APP-01)",
)
async def get_config(_ops: CurrentOpsOperator, svc: AppMetaServiceDep) -> AppConfigOut:
    return await svc.get_config()


@router.put(
    "",
    response_model=AppConfigOut,
    summary="Update app config (OPS-APP-02)",
)
async def put_config(
    body: OpsAppConfigUpdateIn,
    ops: CurrentOpsOperator,
    svc: AppMetaServiceDep,
    db: DbSession,
) -> AppConfigOut:
    result = await svc.ops_update(body)
    await OpsPlatformService(db).record(
        operator=ops,
        action="app_config.update",
        resource_type="app_config",
        summary="Updated remote app config",
        details=body.model_dump(exclude_unset=True),
    )
    return result
