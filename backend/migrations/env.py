"""Alembic environment script.

Reads the database URL from application configuration (which itself reads
from the DATABASE_URL environment variable) rather than duplicating it in
alembic.ini, so migrations always target the same database as the running
application.

Domain models are imported here so that ``Base.metadata`` is fully
populated and ``alembic revision --autogenerate`` can detect schema
changes.  Import order follows foreign-key dependency direction:
  customers → transactions → support_cases → disputes
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Ensure all ORM models are registered on Base.metadata before autogenerate
# inspects it.  Import order matters for FK resolution during table creation.
import app.domain.customer.models  # noqa: F401  — registers Customer
import app.domain.dispute.models  # noqa: F401  — registers Dispute
import app.domain.support.models  # noqa: F401  — registers SupportCase
import app.domain.transaction.models  # noqa: F401  — registers Transaction
from app.config import get_settings
from app.infrastructure.database.base import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The URL normally comes from application settings (DATABASE_URL). Callers
# such as the migration tests may instead pre-set ``sqlalchemy.url`` on the
# Alembic Config object; that takes precedence so they never have to mutate
# process environment. Note: ConfigParser needs literal "%" escaped as "%%".
if not config.get_main_option("sqlalchemy.url"):
    config.set_main_option(
        "sqlalchemy.url", get_settings().DATABASE_URL.get_secret_value().replace("%", "%%")
    )

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations without a live DB connection (generates SQL)."""
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
    """Run migrations against a live DB connection."""
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
