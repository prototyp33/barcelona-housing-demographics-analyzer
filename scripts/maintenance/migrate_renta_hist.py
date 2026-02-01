
import sqlite3
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def migrate_renta_hist():
    db_path = Path("data/processed/database.db")
    if not db_path.exists():
        logger.error(f"Database not found at {db_path}")
        return

    logger.info(f"Connecting to database at {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    logger.info("Creating table fact_renta_hist...")
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS fact_renta_hist (
        renta_hist_id INTEGER PRIMARY KEY AUTOINCREMENT,
        barrio_id INTEGER NOT NULL,
        anio INTEGER NOT NULL,
        renta_media REAL,
        renta_mediana REAL,
        dataset_id TEXT,
        source TEXT DEFAULT 'idescat',
        etl_loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (barrio_id) REFERENCES dim_barrios(barrio_id),
        UNIQUE(barrio_id, anio, dataset_id, source)
    );
    """
    
    try:
        cursor.execute(create_table_sql)
        # Create an index for faster lookups
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_renta_hist_lookup ON fact_renta_hist(barrio_id, anio);")
        conn.commit()
        logger.info("Table fact_renta_hist created successfully.")
    except Exception as e:
        logger.error(f"Error creating table: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_renta_hist()
