from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import log_event
from app.core.exceptions import NotFoundError
from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import require_perm
from app.modules.ai_artifacts.models import AiArtifact
from app.modules.ai_artifacts.schemas import AiArtifactCreate, AiArtifactOut
from app.modules.users.models import User

router = APIRouter(prefix="/ai-artifacts", tags=["AI Artifacts"])


@router.get("/", response_model=PaginatedResponse[AiArtifactOut])
async def api_list_ai_artifacts(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    artifact_type: str | None = None,
    entity_type: str | None = None,
    entity_id: UUID | None = None,
    current_user: User = Depends(require_perm("ai_artifacts", "read")),
    db: AsyncSession = Depends(get_db),
):
    query = select(AiArtifact)
    if artifact_type:
        query = query.where(AiArtifact.artifact_type == artifact_type)
    if entity_type:
        query = query.where(AiArtifact.entity_type == entity_type)
    if entity_id:
        query = query.where(AiArtifact.entity_id == entity_id)
    query = query.order_by(AiArtifact.created_at.desc())

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * size
    result = await db.execute(query.offset(offset).limit(size))
    items = result.scalars().all()

    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/{artifact_id}", response_model=AiArtifactOut)
async def api_get_ai_artifact(
    artifact_id: UUID,
    current_user: User = Depends(require_perm("ai_artifacts", "read")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AiArtifact).where(AiArtifact.id == artifact_id)
    )
    artifact = result.scalar_one_or_none()
    if not artifact:
        raise NotFoundError("AI artifact not found")
    return artifact


@router.post("/", response_model=AiArtifactOut, status_code=201)
async def api_create_ai_artifact(
    data: AiArtifactCreate,
    current_user: User = Depends(require_perm("ai_artifacts", "create")),
    db: AsyncSession = Depends(get_db),
):
    artifact = AiArtifact(**data.model_dump(), created_by=current_user.id)
    db.add(artifact)
    await db.flush()
    await log_event(
        db=db,
        event_type="ai_artifact.created",
        actor_id=current_user.id,
        entity_type="ai_artifact",
        entity_id=artifact.id,
        metadata={"artifact_type": artifact.artifact_type},
    )
    await db.commit()
    return artifact
