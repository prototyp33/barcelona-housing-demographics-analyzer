"""
Database connection and dependency injection for FastAPI
"""
import sqlite3
from pathlib import Path
from typing import Generator
import logging

logger = logging.getLogger(__name__)

# Database path (relative to project root)
DB_PATH = Path(__file__).parent.parent / "data" / "processed" / "database.db"


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """
    Dependency injection for database connection.
    
    Yields SQLite connection with Row factory for dict-like access.
    Connection is automatically closed after request.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable dict-like row access
    try:
        yield conn
    finally:
        conn.close()


def verify_database_exists() -> None:
    """Verify that the database file exists and is accessible"""
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found at {DB_PATH}. "
            "Please run the ETL pipeline first to create the database."
        )
    
    logger.info(f"Database found at {DB_PATH}")
    
    # Test connection
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        logger.info(f"Database contains {len(tables)} tables: {', '.join(tables)}")
        
        required_tables = {"dim_barrios", "fact_precios", "fact_demografia", "fact_renta"}
        missing_tables = required_tables - set(tables)
        if missing_tables:
            logger.warning(f"Missing expected tables: {missing_tables}")
        
    except sqlite3.Error as e:
        raise RuntimeError(f"Failed to connect to database: {e}")
