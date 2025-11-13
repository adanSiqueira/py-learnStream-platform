from __future__ import with_statement
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from alembic import context

from app.models.sql.database import Base  #SQLAlchemy Base
from app.core.config import settings           #config file
from app.models.sql.user import User
from app.models.sql.enrollment import Enrollment
from app.models.sql.refresh_token import RefreshToken

# Load Alembic config
config = context.config

# Interpret Python logging config
fileConfig(config.config_file_name)

# Metadata for autogeneration
target_metadata = Base.metadata

# Get DB URL from config
def get_url():
    return settings.DATABASE_URL

# ---- Async alembic runner ----

def run_migrations_offline():
    """Run migrations in offline mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations():
    """Run migrations in async mode."""
    from sqlalchemy.ext.asyncio import create_async_engine

    connectable = create_async_engine(
        get_url(),
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def do_run_migrations(connection: Connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    asyncio.run(run_async_migrations())

# Entry point
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()