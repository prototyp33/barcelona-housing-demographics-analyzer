"""
Módulo para cargar el Master Table CSV a la base de datos.

Proporciona funciones reutilizables para crear el esquema y cargar datos
del Master Table en la tabla fact_housing_master.
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

# Esquema de la tabla fact_housing_master
CREATE_FACT_HOUSING_MASTER = """
CREATE TABLE IF NOT EXISTS fact_housing_master (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    barrio_nombre TEXT,
    year INTEGER NOT NULL,
    quarter TEXT NOT NULL,
    period TEXT,
    -- Precios
    preu_lloguer_mensual REAL,
    preu_lloguer_m2 REAL,
    preu_venda_total REAL,
    preu_venda_m2 REAL,
    source_rental TEXT,
    source_sales TEXT,
    -- Renta
    renta_annual REAL,
    renta_min REAL,
    renta_max REAL,
    -- Affordability metrics
    price_to_income_ratio REAL,
    rent_burden_pct REAL,
    affordability_index REAL,
    affordability_ratio REAL,
    -- Atributos estructurales
    anyo_construccion_promedio REAL,
    antiguedad_anos REAL,
    num_edificios REAL,
    pct_edificios_pre1950 REAL,
    superficie_m2 REAL,
    pct_edificios_con_ascensor_proxy REAL,
    -- Features transformadas
    log_price_sales REAL,
    log_price_rental REAL,
    building_age_dynamic REAL,
    -- Metadatos
    source TEXT,
    year_quarter TEXT,
    time_index INTEGER,
    etl_loaded_at TEXT,
    FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
);
"""

CREATE_INDEXES = [
    """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_housing_master_unique
    ON fact_housing_master (barrio_id, year, quarter);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_fact_housing_master_year_quarter
    ON fact_housing_master (year, quarter);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_fact_housing_master_barrio_year
    ON fact_housing_master (barrio_id, year);
    """,
]


def create_master_table_schema(conn: sqlite3.Connection) -> None:
    """
    Crea la tabla fact_housing_master y sus índices si no existen.
    
    Args:
        conn: Conexión a la base de datos SQLite
    """
    logger.info("Creando esquema de fact_housing_master")
    with conn:
        conn.executescript(CREATE_FACT_HOUSING_MASTER)
        for index_sql in CREATE_INDEXES:
            conn.executescript(index_sql)
    logger.info("✓ Esquema de fact_housing_master creado exitosamente")


def load_master_table_from_csv(
    conn: sqlite3.Connection,
    csv_path: Path,
    truncate: bool = True,
) -> int:
    """
    Carga los datos del Master Table CSV a la tabla fact_housing_master.
    
    Args:
        conn: Conexión a la base de datos SQLite
        csv_path: Ruta al archivo CSV del Master Table
        truncate: Si True, elimina registros existentes antes de cargar
    
    Returns:
        Número de registros cargados
    
    Raises:
        FileNotFoundError: Si el CSV no existe
        ValueError: Si no hay barrios válidos en dim_barrios
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Master Table CSV no encontrado: {csv_path}")
    
    logger.info(f"Leyendo Master Table desde {csv_path}")
    df = pd.read_csv(csv_path)
    
    # Validar que todos los barrio_id existen en dim_barrios
    logger.debug("Validando integridad referencial")
    cursor = conn.execute("SELECT barrio_id FROM dim_barrios")
    valid_barrio_ids = {row[0] for row in cursor.fetchall()}
    
    if not valid_barrio_ids:
        raise ValueError(
            "No hay barrios en dim_barrios. Cargue dim_barrios primero."
        )
    
    invalid_barrios = set(df['barrio_id'].unique()) - valid_barrio_ids
    if invalid_barrios:
        logger.warning(
            f"Barrios no encontrados en dim_barrios: {sorted(invalid_barrios)}. "
            "Filtrando registros inválidos."
        )
        # Filtrar registros con barrios inválidos
        df = df[df['barrio_id'].isin(valid_barrio_ids)]
        logger.info(f"Filtrados {len(df)} registros válidos")
    
    # Añadir timestamp de carga
    df['etl_loaded_at'] = datetime.now().isoformat()
    
    logger.info(f"Cargando {len(df):,} registros a fact_housing_master")
    
    # Truncar tabla antes de cargar si se solicita
    if truncate:
        conn.execute("DELETE FROM fact_housing_master")
        conn.commit()
        logger.debug("Tabla fact_housing_master truncada")
    
    # Cargar datos en chunks para evitar "too many SQL variables"
    chunk_size = 100
    total_chunks = (len(df) + chunk_size - 1) // chunk_size
    
    for i in range(0, len(df), chunk_size):
        chunk = df.iloc[i:i + chunk_size]
        chunk_num = (i // chunk_size) + 1
        logger.debug(
            f"Cargando chunk {chunk_num}/{total_chunks} ({len(chunk)} registros)"
        )
        chunk.to_sql(
            "fact_housing_master",
            conn,
            if_exists="append",
            index=False,
        )
        conn.commit()
    
    # Verificar carga
    cursor = conn.execute("SELECT COUNT(*) FROM fact_housing_master")
    count = cursor.fetchone()[0]
    logger.info(f"✓ {count:,} registros cargados exitosamente en fact_housing_master")
    
    return count


def load_master_table_if_exists(
    conn: sqlite3.Connection,
    processed_dir: Path,
) -> tuple[bool, int]:
    """
    Carga el Master Table si el CSV existe.
    
    Args:
        conn: Conexión a la base de datos SQLite
        processed_dir: Directorio donde se encuentra el CSV procesado
    
    Returns:
        Tupla (loaded, count) donde:
        - loaded: True si se cargó, False si no existía el CSV
        - count: Número de registros cargados (0 si no se cargó)
    """
    csv_path = processed_dir / "barcelona_housing_master_table.csv"
    
    if not csv_path.exists():
        logger.debug(
            f"Master Table CSV no encontrado en {csv_path}. "
            "Omitiendo carga de fact_housing_master."
        )
        return (False, 0)
    
    try:
        # Asegurar que el esquema existe
        create_master_table_schema(conn)
        
        # Cargar datos
        count = load_master_table_from_csv(conn, csv_path, truncate=True)
        
        return (True, count)
        
    except Exception as e:
        logger.error(f"Error al cargar Master Table: {e}", exc_info=True)
        raise

