import math
from typing import Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int
    pages: int


def paginate_metadata(total: int, page: int, size: int) -> dict:
    """Return pagination metadata dict (for routers that do manual queries)."""
    return {
        "total": total,
        "page": page,
        "size": size,
        "pages": math.ceil(total / size) if size > 0 else 0,
    }


async def paginate(
    db: AsyncSession,
    query,
    page: int = 1,
    size: int = 20,
) -> dict:
    """Execute a paginated query and return items + metadata."""
    size = min(max(size, 1), 100)
    page = max(page, 1)
    offset = (page - 1) * size

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Fetch page
    result = await db.execute(query.offset(offset).limit(size))
    items = result.scalars().all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": math.ceil(total / size) if size > 0 else 0,
    }
