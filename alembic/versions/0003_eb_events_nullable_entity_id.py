"""Make eb_events.entity_id nullable for events without a target entity

Revision ID: 0003
Revises: 0002
Create Date: 2026-02-24
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("eb_events", "entity_id", nullable=True)


def downgrade() -> None:
    op.execute("UPDATE eb_events SET entity_id = '00000000-0000-0000-0000-000000000000' WHERE entity_id IS NULL")
    op.alter_column("eb_events", "entity_id", nullable=False)
