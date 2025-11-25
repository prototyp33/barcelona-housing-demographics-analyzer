"""
Migration script for fact_precios table.

This script migrates the fact_precios table to include dataset_id and source
in the unique constraint, allowing multiple records per barrio-year-trimestre
combination when they come from different sources.

Migration steps:
1. Create backup of the database
2. Create new table with correct unique constraint
3. Copy existing data
4. Drop old table and rename new table
5. Verify data integrity
"""

from __future__ import annotations

import logging
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

DEFAULT_DB_NAME = "database.db"
DEFAULT_PROCESSED_DIR = Path("data/processed")


def create_backup(db_path: Path) -> Path:
    """
    Create a timestamped backup of the database.
    
    Args:
        db_path: Path to the database file
    
    Returns:
        Path to the backup file
    
    Raises:
        FileNotFoundError: If the database file doesn't exist
        OSError: If backup creation fails
    """
    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found: {db_path}")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.parent / f"{db_path.stem}_backup_{timestamp}.db"
    
    logger.info(f"Creating backup: {backup_path}")
    shutil.copy2(db_path, backup_path)
    logger.info(f"Backup created successfully: {backup_path}")
    
    return backup_path


def get_table_info(conn: sqlite3.Connection, table_name: str) -> list[tuple]:
    """
    Get column information for a table.
    
    Args:
        conn: Database connection
        table_name: Name of the table
    
    Returns:
        List of tuples with column information
    """
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    return cursor.fetchall()


def get_row_count(conn: sqlite3.Connection, table_name: str) -> int:
    """
    Get the number of rows in a table.
    
    Args:
        conn: Database connection
        table_name: Name of the table
    
    Returns:
        Number of rows
    """
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    return cursor.fetchone()[0]


def verify_foreign_keys(conn: sqlite3.Connection) -> bool:
    """
    Verify that all foreign key constraints are satisfied.
    
    Args:
        conn: Database connection
    
    Returns:
        True if all foreign keys are valid, False otherwise
    """
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_key_check(fact_precios)")
    violations = cursor.fetchall()
    
    if violations:
        logger.error(f"Foreign key violations found: {len(violations)}")
        for violation in violations[:10]:  # Show first 10
            logger.error(f"  Violation: {violation}")
        return False
    
    logger.info("All foreign key constraints verified")
    return True


