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

# Whitelist de tablas v?lidas para operaciones din?micas (seguridad contra SQL injection)
VALID_TABLES: FrozenSet[str] = frozenset({
    "dim_barrios",
    "dim_tiempo",
    "fact_precios",
    "fact_demografia",
    "fact_demografia_ampliada",
    "fact_renta",
    "fact_oferta_idealista",
    "fact_housing_master",
    "etl_runs",
})


class InvalidTableNameError(ValueError):
    """Excepci?n lanzada cuando se intenta usar un nombre de tabla no v?lido."""

    def __init__(self, table_name: str, valid_tables: FrozenSet[str]) -> None:
        """
        Inicializa la excepci?n.

        Args:
            table_name: Nombre de tabla inv?lido.
            valid_tables: Conjunto de tablas v?lidas.
        """
        self.table_name = table_name
        self.valid_tables = valid_tables
        super().__init__(
            f"Nombre de tabla no v?lido: '{table_name}'. "
            f"Tablas permitidas: {sorted(valid_tables)}"
        )


def validate_table_name(table_name: str) -> str:
    """
    Valida que un nombre de tabla est? en la whitelist.

    Esta funci?n previene SQL injection validando que el nombre de tabla
    sea uno de los conocidos en el esquema.

    Args:
        table_name: Nombre de tabla a validar.

    Returns:
        El nombre de tabla validado (sin modificar).

    Raises:
        InvalidTableNameError: Si el nombre no est? en la whitelist.

    Example:
        >>> validate_table_name("dim_barrios")
        'dim_barrios'
        >>> validate_table_name("malicious_table; DROP TABLE users;--")
        InvalidTableNameError: Nombre de tabla no v?lido...
    """
    if table_name not in VALID_TABLES:
        logger.error(
            "Intento de usar tabla no v?lida: '%s'. Posible SQL injection.",
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
        codigo_ine TEXT,
        centroide_lat REAL,
        centroide_lon REAL,
        area_km2 REAL,
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

    # #region agent log
    try:
        with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps({"id": f"log_{int(datetime.utcnow().timestamp() * 1000)}_conn_start", "timestamp": int(datetime.utcnow().timestamp() * 1000), "location": "database_setup.py:252", "message": "Creating database connection", "data": {"db_path": str(db_path), "exists": db_path.exists(), "is_file": db_path.is_file() if db_path.exists() else False}, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "A"}) + '\n')
    except Exception:
        pass
    # #endregion
    conn = sqlite3.connect(db_path)
    # #region agent log
    try:
        with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a', encoding='utf-8') as f:
            fk_check = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
            f.write(json.dumps({"id": f"log_{int(datetime.utcnow().timestamp() * 1000)}_conn_before_fk", "timestamp": int(datetime.utcnow().timestamp() * 1000), "location": "database_setup.py:256", "message": "Foreign keys status before enabling", "data": {"foreign_keys_enabled": bool(fk_check)}, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "A"}) + '\n')
    except Exception:
        pass
    # #endregion
    conn.execute("PRAGMA foreign_keys = ON;")
    # #region agent log
    try:
        with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a', encoding='utf-8') as f:
            fk_check = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
            f.write(json.dumps({"id": f"log_{int(datetime.utcnow().timestamp() * 1000)}_conn_after_fk", "timestamp": int(datetime.utcnow().timestamp() * 1000), "location": "database_setup.py:257", "message": "Foreign keys status after enabling", "data": {"foreign_keys_enabled": bool(fk_check)}, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "A"}) + '\n')
    except Exception:
        pass
    # #endregion
    return conn


def create_database_schema(conn: sqlite3.Connection) -> None:
    """Create all required tables and indexes for the analytics warehouse."""

    logger.debug("Creating database schema if not present")
    with conn:
        for statement in CREATE_TABLE_STATEMENTS:
            conn.executescript(statement)
    
    # Migraciones: a?adir columnas que puedan faltar en bases de datos existentes
    migrate_database_schema(conn)
    
    # Crear dim_tiempo si no existe
    ensure_dim_tiempo(conn)


def migrate_database_schema(conn: sqlite3.Connection) -> None:
    """
    Aplica migraciones de esquema a bases de datos existentes.
    
    Args:
        conn: Conexi?n SQLite activa.
    """
    logger.debug("Aplicando migraciones de esquema si es necesario")
    
    try:
        # Verificar si la columna is_mock existe en fact_oferta_idealista
        cursor = conn.execute(
            "PRAGMA table_info(fact_oferta_idealista)"
        )
        columns = [row[1] for row in cursor.fetchall()]
        
        if "is_mock" not in columns:
            logger.info("A?adiendo columna is_mock a fact_oferta_idealista")
            conn.execute(
                "ALTER TABLE fact_oferta_idealista ADD COLUMN is_mock INTEGER DEFAULT 0"
            )
            conn.commit()
            logger.info("? Columna is_mock a?adida exitosamente")
            
            # Actualizar registros existentes: si source = 'mock_generator', is_mock = 1
            conn.execute(
                "UPDATE fact_oferta_idealista SET is_mock = 1 WHERE source = 'mock_generator'"
            )
            conn.commit()
            logger.info("? Registros mock actualizados con is_mock = 1")
    except sqlite3.Error as e:
        logger.warning("Error al aplicar migraci?n de esquema: %s", e)
        # No lanzar excepci?n para no romper el flujo si la tabla no existe a?n


