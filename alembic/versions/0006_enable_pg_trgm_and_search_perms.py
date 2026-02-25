"""Enable pg_trgm extension + seed search/analytics/ai_copilot/utility permissions.

Revision ID: 0006
Revises: 0005
"""

revision = "0006"
down_revision = "0005"

from alembic import op


def upgrade():
    # Enable pg_trgm for trigram similarity search (fuzzy matching)
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # Enable pgvector if not already enabled
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Seed permissions for new modules
    new_resources = [
        "search", "analytics", "ai_copilot", "utility",
        "freelance", "push_tokens", "saved_items",
        "leads", "attendance",
    ]
    actions = ["read", "create", "update", "delete"]

    for resource in new_resources:
        for action in actions:
            op.execute(f"""
                INSERT INTO eb_permissions (resource, action)
                SELECT '{resource}', '{action}'
                WHERE NOT EXISTS (
                    SELECT 1 FROM eb_permissions WHERE resource = '{resource}' AND action = '{action}'
                )
            """)

    # Grant all new permissions to admin role
    op.execute("""
        INSERT INTO eb_role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM eb_roles r, eb_permissions p
        WHERE r.name = 'admin'
          AND p.resource IN ('search', 'analytics', 'ai_copilot', 'utility', 'freelance', 'push_tokens', 'saved_items', 'leads', 'attendance')
          AND NOT EXISTS (
              SELECT 1 FROM eb_role_permissions rp WHERE rp.role_id = r.id AND rp.permission_id = p.id
          )
    """)

    # Grant read permissions to manager and counselor roles
    op.execute("""
        INSERT INTO eb_role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM eb_roles r, eb_permissions p
        WHERE r.name IN ('manager', 'counselor')
          AND p.resource IN ('search', 'analytics', 'ai_copilot')
          AND p.action = 'read'
          AND NOT EXISTS (
              SELECT 1 FROM eb_role_permissions rp WHERE rp.role_id = r.id AND rp.permission_id = p.id
          )
    """)

    # Grant leads CRUD to counselor + manager (they work with leads daily)
    op.execute("""
        INSERT INTO eb_role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM eb_roles r, eb_permissions p
        WHERE r.name IN ('manager', 'counselor')
          AND p.resource = 'leads'
          AND NOT EXISTS (
              SELECT 1 FROM eb_role_permissions rp WHERE rp.role_id = r.id AND rp.permission_id = p.id
          )
    """)

    # Grant attendance read+create to all roles (everyone checks in/out)
    op.execute("""
        INSERT INTO eb_role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM eb_roles r, eb_permissions p
        WHERE r.name IN ('manager', 'counselor', 'processor', 'viewer')
          AND p.resource = 'attendance'
          AND p.action IN ('read', 'create')
          AND NOT EXISTS (
              SELECT 1 FROM eb_role_permissions rp WHERE rp.role_id = r.id AND rp.permission_id = p.id
          )
    """)

    # Grant attendance update to manager (to mark check-outs for others)
    op.execute("""
        INSERT INTO eb_role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM eb_roles r, eb_permissions p
        WHERE r.name = 'manager'
          AND p.resource = 'attendance'
          AND p.action = 'update'
          AND NOT EXISTS (
              SELECT 1 FROM eb_role_permissions rp WHERE rp.role_id = r.id AND rp.permission_id = p.id
          )
    """)


def downgrade():
    resources = "('search', 'analytics', 'ai_copilot', 'utility', 'freelance', 'push_tokens', 'saved_items', 'leads', 'attendance')"

    op.execute(f"""
        DELETE FROM eb_role_permissions WHERE permission_id IN (
            SELECT id FROM eb_permissions WHERE resource IN {resources}
        )
    """)
    op.execute(f"DELETE FROM eb_permissions WHERE resource IN {resources}")

    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
