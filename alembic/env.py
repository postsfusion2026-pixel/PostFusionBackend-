import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

# ─────────────────────────────────────────────────────────────────────────────
# IMPORT YOUR APP'S BASE AND SETTINGS
# Alembic needs to know about your models to generate migrations automatically.
# Importing Base here makes Alembic aware of ALL models that inherit from it.
# ─────────────────────────────────────────────────────────────────────────────
from app.core.config import settings
from app.db.base import Base              # ← the DeclarativeBase

# ─────────────────────────────────────────────────────────────────────────────
# IMPORT ALL YOUR MODELS HERE
# Even if you don't use them directly, importing them registers them with Base.
# If you skip this, Alembic won't see the tables and won't generate migrations.
# ─────────────────────────────────────────────────────────────────────────────
from app.models import user               # ← this registers User with Base
# from app.models import post             # ← add this when Post model exists
# from app.models import comment          # ← add this when Comment model exists

# Alembic's config object — reads alembic.ini
config = context.config

# Set up Python logging from alembic.ini's [loggers] section
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ─────────────────────────────────────────────────────────────────────────────
# target_metadata — This tells Alembic "compare the DB against these models"
# When you run `alembic revision --autogenerate`, Alembic:
# 1. Connects to the database
# 2. Reads the current schema
# 3. Compares it against Base.metadata (your Python models)
# 4. Generates a migration script for the difference
# ─────────────────────────────────────────────────────────────────────────────
target_metadata = Base.metadata

# ─────────────────────────────────────────────────────────────────────────────
# OVERRIDE DATABASE URL from our .env (via pydantic settings)
# This ensures we never hardcode the DB URL in alembic.ini
# ─────────────────────────────────────────────────────────────────────────────
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)


# ─────────────────────────────────────────────────────────────────────────────
# ASYNC MIGRATION RUNNER
# Default Alembic runs sync. We override this to run async.
# This is required because our engine is async (asyncpg).
# ─────────────────────────────────────────────────────────────────────────────
def do_run_migrations(connection):
    """Runs the actual migration using a sync-compatible connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # compare_type=True: detect column TYPE changes (e.g., String → Text)
        compare_type=True,
        # render_as_batch=True: needed for SQLite (not strictly needed for PG
        # but good habit if you ever swap to SQLite for testing)
        render_as_batch=False,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    """Creates an async engine and runs migrations through it."""
    connectable = create_async_engine(
        settings.DATABASE_URL,
        poolclass=pool.NullPool,
        # NullPool: don't use a connection pool for migrations
        # Migrations run once and exit — no need to keep connections alive
    )

    async with connectable.connect() as connection:
        # run_sync() lets us run sync Alembic code inside async context
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()  # close the migration connection


def run_migrations_online():
    """Entry point called by Alembic CLI."""
    asyncio.run(run_async_migrations())


# Alembic calls this function when you run `alembic upgrade` or `alembic downgrade`
run_migrations_online()