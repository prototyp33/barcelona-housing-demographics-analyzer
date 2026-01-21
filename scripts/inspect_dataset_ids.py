import os
import psycopg2
from collections import Counter

def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        database=os.getenv("POSTGRES_DATABASE", "barcelona_housing"),
        user=os.getenv("POSTGRES_USER", os.getenv("USER", "postgres")),
        password=os.getenv("POSTGRES_PASSWORD", ""),
        port=int(os.getenv("POSTGRES_PORT", "5432"))
    )

def main():
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT dataset_id, COUNT(*) FROM fact_precios GROUP BY dataset_id ORDER BY COUNT(*) DESC")
    rows = cur.fetchall()
    print("--- DATASET_ID COUNTS IN fact_precios ---")
    for row in rows:
        print(f"ID: {row[0] if row[0] else 'NULL'}, Count: {row[1]}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
