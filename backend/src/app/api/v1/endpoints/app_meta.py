"""App config / bootstrap — Module 13 (APP-01, APP-02)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header
from sqlalchemy import select

from app.api.deps import DbSession
from app.core.config import get_settings
from app.core.security import decode_access_token
from app.models.user import User
from app.schemas.app_meta import AppBootstrapOut, AppConfigOut
from app.services.app_meta import AppMetaService

router = APIRouter(tags=["app"])


def get_app_meta_service(db: DbSession) -> AppMetaService:
    return AppMetaService(session=db)


AppMetaServiceDep = Annotated[AppMetaService, Depends(get_app_meta_service)]


@router.get(
    "/app/config",
    response_model=AppConfigOut,
    summary="Remote app config (APP-01)",
)
async def app_config(svc: AppMetaServiceDep) -> AppConfigOut:
    return await svc.get_config()


@router.get(
    "/app/bootstrap",
    response_model=AppBootstrapOut,
    summary="Cold-start bootstrap (APP-02)",
)
async def app_bootstrap(
    svc: AppMetaServiceDep,
    db: DbSession,
    authorization: Annotated[str | None, Header()] = None,
) -> AppBootstrapOut:
    user: User | None = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        try:
            settings = get_settings()
            payload = decode_access_token(token, settings=settings)
            raw_sub = payload.get("sub")
            if raw_sub:
                user = (
                    await db.execute(select(User).where(User.id == UUID(str(raw_sub))).limit(1))
                ).scalar_one_or_none()
        except Exception:
            user = None
    return await svc.bootstrap(user)
