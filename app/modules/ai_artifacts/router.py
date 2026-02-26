from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import log_event
from app.core.pagination import PaginatedResponse, paginate_metadata
from app.database import get_db
from app.dependencies import require_perm
from app.modules.ai_artifacts import service
from app.modules.ai_artifacts.schemas import AiArtifactCreate, AiArtifactOut
from app.modules.users.models import User

router = APIRouter(prefix="/ai-artifacts", tags=["AI Artifacts"])


@router.get("/", response_model=PaginatedResponse[AiArtifactOut])
async def api_list_ai_artifacts(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    artifact_type: str | None = None,
    entity_type: str | None = None,
    entity_id: UUID | None = None,
    current_user: User = Depends(require_perm("ai_artifacts", "read")),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_ai_artifacts(db, page, size, artifact_type, entity_type, entity_id)
    return {**paginate_metadata(total, page, size), "items": items}


@router.get("/{artifact_id}", response_model=AiArtifactOut)
async def api_get_ai_artifact(
    artifact_id: UUID,
    current_user: User = Depends(require_perm("ai_artifacts", "read")),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_ai_artifact(db, artifact_id)


@router.post("/", response_model=AiArtifactOut, status_code=201)
async def api_create_ai_artifact(
    data: AiArtifactCreate,
    current_user: User = Depends(require_perm("ai_artifacts", "create")),
    db: AsyncSession = Depends(get_db),
):
    artifact = await service.create_ai_artifact(db, data, current_user.id)
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
