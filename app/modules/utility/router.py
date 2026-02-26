from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import log_event
from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import require_perm
from app.modules.utility import service
from app.modules.utility.schemas import ChatbotSessionOut, ShortLinkCreate, ShortLinkOut
from app.modules.users.models import User

router = APIRouter(prefix="/utility", tags=["Utility"])


@router.get("/short-links", response_model=PaginatedResponse[ShortLinkOut])
async def api_list_short_links(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    current_user: User = Depends(require_perm("utility", "read")),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_short_links(db, page, size)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/short-links/{code}", response_model=ShortLinkOut)
async def api_get_short_link(
    code: str,
    current_user: User = Depends(require_perm("utility", "read")),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_short_link(db, code)


@router.post("/short-links", response_model=ShortLinkOut, status_code=201)
async def api_create_short_link(
    data: ShortLinkCreate,
    current_user: User = Depends(require_perm("utility", "create")),
    db: AsyncSession = Depends(get_db),
):
    item = await service.create_short_link(db, data)
    await log_event(db, "short_link.created", current_user.id, "short_link", str(item.id), {
        "code": item.code, "target_url": data.target_url,
    })
    await db.commit()
    return item


@router.get("/chatbot-sessions", response_model=PaginatedResponse[ChatbotSessionOut])
async def api_list_chatbot_sessions(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    current_user: User = Depends(require_perm("utility", "read")),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_chatbot_sessions(db, page, size)
    return {**paginate_metadata(total, page, size), "items": items}
