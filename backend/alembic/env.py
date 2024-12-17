from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

import logging
import sys

config = context.config

# Set up logging before anything else
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
logger = logging.getLogger(__name__)

# Prevent fileConfig from overwriting our logging setup
if config.config_file_name is not None:
    logger_level = logger.level
    fileConfig(config.config_file_name)
    logger.setLevel(logger_level)

logger.debug("Starting Alembic environment")

# Import models package to trigger the imports
logger.debug("About to import models")
from app.models import Base
logger.debug("Models imported")

target_metadata = Base.metadata

 
def include_object(object, name, type_, reflected, compare_to):
    logger.debug(f"Checking object: {name} of type {type_}")
    if type_ == "table" and name == "spatial_ref_sys":
        return False
    return True

# target_metadata = None

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    logger.debug("Starting online migrations")
    logger.debug(f"Tables in metadata: {Base.metadata.tables.keys()}")
    for table in Base.metadata.tables.values():
        logger.debug(f"Columns in {table.name}: {[c.name for c in table.columns]}")
        
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata, include_object=include_object
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
