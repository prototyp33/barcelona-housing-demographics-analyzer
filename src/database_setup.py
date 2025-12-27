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
        "fact_soroll",
        "fact_calidad_aire",
        "fact_educacion",
        "fact_movilidad",
        "fact_vivienda_publica",
        "fact_servicios_salud",
        "fact_medio_ambiente",
        "fact_comercio",
        "fact_desempleo",
        "fact_hut",
        "fact_visados",
        "dim_barrios_extended",
        "fact_airbnb",
        "fact_control_alquiler",
        "fact_accesibilidad",
        "fact_centralidad",
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
    CREATE TABLE IF NOT EXISTS fact_hut (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        barrio_id INTEGER NOT NULL,
        anio INTEGER NOT NULL,
        num_licencias_vut INTEGER,
        densidad_vut_por_100_viviendas REAL,
        dataset_id TEXT,
        source TEXT DEFAULT 'generalitat_vut',
        etl_loaded_at TEXT,
        FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
    );
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_hut_unique ON fact_hut (barrio_id, anio);
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_desempleo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        barrio_id INTEGER NOT NULL,
        anio INTEGER NOT NULL,
        mes INTEGER,
        num_desempleados INTEGER,
        tasa_desempleo_estimada REAL,
        dataset_id TEXT,
        source TEXT DEFAULT 'opendata_bcn_desempleo',
        etl_loaded_at TEXT,
        FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
    );
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_desempleo_unique ON fact_desempleo (barrio_id, anio, COALESCE(mes, 0));
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_visados (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        barrio_id INTEGER NOT NULL,
        anio INTEGER NOT NULL,
        num_visados_obra_nueva INTEGER,
        num_viviendas_proyectadas INTEGER,
        presupuesto_total_euros REAL,
        dataset_id TEXT,
        source TEXT DEFAULT 'coac_visados',
        etl_loaded_at TEXT,
        FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
    );
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_visados_unique ON fact_visados (barrio_id, anio);
    """,
    """
    CREATE TABLE IF NOT EXISTS dim_barrios_extended (
        barrio_id INTEGER PRIMARY KEY,
        barrio_nombre TEXT NOT NULL,
        distrito_nombre TEXT,
        indice_gentrificacion_relativo REAL,
        indice_vulnerabilidad_socioeconomica REAL,
        clase_social_predominante TEXT,
        perfil_demografico_resumen TEXT,
        precio_m2_venta_actual REAL,
        variacion_precio_12m REAL,
        densidad_comercial_kpi REAL,
        etl_updated_at TEXT,
        FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
    );
    """,
    """
    CREATE VIEW IF NOT EXISTS fact_airbnb AS
    SELECT 
        barrio_id, anio, mes,
        num_listings_airbnb AS active_listings,
        pct_entire_home,
        precio_noche_promedio AS price_per_night,
        tasa_ocupacion AS occupancy_rate,
        etl_loaded_at
    FROM fact_presion_turistica;
    """,
    """
    CREATE VIEW IF NOT EXISTS fact_control_alquiler AS
    SELECT 
        barrio_id, anio, zona_tensionada, nivel_tension, indice_referencia_alquiler, etl_loaded_at
    FROM fact_regulacion;
    """,
    """
    CREATE VIEW IF NOT EXISTS fact_accesibilidad AS
    SELECT 
        barrio_id, anio, mes, estaciones_metro, estaciones_bicing, tiempo_medio_centro_minutos, etl_loaded_at
    FROM fact_movilidad;
    """,
    """
    CREATE VIEW IF NOT EXISTS fact_centralidad AS
    SELECT 
        c.barrio_id, c.anio, c.densidad_comercial_por_km2, s.densidad_servicios_por_km2,
        (c.densidad_comercial_por_km2 + COALESCE(s.densidad_servicios_por_km2, 0)) AS indice_centralidad_bruto,
        c.etl_loaded_at
    FROM fact_comercio c
    LEFT JOIN fact_servicios_salud s ON c.barrio_id = s.barrio_id AND c.anio = s.anio;
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
    CREATE TABLE IF NOT EXISTS fact_medio_ambiente (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        barrio_id INTEGER NOT NULL,
        anio INTEGER NOT NULL,
        -- Ruido (mantener compatibilidad con fact_ruido)
        nivel_lden_medio REAL,
        nivel_ld_dia REAL,
        nivel_ln_noche REAL,
        pct_poblacion_expuesta_65db REAL,
        -- Zonas verdes
        superficie_zonas_verdes_m2 REAL,
        num_parques_jardines INTEGER DEFAULT 0,
        num_arboles INTEGER DEFAULT 0,
        m2_zonas_verdes_por_habitante REAL,
        -- Metadata
        dataset_id TEXT,
        source TEXT DEFAULT 'opendata_bcn',
        etl_loaded_at TEXT,
        FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
    );
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_medio_ambiente_unique
    ON fact_medio_ambiente (
        barrio_id,
        anio
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_fact_medio_ambiente_barrio_fecha
    ON fact_medio_ambiente (barrio_id, anio);
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_educacion (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        barrio_id INTEGER NOT NULL,
        anio INTEGER NOT NULL,
        pct_sin_estudios REAL,
        pct_primaria REAL,
        pct_secundaria REAL,
        pct_universitarios REAL,
        poblacion_16plus INTEGER,
        num_centros_infantil INTEGER DEFAULT 0,
        num_centros_primaria INTEGER DEFAULT 0,
        num_centros_secundaria INTEGER DEFAULT 0,
        num_centros_fp INTEGER DEFAULT 0,
        num_centros_universidad INTEGER DEFAULT 0,
        total_centros_educativos INTEGER DEFAULT 0,
        dataset_id TEXT,
        source TEXT DEFAULT 'opendata_bcn_educacion',
        etl_loaded_at TEXT,
        FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
    );
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_educacion_unique
    ON fact_educacion (
        barrio_id,
        anio
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_fact_educacion_barrio_fecha
    ON fact_educacion (barrio_id, anio);
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_movilidad (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        barrio_id INTEGER NOT NULL,
        anio INTEGER NOT NULL,
        mes INTEGER,
        estaciones_metro INTEGER DEFAULT 0,
        estaciones_fgc INTEGER DEFAULT 0,
        paradas_bus INTEGER DEFAULT 0,
        estaciones_bicing INTEGER DEFAULT 0,
        capacidad_bicing INTEGER DEFAULT 0,
        uso_bicing_promedio REAL,
        tiempo_medio_centro_minutos REAL,
        dataset_id TEXT,
        source TEXT DEFAULT 'atm_opendata',
        etl_loaded_at TEXT,
        FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
    );
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_movilidad_unique
    ON fact_movilidad (
        barrio_id,
        anio,
        mes
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_fact_movilidad_barrio_fecha
    ON fact_movilidad (barrio_id, anio, mes);
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_vivienda_publica (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        barrio_id INTEGER NOT NULL,
        anio INTEGER NOT NULL,
        contratos_alquiler_nuevos INTEGER,
        fianzas_depositadas_euros REAL,
        renta_media_mensual_alquiler REAL,
        viviendas_proteccion_oficial INTEGER,
        dataset_id TEXT,
        source TEXT DEFAULT 'incasol_idescat',
        etl_loaded_at TEXT,
        FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
    );
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_vivienda_publica_unique
    ON fact_vivienda_publica (
        barrio_id,
        anio
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_fact_vivienda_publica_barrio_fecha
    ON fact_vivienda_publica (barrio_id, anio);
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_servicios_salud (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        barrio_id INTEGER NOT NULL,
        anio INTEGER NOT NULL,
        num_centros_salud INTEGER DEFAULT 0,
        num_hospitales INTEGER DEFAULT 0,
        num_farmacias INTEGER DEFAULT 0,
        total_servicios_sanitarios INTEGER DEFAULT 0,
        densidad_servicios_por_km2 REAL,
        densidad_servicios_por_1000hab REAL,
        dataset_id TEXT,
        source TEXT DEFAULT 'opendata_bcn',
        etl_loaded_at TEXT,
        FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
    );
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_servicios_salud_unique
    ON fact_servicios_salud (
        barrio_id,
        anio
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_fact_servicios_salud_barrio_fecha
    ON fact_servicios_salud (barrio_id, anio);
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_comercio (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        barrio_id INTEGER NOT NULL,
        anio INTEGER NOT NULL,
        num_locales_comerciales INTEGER DEFAULT 0,
        num_terrazas INTEGER DEFAULT 0,
        num_licencias INTEGER DEFAULT 0,
        total_establecimientos INTEGER DEFAULT 0,
        densidad_comercial_por_km2 REAL,
        densidad_comercial_por_1000hab REAL,
        tasa_ocupacion_locales REAL,
        pct_locales_ocupados REAL,
        dataset_id TEXT,
        source TEXT DEFAULT 'opendata_bcn',
        etl_loaded_at TEXT,
        FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
    );
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_comercio_unique
    ON fact_comercio (
        barrio_id,
        anio
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_fact_comercio_barrio_fecha
    ON fact_comercio (barrio_id, anio);
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_calidad_aire (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        barrio_id INTEGER NOT NULL,
        anio INTEGER NOT NULL,
        no2_mean REAL,
        pm25_mean REAL,
        pm10_mean REAL,
        o3_mean REAL,
        stations_nearby INTEGER,
        max_distance_m REAL,
        etl_loaded_at TEXT,
        FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
    );
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_calidad_aire_unique
    ON fact_calidad_aire (barrio_id, anio);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_fact_calidad_aire_barrio_fecha
    ON fact_calidad_aire (barrio_id, anio);
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_soroll (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        barrio_id INTEGER NOT NULL,
        anio INTEGER NOT NULL,
        lden_mean REAL,
        pct_exposed_65db REAL,
        area_covered_m2 REAL,
        etl_loaded_at TEXT,
        FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
    );
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_soroll_unique
    ON fact_soroll (barrio_id, anio);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_fact_soroll_barrio_fecha
    ON fact_soroll (barrio_id, anio);
    """,
    """
    CREATE VIEW IF NOT EXISTS vw_gentrification_risk AS
    SELECT 
        b.barrio_nombre AS nom_barri,
        e.anio AS year,
        e.pct_universitarios,
        p.precio_m2_venta AS precio_venta_medio_m2,
        a.pm25_mean,
        s.pct_exposed_65db
    FROM dim_barrios b
    LEFT JOIN fact_educacion e ON b.barrio_id = e.barrio_id
    LEFT JOIN fact_precios p ON b.barrio_id = p.barrio_id AND e.anio = p.anio
    LEFT JOIN fact_calidad_aire a ON b.barrio_id = a.barrio_id AND e.anio = a.anio
    LEFT JOIN fact_soroll s ON b.barrio_id = s.barrio_id AND e.anio = s.anio;
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

        # Migración: Quitar num_licencias_vut de fact_regulacion si existe fact_hut
        cursor = conn.execute("PRAGMA table_info(fact_regulacion)")
        reg_columns = [row[1] for row in cursor.fetchall()]
        if "num_licencias_vut" in reg_columns:
            logger.info("Detectada redundancia num_licencias_vut en fact_regulacion.")
            # En SQLite no hay DROP COLUMN directo en versiones antiguas, se suele hacer vía tabla temporal
            # Pero en versiones modernas (3.35.0+) sí existe. Intentaremos el directo primero.
            try:
                conn.execute("ALTER TABLE fact_regulacion DROP COLUMN num_licencias_vut")
                conn.commit()
                logger.info("✓ Columna num_licencias_vut eliminada de fact_regulacion (Redundancia resuelta)")
            except sqlite3.OperationalError:
                logger.warning("No se pudo eliminar columna directamente. Manteniendo por compatibilidad.")

        # Inicializar dim_barrios_extended desde dim_barrios
        conn.execute("""
            INSERT OR IGNORE INTO dim_barrios_extended (barrio_id, barrio_nombre, distrito_nombre, etl_updated_at)
            SELECT barrio_id, barrio_nombre, distrito_nombre, datetime('now')
            FROM dim_barrios
        """)
        conn.commit()
        logger.info("✓ dim_barrios_extended inicializada con datos base de dim_barrios")

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

