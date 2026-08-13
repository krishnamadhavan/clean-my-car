"""Public content + ops publish (Module 12)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import FaqEntry, LegalDocType, LegalDocument
from app.schemas.content import (
    ContactChannelsOut,
    FaqEntryOut,
    FaqListOut,
    LegalDocumentOut,
    OpsFaqReplaceIn,
    OpsLegalDocumentIn,
)
from app.services.app_meta import AppMetaService


class ContentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.app_meta = AppMetaService(session)

    async def list_faq(self) -> FaqListOut:
        rows = (
            (
                await self.session.execute(
                    select(FaqEntry)
                    .where(FaqEntry.is_active.is_(True))
                    .order_by(FaqEntry.display_order.asc(), FaqEntry.created_at.asc())
                )
            )
            .scalars()
            .all()
        )
        if not rows:
            # Sensible defaults until ops publishes
            defaults = [
                FaqEntryOut(
                    id=uuid.uuid4(),
                    question="How does billing work?",
                    answer="You pay a calendar-month subscription. Mid-month starts are pro-rated.",
                    category="billing",
                    display_order=0,
                ),
                FaqEntryOut(
                    id=uuid.uuid4(),
                    question="What if I miss a wash day?",
                    answer="Our team will attempt a next-day retry when possible.",
                    category="service",
                    display_order=1,
                ),
            ]
            return FaqListOut(items=defaults)
        return FaqListOut(items=[FaqEntryOut.model_validate(r) for r in rows])

    async def get_legal(self, doc_type: LegalDocType) -> LegalDocumentOut:
        row = (
            await self.session.execute(
                select(LegalDocument)
                .where(
                    LegalDocument.doc_type == doc_type,
                    LegalDocument.is_active.is_(True),
                )
                .order_by(LegalDocument.published_at.desc().nulls_last())
                .limit(1)
            )
        ).scalar_one_or_none()
        if row is None:
            # Default stub docs
            titles = {
                LegalDocType.terms: "Terms of Service",
                LegalDocType.privacy: "Privacy Policy",
                LegalDocType.cancellation: "Cancellation Policy",
            }
            return LegalDocumentOut(
                doc_type=doc_type,
                version="0.1",
                title=titles[doc_type],
                body=f"Placeholder {titles[doc_type]} — publish via ops to replace.",
                url=None,
                published_at=None,
            )
        return LegalDocumentOut.model_validate(row)

    async def contact(self) -> ContactChannelsOut:
        cfg = await self.app_meta.get_or_create_config()
        return ContactChannelsOut(
            whatsapp=cfg.support_whatsapp,
            whatsapp_url=cfg.support_whatsapp_url,
            email=cfg.support_email,
            phone=cfg.support_phone,
            message="Reach us on WhatsApp or email for support.",
        )

    async def ops_replace_faq(self, body: OpsFaqReplaceIn) -> FaqListOut:
        await self.session.execute(delete(FaqEntry))
        for item in body.items:
            self.session.add(
                FaqEntry(
                    question=item.question,
                    answer=item.answer,
                    category=item.category,
                    display_order=item.display_order,
                    is_active=item.is_active,
                )
            )
        await self.session.commit()
        return await self.list_faq()

    async def ops_upsert_legal(
        self, doc_type: LegalDocType, body: OpsLegalDocumentIn
    ) -> LegalDocumentOut:
        # Deactivate previous active docs of same type
        existing = (
            (
                await self.session.execute(
                    select(LegalDocument).where(
                        LegalDocument.doc_type == doc_type,
                        LegalDocument.is_active.is_(True),
                    )
                )
            )
            .scalars()
            .all()
        )
        for row in existing:
            row.is_active = False
        doc = LegalDocument(
            doc_type=doc_type,
            version=body.version,
            title=body.title,
            body=body.body,
            url=body.url,
            is_active=body.is_active,
            published_at=datetime.now(UTC) if body.is_active else None,
        )
        self.session.add(doc)
        await self.session.commit()
        await self.session.refresh(doc)
        return LegalDocumentOut.model_validate(doc)
