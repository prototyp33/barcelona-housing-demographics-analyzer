"""Database schema and connection helpers for the ETL pipeline."""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import FrozenSet, Iterable, Mapping, Optional

logger = logging.getLogger(__name__)

DEFAULT_DB_NAME = "database.db"

# Whitelist de tablas válidas para operaciones dinámicas (seguridad contra SQL injection)
VALID_TABLES: FrozenSet[str] = frozenset({
    "dim_barrios",
    "fact_precios",
    "fact_demografia",
    "fact_demografia_ampliada",
    "fact_renta",
    "fact_oferta_idealista",
    "fact_housing_master",
    "etl_runs",
})


class InvalidTableNameError(ValueError):
    """Excepción lanzada cuando se intenta usar un nombre de tabla no válido."""

    def __init__(self, table_name: str, valid_tables: FrozenSet[str]) -> None:
        """
        Inicializa la excepción.

        Args:
            table_name: Nombre de tabla inválido.
            valid_tables: Conjunto de tablas válidas.
        """
        self.table_name = table_name
        self.valid_tables = valid_tables
        super().__init__(
            f"Nombre de tabla no válido: '{table_name}'. "
            f"Tablas permitidas: {sorted(valid_tables)}"
        )


def validate_table_name(table_name: str) -> str:
    """
    Valida que un nombre de tabla esté en la whitelist.

    Esta función previene SQL injection validando que el nombre de tabla
    sea uno de los conocidos en el esquema.

    Args:
        table_name: Nombre de tabla a validar.

    Returns:
        El nombre de tabla validado (sin modificar).

    Raises:
        InvalidTableNameError: Si el nombre no está en la whitelist.

    Example:
        >>> validate_table_name("dim_barrios")
        'dim_barrios'
        >>> validate_table_name("malicious_table; DROP TABLE users;--")
        InvalidTableNameError: Nombre de tabla no válido...
    """
    if table_name not in VALID_TABLES:
        logger.error(
            "Intento de usar tabla no válida: '%s'. Posible SQL injection.",
            table_name,
        )
        raise InvalidTableNameError(table_name, VALID_TABLES)
    return table_name


