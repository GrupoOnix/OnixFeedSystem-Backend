import asyncio
import os
import sys
from logging.config import fileConfig

from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from sqlmodel import SQLModel
from src.infrastructure.persistence.database import DATABASE_URL

from src.infrastructure.persistence.models.cage_model import CageModel
from src.infrastructure.persistence.models.silo_model import SiloModel
from src.infrastructure.persistence.models.feeding_line_model import FeedingLineModel
from src.infrastructure.persistence.models.blower_model import BlowerModel
from src.infrastructure.persistence.models.doser_model import DoserModel
from src.infrastructure.persistence.models.selector_model import SelectorModel
from src.infrastructure.persistence.models.sensor_model import SensorModel
from src.infrastructure.persistence.models.slot_assignment_model import (
    SlotAssignmentModel,
)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode with async support."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = DATABASE_URL

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async def do_run_migrations(connection: Connection) -> None:
        await connection.run_sync(do_migrations)

    def do_migrations(connection: Connection) -> None:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()

    async def run_async_migrations() -> None:
        async with connectable.connect() as connection:
            await do_run_migrations(connection)

        await connectable.dispose()

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
