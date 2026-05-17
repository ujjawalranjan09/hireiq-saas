from logging.config import fileConfig
import asyncio
import os
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context

# Import the Base class from our PostgreSQL models
from database.postgres import Base
from database.pg_models import Company, User, Job, Candidate  # noqa: F401 - Ensure all models are imported

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# Get PostgreSQL URL from environment variable (preferred) or config file
POSTGRES_URL = os.getenv("POSTGRES_URL", config.get_main_option("sqlalchemy.url"))


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = POSTGRES_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """Run migrations with the given connection."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode with async engine."""
    connectable = create_async_engine(
        POSTGRES_URL,
        poolclass=pool.NullPool,
        echo=False,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
