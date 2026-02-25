"""Seed employee_automation permissions and grant to admin/ceo roles

Revision ID: 0005
Revises: 0004
Create Date: 2026-02-25
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

RESOURCE = "employee_automation"
ACTIONS = ["read", "create", "update", "delete"]


def upgrade() -> None:
    conn = op.get_bind()

    # Insert permissions (idempotent)
    for action in ACTIONS:
        conn.execute(
            op.inline_literal(
                f"""
                INSERT INTO eb_permissions (resource, action)
                SELECT '{RESOURCE}', '{action}'
                WHERE NOT EXISTS (
                    SELECT 1 FROM eb_permissions
                    WHERE resource = '{RESOURCE}' AND action = '{action}'
                )
                """
            )
        )

    # Grant all employee_automation permissions to admin and ceo roles
    for role_name in ("admin", "ceo"):
        conn.execute(
            op.inline_literal(
                f"""
                INSERT INTO eb_role_permissions (role_id, permission_id)
                SELECT r.id, p.id
                FROM eb_roles r
                CROSS JOIN eb_permissions p
                WHERE r.name = '{role_name}'
                  AND p.resource = '{RESOURCE}'
                  AND NOT EXISTS (
                      SELECT 1 FROM eb_role_permissions rp
                      WHERE rp.role_id = r.id AND rp.permission_id = p.id
                  )
                """
            )
        )


def downgrade() -> None:
    conn = op.get_bind()
    # Remove role-permission mappings
    conn.execute(
        op.inline_literal(
            f"""
            DELETE FROM eb_role_permissions
            WHERE permission_id IN (
                SELECT id FROM eb_permissions WHERE resource = '{RESOURCE}'
            )
            """
        )
    )
    # Remove permissions
    conn.execute(
        op.inline_literal(
            f"""DELETE FROM eb_permissions WHERE resource = '{RESOURCE}'"""
        )
    )
