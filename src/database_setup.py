"""Database schema and connection helpers for the ETL pipeline."""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import FrozenSet, Iterable, Mapping, Optional, Tuple

logger = logging.getLogger(__name__)

DEFAULT_DB_NAME = "database.db"

# Whitelist de tablas válidas para operaciones dinámicas (seguridad contra SQL injection)
VALID_TABLES: FrozenSet[str] = frozenset(
    {
        "dim_barrios",
        "fact_precios",
        "fact_demografia",
        "fact_demografia_ampliada",
        "fact_renta",
        "fact_oferta_idealista",
        "fact_regulacion",
        "fact_presion_turistica",
        "fact_seguridad",
        "fact_ruido",
        "etl_runs",
    }
)


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
        pct_mayores_65 REAL,
        pct_menores_15 REAL,
        indice_envejecimiento REAL,
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
    CREATE TABLE IF NOT EXISTS fact_regulacion (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        barrio_id INTEGER NOT NULL,
        anio INTEGER NOT NULL,
        zona_tensionada INTEGER,
        nivel_tension TEXT,
        indice_referencia_alquiler REAL,
        num_licencias_vut INTEGER,
        derecho_tanteo INTEGER,
        etl_loaded_at TEXT,
        FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
    );
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_regulacion_unique
    ON fact_regulacion (
        barrio_id,
        anio
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_presion_turistica (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        barrio_id INTEGER NOT NULL,
        anio INTEGER NOT NULL,
        mes INTEGER NOT NULL,
        num_listings_airbnb INTEGER,
        pct_entire_home REAL,
        precio_noche_promedio REAL,
        tasa_ocupacion REAL,
        num_reviews_mes INTEGER,
        etl_loaded_at TEXT,
        FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
    );
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_presion_turistica_unique
    ON fact_presion_turistica (
        barrio_id,
        anio,
        mes
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_fact_presion_turistica_barrio_fecha
    ON fact_presion_turistica (barrio_id, anio, mes);
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_seguridad (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        barrio_id INTEGER NOT NULL,
        anio INTEGER NOT NULL,
        trimestre INTEGER NOT NULL,
        delitos_patrimonio INTEGER,
        delitos_seguridad_personal INTEGER,
        tasa_criminalidad_1000hab REAL,
        percepcion_inseguridad REAL,
        etl_loaded_at TEXT,
        FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
    );
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_seguridad_unique
    ON fact_seguridad (
        barrio_id,
        anio,
        trimestre
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_fact_seguridad_barrio_fecha
    ON fact_seguridad (barrio_id, anio, trimestre);
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_ruido (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        barrio_id INTEGER NOT NULL,
        anio INTEGER NOT NULL,
        nivel_lden_medio REAL,
        nivel_ld_dia REAL,
        nivel_ln_noche REAL,
        pct_poblacion_expuesta_65db REAL,
        etl_loaded_at TEXT,
        FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
    );
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_ruido_unique
    ON fact_ruido (
        barrio_id,
        anio
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_fact_ruido_barrio_fecha
    ON fact_ruido (barrio_id, anio);
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

    # Migraciones de esquema y tablas auxiliares
    migrate_database_schema(conn)
    ensure_dim_tiempo(conn)


def migrate_database_schema(conn: sqlite3.Connection) -> None:
    """
    Aplica migraciones de esquema a bases de datos existentes.
    
    Args:
        conn: Conexión SQLite activa.
    """
    logger.debug("Aplicando migraciones de esquema si es necesario")

    try:
        # Verificar si la columna is_mock existe en fact_oferta_idealista
        cursor = conn.execute("PRAGMA table_info(fact_oferta_idealista)")
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

        # Añadir columnas demográficas adicionales si faltan
        cursor = conn.execute("PRAGMA table_info(fact_demografia)")
        dem_columns = {row[1] for row in cursor.fetchall()}
        missing_dem_cols = {
            "pct_mayores_65": "REAL",
            "pct_menores_15": "REAL",
            "indice_envejecimiento": "REAL",
        }
        for col_name, col_type in missing_dem_cols.items():
            if col_name not in dem_columns:
                logger.info("Añadiendo columna %s a fact_demografia", col_name)
                conn.execute(f"ALTER TABLE fact_demografia ADD COLUMN {col_name} {col_type}")
        if missing_dem_cols.keys() - dem_columns:
            conn.commit()
            logger.info("✓ Columnas adicionales añadidas a fact_demografia")
    except sqlite3.Error as e:
        logger.warning("Error al aplicar migración de esquema: %s", e)
        # No lanzar excepción para no romper el flujo si la tabla no existe aún


def _generate_time_dimension_rows(
    year_start: int = 2015,
    year_end: int = 2024,
) -> Iterable[Tuple[int, Optional[int], Optional[int], str, Optional[str], Optional[str]]]:
    """
    Genera filas para ``dim_tiempo`` entre los años indicados.

    Se generan:
    - Un registro anual por año (sin trimestre ni mes)
    - Cuatro registros trimestrales por año (Q1-Q4)

    Args:
        year_start: Año inicial (inclusive).
        year_end: Año final (inclusive).

    Returns:
        Iterable de tuplas con los campos básicos de tiempo.
    """
    for year in range(year_start, year_end + 1):
        # Fila anual
        periodo_anual = f"{year}"
        yield (year, None, None, periodo_anual, None, None)

        # Filas trimestrales
        for quarter in range(1, 5):
            periodo_quarter = f"{year}-Q{quarter}"
            year_quarter = periodo_quarter
            yield (year, quarter, None, periodo_quarter, year_quarter, None)


def ensure_dim_tiempo(conn: sqlite3.Connection) -> None:
    """
    Crea y puebla la tabla ``dim_tiempo`` de forma idempotente.

    La tabla se rellena con períodos anuales y trimestrales entre 2015 y 2024.

    Args:
        conn: Conexión SQLite activa.
    """
    logger.debug("Asegurando existencia y población de dim_tiempo")

    with conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS dim_tiempo (
                time_id INTEGER PRIMARY KEY AUTOINCREMENT,
                anio INTEGER NOT NULL,
                trimestre INTEGER,
                mes INTEGER,
                periodo TEXT NOT NULL,
                year_quarter TEXT,
                year_month TEXT,
                es_fin_de_semana INTEGER,
                es_verano INTEGER,
                estacion TEXT,
                dia_semana TEXT,
                fecha_inicio TEXT,
                fecha_fin TEXT
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_dim_tiempo_periodo
                ON dim_tiempo (periodo);
            CREATE INDEX IF NOT EXISTS idx_dim_tiempo_anio_trimestre
                ON dim_tiempo (anio, trimestre);
            """
        )

    cursor = conn.execute(
        "SELECT MIN(anio), MAX(anio), COUNT(*) FROM dim_tiempo",
    )
    row = cursor.fetchone()
    min_year, max_year, total_rows = row if row else (None, None, 0)

    # Si ya está poblada para el rango deseado, no hacemos nada
    if (
        total_rows > 0
        and min_year is not None
        and max_year is not None
        and min_year <= 2015
        and max_year >= 2024
    ):
        logger.info(
            "dim_tiempo ya está poblada (%s filas, años %s-%s), no se realizan cambios",
            total_rows,
            min_year,
            max_year,
        )
        return

    logger.info("Poblando dim_tiempo para el rango 2015-2024")

    rows = list(_generate_time_dimension_rows(2015, 2024))
    records: List[Tuple[int, Optional[int], Optional[int], str, Optional[str], Optional[str], int, int, str, str, str, str]] = []

    for anio, trimestre, mes, periodo, year_quarter, year_month in rows:
        # Para simplificar, usamos fechas de inicio y fin aproximadas por año y trimestre.
        if trimestre is None:
            fecha_inicio = date(anio, 1, 1)
            fecha_fin = date(anio, 12, 31)
        else:
            month_start = (trimestre - 1) * 3 + 1
            month_end = month_start + 2
            fecha_inicio = date(anio, month_start, 1)
            # Fecha fin aproximada al último día del mes final (no crítico para análisis)
            if month_end in (1, 3, 5, 7, 8, 10, 12):
                day_end = 31
            elif month_end == 2:
                day_end = 28
            else:
                day_end = 30
            fecha_fin = date(anio, month_end, day_end)

        es_verano = 1 if 6 <= fecha_inicio.month <= 9 else 0
        estacion = (
            "primavera"
            if 3 <= fecha_inicio.month <= 5
            else "verano"
            if 6 <= fecha_inicio.month <= 9
            else "otoño"
            if 9 < fecha_inicio.month <= 11
            else "invierno"
        )

        records.append(
            (
                anio,
                trimestre,
                mes,
                periodo,
                year_quarter,
                year_month,
                0,  # es_fin_de_semana (no aplica a períodos agregados)
                es_verano,
                estacion,
                "",  # dia_semana (no aplica a períodos agregados)
                fecha_inicio.isoformat(),
                fecha_fin.isoformat(),
            )
        )

    with conn:
        conn.executemany(
            """
            INSERT OR IGNORE INTO dim_tiempo (
                anio,
                trimestre,
                mes,
                periodo,
                year_quarter,
                year_month,
                es_fin_de_semana,
                es_verano,
                estacion,
                dia_semana,
                fecha_inicio,
                fecha_fin
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            records,
        )

    logger.info("dim_tiempo poblada con %s registros", len(records))


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

