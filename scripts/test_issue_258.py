"""
Test script for Issue #258: Mobility Feature Engineering.
"""

import pandas as pd
from pathlib import Path
from src.processing.prepare_movilidad import prepare_movilidad
from src.database_setup import create_connection, create_database_schema, ensure_database_path

def test_mobility_processing():
    raw_dir = Path("data/raw")
    db_path = ensure_database_path(None, Path("data/processed"))
    conn = create_connection(db_path)
    
    # Need dim_barrios
    try:
        dim_barrios = pd.read_sql("SELECT * FROM dim_barrios", conn)
        if dim_barrios.empty:
            print("⚠️ dim_barrios is empty in DB. Cannot test spatial logic.")
            return
    except Exception as e:
        print(f"❌ Error reading dim_barrios: {e}")
        return
    
    print(f"Loaded {len(dim_barrios)} barrios from DB.")
    
    # Run mobility processing
    df_movilidad = prepare_movilidad(raw_dir, dim_barrios)
    
    if not df_movilidad.empty:
        print("✅ Mobility features engineered successfully.")
        print(f"   Rows: {len(df_movilidad)}")
        print(f"   Columns: {df_movilidad.columns.tolist()}")
        print("\nSample Data:")
        print(df_movilidad.head())
        
        # Test loading
        try:
            df_movilidad.to_sql("fact_movilidad", conn, if_exists="replace", index=False)
            print("✅ Loaded into fact_movilidad successfully.")
        except Exception as e:
            print(f"❌ Error loading into DB: {e}")
    else:
        print("❌ Mobility processing failed (empty result).")
    
    conn.close()

if __name__ == "__main__":
    test_mobility_processing()