def ensure_dim_tiempo(conn: sqlite3.Connection, start_year: int = 2015, end_year: int = 2024) -> None:
    """
    Crea y pobla la tabla dim_tiempo si no existe.
    
    Args:
        conn: Conexión SQLite activa
        start_year: Año inicial (default: 2015)
        end_year: Año final inclusive (default: 2024)
    """
    logger.debug("Verificando creación de dim_tiempo")
    
    # Verificar si la tabla existe
    cursor = conn.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='dim_tiempo'
    """)
    
    table_exists = cursor.fetchone() is not None
    
    if not table_exists:
        logger.info("Creando tabla dim_tiempo")
        _create_dim_tiempo_table(conn, start_year, end_year)
    else:
        # Verificar si tiene datos
        cursor = conn.execute("SELECT COUNT(*) FROM dim_tiempo")
        count = cursor.fetchone()[0]
        if count == 0:
            logger.info("dim_tiempo existe pero está vacía, poblando...")
            _populate_dim_tiempo(conn, start_year, end_year)
        else:
            logger.debug(f"dim_tiempo ya existe con {count} registros")


def _create_dim_tiempo_table(conn: sqlite3.Connection, start_year: int, end_year: int) -> None:
    """Crea la tabla dim_tiempo y la pobla."""
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
    
    with conn:
        conn.executescript(CREATE_DIM_TIEMPO)
        for index_sql in CREATE_INDEXES:
            conn.executescript(index_sql)
    
    _populate_dim_tiempo(conn, start_year, end_year)


def _populate_dim_tiempo(conn: sqlite3.Connection, start_year: int, end_year: int) -> None:
    """Pobla la tabla dim_tiempo con períodos."""
    
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
    
    # Insertar registros
    conn.executemany("""
        INSERT OR IGNORE INTO dim_tiempo (
            time_id, anio, trimestre, mes, periodo, year_quarter, year_month,
            es_fin_de_semana, es_verano, estacion, dia_semana,
            fecha_inicio, fecha_fin
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, records)
    
    conn.commit()
    logger.info(f"✓ dim_tiempo poblada con {len(records)} registros")


def truncate_tables(conn: sqlite3.Connection, tables: Iterable[str]) -> None:
    """
    Elimina todas las filas de las tablas especificadas dentro de una transacci?n.

    Args:
        conn: Conexi?n SQLite activa.
        tables: Iterable de nombres de tabla a truncar.

    Raises:
        InvalidTableNameError: Si alguna tabla no est? en la whitelist VALID_TABLES.
    """
    # #region agent log
    try:
        with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps({"id": f"log_{int(datetime.utcnow().timestamp() * 1000)}_truncate_start", "timestamp": int(datetime.utcnow().timestamp() * 1000), "location": "database_setup.py:307", "message": "Starting table truncation", "data": {"tables": list(tables)}, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "B"}) + '\n')
    except Exception:
        pass
    # #endregion
    # Validar todas las tablas antes de ejecutar cualquier operaci?n
    validated_tables = [validate_table_name(table) for table in tables]

    # Desactivar temporalmente foreign keys para permitir truncado en cualquier orden
    conn.execute("PRAGMA foreign_keys = OFF;")
    try:
        with conn:
            for table in validated_tables:
                # #region agent log
                try:
                    with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a', encoding='utf-8') as f:
                        row_count_before = conn.execute(f"SELECT COUNT(*) FROM {table};").fetchone()[0]
                        f.write(json.dumps({"id": f"log_{int(datetime.utcnow().timestamp() * 1000)}_truncate_before", "timestamp": int(datetime.utcnow().timestamp() * 1000), "location": "database_setup.py:327", "message": "Before truncating table", "data": {"table": table, "row_count": row_count_before}, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "B"}) + '\n')
                except Exception:
                    pass
                # #endregion
                # Seguro: table ya est? validado contra whitelist
                conn.execute(f"DELETE FROM {table};")
                # #region agent log
                try:
                    with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a', encoding='utf-8') as f:
                        row_count_after = conn.execute(f"SELECT COUNT(*) FROM {table};").fetchone()[0]
                        f.write(json.dumps({"id": f"log_{int(datetime.utcnow().timestamp() * 1000)}_truncate_after", "timestamp": int(datetime.utcnow().timestamp() * 1000), "location": "database_setup.py:328", "message": "After truncating table", "data": {"table": table, "row_count": row_count_after}, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "B"}) + '\n')
                except Exception:
                    pass
                # #endregion
                logger.debug("Tabla %s truncada", table)
    finally:
        # Reactivar foreign keys
        conn.execute("PRAGMA foreign_keys = ON;")
        # #region agent log
        try:
            with open('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log', 'a', encoding='utf-8') as f:
                fk_check = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
                f.write(json.dumps({"id": f"log_{int(datetime.utcnow().timestamp() * 1000)}_truncate_fk_restored", "timestamp": int(datetime.utcnow().timestamp() * 1000), "location": "database_setup.py:331", "message": "Foreign keys restored after truncation", "data": {"foreign_keys_enabled": bool(fk_check)}, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "B"}) + '\n')
        except Exception:
            pass
        # #endregion


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
        "Registrando ejecuci?n ETL %s con estado %s", run_id, status
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

