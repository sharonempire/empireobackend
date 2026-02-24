"""Initial baseline schema

Revision ID: 0001
Revises:
Create Date: 2026-02-24

This is a BASELINE migration.
- On the live Supabase DB: run `alembic stamp head` (tables already exist)
- On fresh local dev: run `alembic upgrade head` (creates all tables)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =====================================================================
    # GROUP 1: Tables with no foreign keys (create first)
    # =====================================================================

    op.create_table(
        "profiles",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("diplay_name", sa.Text(), nullable=True),
        sa.Column("profilepicture", sa.Text(), nullable=True),
        sa.Column("user_type", sa.Text(), nullable=True),
        sa.Column("phone", sa.BigInteger(), nullable=True),
        sa.Column("designation", sa.Text(), nullable=True),
        sa.Column("freelancer_status", sa.Text(), nullable=True),
        sa.Column("location", sa.Text(), nullable=True),
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column("callerId", sa.Text(), nullable=True),
        sa.Column("countries", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("fcm_token", sa.Text(), nullable=True),
        sa.Column("user_id", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("callerId"),
    )

    op.create_table(
        "eb_users",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("department", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True, server_default=sa.text("true")),
        sa.Column("profile_picture", sa.Text(), nullable=True),
        sa.Column("caller_id", sa.String(50), nullable=True),
        sa.Column("location", sa.String(100), nullable=True),
        sa.Column("countries", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("legacy_supabase_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("legacy_supabase_id"),
    )

    op.create_table(
        "eb_roles",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "eb_permissions",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("resource", sa.String(50), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "countries",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("language", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("description", sa.VARCHAR(), nullable=True),
        sa.Column("cities", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("images", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("currency", sa.Text(), nullable=True),
        sa.Column("top_attractions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("portion", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("commission", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("displayimage", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "job_profiles",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("company_name", sa.Text(), nullable=True),
        sa.Column("email_address", sa.Text(), nullable=True),
        sa.Column("profile_id", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=True),
        sa.Column("company_website", sa.Text(), nullable=True),
        sa.Column("company_address", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email_address"),
    )

    op.create_table(
        "jobs_countries",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("country", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("country"),
    )

    op.create_table(
        "short_links",
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("target_url", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("code"),
    )

    op.create_table(
        "chatbot_sessions",
        sa.Column("session_id", sa.Text(), nullable=False),
        sa.Column("last_intent", sa.Text(), nullable=True),
        sa.Column("last_country", sa.Text(), nullable=True),
        sa.Column("last_field", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("session_id"),
    )

    op.create_table(
        "lead_assignment_tracker",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("last_assigned_employee", sa.UUID(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "commission",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("commission_name", sa.VARCHAR(), nullable=True),
        sa.Column("commission_amount", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "domain_keyword_map",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("domain", sa.Text(), nullable=True),
        sa.Column("keywords", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "search_synonyms",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("term", sa.Text(), nullable=True),
        sa.Column("synonyms", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "stopwords",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("word", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("word"),
    )

    op.create_table(
        "backlog_participants",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("participant_id", sa.Text(), nullable=True),
        sa.Column("backlog_data", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "user_profiles",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Text(), nullable=True),
        sa.Column("profile_data", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "eb_workflow_definitions",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("stages", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("transitions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "chat_conversations",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("counselor_id", sa.Text(), nullable=True),
        sa.Column("lead_uuid", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "payments",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("amount", sa.Numeric(), nullable=True),
        sa.Column("currency", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=True),
        sa.Column("payment_method", sa.Text(), nullable=True),
        sa.Column("transaction_id", sa.Text(), nullable=True),
        sa.Column("payment_details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("platform", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # =====================================================================
    # GROUP 2: Tables with FKs to Group 1 (profiles, eb_users, countries, etc.)
    # =====================================================================

    op.create_table(
        "eb_user_roles",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("role_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["eb_users.id"]),
        sa.ForeignKeyConstraint(["role_id"], ["eb_roles.id"]),
        sa.PrimaryKeyConstraint("user_id", "role_id"),
    )

    op.create_table(
        "eb_role_permissions",
        sa.Column("role_id", sa.UUID(), nullable=False),
        sa.Column("permission_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["eb_roles.id"]),
        sa.ForeignKeyConstraint(["permission_id"], ["eb_permissions.id"]),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
    )

    op.create_table(
        "leadslist",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column("phone", sa.BigInteger(), nullable=True),
        sa.Column("freelancer_manager", sa.Text(), nullable=True),
        sa.Column("freelancer", sa.Text(), nullable=True),
        sa.Column("source", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=True),
        sa.Column("follow_up", sa.Text(), nullable=True),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("assigned_to", sa.UUID(), nullable=True),
        sa.Column("draft_status", sa.Text(), nullable=True, server_default=sa.text("'draft'")),
        sa.Column("sl_no", sa.Integer(), autoincrement=True, nullable=True),
        sa.Column("heat_status", sa.Text(), nullable=True),
        sa.Column("info_progress", sa.Text(), nullable=True),
        sa.Column("call_summary", sa.Text(), nullable=True),
        sa.Column("phone_norm", sa.Text(), nullable=True),
        sa.Column("lead_tab", sa.Text(), nullable=True, server_default=sa.text("'student'")),
        sa.Column("date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("changes_history", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("lead_type", sa.Text(), nullable=True),
        sa.Column("documents_status", sa.Text(), nullable=True),
        sa.Column("fresh", sa.Boolean(), nullable=True, server_default=sa.text("true")),
        sa.Column("profile_image", sa.Text(), nullable=True),
        sa.Column("is_premium_jobs", sa.Boolean(), nullable=True),
        sa.Column("is_premium_courses", sa.Boolean(), nullable=True),
        sa.Column("is_resume_downloaded", sa.Boolean(), nullable=True),
        sa.Column("country_preference", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("is_registered", sa.Boolean(), nullable=True),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("fcm_token", sa.Text(), nullable=True),
        sa.Column("finder_type", sa.Text(), nullable=True),
        sa.Column("current_module", sa.Text(), nullable=True),
        sa.Column("preferences_completed", sa.Boolean(), nullable=True),
        sa.Column("profile_completion", sa.BigInteger(), nullable=True),
        sa.Column("ig_handle", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["assigned_to"], ["profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sl_no"),
    )

    op.create_table(
        "eb_students",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("lead_id", sa.BigInteger(), nullable=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("nationality", sa.String(100), nullable=True),
        sa.Column("passport_number", sa.String(50), nullable=True),
        sa.Column("passport_expiry", sa.Date(), nullable=True),
        sa.Column("education_level", sa.String(50), nullable=True),
        sa.Column("education_details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("english_test_type", sa.String(20), nullable=True),
        sa.Column("english_test_score", sa.String(20), nullable=True),
        sa.Column("work_experience_years", sa.Integer(), nullable=True, server_default=sa.text("0")),
        sa.Column("preferred_countries", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("preferred_programs", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("assigned_counselor_id", sa.UUID(), nullable=True),
        sa.Column("assigned_processor_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["assigned_counselor_id"], ["eb_users.id"]),
        sa.ForeignKeyConstraint(["assigned_processor_id"], ["eb_users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("lead_id"),
    )

    op.create_table(
        "eb_notifications",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("notification_type", sa.String(30), nullable=True, server_default=sa.text("'general'")),
        sa.Column("entity_type", sa.String(30), nullable=True),
        sa.Column("entity_id", sa.UUID(), nullable=True),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=True, server_default=sa.text("false")),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["eb_users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "eb_events",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("actor_type", sa.String(30), nullable=True),
        sa.Column("actor_id", sa.UUID(), nullable=True),
        sa.Column("entity_type", sa.String(30), nullable=False),
        sa.Column("entity_id", sa.UUID(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "eb_tasks",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("entity_type", sa.String(30), nullable=True),
        sa.Column("entity_id", sa.UUID(), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("task_type", sa.String(30), nullable=True, server_default=sa.text("'general'")),
        sa.Column("assigned_to", sa.UUID(), nullable=True),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("priority", sa.String(20), nullable=True, server_default=sa.text("'normal'")),
        sa.Column("status", sa.String(20), nullable=True, server_default=sa.text("'pending'")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["assigned_to"], ["eb_users.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["eb_users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "eb_documents",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("entity_type", sa.String(30), nullable=False),
        sa.Column("entity_id", sa.UUID(), nullable=False),
        sa.Column("document_type", sa.String(50), nullable=True),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_key", sa.String(500), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("uploaded_by", sa.UUID(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=True, server_default=sa.text("false")),
        sa.Column("verified_by", sa.UUID(), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["uploaded_by"], ["eb_users.id"]),
        sa.ForeignKeyConstraint(["verified_by"], ["eb_users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "eb_action_drafts",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("entity_type", sa.String(30), nullable=False),
        sa.Column("entity_id", sa.UUID(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_by_type", sa.String(10), nullable=True, server_default=sa.text("'user'")),
        sa.Column("created_by_id", sa.UUID(), nullable=True),
        sa.Column("status", sa.String(30), nullable=True, server_default=sa.text("'pending_approval'")),
        sa.Column("requires_approval", sa.Boolean(), nullable=True, server_default=sa.text("true")),
        sa.Column("approved_by", sa.UUID(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("execution_result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["approved_by"], ["eb_users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "eb_ai_artifacts",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("artifact_type", sa.String(), nullable=False),
        sa.Column("entity_type", sa.String(), nullable=False),
        sa.Column("entity_id", sa.UUID(), nullable=False),
        sa.Column("model_used", sa.String(), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
        sa.Column("input_summary", sa.Text(), nullable=True),
        sa.Column("output", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["eb_users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "eb_policies",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("department", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True, server_default=sa.text("true")),
        sa.Column("version", sa.Integer(), nullable=True, server_default=sa.text("1")),
        sa.Column("embedding", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "attendance",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("checkinat", sa.Text(), nullable=True),
        sa.Column("checkoutat", sa.Text(), nullable=True),
        sa.Column("attendance_status", sa.Text(), nullable=True),
        sa.Column("date", sa.Text(), nullable=True),
        sa.Column("employee_id", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(["employee_id"], ["profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "freelancers",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.VARCHAR(), nullable=True),
        sa.Column("phone_number", sa.BigInteger(), nullable=True),
        sa.Column("email", sa.VARCHAR(), nullable=True),
        sa.Column("address", sa.VARCHAR(), nullable=True),
        sa.Column("description", sa.VARCHAR(), nullable=True),
        sa.Column("creator_id", sa.UUID(), nullable=True),
        sa.Column("commission_percentage", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(["creator_id"], ["profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "freelance_managers",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.VARCHAR(), nullable=False),
        sa.Column("phone_number", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.VARCHAR(), nullable=False),
        sa.Column("commission_tier_id", sa.BigInteger(), nullable=True),
        sa.Column("email", sa.VARCHAR(), nullable=True),
        sa.Column("address", sa.VARCHAR(), nullable=True),
        sa.Column("description", sa.VARCHAR(), nullable=True),
        sa.Column("commission_tier_name", sa.VARCHAR(), nullable=True),
        sa.Column("profile_id", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("phone_number"),
    )

    op.create_table(
        "agent_endpoints",
        sa.Column("agent_key", sa.Text(), nullable=False),
        sa.Column("ext_norm", sa.Text(), nullable=True),
        sa.Column("profile_id", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"]),
        sa.PrimaryKeyConstraint("agent_key"),
        sa.UniqueConstraint("ext_norm"),
    )

    op.create_table(
        "cities",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("country_id", sa.BigInteger(), nullable=True),
        sa.Column("language", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("description", sa.VARCHAR(), nullable=True),
        sa.Column("universities", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("images", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("population", sa.Text(), nullable=True),
        sa.Column("top_attractions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("portion", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("commission", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["country_id"], ["countries.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "call_events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("call_uuid", sa.Text(), nullable=True),
        sa.Column("caller_number", sa.Text(), nullable=True),
        sa.Column("called_number", sa.Text(), nullable=True),
        sa.Column("agent_number", sa.Text(), nullable=True),
        sa.Column("call_status", sa.Text(), nullable=True),
        sa.Column("total_duration", sa.Integer(), nullable=True),
        sa.Column("conversation_duration", sa.Integer(), nullable=True),
        sa.Column("call_start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("call_end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recording_url", sa.Text(), nullable=True),
        sa.Column("dtmf", sa.Text(), nullable=True),
        sa.Column("transferred_number", sa.Text(), nullable=True),
        sa.Column("destination", sa.Text(), nullable=True),
        sa.Column("callerid", sa.Text(), nullable=True),
        sa.Column("call_date", sa.Text(), nullable=True),
        sa.Column("extension", sa.Text(), nullable=True),
        sa.Column("caller_phone_norm", sa.Text(), nullable=True),
        sa.Column("agent_phone_norm", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "jobs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("job_information", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("location_salary_details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("job_details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("required_qualification", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.Text(), nullable=True),
        sa.Column("job_profile_id", sa.BigInteger(), nullable=True),
        sa.Column("application_status", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["job_profile_id"], ["job_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "intakes",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("application_deadline", sa.Date(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("universities", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("courses", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("requirements", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("fees", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("scholarships", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("additional_info", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("commission", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "conversation_sessions",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("lead_id", sa.BigInteger(), nullable=True),
        sa.Column("ig_user_id", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default=sa.text("'active'")),
        sa.Column("messages", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("extracted_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("conversation_stage", sa.Text(), nullable=True, server_default=sa.text("'greeting'")),
        sa.Column("assigned_counsellor_id", sa.UUID(), nullable=True),
        sa.Column("handoff_reason", sa.Text(), nullable=True),
        sa.Column("last_message_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("message_count", sa.Integer(), nullable=True, server_default=sa.text("0")),
        sa.Column("retry_count", sa.Integer(), nullable=True, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "dm_templates",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("trigger_type", sa.Text(), nullable=False),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column("opening_message", sa.Text(), nullable=False),
        sa.Column("qualification_fields", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "eb_file_ingestions",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("file_name", sa.String(), nullable=False),
        sa.Column("file_key", sa.String(), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("mime_type", sa.String(), nullable=True),
        sa.Column("source_type", sa.String(), nullable=False, server_default=sa.text("'upload'")),
        sa.Column("processing_status", sa.String(), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("processing_error", sa.Text(), nullable=True),
        sa.Column("entity_type", sa.String(), nullable=True),
        sa.Column("entity_id", sa.UUID(), nullable=True),
        sa.Column("employee_id", sa.UUID(), nullable=True),
        sa.Column("uploaded_by", sa.UUID(), nullable=True),
        sa.Column("extracted_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ai_model_used", sa.String(), nullable=True),
        sa.Column("ai_tokens_used", sa.Integer(), nullable=True),
        sa.Column("processing_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processing_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["employee_id"], ["eb_users.id"]),
        sa.ForeignKeyConstraint(["uploaded_by"], ["eb_users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "eb_employee_metrics",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("employee_id", sa.UUID(), nullable=False),
        sa.Column("period_type", sa.String(), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("calls_made", sa.Integer(), nullable=True, server_default=sa.text("0")),
        sa.Column("calls_received", sa.Integer(), nullable=True, server_default=sa.text("0")),
        sa.Column("calls_missed", sa.Integer(), nullable=True, server_default=sa.text("0")),
        sa.Column("total_call_duration_mins", sa.Float(), nullable=True, server_default=sa.text("0")),
        sa.Column("avg_call_duration_mins", sa.Float(), nullable=True, server_default=sa.text("0")),
        sa.Column("avg_call_quality_score", sa.Float(), nullable=True),
        sa.Column("avg_call_sentiment", sa.Float(), nullable=True),
        sa.Column("leads_contacted", sa.Integer(), nullable=True, server_default=sa.text("0")),
        sa.Column("leads_converted", sa.Integer(), nullable=True, server_default=sa.text("0")),
        sa.Column("new_students_onboarded", sa.Integer(), nullable=True, server_default=sa.text("0")),
        sa.Column("cases_progressed", sa.Integer(), nullable=True, server_default=sa.text("0")),
        sa.Column("cases_closed", sa.Integer(), nullable=True, server_default=sa.text("0")),
        sa.Column("applications_submitted", sa.Integer(), nullable=True, server_default=sa.text("0")),
        sa.Column("documents_processed", sa.Integer(), nullable=True, server_default=sa.text("0")),
        sa.Column("documents_verified", sa.Integer(), nullable=True, server_default=sa.text("0")),
        sa.Column("days_present", sa.Integer(), nullable=True, server_default=sa.text("0")),
        sa.Column("days_absent", sa.Integer(), nullable=True, server_default=sa.text("0")),
        sa.Column("days_late", sa.Integer(), nullable=True, server_default=sa.text("0")),
        sa.Column("avg_checkin_time", sa.Time(), nullable=True),
        sa.Column("avg_checkout_time", sa.Time(), nullable=True),
        sa.Column("total_hours_worked", sa.Float(), nullable=True, server_default=sa.text("0")),
        sa.Column("tasks_completed", sa.Integer(), nullable=True, server_default=sa.text("0")),
        sa.Column("tasks_overdue", sa.Integer(), nullable=True, server_default=sa.text("0")),
        sa.Column("avg_task_completion_hours", sa.Float(), nullable=True),
        sa.Column("ai_performance_score", sa.Float(), nullable=True),
        sa.Column("ai_efficiency_score", sa.Float(), nullable=True),
        sa.Column("ai_quality_score", sa.Float(), nullable=True),
        sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["employee_id"], ["eb_users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "eb_performance_reviews",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("employee_id", sa.UUID(), nullable=False),
        sa.Column("reviewer_id", sa.UUID(), nullable=True),
        sa.Column("review_type", sa.String(), nullable=False, server_default=sa.text("'monthly'")),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("scores", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=True),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column("ai_strengths", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ai_improvements", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ai_recommendations", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ai_comparison", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("metrics_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("call_analysis_ids", postgresql.ARRAY(sa.UUID()), nullable=True),
        sa.Column("file_ingestion_ids", postgresql.ARRAY(sa.UUID()), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default=sa.text("'draft'")),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("employee_feedback", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["employee_id"], ["eb_users.id"]),
        sa.ForeignKeyConstraint(["reviewer_id"], ["eb_users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "eb_employee_goals",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("employee_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("goal_type", sa.String(), nullable=False),
        sa.Column("target_value", sa.Float(), nullable=False),
        sa.Column("current_value", sa.Float(), nullable=True, server_default=sa.text("0")),
        sa.Column("unit", sa.String(), nullable=True, server_default=sa.text("'count'")),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default=sa.text("'active'")),
        sa.Column("progress_percentage", sa.Float(), nullable=True, server_default=sa.text("0")),
        sa.Column("auto_track", sa.Boolean(), nullable=True, server_default=sa.text("true")),
        sa.Column("tracking_query", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["employee_id"], ["eb_users.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["eb_users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "eb_employee_patterns",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("employee_id", sa.UUID(), nullable=False),
        sa.Column("pattern_type", sa.String(), nullable=False),
        sa.Column("pattern_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("sample_size", sa.Integer(), nullable=True),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("valid_until", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True, server_default=sa.text("true")),
        sa.Column("ai_model_used", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["employee_id"], ["eb_users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "eb_employee_schedules",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("employee_id", sa.UUID(), nullable=False),
        sa.Column("schedule_type", sa.String(), nullable=False, server_default=sa.text("'regular'")),
        sa.Column("day_of_week", sa.Integer(), nullable=True),
        sa.Column("specific_date", sa.Date(), nullable=True),
        sa.Column("start_time", sa.Time(), nullable=True),
        sa.Column("end_time", sa.Time(), nullable=True),
        sa.Column("break_minutes", sa.Integer(), nullable=True, server_default=sa.text("60")),
        sa.Column("is_working_day", sa.Boolean(), nullable=True, server_default=sa.text("true")),
        sa.Column("leave_type", sa.String(), nullable=True),
        sa.Column("leave_reason", sa.Text(), nullable=True),
        sa.Column("approved_by", sa.UUID(), nullable=True),
        sa.Column("status", sa.String(), nullable=True, server_default=sa.text("'active'")),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_until", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["employee_id"], ["eb_users.id"]),
        sa.ForeignKeyConstraint(["approved_by"], ["eb_users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "eb_training_records",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("employee_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("training_type", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("provider", sa.String(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default=sa.text("'assigned'")),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("max_score", sa.Float(), nullable=True),
        sa.Column("certificate_url", sa.Text(), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("assigned_by", sa.UUID(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["employee_id"], ["eb_users.id"]),
        sa.ForeignKeyConstraint(["assigned_by"], ["eb_users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # =====================================================================
    # GROUP 3: Tables with FKs to Group 2
    # =====================================================================

    op.create_table(
        "lead_info",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("basic_info", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("education", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("work_expierience", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("budget_info", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("preferences", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("english_proficiency", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("call_info", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("changes_history", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("documents", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("fcm_token", sa.Text(), nullable=True),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("domain_tags", postgresql.ARRAY(sa.Text()), nullable=True, server_default=sa.text("'{}'")),
        sa.Column("interest_embedding", sa.Text(), nullable=True),
        sa.Column("profile_text", sa.Text(), nullable=True),
        sa.Column("needs_enrichment", sa.Boolean(), nullable=True, server_default=sa.text("true")),
        sa.Column("enrichment_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["id"], ["leadslist.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "eb_cases",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("student_id", sa.UUID(), nullable=True),
        sa.Column("case_type", sa.String(50), nullable=True, server_default=sa.text("'study_abroad'")),
        sa.Column("current_stage", sa.String(50), nullable=True, server_default=sa.text("'initial_consultation'")),
        sa.Column("priority", sa.String(20), nullable=True, server_default=sa.text("'normal'")),
        sa.Column("assigned_counselor_id", sa.UUID(), nullable=True),
        sa.Column("assigned_processor_id", sa.UUID(), nullable=True),
        sa.Column("assigned_visa_officer_id", sa.UUID(), nullable=True),
        sa.Column("target_intake", sa.String(50), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True, server_default=sa.text("true")),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("close_reason", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["student_id"], ["eb_students.id"]),
        sa.ForeignKeyConstraint(["assigned_counselor_id"], ["eb_users.id"]),
        sa.ForeignKeyConstraint(["assigned_processor_id"], ["eb_users.id"]),
        sa.ForeignKeyConstraint(["assigned_visa_officer_id"], ["eb_users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "eb_workflow_instances",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("workflow_definition_id", sa.UUID(), nullable=False),
        sa.Column("entity_type", sa.String(30), nullable=False),
        sa.Column("entity_id", sa.UUID(), nullable=False),
        sa.Column("current_stage", sa.String(50), nullable=True),
        sa.Column("stage_entered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("history", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["workflow_definition_id"], ["eb_workflow_definitions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "eb_action_runs",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("action_draft_id", sa.UUID(), nullable=False),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=True, server_default=sa.text("'started'")),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=True, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["action_draft_id"], ["eb_action_drafts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "eb_work_logs",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("employee_id", sa.UUID(), nullable=False),
        sa.Column("activity_type", sa.String(), nullable=False),
        sa.Column("entity_type", sa.String(), nullable=True),
        sa.Column("entity_id", sa.UUID(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_minutes", sa.Float(), nullable=True),
        sa.Column("source", sa.String(), nullable=False, server_default=sa.text("'system'")),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("event_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["employee_id"], ["eb_users.id"]),
        sa.ForeignKeyConstraint(["event_id"], ["eb_events.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "eb_call_analyses",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("call_event_id", sa.BigInteger(), nullable=True),
        sa.Column("call_uuid", sa.Text(), nullable=True),
        sa.Column("employee_id", sa.UUID(), nullable=True),
        sa.Column("recording_url", sa.Text(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("transcription", sa.Text(), nullable=True),
        sa.Column("transcription_status", sa.String(), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("transcription_model", sa.String(), nullable=True),
        sa.Column("sentiment_score", sa.Float(), nullable=True),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("professionalism_score", sa.Float(), nullable=True),
        sa.Column("resolution_score", sa.Float(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("topics", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("action_items", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("flags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("key_phrases", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("caller_intent", sa.String(), nullable=True),
        sa.Column("outcome", sa.String(), nullable=True),
        sa.Column("language_detected", sa.String(), nullable=True),
        sa.Column("ai_model_used", sa.String(), nullable=True),
        sa.Column("ai_tokens_used", sa.Integer(), nullable=True),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("file_ingestion_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["call_event_id"], ["call_events.id"]),
        sa.ForeignKeyConstraint(["employee_id"], ["eb_users.id"]),
        sa.ForeignKeyConstraint(["file_ingestion_id"], ["eb_file_ingestions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "universities",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("city_id", sa.BigInteger(), nullable=True),
        sa.Column("established_year", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("description", sa.VARCHAR(), nullable=True),
        sa.Column("campuses", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("images", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("website", sa.Text(), nullable=True),
        sa.Column("accreditation", sa.Text(), nullable=True),
        sa.Column("ranking", sa.Text(), nullable=True),
        sa.Column("portion", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("commission", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("conversation_id", sa.BigInteger(), nullable=True),
        sa.Column("sender_id", sa.Text(), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("message_type", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("voice_duration", sa.Integer(), nullable=True),
        sa.Column("course_id", sa.Text(), nullable=True),
        sa.Column("course_deatails", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "applied_jobs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("job_id", sa.BigInteger(), nullable=True),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.Column("status", sa.Text(), nullable=True),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("candidate_name", sa.Text(), nullable=True),
        sa.Column("job_title", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "saved_courses",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.Column("course_id", sa.BigInteger(), nullable=True),
        sa.Column("course_details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "saved_jobs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.Column("job_id", sa.BigInteger(), nullable=True),
        sa.Column("job_details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "courses",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("program_name", sa.Text(), nullable=True),
        sa.Column("university", sa.Text(), nullable=True),
        sa.Column("country", sa.Text(), nullable=True),
        sa.Column("city", sa.Text(), nullable=True),
        sa.Column("campus", sa.Text(), nullable=True),
        sa.Column("application_fee", sa.Text(), nullable=True),
        sa.Column("tuition_fee", sa.Text(), nullable=True),
        sa.Column("deposit_amount", sa.Text(), nullable=True),
        sa.Column("currency", sa.Text(), nullable=True),
        sa.Column("duration", sa.Text(), nullable=True),
        sa.Column("language", sa.Text(), nullable=True),
        sa.Column("study_type", sa.Text(), nullable=True),
        sa.Column("program_level", sa.Text(), nullable=True),
        sa.Column("english_proficiency", sa.Text(), nullable=True),
        sa.Column("minimum_percentage", sa.Text(), nullable=True),
        sa.Column("age_limit", sa.Text(), nullable=True),
        sa.Column("academic_gap", sa.Text(), nullable=True),
        sa.Column("max_backlogs", sa.Text(), nullable=True),
        sa.Column("work_experience_requirement", sa.Text(), nullable=True),
        sa.Column("required_subjects", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("intakes", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("links", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("media_links", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("course_description", sa.String(), nullable=True),
        sa.Column("special_requirements", sa.String(), nullable=True),
        sa.Column("field_of_study", sa.Text(), nullable=True),
        sa.Column("embedding", sa.Text(), nullable=True),
        sa.Column("commission", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("search_text", sa.Text(), nullable=True),
        sa.Column("domain", sa.Text(), nullable=True),
        sa.Column("keywords", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("application_status", sa.Text(), nullable=True, server_default=sa.text("'not_applied'")),
        sa.Column("approval_status", sa.Text(), nullable=False, server_default=sa.text("'not_approved'")),
        sa.Column("approved_detail", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("insertion_details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("program_level_normalized", sa.Text(), nullable=True),
        sa.Column("age_limit_num", sa.Integer(), nullable=True),
        sa.Column("academic_gap_num", sa.Integer(), nullable=True),
        sa.Column("max_backlogs_num", sa.Integer(), nullable=True),
        sa.Column("min_pct_num", sa.Numeric(), nullable=True),
        sa.Column("domain_tags", postgresql.ARRAY(sa.Text()), nullable=True, server_default=sa.text("'{}'")),
        sa.Column("study_type_raw", sa.Text(), nullable=True),
        sa.Column("field_of_study_raw", sa.Text(), nullable=True),
        sa.Column("intakes_raw", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("field_of_study_ai", sa.Text(), nullable=True),
        sa.Column("fos_processing", sa.Boolean(), nullable=True, server_default=sa.text("false")),
        sa.Column("fos_processing_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fos_needs_recompute", sa.Boolean(), nullable=True, server_default=sa.text("true")),
        sa.Column("field_of_study_raw_backup", sa.Text(), nullable=True),
        sa.Column("english_proficiency_normalized_v2", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("english_proficiency_v2_processed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("required_subjects_normalized", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("required_subjects_ai_processed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("required_subjects_ai_processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "university_courses",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("program_name", sa.Text(), nullable=True),
        sa.Column("university", sa.Text(), nullable=True),
        sa.Column("country", sa.Text(), nullable=True),
        sa.Column("city", sa.Text(), nullable=True),
        sa.Column("campus", sa.Text(), nullable=True),
        sa.Column("application_fee", sa.Text(), nullable=True),
        sa.Column("tuition_fee", sa.Text(), nullable=True),
        sa.Column("deposit_amount", sa.Text(), nullable=True),
        sa.Column("currency", sa.Text(), nullable=True),
        sa.Column("duration", sa.Text(), nullable=True),
        sa.Column("language", sa.Text(), nullable=True),
        sa.Column("study_type", sa.Text(), nullable=True),
        sa.Column("program_level", sa.Text(), nullable=True),
        sa.Column("english_proficiency", sa.Text(), nullable=True),
        sa.Column("minimum_percentage", sa.Text(), nullable=True),
        sa.Column("age_limit", sa.Text(), nullable=True),
        sa.Column("academic_gap", sa.Text(), nullable=True),
        sa.Column("max_backlogs", sa.Text(), nullable=True),
        sa.Column("work_experience_requirement", sa.Text(), nullable=True),
        sa.Column("required_subjects", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("intakes", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("links", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("media_links", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("course_description", sa.String(), nullable=True),
        sa.Column("special_requirements", sa.String(), nullable=True),
        sa.Column("field_of_study", sa.Text(), nullable=True),
        sa.Column("embedding", sa.Text(), nullable=True),
        sa.Column("commission", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("search_text", sa.Text(), nullable=True),
        sa.Column("domain", sa.Text(), nullable=True),
        sa.Column("keywords", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("application_status", sa.Text(), nullable=True, server_default=sa.text("'not_applied'")),
        sa.Column("approval_status", sa.Text(), nullable=False, server_default=sa.text("'not_approved'")),
        sa.Column("approved_detail", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("insertion_details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("source_key", sa.Text(), nullable=True),
        sa.Column("university_image", sa.Text(), nullable=True),
        sa.Column("tuition_fee_international_amount", sa.Numeric(), nullable=True),
        sa.Column("tuition_fee_international_currency", sa.Text(), nullable=True),
        sa.Column("tuition_fee_international_basis", sa.Text(), nullable=True),
        sa.Column("tuition_fee_international_raw", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "course_approval_requests",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.Text(), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("submitted_by", sa.String(), nullable=True),
        sa.Column("submitted_designation", sa.Text(), nullable=True),
        sa.Column("approved_by", sa.Text(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_course_id", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "applied_courses",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("course_id", sa.Text(), nullable=False),
        sa.Column("course_details", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default=sa.text("'applied'")),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # =====================================================================
    # GROUP 4: Tables with FKs to Group 3
    # =====================================================================

    op.create_table(
        "eb_applications",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("university_name", sa.String(255), nullable=False),
        sa.Column("university_country", sa.String(100), nullable=True),
        sa.Column("program_name", sa.String(255), nullable=False),
        sa.Column("program_level", sa.String(50), nullable=True),
        sa.Column("status", sa.String(30), nullable=True, server_default=sa.text("'draft'")),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("response_received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("offer_deadline", sa.Date(), nullable=True),
        sa.Column("offer_details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["case_id"], ["eb_cases.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "campuses",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("university_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("city", sa.Text(), nullable=True),
        sa.Column("country", sa.Text(), nullable=True),
        sa.Column("description", sa.VARCHAR(), nullable=True),
        sa.Column("courses", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("images", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("contact_info", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("facilities", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("portion", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("commission", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["university_id"], ["universities.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # =====================================================================
    # INDEXES
    # =====================================================================

    # eb_events indexes
    op.create_index(
        "ix_eb_events_entity",
        "eb_events",
        ["entity_type", "entity_id"],
    )
    op.create_index(
        "ix_eb_events_event_type",
        "eb_events",
        ["event_type"],
    )
    op.create_index(
        "ix_eb_events_actor",
        "eb_events",
        ["actor_id"],
    )

    # eb_students indexes
    op.create_index(
        "ix_eb_students_counselor",
        "eb_students",
        ["assigned_counselor_id"],
    )

    # eb_cases indexes
    op.create_index(
        "ix_eb_cases_student",
        "eb_cases",
        ["student_id"],
    )
    op.create_index(
        "ix_eb_cases_stage",
        "eb_cases",
        ["current_stage"],
    )

    # eb_tasks indexes
    op.create_index(
        "ix_eb_tasks_assigned",
        "eb_tasks",
        ["assigned_to"],
    )

    # eb_notifications indexes
    op.create_index(
        "ix_eb_notifications_user",
        "eb_notifications",
        ["user_id"],
    )

    # leadslist indexes
    op.create_index(
        "ix_leadslist_assigned",
        "leadslist",
        ["assigned_to"],
    )
    op.create_index(
        "ix_leadslist_status",
        "leadslist",
        ["status"],
    )

    # call_events indexes
    op.create_index(
        "ix_call_events_uuid",
        "call_events",
        ["call_uuid"],
    )

    # eb_call_analyses indexes
    op.create_index(
        "ix_eb_call_analyses_employee",
        "eb_call_analyses",
        ["employee_id"],
    )

    # eb_employee_metrics indexes
    op.create_index(
        "ix_eb_employee_metrics_employee",
        "eb_employee_metrics",
        ["employee_id"],
    )


def downgrade() -> None:
    # =====================================================================
    # Drop indexes first
    # =====================================================================
    op.drop_index("ix_eb_employee_metrics_employee", table_name="eb_employee_metrics")
    op.drop_index("ix_eb_call_analyses_employee", table_name="eb_call_analyses")
    op.drop_index("ix_call_events_uuid", table_name="call_events")
    op.drop_index("ix_leadslist_status", table_name="leadslist")
    op.drop_index("ix_leadslist_assigned", table_name="leadslist")
    op.drop_index("ix_eb_notifications_user", table_name="eb_notifications")
    op.drop_index("ix_eb_tasks_assigned", table_name="eb_tasks")
    op.drop_index("ix_eb_cases_stage", table_name="eb_cases")
    op.drop_index("ix_eb_cases_student", table_name="eb_cases")
    op.drop_index("ix_eb_students_counselor", table_name="eb_students")
    op.drop_index("ix_eb_events_actor", table_name="eb_events")
    op.drop_index("ix_eb_events_event_type", table_name="eb_events")
    op.drop_index("ix_eb_events_entity", table_name="eb_events")

    # =====================================================================
    # GROUP 4: Drop tables with deepest FK dependencies first
    # =====================================================================
    op.drop_table("campuses")
    op.drop_table("eb_applications")

    # =====================================================================
    # GROUP 3: Tables with FKs to Group 2
    # =====================================================================
    op.drop_table("applied_courses")
    op.drop_table("course_approval_requests")
    op.drop_table("university_courses")
    op.drop_table("courses")
    op.drop_table("saved_jobs")
    op.drop_table("saved_courses")
    op.drop_table("applied_jobs")
    op.drop_table("chat_messages")
    op.drop_table("universities")
    op.drop_table("eb_call_analyses")
    op.drop_table("eb_work_logs")
    op.drop_table("eb_action_runs")
    op.drop_table("eb_workflow_instances")
    op.drop_table("eb_cases")
    op.drop_table("lead_info")

    # =====================================================================
    # GROUP 2: Tables with FKs to Group 1
    # =====================================================================
    op.drop_table("eb_training_records")
    op.drop_table("eb_employee_schedules")
    op.drop_table("eb_employee_patterns")
    op.drop_table("eb_employee_goals")
    op.drop_table("eb_performance_reviews")
    op.drop_table("eb_employee_metrics")
    op.drop_table("eb_file_ingestions")
    op.drop_table("dm_templates")
    op.drop_table("conversation_sessions")
    op.drop_table("intakes")
    op.drop_table("jobs")
    op.drop_table("call_events")
    op.drop_table("cities")
    op.drop_table("agent_endpoints")
    op.drop_table("freelance_managers")
    op.drop_table("freelancers")
    op.drop_table("attendance")
    op.drop_table("eb_policies")
    op.drop_table("eb_ai_artifacts")
    op.drop_table("eb_action_drafts")
    op.drop_table("eb_documents")
    op.drop_table("eb_tasks")
    op.drop_table("eb_events")
    op.drop_table("eb_notifications")
    op.drop_table("eb_students")
    op.drop_table("leadslist")
    op.drop_table("eb_role_permissions")
    op.drop_table("eb_user_roles")

    # =====================================================================
    # GROUP 1: Base tables with no FK dependencies
    # =====================================================================
    op.drop_table("payments")
    op.drop_table("chat_conversations")
    op.drop_table("eb_workflow_definitions")
    op.drop_table("user_profiles")
    op.drop_table("backlog_participants")
    op.drop_table("stopwords")
    op.drop_table("search_synonyms")
    op.drop_table("domain_keyword_map")
    op.drop_table("commission")
    op.drop_table("lead_assignment_tracker")
    op.drop_table("chatbot_sessions")
    op.drop_table("short_links")
    op.drop_table("jobs_countries")
    op.drop_table("job_profiles")
    op.drop_table("countries")
    op.drop_table("eb_permissions")
    op.drop_table("eb_roles")
    op.drop_table("eb_users")
    op.drop_table("profiles")
