# alembic/env.py

from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

import logging
import sys

# In alembic/env.py at the top:
from dotenv import load_dotenv
import os

load_dotenv()

# Make sure this stays at the top after imports
load_dotenv()

def get_url():
    url = os.getenv("DATABASE_URL")
    if url is None:
        raise ValueError("DATABASE_URL environment variable is not set")
    return url

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    logger.debug("Starting online migrations")
    
    # Replace the engine configuration to use get_url()
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata, include_object=include_object
        )

        with context.begin_transaction():
            context.run_migrations()

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
    
    # List of PostGIS-managed tables to exclude
    postgis_tables = {
        'spatial_ref_sys',
        'topology',
        'layer',
        'topology_id_seq',
        # Add any other PostGIS tables you want to exclude
    }
    
    if type_ == "table" and name in postgis_tables:
        logger.debug(f"Excluding PostGIS table: {name}")
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
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object
    )

    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
