from __future__ import with_statement
import asyncio
from logging.config import fileConfig
import os
from dotenv import load_dotenv

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from alembic import context

from app.models.sql.database import Base  # SQLAlchemy Base
from app.core.config import settings      # your settings loader
from app.models.sql.user import User
from app.models.sql.enrollment import Enrollment
from app.models.sql.refresh_token import RefreshToken

# -------------------------------
# Load environment variables
# -------------------------------
load_dotenv()  # Loads .env from project root

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL missing — ensure it is defined inside .env")

# -------------------------------
# Alembic config
# -------------------------------
config = context.config
fileConfig(config.config_file_name)

# Inject URL so alembic.ini stays secret-free
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Metadata for autogenerate
target_metadata = Base.metadata


# -------------------------------
# Migration runners
# -------------------------------
def run_migrations_offline():
    """Run migrations without DB connection"""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    """Run migrations async (recommended)"""
    from sqlalchemy.ext.asyncio import create_async_engine

    connectable = create_async_engine(
        DATABASE_URL,
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


# Entry Point
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()