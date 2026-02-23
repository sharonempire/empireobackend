from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.documents.models import Document
from app.modules.documents.schemas import DocumentCreate


async def list_documents(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    entity_type: str | None = None,
    entity_id: UUID | None = None,
) -> tuple[list[Document], int]:
    stmt = select(Document)
    count_stmt = select(func.count()).select_from(Document)

    if entity_type:
        stmt = stmt.where(Document.entity_type == entity_type)
        count_stmt = count_stmt.where(Document.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(Document.entity_id == entity_id)
        count_stmt = count_stmt.where(Document.entity_id == entity_id)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(Document.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def get_document(db: AsyncSession, document_id: UUID) -> Document:
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise NotFoundError("Document not found")
    return doc


async def create_document(db: AsyncSession, data: DocumentCreate, uploaded_by: UUID) -> Document:
    doc = Document(**data.model_dump(), uploaded_by=uploaded_by)
    db.add(doc)
    await db.flush()
    return doc


async def verify_document(db: AsyncSession, document_id: UUID, verified_by: UUID) -> Document:
    doc = await get_document(db, document_id)
    doc.is_verified = True
    doc.verified_by = verified_by
    doc.verified_at = datetime.now(timezone.utc)
    await db.flush()
    return doc
