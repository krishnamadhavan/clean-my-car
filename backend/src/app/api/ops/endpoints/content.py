"""Ops content publish — Module 12 (OPS-SUP-01/02)."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import DbSession
from app.api.ops.deps import CurrentOpsOperator
from app.models.content import LegalDocType
from app.schemas.content import FaqListOut, LegalDocumentOut, OpsFaqReplaceIn, OpsLegalDocumentIn
from app.services.content import ContentService
from app.services.ops_platform import OpsPlatformService

router = APIRouter(tags=["ops-content"])


def get_content_service(db: DbSession) -> ContentService:
    return ContentService(session=db)


ContentServiceDep = Annotated[ContentService, Depends(get_content_service)]


@router.put(
    "/content/faq",
    response_model=FaqListOut,
    summary="Publish FAQ entries (OPS-SUP-01)",
)
async def put_faq(
    body: OpsFaqReplaceIn,
    ops: CurrentOpsOperator,
    svc: ContentServiceDep,
    db: DbSession,
) -> FaqListOut:
    result = await svc.ops_replace_faq(body)
    await OpsPlatformService(db).record(
        operator=ops,
        action="faq.replace",
        resource_type="faq",
        summary=f"Replaced FAQ with {len(body.items)} item(s)",
    )
    return result


@router.put(
    "/content/legal/{doc_type}",
    response_model=LegalDocumentOut,
    summary="Publish legal document (OPS-SUP-02)",
)
async def put_legal(
    doc_type: LegalDocType,
    body: OpsLegalDocumentIn,
    ops: CurrentOpsOperator,
    svc: ContentServiceDep,
    db: DbSession,
) -> LegalDocumentOut:
    result = await svc.ops_upsert_legal(doc_type, body)
    await OpsPlatformService(db).record(
        operator=ops,
        action="legal.publish",
        resource_type="legal",
        resource_id=doc_type.value,
        summary=f"Published {doc_type.value} v{body.version}",
    )
    return result
