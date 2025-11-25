import sqlite3
import pandas as pd
from pathlib import Path

db_path = Path("data/processed/database.db")

def inspect_db():
    if not db_path.exists():
        print("Database not found.")
        return

    conn = sqlite3.connect(db_path)
    
    print("--- fact_precios stats ---")
    count_precios = pd.read_sql("SELECT COUNT(*) as count FROM fact_precios", conn)
    print(f"Total rows: {count_precios['count'][0]}")
    
    print("\n--- fact_demografia stats ---")
    query_demo = """
    SELECT 
        COUNT(*) as total_rows,
        COUNT(hogares_totales) as hogares_filled,
        COUNT(edad_media) as edad_filled,
        COUNT(porc_inmigracion) as inmigracion_filled,
        COUNT(densidad_hab_km2) as densidad_filled
    FROM fact_demografia
    """
    counts_demo = pd.read_sql(query_demo, conn)
    print(counts_demo.to_string())
    
    print("\n--- fact_demografia NULLs check ---")
    query_nulls = """
    SELECT barrio_id, anio, hogares_totales, edad_media, porc_inmigracion, densidad_hab_km2
    FROM fact_demografia 
    WHERE hogares_totales IS NULL 
       OR edad_media IS NULL 
       OR porc_inmigracion IS NULL 
       OR densidad_hab_km2 IS NULL
    LIMIT 10
    """
    nulls = pd.read_sql(query_nulls, conn)
    if not nulls.empty:
        print("Found rows with NULLs:")
        print(nulls.to_string())
    else:
        print("No rows with NULLs found in the sample.")

    conn.close()

if __name__ == "__main__":
    inspect_db()
