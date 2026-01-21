#!/usr/bin/env python3
"""
Migrate SQLite database to PostgreSQL for Looker integration.

This script migrates all tables from SQLite to PostgreSQL, preserving
the star schema structure and data integrity.

Usage:
    python scripts/migrate_sqlite_to_postgresql.py

Requirements:
    pip install psycopg2-binary pandas sqlalchemy
"""

import sys
import os
import logging
from pathlib import Path
from typing import List, Optional

import pandas as pd
import sqlite3
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables from .env file
load_dotenv(PROJECT_ROOT / ".env")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# PostgreSQL connection config (from environment variables or defaults)
POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "database": os.getenv("POSTGRES_DATABASE", "barcelona_housing"),
    "user": os.getenv("POSTGRES_USER", os.getenv("USER", "postgres")),
    "password": os.getenv("POSTGRES_PASSWORD", ""),
    "port": int(os.getenv("POSTGRES_PORT", "5432"))
}

# SQLite database path
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "data/processed/database.db")
SQLITE_DB = PROJECT_ROOT / SQLITE_DB_PATH


def check_dependencies() -> bool:
    """Check if required dependencies are installed."""
    try:
        import psycopg2
        from sqlalchemy import create_engine
        return True
    except ImportError:
        logger.error(
            "Missing dependencies. Install with:\n"
            "  pip install psycopg2-binary pandas sqlalchemy"
        )
        return False


def get_sqlite_tables(conn: sqlite3.Connection) -> List[str]:
    """Get list of all user tables from SQLite."""
    query = """
        SELECT name 
        FROM sqlite_master 
        WHERE type='table' 
          AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """
    df = pd.read_sql_query(query, conn)
    return df['name'].tolist()


def get_table_schema(conn: sqlite3.Connection, table_name: str) -> pd.DataFrame:
    """Get table schema from SQLite."""
    query = f"PRAGMA table_info({table_name})"
    return pd.read_sql_query(query, conn)


def migrate_table(
    table_name: str,
    sqlite_conn: sqlite3.Connection,
    pg_engine,
    chunk_size: int = 1000
) -> int:
    """
    Migrate a single table from SQLite to PostgreSQL.
    
    Args:
        table_name: Name of the table to migrate.
        sqlite_conn: SQLite connection.
        pg_engine: SQLAlchemy engine for PostgreSQL.
        chunk_size: Number of rows to process per chunk.
    
    Returns:
        Number of rows migrated.
    """
    try:
        # Read from SQLite
        logger.info(f"Reading table: {table_name}")
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", sqlite_conn)
        
        if df.empty:
            logger.warning(f"  ⚠️  Table {table_name} is empty, skipping...")
            return 0
        
        # Handle datetime columns (SQLite stores as TEXT, PostgreSQL needs TIMESTAMP)
        for col in df.columns:
            if df[col].dtype == 'object':
                # Try to convert to datetime
                try:
                    df[col] = pd.to_datetime(df[col], errors='ignore')
                except:
                    pass
        
        # Write to PostgreSQL
        logger.info(f"  Writing {len(df)} rows to PostgreSQL...")
        df.to_sql(
            table_name,
            pg_engine,
            if_exists='replace',
            index=False,
            method='multi',
            chunksize=chunk_size
        )
        
        logger.info(f"  ✅ Migrated {table_name}: {len(df)} rows")
        return len(df)
        
    except Exception as e:
        logger.error(f"  ❌ Error migrating {table_name}: {e}")
        raise


def create_postgres_indexes(pg_engine, table_name: str) -> None:
    """Create indexes on foreign keys and common query columns."""
    try:
        with pg_engine.connect() as conn:
            from sqlalchemy import text
            # Index on barrio_id (most common foreign key)
            if table_name.startswith('fact_'):
                conn.execute(text(f"""
                    CREATE INDEX IF NOT EXISTS idx_{table_name}_barrio_id 
                    ON {table_name}(barrio_id)
                """))
            
            # Index on anio (common filter)
            conn.execute(text(f"""
                CREATE INDEX IF NOT EXISTS idx_{table_name}_anio 
                ON {table_name}(anio)
            """))
            
            conn.commit()
    except Exception as e:
        logger.warning(f"  ⚠️  Could not create indexes for {table_name}: {e}")


