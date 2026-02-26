"""Seed missing payments and chat permissions (create, delete)

The payments router uses require_perm("payments", "create") and
require_perm("payments", "delete") but only payments:read was seeded
in migration 0004. Similarly, chat:create was missing.

Revision ID: 0007
Revises: 0006
Create Date: 2026-02-26
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Permissions missing from migration 0004 but used in routers
MISSING_PERMISSIONS = [
    ("payments", "create"),
    ("payments", "delete"),
    ("chat", "create"),
]


def upgrade() -> None:
    # Insert missing permissions (idempotent)
    for resource, action in MISSING_PERMISSIONS:
        desc = f"{resource}:{action}"
        op.execute(f"""
            INSERT INTO eb_permissions (id, resource, action, description)
            SELECT gen_random_uuid(), '{resource}', '{action}', '{desc}'
            WHERE NOT EXISTS (
                SELECT 1 FROM eb_permissions
                WHERE resource = '{resource}' AND action = '{action}'
            )
        """)

    # Grant all new permissions to admin and ceo roles
    for role_name in ("admin", "ceo"):
        for resource, action in MISSING_PERMISSIONS:
            op.execute(f"""
                INSERT INTO eb_role_permissions (role_id, permission_id)
                SELECT r.id, p.id
                FROM eb_roles r
                CROSS JOIN eb_permissions p
                WHERE r.name = '{role_name}'
                  AND p.resource = '{resource}' AND p.action = '{action}'
                  AND NOT EXISTS (
                      SELECT 1 FROM eb_role_permissions rp
                      WHERE rp.role_id = r.id AND rp.permission_id = p.id
                  )
            """)

    # Grant payments:create to manager (can create orders)
    op.execute("""
        INSERT INTO eb_role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM eb_roles r
        CROSS JOIN eb_permissions p
        WHERE r.name = 'manager'
          AND p.resource = 'payments' AND p.action = 'create'
          AND NOT EXISTS (
              SELECT 1 FROM eb_role_permissions rp
              WHERE rp.role_id = r.id AND rp.permission_id = p.id
          )
    """)

    # Grant chat:create to manager and counselor (they send messages)
    op.execute("""
        INSERT INTO eb_role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM eb_roles r
        CROSS JOIN eb_permissions p
        WHERE r.name IN ('manager', 'counselor')
          AND p.resource = 'chat' AND p.action = 'create'
          AND NOT EXISTS (
              SELECT 1 FROM eb_role_permissions rp
              WHERE rp.role_id = r.id AND rp.permission_id = p.id
          )
    """)


def downgrade() -> None:
    # Remove role-permission mappings for the newly added permissions
    for resource, action in MISSING_PERMISSIONS:
        op.execute(f"""
            DELETE FROM eb_role_permissions
            WHERE permission_id IN (
                SELECT id FROM eb_permissions
                WHERE resource = '{resource}' AND action = '{action}'
            )
        """)

    # Remove the permissions themselves
    for resource, action in MISSING_PERMISSIONS:
        op.execute(f"""
            DELETE FROM eb_permissions
            WHERE resource = '{resource}' AND action = '{action}'
        """)
