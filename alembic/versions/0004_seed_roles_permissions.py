"""Seed default roles, permissions, and admin/ceo role-permission mappings

Revision ID: 0004
Revises: 0003
Create Date: 2026-02-24
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ── Seed data ────────────────────────────────────────────────────────────────

ROLES = [
    ("ceo", "Chief Executive Officer — full access"),
    ("admin", "Administrator — full access"),
    ("manager", "Manager — broad read/write"),
    ("counselor", "Counselor — student-facing"),
    ("processor", "Processor — application processing"),
    ("viewer", "Viewer — read-only"),
]

# Every resource:action pair actually enforced by require_perm() in the codebase,
# plus standard CRUD actions for core resources.
PERMISSIONS = [
    # Core CRM — full CRUD
    ("users", "read"), ("users", "create"), ("users", "update"), ("users", "delete"),
    ("students", "read"), ("students", "create"), ("students", "update"), ("students", "delete"),
    ("cases", "read"), ("cases", "create"), ("cases", "update"), ("cases", "delete"),
    ("applications", "read"), ("applications", "create"), ("applications", "update"), ("applications", "delete"),
    ("documents", "read"), ("documents", "create"), ("documents", "update"), ("documents", "delete"),
    ("tasks", "read"), ("tasks", "create"), ("tasks", "update"), ("tasks", "delete"),
    ("approvals", "read"), ("approvals", "review"),
    ("events", "read"),
    ("notifications", "read"), ("notifications", "update"),
    # Legacy / read-heavy
    ("leads", "read"),
    ("courses", "read"),
    ("geography", "read"),
    ("intakes", "read"),
    ("jobs", "read"),
    ("profiles", "read"),
    ("call_events", "read"),
    ("chat", "read"),
    ("payments", "read"),
    ("attendance", "read"),
    ("ig_sessions", "read"),
    # AI & policies
    ("ai_artifacts", "read"), ("ai_artifacts", "create"),
    ("policies", "read"), ("policies", "create"), ("policies", "update"),
    ("workflows", "read"),
]

# Roles that get every permission
FULL_ACCESS_ROLES = ["admin", "ceo"]


def upgrade() -> None:
    # ── 1. Seed roles ────────────────────────────────────────────────────────
    for name, description in ROLES:
        op.execute(f"""
            INSERT INTO eb_roles (id, name, description, created_at)
            SELECT gen_random_uuid(), '{name}', '{description}', now()
            WHERE NOT EXISTS (
                SELECT 1 FROM eb_roles WHERE name = '{name}'
            )
        """)

    # ── 2. Seed permissions ──────────────────────────────────────────────────
    for resource, action in PERMISSIONS:
        desc = f"{resource}:{action}"
        op.execute(f"""
            INSERT INTO eb_permissions (id, resource, action, description)
            SELECT gen_random_uuid(), '{resource}', '{action}', '{desc}'
            WHERE NOT EXISTS (
                SELECT 1 FROM eb_permissions
                WHERE resource = '{resource}' AND action = '{action}'
            )
        """)

    # ── 3. Grant all permissions to admin and ceo roles ──────────────────────
    for role_name in FULL_ACCESS_ROLES:
        op.execute(f"""
            INSERT INTO eb_role_permissions (role_id, permission_id)
            SELECT r.id, p.id
            FROM eb_roles r
            CROSS JOIN eb_permissions p
            WHERE r.name = '{role_name}'
              AND NOT EXISTS (
                  SELECT 1 FROM eb_role_permissions rp
                  WHERE rp.role_id = r.id AND rp.permission_id = p.id
              )
        """)


def downgrade() -> None:
    # Remove role-permission mappings for seeded roles
    for role_name in FULL_ACCESS_ROLES:
        op.execute(f"""
            DELETE FROM eb_role_permissions
            WHERE role_id = (SELECT id FROM eb_roles WHERE name = '{role_name}')
        """)

    # Remove seeded permissions
    for resource, action in PERMISSIONS:
        op.execute(f"""
            DELETE FROM eb_permissions
            WHERE resource = '{resource}' AND action = '{action}'
        """)

    # Remove seeded roles
    for name, _ in ROLES:
        op.execute(f"""
            DELETE FROM eb_roles WHERE name = '{name}'
        """)