CREATE_TABLE_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS dim_barrios (
        barrio_id INTEGER PRIMARY KEY,
        barrio_nombre TEXT NOT NULL,
        barrio_nombre_normalizado TEXT NOT NULL,
        distrito_id INTEGER,
        distrito_nombre TEXT,
        municipio TEXT,
        ambito TEXT,
        codi_districte TEXT,
        codi_barri TEXT,
        geometry_json TEXT,
        source_dataset TEXT,
        etl_created_at TEXT,
        etl_updated_at TEXT
    );
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_dim_barrios_nombre
    ON dim_barrios (barrio_nombre_normalizado);
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_precios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        barrio_id INTEGER NOT NULL,
        anio INTEGER NOT NULL,
        periodo TEXT,
        trimestre INTEGER,
        precio_m2_venta REAL,
        precio_mes_alquiler REAL,
        dataset_id TEXT,
        source TEXT,
        etl_loaded_at TEXT,
        FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
    );
    """,
    """
    DROP INDEX IF EXISTS idx_fact_precios_unique;
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_precios_unique
    ON fact_precios (
        barrio_id,
        anio,
        COALESCE(trimestre, -1),
        COALESCE(dataset_id, ''),
        COALESCE(source, '')
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_demografia (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        barrio_id INTEGER NOT NULL,
        anio INTEGER NOT NULL,
        poblacion_total INTEGER,
        poblacion_hombres INTEGER,
        poblacion_mujeres INTEGER,
        hogares_totales INTEGER,
        edad_media REAL,
        porc_inmigracion REAL,
        densidad_hab_km2 REAL,
        dataset_id TEXT,
        source TEXT,
        etl_loaded_at TEXT,
        FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
    );
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_demografia_unique
    ON fact_demografia (barrio_id, anio);
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_demografia_ampliada (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        barrio_id INTEGER NOT NULL,
        anio INTEGER NOT NULL,
        sexo TEXT,
        grupo_edad TEXT,
        nacionalidad TEXT,
        poblacion INTEGER,
        barrio_nombre_normalizado TEXT,
        dataset_id TEXT,
        source TEXT,
        etl_loaded_at TEXT,
        FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_fact_demografia_ampliada_barrio_anio
    ON fact_demografia_ampliada (barrio_id, anio);
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_renta (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        barrio_id INTEGER NOT NULL,
        anio INTEGER NOT NULL,
        renta_euros REAL,
        renta_promedio REAL,
        renta_mediana REAL,
        renta_min REAL,
        renta_max REAL,
        num_secciones INTEGER,
        barrio_nombre_normalizado TEXT,
        dataset_id TEXT,
        source TEXT,
        etl_loaded_at TEXT,
        FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
    );
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_renta_unique
    ON fact_renta (barrio_id, anio);
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_oferta_idealista (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        barrio_id INTEGER NOT NULL,
        operacion TEXT NOT NULL,
        anio INTEGER NOT NULL,
        mes INTEGER NOT NULL,
        num_anuncios INTEGER,
        precio_medio REAL,
        precio_mediano REAL,
        precio_min REAL,
        precio_max REAL,
        precio_m2_medio REAL,
        precio_m2_mediano REAL,
        superficie_media REAL,
        superficie_mediana REAL,
        habitaciones_media REAL,
        barrio_nombre_normalizado TEXT,
        dataset_id TEXT,
        source TEXT,
        etl_loaded_at TEXT,
        is_mock INTEGER DEFAULT 0,
        FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
    );
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_oferta_idealista_unique
    ON fact_oferta_idealista (barrio_id, operacion, anio, mes);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_fact_oferta_idealista_barrio_fecha
    ON fact_oferta_idealista (barrio_id, anio, mes);
    """,
    """
    CREATE TABLE IF NOT EXISTS etl_runs (
        run_id TEXT PRIMARY KEY,
        started_at TEXT NOT NULL,
        finished_at TEXT NOT NULL,
        status TEXT NOT NULL,
        parameters TEXT
    );
    """,
)


def ensure_database_path(db_path: Optional[Path], processed_dir: Path) -> Path:
    """Return a fully qualified database path, creating directories if required."""

    processed_dir.mkdir(parents=True, exist_ok=True)
    if db_path is None:
        db_path = processed_dir / DEFAULT_DB_NAME
    else:
        db_path = Path(db_path)
        if not db_path.is_absolute():
            db_path = processed_dir / db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


def create_connection(db_path: Path) -> sqlite3.Connection:
    """Create an SQLite connection with foreign keys enabled."""

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def create_database_schema(conn: sqlite3.Connection) -> None:
    """Create all required tables and indexes for the analytics warehouse."""

    logger.debug("Creating database schema if not present")
    with conn:
        for statement in CREATE_TABLE_STATEMENTS:
            conn.executescript(statement)
    
    # Migraciones: añadir columnas que puedan faltar en bases de datos existentes
    migrate_database_schema(conn)


def migrate_database_schema(conn: sqlite3.Connection) -> None:
    """
    Aplica migraciones de esquema a bases de datos existentes.
    
    Args:
        conn: Conexión SQLite activa.
    """
    logger.debug("Aplicando migraciones de esquema si es necesario")
    
    try:
        # Verificar si la columna is_mock existe en fact_oferta_idealista
        cursor = conn.execute(
            "PRAGMA table_info(fact_oferta_idealista)"
        )
        columns = [row[1] for row in cursor.fetchall()]
        
        if "is_mock" not in columns:
            logger.info("Añadiendo columna is_mock a fact_oferta_idealista")
            conn.execute(
                "ALTER TABLE fact_oferta_idealista ADD COLUMN is_mock INTEGER DEFAULT 0"
            )
            conn.commit()
            logger.info("✓ Columna is_mock añadida exitosamente")
            
            # Actualizar registros existentes: si source = 'mock_generator', is_mock = 1
            conn.execute(
                "UPDATE fact_oferta_idealista SET is_mock = 1 WHERE source = 'mock_generator'"
            )
            conn.commit()
            logger.info("✓ Registros mock actualizados con is_mock = 1")
    except sqlite3.Error as e:
        logger.warning("Error al aplicar migración de esquema: %s", e)
        # No lanzar excepción para no romper el flujo si la tabla no existe aún


def truncate_tables(conn: sqlite3.Connection, tables: Iterable[str]) -> None:
    """
    Elimina todas las filas de las tablas especificadas dentro de una transacción.

    Args:
        conn: Conexión SQLite activa.
        tables: Iterable de nombres de tabla a truncar.

    Raises:
        InvalidTableNameError: Si alguna tabla no está en la whitelist VALID_TABLES.
    """
    # Validar todas las tablas antes de ejecutar cualquier operación
    validated_tables = [validate_table_name(table) for table in tables]

    # Desactivar temporalmente foreign keys para permitir truncado en cualquier orden
    conn.execute("PRAGMA foreign_keys = OFF;")
    try:
        with conn:
            for table in validated_tables:
                # Seguro: table ya está validado contra whitelist
                conn.execute(f"DELETE FROM {table};")
                logger.debug("Tabla %s truncada", table)
    finally:
        # Reactivar foreign keys
        conn.execute("PRAGMA foreign_keys = ON;")


def register_etl_run(
    conn: sqlite3.Connection,
    run_id: str,
    started_at: datetime,
    finished_at: datetime,
    status: str,
    parameters: Optional[Mapping[str, object]] = None,
) -> None:
    """Insert a new record into the etl_runs audit table."""

    params_json = json.dumps(parameters or {}, ensure_ascii=False)
    logger.info(
        "Registrando ejecución ETL %s con estado %s", run_id, status
    )
    with conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO etl_runs (run_id, started_at, finished_at, status, parameters)
            VALUES (?, ?, ?, ?, ?);
            """,
            (
                run_id,
                started_at.isoformat(),
                finished_at.isoformat(),
                status,
                params_json,
            ),
        )

