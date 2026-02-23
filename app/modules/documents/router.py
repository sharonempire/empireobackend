from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import log_event
from app.core.pagination import PaginatedResponse, paginate
from app.database import get_db
from app.dependencies import get_current_user, require_perm
from app.modules.documents.schemas import DocumentCreate, DocumentOut
from app.modules.documents.service import create_document, list_documents, verify_document
from app.modules.users.models import User

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("/", response_model=PaginatedResponse[DocumentOut])
async def api_list_documents(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    entity_type: str | None = None,
    entity_id: UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    docs, total = await list_documents(db, page, size, entity_type, entity_id)
    return {**paginate(total, page, size), "items": docs}


@router.post("/", response_model=DocumentOut, status_code=201)
async def api_create_document(
    data: DocumentCreate,
    current_user: User = Depends(require_perm("documents", "create")),
    db: AsyncSession = Depends(get_db),
):
    doc = await create_document(db, data, current_user.id)
    await log_event(db, "document.created", current_user.id, "document", doc.id, {"file_name": doc.file_name})
    await db.commit()
    return doc


@router.patch("/{document_id}/verify", response_model=DocumentOut)
async def api_verify_document(
    document_id: UUID,
    current_user: User = Depends(require_perm("documents", "update")),
    db: AsyncSession = Depends(get_db),
):
    doc = await verify_document(db, document_id, current_user.id)
    await log_event(db, "document.verified", current_user.id, "document", doc.id)
    await db.commit()
    return doc
