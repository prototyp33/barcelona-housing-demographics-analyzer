#!/usr/bin/env python3
"""
Script para crear datos de ejemplo de criminalidad del ICGC.

Este script genera un archivo CSV de ejemplo con datos sintéticos de criminalidad
para todos los barrios de Barcelona, útil para probar el módulo de seguridad.

Uso:
    python scripts/create_sample_icgc_data.py
"""

import sys
from pathlib import Path

# Añadir el directorio raíz al path para importar módulos
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import sqlite3
from src.database_setup import DEFAULT_DB_NAME, create_database_schema


def main() -> int:
    """Crea un archivo CSV de ejemplo con datos sintéticos de criminalidad."""
    # Determinar ruta de la base de datos
    db_path = project_root / "data" / "processed" / DEFAULT_DB_NAME
    
    if not db_path.exists():
        print(f"⚠️  Base de datos no encontrada: {db_path}")
        print("   Creando datos de ejemplo sin barrios de la BD...")
        barrios = []
        for i in range(1, 74):  # 73 barrios
            barrios.append({
                "barrio_id": i,
                "barrio_nombre": f"Barrio {i}",
            })
        barrios_df = pd.DataFrame(barrios)
    else:
        print(f"✓ Cargando barrios desde: {db_path}")
        conn = sqlite3.connect(db_path)
        try:
            create_database_schema(conn)
            barrios_df = pd.read_sql_query(
                "SELECT barrio_id, barrio_nombre FROM dim_barrios ORDER BY barrio_id",
                conn
            )
            print(f"✓ {len(barrios_df)} barrios cargados")
        finally:
            conn.close()
    
    # Crear directorio de salida
    output_dir = project_root / "data" / "raw" / "icgc"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generar datos sintéticos para 2020-2024, trimestres 1-4
    records = []
    
    for _, barrio in barrios_df.iterrows():
        barrio_id = barrio["barrio_id"]
        barrio_nombre = barrio["barrio_nombre"]
        
        # Generar datos para cada año y trimestre
        for anio in range(2020, 2025):  # 2020-2024
            for trimestre in range(1, 5):  # 1-4
                # Datos sintéticos: variación por barrio y año
                # Barrios con ID más bajo tienen más delitos (simulación)
                base_factor = 1.0 - (barrio_id / 73) * 0.5  # Factor 0.5 a 1.0
                year_factor = 1.0 + (anio - 2020) * 0.1  # Aumento anual del 10%
                
                robos = int(10 * base_factor * year_factor + (trimestre * 2))
                hurtos = int(15 * base_factor * year_factor + (trimestre * 3))
                agresiones = int(3 * base_factor * year_factor + (trimestre * 1))
                
                records.append({
                    "barrio": barrio_nombre,
                    "anio": anio,
                    "trimestre": trimestre,
                    "robos": robos,
                    "hurtos": hurtos,
                    "agresiones": agresiones,
                })
    
    df = pd.DataFrame(records)
    
    # Guardar CSV
    output_file = output_dir / "icgc_criminalidad_2020_2024.csv"
    df.to_csv(output_file, index=False)
    
    print(f"\n✓ Archivo CSV de ejemplo creado: {output_file}")
    print(f"  - Registros: {len(df)}")
    print(f"  - Barrios: {df['barrio'].nunique()}")
    print(f"  - Años: {df['anio'].min()}-{df['anio'].max()}")
    print(f"  - Trimestres: {df['trimestre'].min()}-{df['trimestre'].max()}")
    print()
    print("Ahora puedes ejecutar:")
    print("  1. python -m src.etl.pipeline  (para procesar los datos)")
    print("  2. python scripts/validate_seguridad.py  (para validar)")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

