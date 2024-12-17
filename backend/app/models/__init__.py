from app.database import Base
from pathlib import Path
import importlib
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Automatically import all models
models_dir = Path(__file__).parent
for file in models_dir.glob("*.py"):
    if file.stem not in ["__init__"]:
        logger.debug(f"Importing model from {file.stem}")
        importlib.import_module(f"app.models.{file.stem}")

# Debug: Print all tables and relationships
for table in Base.metadata.tables.values():
    logger.debug(f"Table: {table.name}")
    for fk in table.foreign_keys:
        logger.debug(f"  FK: {fk.target_fullname}")

# This ensures all models are registered with Base.metadata
__all__ = ['Base']