import os
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "database": os.getenv("POSTGRES_DATABASE", "barcelona_housing"),
    "user": os.getenv("POSTGRES_USER", os.getenv("USER", "postgres")),
    "password": os.getenv("POSTGRES_PASSWORD", ""),
    "port": int(os.getenv("POSTGRES_PORT", "5432"))
}

def check_datasets():
    conn = psycopg2.connect(**POSTGRES_CONFIG)
    query = "SELECT dataset_id, source, COUNT(*), MIN(anio), MAX(anio) FROM fact_precios GROUP BY dataset_id, source ORDER BY COUNT(*) DESC"
    df = pd.read_sql_query(query, conn)
    print("Precios por Dataset ID:")
    print(df)
    conn.close()

if __name__ == "__main__":
    check_datasets()
