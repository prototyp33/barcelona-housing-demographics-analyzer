#!/usr/bin/env python3
"""
Download and Load Renta 2022 Data
Downloads the 2022 disposable income CSV from Open Data BCN and loads it into fact_renta.
"""

import pandas as pd
import sqlite3
from pathlib import Path
import urllib.request
import io

# URL found in previous search
CSV_URL = "https://opendata-ajuntament.barcelona.cat/data/dataset/78db0c75-fa56-4604-9510-8b92834a7fd2/resource/3df0c5b9-de69-4c94-b924-57540e52932f/download"
DB_PATH = Path("data/processed/database.db")

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def download_and_load():
    print(f"Downloading data from {CSV_URL}...")
    
    try:
        # Download CSV
        with urllib.request.urlopen(CSV_URL) as response:
            csv_content = response.read()
            
        # Read into DataFrame
        df = pd.read_csv(io.BytesIO(csv_content))
        print(f"Downloaded {len(df)} rows.")
        print("Columns:", df.columns.tolist())
        
        # Transform
        # Expected columns in CSV: Any, Codi_Districte, Nom_Districte, Codi_Barri, Nom_Barri, Import_Renda_Bruta_€
        # Note: Column names might vary slightly, so we inspect and map carefully.
        
        # Mapping based on typical Open Data BCN format
        # We need: barrio_id, anio, renta_euros, barrio_nombre_normalizado
        
        # Inspect columns to be sure
        print("Sample data:\n", df.head())
        
        # Prepare data for DB
        # Assuming columns: 'Any', 'Codi_Barri', 'Import_€_Any' (or similar)
        
        # Let's try to identify the correct columns dynamically
        year_col = next((c for c in df.columns if 'Any' in c), None)
        barrio_id_col = next((c for c in df.columns if 'Codi_Barri' in c), None)
        amount_col = 'Import_Euros' # Explicitly identified from output
        
        if not (year_col and barrio_id_col and amount_col in df.columns):
            print(f"❌ Could not identify required columns. Found: {df.columns.tolist()}")
            return

        print(f"Mapped columns: Year={year_col}, BarrioID={barrio_id_col}, Amount={amount_col}")

        # Filter for 2022
        df = df[df[year_col] == 2022].copy()
        
        # Clean amount column
        if df[amount_col].dtype == object:
             df[amount_col] = pd.to_numeric(df[amount_col], errors='coerce')

        # AGGREGATE BY BARRIO (Data is by Census Section!)
        # Method: Mean of 'Import_Euros' per 'Codi_Barri'
        # Note: Ideally this should be weighted by population, but we lack that granularity here.
        print("Aggregating by barrio (averaging census sections)...")
        df_agg = df.groupby(barrio_id_col)[amount_col].mean().reset_index()

        # VALIDATION
        if len(df_agg) != 73:
            print(f"⚠️ Warning: Expected 73 barrios, found {len(df_agg)}")
        
        # Range check (sanity check for annual income)
        min_income = df_agg[amount_col].min()
        max_income = df_agg[amount_col].max()
        if min_income < 5000 or max_income > 100000:
             print(f"⚠️ Warning: Income values seem suspicious (Min: {min_income}, Max: {max_income})")

        records = []
        conn = get_db_connection()
        
        # Get existing barrio IDs to ensure integrity
        existing_barrios = pd.read_sql("SELECT barrio_id FROM dim_barrios", conn)
        valid_ids = set(existing_barrios['barrio_id'].tolist())
        
        load_timestamp = pd.Timestamp.now().isoformat()
        
        for _, row in df_agg.iterrows():
            barrio_id = int(row[barrio_id_col])
            
            if barrio_id in valid_ids:
                records.append({
                    "barrio_id": barrio_id,
                    "anio": 2022,
                    "renta_euros": row[amount_col],
                    "renta_promedio": row[amount_col], 
                    "renta_mediana": None,
                    "renta_min": None,
                    "renta_max": None,
                    "num_secciones": None,
                    "barrio_nombre_normalizado": None,
                    "dataset_id": "opendatabcn_renta_2022",
                    "source": "opendatabcn",
                    "source_url": CSV_URL,
                    "aggregation_method": "mean_of_census_sections",
                    "etl_loaded_at": load_timestamp
                })
        
        if not records:
            print("No valid records found to insert.")
            return

        # Insert into DB
        df_insert = pd.DataFrame(records)
        
        # Clear existing 2022 data to avoid duplicates (Idempotency)
        conn.execute("DELETE FROM fact_renta WHERE anio = 2022")
        
        df_insert.to_sql("fact_renta", conn, if_exists="append", index=False)
        print(f"✅ Successfully loaded {len(df_insert)} records for 2022.")
        print(f"   Source: {CSV_URL}")
        print(f"   Aggregation: Mean of census sections")
        
        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    download_and_load()
