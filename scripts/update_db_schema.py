"""Script to update the database schema to the latest version."""

import logging
from pathlib import Path
from src.database_setup import create_connection, create_database_schema, DEFAULT_DB_NAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_db():
    db_path = Path("data/processed") / DEFAULT_DB_NAME
    if not db_path.exists():
        logger.error(f"Database not found at {db_path}")
        return

    logger.info(f"Updating schema for database at {db_path}...")
    conn = create_connection(db_path)
    try:
        create_database_schema(conn)
        logger.info("✓ Database schema updated successfully.")
    except Exception as e:
        logger.error(f"Error updating database schema: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    update_db()

