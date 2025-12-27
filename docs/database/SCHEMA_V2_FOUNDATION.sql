-- SCHEMA_V2_FOUNDATION.sql
-- Barcelona Housing Demographics Analyzer
-- Foundation v2.0 (8 Fact Table/View Layers + 2 Dimension Table Layers)

-- =============================================================================
-- 1. DIMENSION TABLES
-- =============================================================================

-- dim_barrios_extended
-- Extends the base dim_barrios with calculated structural KPIs and indicators
CREATE TABLE IF NOT EXISTS dim_barrios_extended (
    barrio_id INTEGER PRIMARY KEY,
    barrio_nombre TEXT NOT NULL,
    distrito_nombre TEXT,
    -- Structural KPIs (Updated via ETL)
    indice_gentrificacion_relativo REAL,
    indice_vulnerabilidad_socioeconomica REAL,
    clase_social_predominante TEXT,
    perfil_demografico_resumen TEXT,
    -- Aggregated Metrics (Last updated)
    precio_m2_venta_actual REAL,
    variacion_precio_12m REAL,
    densidad_comercial_kpi REAL,
    -- Metadata
    etl_updated_at TEXT,
    FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
);

-- dim_tiempo (Note: already exists in src, here for documentation)
-- CREATE TABLE IF NOT EXISTS dim_tiempo (...)

-- =============================================================================
-- 2. NEW FACT TABLES (FOUNDATION)
-- =============================================================================

-- fact_desempleo
-- Unemployment metrics by barrio
CREATE TABLE IF NOT EXISTS fact_desempleo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    mes INTEGER,
    num_desempleados INTEGER,
    tasa_desempleo_estimada REAL,
    -- Metadata
    dataset_id TEXT,
    source TEXT DEFAULT 'opendata_bcn_desempleo',
    etl_loaded_at TEXT,
    FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
);

-- fact_hut (Viviendas de Uso Turístico)
-- Official licenses from Generalitat/Ayuntamiento
CREATE TABLE IF NOT EXISTS fact_hut (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    num_licencias_vut INTEGER,
    densidad_vut_por_100_viviendas REAL,
    -- Metadata
    dataset_id TEXT,
    source TEXT DEFAULT 'generalitat_vut',
    etl_loaded_at TEXT,
    FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
);

-- fact_visados (Construction Permits)
-- Building permits for new construction or major renovation
CREATE TABLE IF NOT EXISTS fact_visados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    num_visados_obra_nueva INTEGER,
    num_viviendas_proyectadas INTEGER,
    presupuesto_total_euros REAL,
    -- Metadata
    dataset_id TEXT,
    source TEXT DEFAULT 'coac_visados',
    etl_loaded_at TEXT,
    FOREIGN KEY (barrio_id) REFERENCES dim_barrios (barrio_id)
);

-- =============================================================================
-- 3. COMPATIBILITY VIEWS (ALIASING & AGGREGATION)
-- =============================================================================

-- fact_airbnb (Alias for fact_presion_turistica)
CREATE VIEW IF NOT EXISTS fact_airbnb AS
SELECT 
    barrio_id,
    anio,
    mes,
    num_listings_airbnb AS active_listings,
    pct_entire_home,
    precio_noche_promedio AS price_per_night,
    tasa_ocupacion AS occupancy_rate,
    etl_loaded_at
FROM fact_presion_turistica;

-- fact_control_alquiler (Alias for fact_regulacion)
CREATE VIEW IF NOT EXISTS fact_control_alquiler AS
SELECT 
    barrio_id,
    anio,
    zona_tensionada,
    nivel_tension,
    indice_referencia_alquiler,
    etl_loaded_at
FROM fact_regulacion;

-- fact_accesibilidad (Alias for fact_movilidad)
CREATE VIEW IF NOT EXISTS fact_accesibilidad AS
SELECT 
    barrio_id,
    anio,
    mes,
    estaciones_metro,
    estaciones_bicing,
    tiempo_medio_centro_minutos,
    etl_loaded_at
FROM fact_movilidad;

-- fact_centralidad (Aggregate POI Density)
-- Combines commerce and health services to measure neighborhood centrality
CREATE VIEW IF NOT EXISTS fact_centralidad AS
SELECT 
    c.barrio_id,
    c.anio,
    c.densidad_comercial_por_km2,
    s.densidad_servicios_por_km2,
    (c.densidad_comercial_por_km2 + COALESCE(s.densidad_servicios_por_km2, 0)) AS indice_centralidad_bruto,
    c.etl_loaded_at
FROM fact_comercio c
LEFT JOIN fact_servicios_salud s ON c.barrio_id = s.barrio_id AND c.anio = s.anio;

-- =============================================================================
-- 4. INDICES
-- =============================================================================

CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_desempleo_unique ON fact_desempleo (barrio_id, anio, COALESCE(mes, 0));
CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_hut_unique ON fact_hut (barrio_id, anio);
CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_visados_unique ON fact_visados (barrio_id, anio);
