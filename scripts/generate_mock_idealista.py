#!/usr/bin/env python3
"""
Generate Mock Idealista Data
Populates fact_oferta_idealista with realistic dummy data for testing purposes.
"""

import sqlite3
import random
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

def get_db_connection():
    db_path = Path("data/processed/database.db")
    return sqlite3.connect(db_path)

def generate_mock_data():
    conn = get_db_connection()
    
    # Get barrios
    barrios = pd.read_sql("SELECT barrio_id, barrio_nombre, distrito_nombre FROM dim_barrios", conn)
    
    # Reproducibility
    SEED = 42
    GENERATOR_VERSION = "1.0.0"
    random.seed(SEED)
    
    mock_data = []
    
    # Generate data for the last 12 months
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    current_date = start_date
    while current_date <= end_date:
        year = current_date.year
        month = current_date.month
        
        for _, barrio in barrios.iterrows():
            # Base prices based on district (simplified logic)
            base_price_m2 = 3000
            if barrio["distrito_nombre"] in ["Eixample", "Sarrià-Sant Gervasi", "Les Corts"]:
                base_price_m2 = 5000
            elif barrio["distrito_nombre"] in ["Nou Barris", "Sant Andreu"]:
                base_price_m2 = 2000
                
            # Random variation
            variation = random.uniform(0.9, 1.1)
            price_m2 = base_price_m2 * variation
            
            # SALE
            mock_data.append({
                "barrio_id": barrio["barrio_id"],
                "operacion": "sale",
                "anio": year,
                "mes": month,
                "num_anuncios": random.randint(10, 150),
                "precio_medio": price_m2 * 80, # Approx 80m2
                "precio_mediano": price_m2 * 80 * 0.95,
                "precio_min": price_m2 * 80 * 0.6,
                "precio_max": price_m2 * 80 * 1.5,
                "precio_m2_medio": price_m2,
                "precio_m2_mediano": price_m2 * 0.95,
                "superficie_media": 80,
                "superficie_mediana": 75,
                "habitaciones_media": 2.5,
                "barrio_nombre_normalizado": barrio["barrio_nombre"],
                "dataset_id": "mock_generated",
                "source": "mock_generator",
                "etl_loaded_at": datetime.now().isoformat(),
                "is_mock": True,
                "generator_version": GENERATOR_VERSION,
                "seed": SEED
            })
            
            # RENT
            rent_price_m2 = price_m2 / 200 # Approx ratio
            mock_data.append({
                "barrio_id": barrio["barrio_id"],
                "operacion": "rent",
                "anio": year,
                "mes": month,
                "num_anuncios": random.randint(5, 80),
                "precio_medio": rent_price_m2 * 70,
                "precio_mediano": rent_price_m2 * 70 * 0.95,
                "precio_min": rent_price_m2 * 70 * 0.7,
                "precio_max": rent_price_m2 * 70 * 1.3,
                "precio_m2_medio": rent_price_m2,
                "precio_m2_mediano": rent_price_m2 * 0.95,
                "superficie_media": 70,
                "superficie_mediana": 65,
                "habitaciones_media": 2.0,
                "barrio_nombre_normalizado": barrio["barrio_nombre"],
                "dataset_id": "mock_generated",
                "source": "mock_generator",
                "etl_loaded_at": datetime.now().isoformat(),
                "is_mock": True,
                "generator_version": GENERATOR_VERSION,
                "seed": SEED
            })
            
        # Next month
        if month == 12:
            current_date = datetime(year + 1, 1, 1)
        else:
            current_date = datetime(year, month + 1, 1)
            
    # Insert into DB
    df = pd.DataFrame(mock_data)
    
    # Filtrar solo las columnas que existen en la tabla
    # Obtener columnas de la tabla
    table_info = pd.read_sql("PRAGMA table_info(fact_oferta_idealista)", conn)
    valid_columns = set(table_info["name"].tolist())
    
    # Filtrar DataFrame para incluir solo columnas válidas
    df_filtered = df[[col for col in df.columns if col in valid_columns]]
    
    # Clear existing mock data
    conn.execute("DELETE FROM fact_oferta_idealista WHERE source = 'mock_generator'")
    
    # Append new data
    df_filtered.to_sql("fact_oferta_idealista", conn, if_exists="append", index=False)
    
    print(f"✅ Generated {len(df)} mock records for Idealista")
    conn.close()

if __name__ == "__main__":
    generate_mock_data()
