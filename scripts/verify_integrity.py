import sqlite3
import pandas as pd
from pathlib import Path

db_path = Path("data/processed/database.db")

def verify_integrity():
    if not db_path.exists():
        print("Database not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("--- Integrity Verification ---")
    
    # Check 1: Do we have fragmented rows? (The Risk identified in point 1)
    cursor.execute("""
        SELECT barrio_id, anio, trimestre, COUNT(*) 
        FROM fact_precios 
        GROUP BY barrio_id, anio, trimestre 
        HAVING COUNT(*) > 1
    """)
    duplicates = cursor.fetchall()
    if duplicates:
        print(f"WARNING: {len(duplicates)} fragmented records found. Analytics will be difficult.")
        for dup in duplicates[:5]:
            print(f"  - Barrio {dup[0]}, Year {dup[1]}, Q{dup[2]}: {dup[3]} rows")
    else:
        print("✅ No fragmented records found in fact_precios.")
    
    # Check 2: Demographics Completeness
    cursor.execute("""
        SELECT COUNT(*) FROM fact_demografia 
        WHERE edad_media IS NULL OR densidad_hab_km2 IS NULL
    """)
    nulls = cursor.fetchone()[0]
    print(f"Demographic Nulls: {nulls}")
    
    # Check 3: Verify merged sources
    cursor.execute("""
        SELECT dataset_id, source FROM fact_precios 
        WHERE dataset_id LIKE '%|%' OR source LIKE '%|%'
        LIMIT 5
    """)
    merged_rows = cursor.fetchall()
    if merged_rows:
        print(f"✅ Found {len(merged_rows)} sample rows with merged sources (indicating successful upsert).")
        for row in merged_rows:
            print(f"  - Dataset IDs: {row[0]}")
    else:
        print("ℹ️ No merged source rows found (might be expected if no overlap occurred).")

    conn.close()

if __name__ == "__main__":
    verify_integrity()