def migrate_fact_precios(
    db_path: Optional[Path] = None,
    processed_dir: Optional[Path] = None,
    create_backup_flag: bool = True,
) -> bool:
    """
    Migrate fact_precios table to include dataset_id and source in unique constraint.
    
    Args:
        db_path: Path to database file (defaults to data/processed/database.db)
        processed_dir: Directory containing processed data (defaults to data/processed)
        create_backup_flag: Whether to create a backup before migration
    
    Returns:
        True if migration succeeded, False otherwise
    
    Raises:
        sqlite3.Error: If database operations fail
    """
    # Determine database path
    if processed_dir is None:
        processed_dir = DEFAULT_PROCESSED_DIR
    
    if db_path is None:
        db_path = processed_dir / DEFAULT_DB_NAME
    else:
        db_path = Path(db_path)
        if not db_path.is_absolute():
            db_path = processed_dir / db_path
    
    logger.info(f"Starting migration for: {db_path}")
    
    if not db_path.exists():
        logger.error(f"Database file not found: {db_path}")
        return False
    
    # Create backup
    backup_path = None
    if create_backup_flag:
        try:
            backup_path = create_backup(db_path)
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    
    try:
        # Get current table info
        logger.info("Analyzing current table structure...")
        table_info = get_table_info(conn, "fact_precios")
        logger.info(f"Current table has {len(table_info)} columns")
        
        # Get current row count
        original_count = get_row_count(conn, "fact_precios")
        logger.info(f"Current row count: {original_count}")
        
        # Check for existing index
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name='idx_fact_precios_unique'
        """)
        existing_index = cursor.fetchone()
        if existing_index:
            logger.info("Found existing unique index: idx_fact_precios_unique")
        
        # Start transaction
        logger.info("Starting migration transaction...")
        with conn:
            # Step 1: Create new table with correct schema
            logger.info("Creating new table: fact_precios_new")
            conn.execute("""
                CREATE TABLE fact_precios_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    barrio_id INTEGER NOT NULL,
                    anio INTEGER NOT NULL,
                    periodo TEXT,
                    trimestre INTEGER,
                    precio_m2_venta REAL,
                    precio_mes_alquiler REAL,
                    dataset_id TEXT,
                    source TEXT,
                    etl_loaded_at TEXT,
                    FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
                )
            """)
            logger.info("New table created successfully")
            
            # Step 2: Copy data from old table to new table
            logger.info("Copying data from old table to new table...")
            conn.execute("""
                INSERT INTO fact_precios_new (
                    id,
                    barrio_id,
                    anio,
                    periodo,
                    trimestre,
                    precio_m2_venta,
                    precio_mes_alquiler,
                    dataset_id,
                    source,
                    etl_loaded_at
                )
                SELECT 
                    id,
                    barrio_id,
                    anio,
                    periodo,
                    trimestre,
                    precio_m2_venta,
                    precio_mes_alquiler,
                    dataset_id,
                    source,
                    etl_loaded_at
                FROM fact_precios
            """)
            
            copied_count = get_row_count(conn, "fact_precios_new")
            logger.info(f"Copied {copied_count} rows to new table")
            
            if copied_count != original_count:
                logger.error(
                    f"Row count mismatch! Original: {original_count}, "
                    f"Copied: {copied_count}"
                )
                raise sqlite3.Error("Data copy failed: row count mismatch")
            
            # Step 3: Drop old unique index if it exists
            logger.info("Dropping old unique index...")
            conn.execute("DROP INDEX IF EXISTS idx_fact_precios_unique")
            
            # Step 4: Create new unique index with dataset_id and source
            logger.info("Creating new unique index with dataset_id and source...")
            conn.execute("""
                CREATE UNIQUE INDEX idx_fact_precios_unique
                ON fact_precios_new (
                    barrio_id,
                    anio,
                    COALESCE(trimestre, -1),
                    COALESCE(dataset_id, ''),
                    COALESCE(source, '')
                )
            """)
            logger.info("New unique index created successfully")
            
            # Step 5: Drop old table
            logger.info("Dropping old table...")
            conn.execute("DROP TABLE fact_precios")
            logger.info("Old table dropped")
            
            # Step 6: Rename new table to original name
            logger.info("Renaming new table to fact_precios...")
            conn.execute("ALTER TABLE fact_precios_new RENAME TO fact_precios")
            logger.info("Table renamed successfully")
        
        # Verify migration
        logger.info("Verifying migration...")
        
        # Check row count
        final_count = get_row_count(conn, "fact_precios")
        if final_count != original_count:
            logger.error(
                f"Row count verification failed! Original: {original_count}, "
                f"Final: {final_count}"
            )
            return False
        
        logger.info(f"Row count verified: {final_count} rows")
        
        # Verify foreign keys
        if not verify_foreign_keys(conn):
            logger.error("Foreign key verification failed")
            return False
        
        # Verify new index exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name='idx_fact_precios_unique'
        """)
        index_check = cursor.fetchone()
        if not index_check:
            logger.error("New unique index not found")
            return False
        
        logger.info("Migration completed successfully!")
        logger.info(f"Backup available at: {backup_path}" if backup_path else "")
        
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Database error during migration: {e}", exc_info=True)
        if backup_path:
            logger.info(f"Database can be restored from backup: {backup_path}")
        return False
    
    except Exception as e:
        logger.error(f"Unexpected error during migration: {e}", exc_info=True)
        if backup_path:
            logger.info(f"Database can be restored from backup: {backup_path}")
        return False
    
    finally:
        conn.close()
        logger.info("Database connection closed")


def main() -> None:
    """Main entry point for the migration script."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Migrate fact_precios table to include dataset_id and source in unique constraint"
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=None,
        help="Path to database file (defaults to data/processed/database.db)",
    )
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=None,
        help="Directory containing processed data (defaults to data/processed)",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating a backup before migration",
    )
    
    args = parser.parse_args()
    
    success = migrate_fact_precios(
        db_path=args.db_path,
        processed_dir=args.processed_dir,
        create_backup_flag=not args.no_backup,
    )
    
    if success:
        logger.info("Migration completed successfully")
        exit(0)
    else:
        logger.error("Migration failed")
        exit(1)


if __name__ == "__main__":
    main()

