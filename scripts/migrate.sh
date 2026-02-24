#!/usr/bin/env bash
set -euo pipefail

# ─── Empireo Brain — Migration Helper ───────────────────────────────────────
#
# Usage:
#   ./scripts/migrate.sh                    # Run pending migrations (upgrade head)
#   ./scripts/migrate.sh upgrade head       # Same as above
#   ./scripts/migrate.sh downgrade -1       # Roll back one migration
#   ./scripts/migrate.sh stamp head         # Mark DB as current (for existing DBs)
#   ./scripts/migrate.sh revision "msg"     # Create new migration
#   ./scripts/migrate.sh autogenerate "msg" # Auto-generate migration from models
#   ./scripts/migrate.sh current            # Show current revision
#   ./scripts/migrate.sh history            # Show migration history
#   ./scripts/migrate.sh seed               # Run permission seeder
#
# For Docker:
#   docker compose exec api ./scripts/migrate.sh
# ─────────────────────────────────────────────────────────────────────────────

CMD="${1:-upgrade}"

case "$CMD" in
    upgrade)
        TARGET="${2:-head}"
        echo "⬆ Running migrations up to: $TARGET"
        alembic upgrade "$TARGET"
        ;;
    downgrade)
        TARGET="${2:--1}"
        echo "⬇ Rolling back to: $TARGET"
        alembic downgrade "$TARGET"
        ;;
    stamp)
        TARGET="${2:-head}"
        echo "📌 Stamping database at: $TARGET"
        alembic stamp "$TARGET"
        ;;
    revision)
        MSG="${2:?Usage: migrate.sh revision \"description\"}"
        echo "📝 Creating new migration: $MSG"
        alembic revision -m "$MSG"
        ;;
    autogenerate)
        MSG="${2:?Usage: migrate.sh autogenerate \"description\"}"
        echo "🔄 Auto-generating migration: $MSG"
        alembic revision --autogenerate -m "$MSG"
        ;;
    current)
        echo "📍 Current migration revision:"
        alembic current
        ;;
    history)
        echo "📜 Migration history:"
        alembic history --verbose
        ;;
    seed)
        echo "🌱 Seeding roles and permissions..."
        python -m app.scripts.seed_permissions
        ;;
    *)
        echo "Unknown command: $CMD"
        echo "Usage: migrate.sh [upgrade|downgrade|stamp|revision|autogenerate|current|history|seed]"
        exit 1
        ;;
esac

echo "✅ Done."
