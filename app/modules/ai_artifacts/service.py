"""AI Artifacts service layer."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.ai_artifacts.models import AiArtifact
from app.modules.ai_artifacts.schemas import AiArtifactCreate


async def list_ai_artifacts(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    artifact_type: str | None = None,
    entity_type: str | None = None,
    entity_id: UUID | None = None,
) -> tuple[list[AiArtifact], int]:
    stmt = select(AiArtifact)
    if artifact_type:
        stmt = stmt.where(AiArtifact.artifact_type == artifact_type)
    if entity_type:
        stmt = stmt.where(AiArtifact.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(AiArtifact.entity_id == entity_id)
    stmt = stmt.order_by(AiArtifact.created_at.desc())

    count_query = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    result = await db.execute(stmt.offset((page - 1) * size).limit(size))
    return result.scalars().all(), total


async def get_ai_artifact(db: AsyncSession, artifact_id: UUID) -> AiArtifact:
    result = await db.execute(
        select(AiArtifact).where(AiArtifact.id == artifact_id)
    )
    artifact = result.scalar_one_or_none()
    if not artifact:
        raise NotFoundError("AI artifact not found")
    return artifact


async def create_ai_artifact(
    db: AsyncSession, data: AiArtifactCreate, created_by: UUID
) -> AiArtifact:
    artifact = AiArtifact(**data.model_dump(), created_by=created_by)
    db.add(artifact)
    await db.flush()
    return artifact