def migrate_views(sqlite_conn: sqlite3.Connection, pg_engine) -> None:
    """Migrate SQL views (requires manual conversion due to SQL dialect differences)."""
    query = """
        SELECT name, sql
        FROM sqlite_master
        WHERE type='view'
    """
    views = pd.read_sql_query(query, sqlite_conn)
    
    if views.empty:
        logger.info("No views to migrate")
        return
    
    logger.info(f"\n📋 Found {len(views)} views. Manual conversion required:")
    logger.info("   SQLite and PostgreSQL have different SQL dialects.")
    logger.info("   Please review and convert these views manually:\n")
    
    for _, row in views.iterrows():
        logger.info(f"   View: {row['name']}")
        logger.info(f"   SQL: {row['sql'][:100]}...")
        logger.info("")


def main() -> int:
    """Main migration function."""
    logger.info("=" * 60)
    logger.info("🔄 SQLite to PostgreSQL Migration")
    logger.info("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    # Check SQLite database exists
    if not SQLITE_DB.exists():
        logger.error(f"SQLite database not found: {SQLITE_DB}")
        logger.info(f"Expected location: {SQLITE_DB.absolute()}")
        return 1
    
    # Try without password first (peer authentication on macOS)
    # If that fails, prompt for password
    test_config = POSTGRES_CONFIG.copy()
    if not test_config['password']:
        test_config['password'] = ''
    
    # Import here to avoid errors if not installed
    from sqlalchemy import create_engine, text
    
    # Create PostgreSQL connection string
    pg_connection_string = (
        f"postgresql://{POSTGRES_CONFIG['user']}:{POSTGRES_CONFIG['password']}"
        f"@{POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}"
        f"/{POSTGRES_CONFIG['database']}"
    )
    
    logger.info(f"PostgreSQL target: {POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}/{POSTGRES_CONFIG['database']}")
    logger.info(f"SQLite source: {SQLITE_DB}")
    
    try:
        # Test PostgreSQL connection (try without password first for peer auth)
        logger.info("Testing PostgreSQL connection...")
        try:
            pg_engine = create_engine(pg_connection_string)
            with pg_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("✅ PostgreSQL connection successful")
        except Exception as e:
            if "password" in str(e).lower() or "authentication" in str(e).lower():
                # Password required - prompt for it
                logger.info("Password required for PostgreSQL connection")
                import sys
                if sys.stdin.isatty():
                    import getpass
                    POSTGRES_CONFIG['password'] = getpass.getpass(
                        f"Enter PostgreSQL password for user '{POSTGRES_CONFIG['user']}': "
                    )
                    # Recreate connection string with password
                    pg_connection_string = (
                        f"postgresql://{POSTGRES_CONFIG['user']}:{POSTGRES_CONFIG['password']}"
                        f"@{POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}"
                        f"/{POSTGRES_CONFIG['database']}"
                    )
                    pg_engine = create_engine(pg_connection_string)
                    with pg_engine.connect() as conn:
                        conn.execute(text("SELECT 1"))
                    logger.info("✅ PostgreSQL connection successful with password")
                else:
                    logger.error("Password required but running in non-interactive mode")
                    logger.error("Please set POSTGRES_PASSWORD in .env file")
                    return 1
            else:
                raise
        
        # Connect to SQLite
        logger.info(f"Connecting to SQLite: {SQLITE_DB}")
        sqlite_conn = sqlite3.connect(str(SQLITE_DB))
        
        # Get list of tables
        tables = get_sqlite_tables(sqlite_conn)
        logger.info(f"\n📦 Found {len(tables)} tables to migrate:")
        logger.info(f"   {', '.join(tables[:5])}{'...' if len(tables) > 5 else ''}")
        
        # Migrate tables
        total_rows = 0
        successful = 0
        failed = []
        
        for table in tables:
            try:
                rows = migrate_table(table, sqlite_conn, pg_engine)
                if rows > 0:
                    total_rows += rows
                    successful += 1
                    # Create indexes
                    create_postgres_indexes(pg_engine, table)
            except Exception as e:
                logger.error(f"Failed to migrate {table}: {e}")
                failed.append(table)
        
        # Migrate views (informational only)
        migrate_views(sqlite_conn, pg_engine)
        
        # Close connections
        sqlite_conn.close()
        pg_engine.dispose()
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("📊 MIGRATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"✅ Successfully migrated: {successful}/{len(tables)} tables")
        logger.info(f"📈 Total rows migrated: {total_rows:,}")
        
        if failed:
            logger.warning(f"❌ Failed tables: {', '.join(failed)}")
        
        logger.info("\n✅ Migration complete!")
        logger.info("\nNext steps:")
        logger.info("  1. Verify data in PostgreSQL")
        logger.info("  2. Configure Looker connection")
        logger.info("  3. Create LookML models")
        
        return 0
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
