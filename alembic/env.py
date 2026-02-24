"""Alembic async migration environment.

Reads DATABASE_URL_SYNC from app.config.settings so there is a single
source of truth for the connection string.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import settings
from app.database import Base

# ── Import ALL model modules so Base.metadata is fully populated ────────────
# Core CRM
from app.modules.users import models as _users  # noqa: F401
from app.modules.students import models as _students  # noqa: F401
from app.modules.cases import models as _cases  # noqa: F401
from app.modules.applications import models as _applications  # noqa: F401
from app.modules.documents import models as _documents  # noqa: F401
from app.modules.tasks import models as _tasks  # noqa: F401
from app.modules.events import models as _events  # noqa: F401
from app.modules.approvals import models as _approvals  # noqa: F401
from app.modules.notifications import models as _notifications  # noqa: F401
from app.modules.workflows import models as _workflows  # noqa: F401
from app.modules.ai_artifacts import models as _ai_artifacts  # noqa: F401
from app.modules.policies import models as _policies  # noqa: F401

# Legacy tables (read-only — included for completeness, Alembic won't modify)
from app.modules.leads import models as _leads  # noqa: F401
from app.modules.courses import models as _courses  # noqa: F401
from app.modules.profiles import models as _profiles  # noqa: F401
from app.modules.geography import models as _geography  # noqa: F401
from app.modules.intakes import models as _intakes  # noqa: F401
from app.modules.jobs import models as _jobs  # noqa: F401
from app.modules.call_events import models as _call_events  # noqa: F401
from app.modules.chat import models as _chat  # noqa: F401
from app.modules.payments import models as _payments  # noqa: F401
from app.modules.attendance import models as _attendance  # noqa: F401
from app.modules.ig_sessions import models as _ig_sessions  # noqa: F401
from app.modules.saved_items import models as _saved_items  # noqa: F401
from app.modules.search import models as _search  # noqa: F401
from app.modules.freelance import models as _freelance  # noqa: F401
from app.modules.push_tokens import models as _push_tokens  # noqa: F401
from app.modules.utility import models as _utility  # noqa: F401

# Employee automation
from app.modules.employee_automation import models as _emp_auto  # noqa: F401

# ── Alembic Config object ──────────────────────────────────────────────────
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set SQLAlchemy URL from application settings (single source of truth)
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL_SYNC)

# Metadata for autogenerate support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Generates SQL script output instead of connecting to the database.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Creates an engine and connects to the database.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
