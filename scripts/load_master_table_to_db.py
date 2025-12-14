#!/usr/bin/env python3
"""
Script para cargar el Master Table CSV a la base de datos como fact_housing_master.

Este script:
1. Crea la tabla fact_housing_master si no existe
2. Carga los datos del CSV
3. Crea índices apropiados
4. Valida la integridad referencial
"""

from __future__ import annotations

import logging
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database_setup import create_connection
from src.etl.load_master_table import (
    create_master_table_schema,
    load_master_table_from_csv,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

DB_PATH = PROJECT_ROOT / "data" / "processed" / "database.db"
MASTER_TABLE_CSV = PROJECT_ROOT / "data" / "processed" / "barcelona_housing_master_table.csv"


def validate_data_quality(conn: sqlite3.Connection) -> dict:
    """
    Valida la calidad de los datos cargados.
    
    Returns:
        Diccionario con estadísticas de validación
    """
    logger.info("Validando calidad de datos")
    
    stats = {}
    
    # Conteo total
    cursor = conn.execute("SELECT COUNT(*) FROM fact_housing_master")
    stats["total_records"] = cursor.fetchone()[0]
    
    # Barrios únicos
    cursor = conn.execute("SELECT COUNT(DISTINCT barrio_id) FROM fact_housing_master")
    stats["unique_barrios"] = cursor.fetchone()[0]
    
    # Rango de años
    cursor = conn.execute(
        "SELECT MIN(year), MAX(year) FROM fact_housing_master"
    )
    min_year, max_year = cursor.fetchone()
    stats["year_range"] = (min_year, max_year)
    
    # Valores nulos en columnas clave
    key_columns = [
        "preu_venda_m2",
        "preu_lloguer_m2",
        "renta_annual",
        "price_to_income_ratio",
    ]
    null_counts = {}
    for col in key_columns:
        cursor = conn.execute(
            f"SELECT COUNT(*) FROM fact_housing_master WHERE {col} IS NULL"
        )
        null_counts[col] = cursor.fetchone()[0]
    stats["null_counts"] = null_counts
    
    # Verificar foreign keys
    cursor = conn.execute("""
        SELECT COUNT(*) 
        FROM fact_housing_master f
        LEFT JOIN dim_barrios d ON f.barrio_id = d.barrio_id
        WHERE d.barrio_id IS NULL
    """)
    orphan_count = cursor.fetchone()[0]
    stats["orphan_records"] = orphan_count
    
    logger.info(f"  Total registros: {stats['total_records']:,}")
    logger.info(f"  Barrios únicos: {stats['unique_barrios']}/73")
    logger.info(f"  Rango años: {stats['year_range'][0]}-{stats['year_range'][1]}")
    logger.info(f"  Registros huérfanos: {stats['orphan_records']}")
    
    return stats


def main() -> int:
    """Función principal."""
    if not DB_PATH.exists():
        logger.error(f"Base de datos no encontrada: {DB_PATH}")
        return 1
    
    if not MASTER_TABLE_CSV.exists():
        logger.error(f"Master Table CSV no encontrado: {MASTER_TABLE_CSV}")
        return 1
    
    try:
        conn = create_connection(DB_PATH)
        
        try:
            # Crear esquema
            create_master_table_schema(conn)
            
            # Cargar datos
            count = load_master_table_from_csv(conn, MASTER_TABLE_CSV, truncate=True)
            
            # Validar
            stats = validate_data_quality(conn)
            
            logger.info("=" * 80)
            logger.info("✅ Carga completada exitosamente")
            logger.info(f"   Registros cargados: {count:,}")
            logger.info(f"   Barrios: {stats['unique_barrios']}/73")
            logger.info(f"   Período: {stats['year_range'][0]}-{stats['year_range'][1]}")
            
            return 0
            
        finally:
            conn.close()
            
    except Exception as e:
        logger.exception(f"Error al cargar Master Table: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

