#!/usr/bin/env python3
"""
Script para crear y poblar la tabla dim_tiempo.

Genera períodos desde 2015 hasta 2024 con granularidades:
- Anual
- Quarterly (Q1-Q4)
- Mensual (opcional)
"""

from __future__ import annotations

import logging
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database_setup import create_connection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

DB_PATH = PROJECT_ROOT / "data" / "processed" / "database.db"

CREATE_DIM_TIEMPO = """
CREATE TABLE IF NOT EXISTS dim_tiempo (
    time_id INTEGER PRIMARY KEY AUTOINCREMENT,
    anio INTEGER NOT NULL,
    trimestre INTEGER,
    mes INTEGER,
    periodo TEXT,
    year_quarter TEXT,
    year_month TEXT,
    es_fin_de_semana INTEGER DEFAULT 0,
    es_verano INTEGER DEFAULT 0,
    estacion TEXT,
    dia_semana TEXT,
    fecha_inicio TEXT,
    fecha_fin TEXT
);
"""

CREATE_INDEXES = [
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_dim_tiempo_periodo ON dim_tiempo(periodo);",
    "CREATE INDEX IF NOT EXISTS idx_dim_tiempo_anio_trimestre ON dim_tiempo(anio, trimestre);",
    "CREATE INDEX IF NOT EXISTS idx_dim_tiempo_anio ON dim_tiempo(anio);",
]


def get_estacion(mes: int) -> str:
    """Determina la estación del año según el mes."""
    if mes in [12, 1, 2]:
        return "invierno"
    elif mes in [3, 4, 5]:
        return "primavera"
    elif mes in [6, 7, 8]:
        return "verano"
    else:
        return "otoño"


def create_dim_tiempo(conn: sqlite3.Connection, start_year: int = 2015, end_year: int = 2024) -> int:
    """
    Crea y pobla la tabla dim_tiempo.
    
    Args:
        conn: Conexión a la base de datos
        start_year: Año inicial
        end_year: Año final (inclusive)
    
    Returns:
        Número de registros creados
    """
    logger.info(f"Creando tabla dim_tiempo para período {start_year}-{end_year}")
    
    # Crear tabla
    conn.executescript(CREATE_DIM_TIEMPO)
    for index_sql in CREATE_INDEXES:
        conn.executescript(index_sql)
    logger.info("✓ Tabla dim_tiempo creada")
    
    # Truncar si ya existe
    conn.execute("DELETE FROM dim_tiempo")
    conn.commit()
    
    # Generar registros
    records = []
    time_id = 1
    
    for year in range(start_year, end_year + 1):
        # Registro anual
        records.append((
            time_id, year, None, None, str(year), None, None,
            0, 0, None, None,
            f"{year}-01-01", f"{year}-12-31"
        ))
        time_id += 1
        
        # Registros quarterly
        quarters = [
            (1, "Q1", f"{year}-01-01", f"{year}-03-31"),
            (2, "Q2", f"{year}-04-01", f"{year}-06-30"),
            (3, "Q3", f"{year}-07-01", f"{year}-09-30"),
            (4, "Q4", f"{year}-10-01", f"{year}-12-31"),
        ]
        
        for quarter_num, quarter_str, fecha_inicio, fecha_fin in quarters:
            # Determinar estación (usar mes medio del trimestre)
            mes_medio = (quarter_num - 1) * 3 + 2
            estacion = get_estacion(mes_medio)
            es_verano = 1 if estacion == "verano" else 0
            
            year_quarter = f"{year}-{quarter_str}"
            periodo = f"{year}{quarter_str}"
            
            records.append((
                time_id, year, quarter_num, None, periodo, year_quarter, None,
                0, es_verano, estacion, None,
                fecha_inicio, fecha_fin
            ))
            time_id += 1
        
        # Registros mensuales (opcional, comentado por ahora)
        # for month in range(1, 13):
        #     ...
    
    # Insertar registros
    conn.executemany("""
        INSERT INTO dim_tiempo (
            time_id, anio, trimestre, mes, periodo, year_quarter, year_month,
            es_fin_de_semana, es_verano, estacion, dia_semana,
            fecha_inicio, fecha_fin
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, records)
    
    conn.commit()
    
    logger.info(f"✓ {len(records)} registros insertados")
    
    # Verificar
    cursor = conn.execute("SELECT COUNT(*) FROM dim_tiempo")
    count = cursor.fetchone()[0]
    
    logger.info(f"✓ Total registros en dim_tiempo: {count}")
    
    return count


def main() -> int:
    """Función principal."""
    if not DB_PATH.exists():
        logger.error(f"Base de datos no encontrada: {DB_PATH}")
        return 1
    
    try:
        conn = create_connection(DB_PATH)
        
        try:
            count = create_dim_tiempo(conn, start_year=2015, end_year=2024)
            logger.info("=" * 80)
            logger.info("✅ dim_tiempo creada y poblada exitosamente")
            logger.info(f"   Registros: {count}")
            logger.info("=" * 80)
            return 0
        finally:
            conn.close()
            
    except Exception as e:
        logger.exception(f"Error al crear dim_tiempo: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

