"""Public content endpoints — Module 12 (SUP-01, SUP-02, SUP-06)."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import DbSession
from app.models.content import LegalDocType
from app.schemas.content import ContactChannelsOut, FaqListOut, LegalDocumentOut
from app.services.content import ContentService

router = APIRouter(tags=["content"])


def get_content_service(db: DbSession) -> ContentService:
    return ContentService(session=db)


ContentServiceDep = Annotated[ContentService, Depends(get_content_service)]


@router.get(
    "/content/faq",
    response_model=FaqListOut,
    summary="FAQ entries (SUP-01)",
)
async def list_faq(svc: ContentServiceDep) -> FaqListOut:
    return await svc.list_faq()


@router.get(
    "/content/legal/{doc_type}",
    response_model=LegalDocumentOut,
    summary="Legal document (SUP-02)",
)
async def get_legal(doc_type: LegalDocType, svc: ContentServiceDep) -> LegalDocumentOut:
    return await svc.get_legal(doc_type)


@router.get(
    "/support/contact",
    response_model=ContactChannelsOut,
    summary="Contact channels (SUP-06)",
)
async def support_contact(svc: ContentServiceDep) -> ContactChannelsOut:
    return await svc.contact()
