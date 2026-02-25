from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import require_perm
from app.modules.saved_items import service
from app.modules.saved_items.schemas import SavedJobOut
from app.modules.users.models import User

router = APIRouter(prefix="/saved-items", tags=["Saved Items"])


@router.get("/jobs", response_model=PaginatedResponse[SavedJobOut])
async def api_list_saved_jobs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user_id: int | None = None,
    current_user: User = Depends(require_perm("saved_items", "read")),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_saved_jobs(db, page, size, user_id)
    return {**paginate_metadata(total, page, size), "items": items}
