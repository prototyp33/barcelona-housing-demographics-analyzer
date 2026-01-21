"""Database schema and connection helpers for the ETL pipeline."""

from __future__ import annotations

import calendar
import json
import logging
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import FrozenSet, Iterable, List, Mapping, Optional, Tuple

logger = logging.getLogger(__name__)

DEFAULT_DB_NAME = "database.db"

# Whitelist de tablas v?lidas para operaciones din?micas (seguridad contra SQL injection)
VALID_TABLES: FrozenSet[str] = frozenset(
    {
        "dim_barrios",
        "dim_tiempo",
        "fact_precios",
        "fact_alquiler_mensual",
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
        "fact_renta_avanzada",
        "fact_catastro_avanzado",
        "fact_hogares_avanzado",
        "fact_turismo_intensidad",
        "fact_vivienda_contexto_metropolitano",
        "dim_barrios_extended",
        "fact_airbnb",
        "fact_control_alquiler",
        "fact_accesibilidad",
        "fact_centralidad",
        "etl_runs",
        "etl_quality_metrics",
    }
)


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
    CREATE TABLE IF NOT EXISTS fact_alquiler_mensual (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        barrio_id INTEGER NOT NULL,
        anio INTEGER NOT NULL,
        mes INTEGER NOT NULL,
        precio_mes_alquiler REAL,
        dataset_id TEXT,
        source TEXT DEFAULT 'opendatabcn',
        etl_loaded_at TEXT,
        FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
    );
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_alquiler_mensual_unique
    ON fact_alquiler_mensual (
        barrio_id,
        anio,
        mes,
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
        tasa_ocupacion AS occupancy_rate
    FROM fact_presion_turistica;
    """,
    """
    CREATE VIEW IF NOT EXISTS fact_control_alquiler AS
    SELECT 
        barrio_id, anio, zona_tensionada, nivel_tension, indice_referencia_alquiler
    FROM fact_regulacion;
    """,
    """
    CREATE VIEW IF NOT EXISTS fact_accesibilidad AS
    SELECT 
        barrio_id, anio, mes, 
        estaciones_metro, estaciones_bus, estaciones_bicing, 
        dist_metro_m, dist_bus_m, access_score
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
        estaciones_bus INTEGER DEFAULT 0,
        estaciones_bicing INTEGER DEFAULT 0,
        dist_metro_m REAL,
        dist_bus_m REAL,
        access_score REAL,
        tiempo_medio_centro_minutos REAL,
        dataset_id TEXT,
        source TEXT DEFAULT 'tmb_bcn_spatial',
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
        viviendas_iniciadas_vpo INTEGER,
        viviendas_iniciadas_total INTEGER,
        viviendas_terminadas_vpo INTEGER,
        viviendas_terminadas_total INTEGER,
        viviendas_principales INTEGER,
        viviendas_no_principales INTEGER,
        num_licencias_mayor INTEGER,
        num_licencias_menor INTEGER,
        viviendas_vacias REAL,
        demanda_vpo REAL,
        ayudas_alquiler REAL,
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
    CREATE VIEW IF NOT EXISTS vw_gentrification_risk AS
    SELECT 
        b.barrio_nombre AS nom_barri,
        b.barrio_id,
        e.anio AS year,
        e.total_centros_educativos AS num_centros_educativos,
        e.num_centros_universidad AS num_universidades,
        p.precio_m2_venta AS precio_venta_medio_m2,
        a.pm25_mean,
        r.pct_poblacion_expuesta_65db AS pct_exposed_65db
    FROM dim_barrios b
    LEFT JOIN fact_educacion e ON b.barrio_id = e.barrio_id
    LEFT JOIN fact_precios p ON b.barrio_id = p.barrio_id AND e.anio = p.anio
    LEFT JOIN fact_calidad_aire a ON b.barrio_id = a.barrio_id AND e.anio = a.anio
    LEFT JOIN fact_ruido r ON b.barrio_id = r.barrio_id AND e.anio = r.anio;
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
    """
    CREATE TABLE IF NOT EXISTS etl_quality_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        completeness REAL,
        validity REAL,
        consistency REAL,
        timeliness INTEGER,
        run_id TEXT,
        FOREIGN KEY (run_id) REFERENCES etl_runs (run_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_renta_avanzada (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        barrio_id INTEGER NOT NULL,
        anio INTEGER NOT NULL,
        renta_bruta_llar REAL,
        indice_gini REAL,
        ratio_p80_p20 REAL,
        dataset_id TEXT,
        source TEXT DEFAULT 'opendata_bcn_atles_renda',
        etl_loaded_at TEXT,
        FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
    );
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_renta_avanzada_unique ON fact_renta_avanzada (barrio_id, anio);
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_catastro_avanzado (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        barrio_id INTEGER NOT NULL,
        anio INTEGER NOT NULL,
        num_propietarios_fisica INTEGER,
        num_propietarios_juridica INTEGER,
        pct_propietarios_extranjeros REAL,
        superficie_media_m2 REAL,
        num_plantas_avg REAL,
        antiguedad_media_bloque REAL,
        indice_penalizacion_topografica REAL,
        dataset_id TEXT,
        source TEXT DEFAULT 'opendata_bcn_cadastre',
        etl_loaded_at TEXT,
        FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
    );
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_catastro_avanzado_unique ON fact_catastro_avanzado (barrio_id, anio);
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_hogares_avanzado (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        barrio_id INTEGER NOT NULL,
        anio INTEGER NOT NULL,
        promedio_personas_por_hogar REAL,
        pct_hogares_unipersonales REAL,
        num_hogares_con_menores INTEGER,
        pct_hogares_nacionalidad_extranjera REAL,
        pct_presencia_mujeres REAL,
        dataset_id TEXT,
        source TEXT DEFAULT 'opendata_bcn_padro',
        etl_loaded_at TEXT,
        FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
    );
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_hogares_avanzado_unique ON fact_hogares_avanzado (barrio_id, anio);
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_turismo_intensidad (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        barrio_id INTEGER NOT NULL,
        anio INTEGER NOT NULL,
        indice_intensidad_turistica REAL,
        num_establecimientos_turisticos INTEGER,
        dataset_id TEXT,
        source TEXT DEFAULT 'opendata_bcn_turisme',
        etl_loaded_at TEXT,
        FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
    );
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_turismo_intensidad_unique ON fact_turismo_intensidad (barrio_id, anio);
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_vivienda_contexto_metropolitano (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ambito TEXT NOT NULL,  -- 'Barcelona', 'AMB', 'AMB sense Barcelona'
        anio_inicio INTEGER NOT NULL,
        anio_fin INTEGER NOT NULL,
        -- R?gimen de tenencia (%)
        propiedad_total REAL,
        propiedad_pagada REAL,
        propiedad_pendiente REAL,
        alquiler_total REAL,
        alquiler_mercado REAL,
        alquiler_social REAL,
        cesion_gratuita REAL,
        -- Concentraci?n de propiedad (%)
        pct_persona_fisica REAL,
        pct_persona_juridica REAL,
        pct_grandes_tenedores REAL,
        -- Metadatos
        source TEXT,
        etl_loaded_at TEXT,
        UNIQUE(ambito, anio_inicio, anio_fin)
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
        schema_sql = "\n".join(
            statement.strip()
            for statement in CREATE_TABLE_STATEMENTS
            if statement and isinstance(statement, str) and statement.strip()
        )
        conn.executescript(schema_sql)

    # Migraciones de esquema y tablas auxiliares
    migrate_database_schema(conn)
    ensure_dim_tiempo(conn)


def migrate_database_schema(conn: sqlite3.Connection) -> None:
    """
    Aplica migraciones de esquema a bases de datos existentes.
    
    Args:
        conn: Conexi?n SQLite activa.
    """
    logger.debug("Aplicando migraciones de esquema si es necesario")

    try:
        # IMPORTANTE: todas las migraciones deben ser atómicas (commit/rollback como unidad).
        with conn:
            # Verificar si la columna is_mock existe en fact_oferta_idealista
            cursor = conn.execute("PRAGMA table_info(fact_oferta_idealista)")
            columns = [row[1] for row in cursor.fetchall()]

            if "is_mock" not in columns:
                logger.info("A?adiendo columna is_mock a fact_oferta_idealista")
                conn.execute(
                    "ALTER TABLE fact_oferta_idealista ADD COLUMN is_mock INTEGER DEFAULT 0"
                )
                logger.info("? Columna is_mock a?adida exitosamente")

                # Actualizar registros existentes: si source = 'mock_generator', is_mock = 1
                conn.execute(
                    "UPDATE fact_oferta_idealista SET is_mock = 1 WHERE source = 'mock_generator'"
                )
                logger.info("? Registros mock actualizados con is_mock = 1")

            # Migraci?n: Quitar num_licencias_vut de fact_regulacion si existe fact_hut
            cursor = conn.execute("PRAGMA table_info(fact_regulacion)")
            reg_columns = [row[1] for row in cursor.fetchall()]
            if "num_licencias_vut" in reg_columns:
                logger.info("Detectada redundancia num_licencias_vut en fact_regulacion.")
                # En SQLite no hay DROP COLUMN directo en versiones antiguas, se suele hacer v?a tabla temporal
                # Pero en versiones modernas (3.35.0+) s? existe. Intentaremos el directo primero.
                try:
                    conn.execute("ALTER TABLE fact_regulacion DROP COLUMN num_licencias_vut")
                    logger.info(
                        "? Columna num_licencias_vut eliminada de fact_regulacion "
                        "(Redundancia resuelta)"
                    )
                except sqlite3.OperationalError:
                    logger.warning(
                        "No se pudo eliminar columna directamente. Manteniendo por compatibilidad."
                    )

            # Inicializar dim_barrios_extended desde dim_barrios
            conn.execute(
                """
                INSERT OR IGNORE INTO dim_barrios_extended (
                    barrio_id, barrio_nombre, distrito_nombre, etl_updated_at
                )
                SELECT barrio_id, barrio_nombre, distrito_nombre, datetime('now')
                FROM dim_barrios
                """
            )
            logger.info("? dim_barrios_extended inicializada con datos base de dim_barrios")

            # A?adir columnas demogr?ficas adicionales si faltan
            cursor = conn.execute("PRAGMA table_info(fact_demografia)")
            dem_columns = {row[1] for row in cursor.fetchall()}
            missing_dem_cols = {
                "pct_mayores_65": "REAL",
                "pct_menores_15": "REAL",
                "indice_envejecimiento": "REAL",
            }
            for col_name, col_type in missing_dem_cols.items():
                if col_name not in dem_columns:
                    logger.info("A?adiendo columna %s a fact_demografia", col_name)
                    conn.execute(
                        f"ALTER TABLE fact_demografia ADD COLUMN {col_name} {col_type}"
                    )
            if missing_dem_cols.keys() - dem_columns:
                logger.info("? Columnas adicionales a?adidas a fact_demografia")

            # A?adir columnas adicionales a fact_vivienda_publica
            cursor = conn.execute("PRAGMA table_info(fact_vivienda_publica)")
            vpo_columns = {row[1] for row in cursor.fetchall()}
            missing_vpo_cols = {
                "viviendas_iniciadas_vpo": "INTEGER",
                "viviendas_iniciadas_total": "INTEGER",
                "viviendas_terminadas_vpo": "INTEGER",
                "viviendas_terminadas_total": "INTEGER",
                "viviendas_principales": "INTEGER",
                "viviendas_no_principales": "INTEGER",
                "num_licencias_mayor": "INTEGER",
                "num_licencias_menor": "INTEGER",
                "viviendas_vacias": "REAL",
                "demanda_vpo": "REAL",
                "ayudas_alquiler": "REAL",
            }
            for col_name, col_type in missing_vpo_cols.items():
                if col_name not in vpo_columns:
                    logger.info("A?adiendo columna %s a fact_vivienda_publica", col_name)
                    conn.execute(
                        f"ALTER TABLE fact_vivienda_publica ADD COLUMN {col_name} {col_type}"
                    )
            if missing_vpo_cols.keys() - vpo_columns:
                logger.info("? Columnas adicionales a?adidas a fact_vivienda_publica")
    except sqlite3.Error as e:
        logger.warning("Error al aplicar migraci?n de esquema: %s", e)
        # No lanzar excepci?n para no romper el flujo si la tabla no existe a?n


def _generate_time_dimension_rows(
    year_start: int = 2015,
    year_end: int = 2024,
) -> Iterable[Tuple[int, Optional[int], Optional[int], str, Optional[str], Optional[str]]]:
    """
    Genera filas para ``dim_tiempo`` entre los a?os indicados.

    Se generan:
    - Un registro anual por a?o (sin trimestre ni mes)
    - Cuatro registros trimestrales por a?o (Q1-Q4)
    - Doce registros mensuales por a?o (YYYY-MM)

    Args:
        year_start: A?o inicial (inclusive).
        year_end: A?o final (inclusive).

    Returns:
        Iterable de tuplas con los campos b?sicos de tiempo.
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

        # Filas mensuales
        for month in range(1, 13):
            quarter = ((month - 1) // 3) + 1
            periodo_month = f"{year}-{month:02d}"
            year_quarter = f"{year}-Q{quarter}"
            year_month = periodo_month
            yield (year, quarter, month, periodo_month, year_quarter, year_month)


def ensure_dim_tiempo(conn: sqlite3.Connection) -> None:
    """
    Crea y puebla la tabla ``dim_tiempo`` de forma idempotente.

    La tabla se rellena con per?odos anuales, trimestrales y mensuales.

    Args:
        conn: Conexi?n SQLite activa.
    """
    logger.debug("Asegurando existencia y poblaci?n de dim_tiempo")

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

    # Insert idempotente: insertamos (OR IGNORE) el rango objetivo aunque ya existan filas.
    # Incluimos 2012+ porque hay series anuales que arrancan antes (ej. precios).
    year_start = 2012
    year_end = 2025
    logger.info("Asegurando dim_tiempo para el rango %s-%s", year_start, year_end)

    rows = list(_generate_time_dimension_rows(year_start, year_end))
    records: List[Tuple[int, Optional[int], Optional[int], str, Optional[str], Optional[str], int, int, str, str, str, str]] = []

    for anio, trimestre, mes, periodo, year_quarter, year_month in rows:
        # Para simplificar, usamos fechas de inicio y fin por período.
        if trimestre is None and mes is None:
            fecha_inicio = date(anio, 1, 1)
            fecha_fin = date(anio, 12, 31)
        elif mes is None:
            month_start = (trimestre - 1) * 3 + 1
            month_end = month_start + 2
            fecha_inicio = date(anio, month_start, 1)
            day_end = calendar.monthrange(anio, month_end)[1]
            fecha_fin = date(anio, month_end, day_end)
        else:
            fecha_inicio = date(anio, mes, 1)
            day_end = calendar.monthrange(anio, mes)[1]
            fecha_fin = date(anio, mes, day_end)

        es_verano = 1 if 6 <= fecha_inicio.month <= 9 else 0
        estacion = (
            "primavera"
            if 3 <= fecha_inicio.month <= 5
            else "verano"
            if 6 <= fecha_inicio.month <= 9
            else "oto?o"
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
                0,  # es_fin_de_semana (no aplica a per?odos agregados)
                es_verano,
                estacion,
                "",  # dia_semana (no aplica a per?odos agregados)
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

    # Limpieza de legacy: algunas versiones anteriores insertaron trimestres con formato 'YYYYQn'
    # en vez de 'YYYY-Qn'. Para evitar ambigüedad en joins, eliminamos el formato no estándar.
    with conn:
        conn.execute(
            """
            DELETE FROM dim_tiempo
            WHERE mes IS NULL
              AND trimestre IS NOT NULL
              AND periodo GLOB '????Q?'
            """
        )

    logger.info("dim_tiempo poblada con %s registros", len(records))


def truncate_tables(
    conn: sqlite3.Connection,
    tables: Iterable[str],
    reset_autoincrement: bool = False,
) -> None:
    """
    Elimina todas las filas de las tablas especificadas dentro de una transacci?n.

    Args:
        conn: Conexi?n SQLite activa.
        tables: Iterable de nombres de tabla a truncar.
        reset_autoincrement: Si True, resetea el contador AUTOINCREMENT (sqlite_sequence).

    Raises:
        InvalidTableNameError: Si alguna tabla no est? en la whitelist VALID_TABLES.
    """
    # Validar todas las tablas antes de ejecutar cualquier operaci?n
    validated_tables = [validate_table_name(table) for table in tables]

    # Desactivar temporalmente foreign keys para permitir truncado en cualquier orden
    conn.execute("PRAGMA foreign_keys = OFF;")
    try:
        with conn:
            for table in validated_tables:
                # Seguro: table ya est? validado contra whitelist
                try:
                    conn.execute(f"DELETE FROM {table};")
                    logger.debug("Tabla %s truncada", table)
                    if reset_autoincrement:
                        conn.execute(
                            "DELETE FROM sqlite_sequence WHERE name = ?;",
                            (table,),
                        )
                except sqlite3.OperationalError as exc:
                    # Caso común en migraciones: tabla nueva aún no existe en DB antigua.
                    # No debe bloquear el ETL, porque `create_database_schema()` se ejecuta después.
                    if "no such table" in str(exc).lower():
                        logger.info(
                            "Tabla %s no existe todavía (migración). Se omite truncado.",
                            table,
                        )
                        continue
                    raise
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

