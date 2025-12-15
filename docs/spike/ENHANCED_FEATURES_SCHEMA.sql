-- ============================================================================
-- ESQUEMA SQL PARA VARIABLES ADICIONALES DE ALTO IMPACTO
-- ============================================================================
-- Fecha: 2025-12-14
-- Objetivo: Mejorar modelos predictivos con variables de alta correlación
-- ============================================================================

-- ============================================================================
-- 1. CALIDAD AMBIENTAL (Impacto: -3.4% a +20%)
-- Correlación: r = -0.35 (ruido), r = -0.28 (aire)
-- ============================================================================

CREATE TABLE IF NOT EXISTS fact_calidad_ambiental (
    calidad_id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    trimestre INTEGER,
    
    -- RUIDO (decibelios dB)
    nivel_ruido_dia_promedio_db REAL,      -- 7:00-19:00
    nivel_ruido_tarde_promedio_db REAL,    -- 19:00-23:00
    nivel_ruido_noche_promedio_db REAL,    -- 23:00-7:00 (MAYOR IMPACTO)
    nivel_ruido_max_db REAL,               -- Pico máximo
    
    -- Clasificación según OMS
    categoria_ruido TEXT,                   -- 'bajo_45db', 'moderado_45_55', 
                                           -- 'alto_55_65', 'muy_alto_65+'
    
    pct_viviendas_expuestas_ruido_alto REAL, -- % > 65 dB
    
    -- CONTAMINACIÓN AIRE
    concentracion_pm25 REAL,                -- Partículas 2.5 micrones (µg/m³)
    concentracion_pm10 REAL,                -- Partículas 10 micrones
    concentracion_no2 REAL,                 -- Dióxido de nitrógeno
    concentracion_o3 REAL,                  -- Ozono
    
    indice_calidad_aire INTEGER,           -- 0-100 (EPA Index)
    dias_superacion_limites INTEGER,        -- Días/año superando límites UE
    
    -- ZONAS VERDES
    superficie_zonas_verdes_m2 REAL,
    pct_area_verde REAL,                    -- % área del barrio con vegetación
    num_arboles_por_habitante REAL,
    
    -- Metadata
    source_ruido TEXT,                      -- 'ayuntamiento_barcelona', 'osm'
    source_aire TEXT,                       -- 'generalitat', 'ministerio'
    etl_created_at TEXT,
    etl_updated_at TEXT,
    
    FOREIGN KEY(barrio_id) REFERENCES dim_barrios(barrio_id),
    UNIQUE(barrio_id, anio, trimestre)
);

CREATE INDEX IF NOT EXISTS idx_calidad_ambiental_barrio_anio 
    ON fact_calidad_ambiental(barrio_id, anio);

-- ============================================================================
-- 2. SEGURIDAD Y CRIMINALIDAD (Impacto: -30% a +20%)
-- Correlación: r = -0.61 (LA MÁS ALTA - INVERSA)
-- ============================================================================

CREATE TABLE IF NOT EXISTS fact_seguridad (
    seguridad_id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    trimestre INTEGER,
    
    -- CRIMINALIDAD (por 1000 habitantes)
    tasa_delitos_total REAL,               -- Total delitos/1000 hab
    tasa_delitos_violentos REAL,           -- Agresiones, robos con violencia
    tasa_robos_con_fuerza REAL,            -- Robo en domicilios (ALTO IMPACTO: -0.8%)
    tasa_robos_con_violencia REAL,         -- Robo con violencia (MÁXIMO IMPACTO: -1.3%)
    tasa_hurtos REAL,                      -- Hurtos sin violencia
    tasa_delitos_patrimoniales REAL,       -- Total contra patrimonio
    
    -- PERCEPCIÓN DE SEGURIDAD
    indice_seguridad_percibida REAL,       -- 0-100 (encuestas)
    pct_residentes_sienten_seguros REAL,   -- % que se sienten seguros
    
    -- INFRAESTRUCTURA DE SEGURIDAD
    num_camaras_vigilancia INTEGER,        -- Cámaras públicas
    num_comisarias_500m INTEGER,           -- Comisarías en 500m
    num_patrullas_diarias INTEGER,         -- Patrullas/día
    tiene_patrulla_vecinal BOOLEAN,
    
    -- ILUMINACIÓN PÚBLICA
    densidad_farolas_km2 REAL,             -- Farolas por km²
    pct_calles_bien_iluminadas REAL,
    
    -- INCIDENTES ESPECÍFICOS (últimos 12 meses)
    num_robos_domicilio INTEGER,
    num_agresiones INTEGER,
    num_vandalismo INTEGER,
    
    -- Metadata
    source TEXT,                           -- 'mossos', 'policia_nacional', 'encuestas'
    metodologia_calculo TEXT,
    etl_created_at TEXT,
    etl_updated_at TEXT,
    
    FOREIGN KEY(barrio_id) REFERENCES dim_barrios(barrio_id),
    UNIQUE(barrio_id, anio, trimestre)
);

CREATE INDEX IF NOT EXISTS idx_seguridad_barrio_anio 
    ON fact_seguridad(barrio_id, anio);

-- Vista: Índice de seguridad ponderado
CREATE VIEW IF NOT EXISTS vista_indice_seguridad AS
SELECT 
    barrio_id,
    anio,
    trimestre,
    -- Fórmula ponderada (100 = muy seguro, 0 = muy inseguro)
    (100 - (tasa_delitos_violentos * 10 + 
            tasa_robos_con_fuerza * 15 + 
            tasa_robos_con_violencia * 20)) * 
    (indice_seguridad_percibida / 100.0) as indice_seguridad_total
FROM fact_seguridad
WHERE indice_seguridad_percibida IS NOT NULL;

-- ============================================================================
-- 3. EDUCACIÓN - CALIDAD DE COLEGIOS (Impacto: +10% a +51%)
-- Correlación: r = 0.55 (ubicación cerca de buenos colegios)
-- ============================================================================

CREATE TABLE IF NOT EXISTS fact_educacion (
    educacion_id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    
    -- COLEGIOS EN EL BARRIO
    num_colegios_publicos INTEGER,
    num_colegios_concertados INTEGER,
    num_colegios_privados INTEGER,
    num_institutos INTEGER,
    num_universidades INTEGER,
    
    -- CALIDAD EDUCATIVA
    nota_media_selectividad REAL,          -- Nota media PAU/EBAU
    pct_aprobados_selectividad REAL,
    ratio_alumnos_profesor REAL,           -- Alumnos por profesor (MENOR = MEJOR)
    
    -- RANKINGS Y REPUTACIÓN
    tiene_colegio_top100_ranking BOOLEAN,  -- Según El Mundo, Micole, etc
    posicion_mejor_colegio INTEGER,        -- 1-100 en ranking nacional
    nombre_mejor_colegio TEXT,
    
    -- INFRAESTRUCTURA EDUCATIVA
    pct_colegios_con_instalaciones_deportivas REAL,
    pct_colegios_bilingues REAL,
    pct_colegios_certificacion_calidad REAL,
    
    -- ACCESIBILIDAD
    distancia_colegio_publico_mas_cercano_m INTEGER,
    num_plazas_escolares_disponibles INTEGER,
    ratio_demanda_plazas REAL,             -- Demanda/Oferta (>1 = saturación)
    
    -- NIVEL EDUCATIVO DE LA POBLACIÓN
    pct_poblacion_con_estudios_universitarios REAL,
    pct_poblacion_con_estudios_secundarios REAL,
    pct_poblacion_sin_estudios REAL,
    
    -- Metadata
    source_rankings TEXT,
    source_academico TEXT,
    etl_created_at TEXT,
    etl_updated_at TEXT,
    
    FOREIGN KEY(barrio_id) REFERENCES dim_barrios(barrio_id),
    UNIQUE(barrio_id, anio)
);

CREATE INDEX IF NOT EXISTS idx_educacion_barrio_anio 
    ON fact_educacion(barrio_id, anio);

-- Vista: Índice de calidad educativa
CREATE VIEW IF NOT EXISTS vista_indice_educacion AS
SELECT 
    db.barrio_nombre,
    fe.barrio_id,
    fe.anio,
    -- Score 0-100
    (CASE WHEN fe.tiene_colegio_top100_ranking THEN 30 ELSE 0 END +
     COALESCE((100 - fe.posicion_mejor_colegio) * 0.3, 0) +
     COALESCE(fe.nota_media_selectividad * 10, 0) +
     COALESCE((10 - fe.ratio_alumnos_profesor) * 2, 0)) as indice_calidad_educativa,
    fe.nombre_mejor_colegio
FROM fact_educacion fe
JOIN dim_barrios db ON fe.barrio_id = db.barrio_id;

-- ============================================================================
-- 4. CARACTERÍSTICAS TÉCNICAS AVANZADAS (Impacto: +15% a +40%)
-- Correlación: r = 0.70-0.82 (calidad construcción)
-- ============================================================================

CREATE TABLE IF NOT EXISTS fact_caracteristicas_tecnicas (
    tecnicas_id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    
    -- CALIDAD CONSTRUCCIÓN (escala 1-10)
    calidad_global_media REAL,             -- Overall Quality (MÁXIMA CORRELACIÓN: 0.82)
    calidad_materiales REAL,
    calidad_acabados_interiores REAL,
    calidad_cocina REAL,
    calidad_banos REAL,
    
    -- SUPERFICIE DETALLADA
    superficie_sobre_rasante_media_m2 REAL,  -- Correlación: 0.60
    superficie_sotano_media_m2 REAL,
    superficie_terraza_media_m2 REAL,
    superficie_jardin_privado_media_m2 REAL,
    
    -- DISTRIBUCIÓN
    num_dormitorios_medio REAL,             -- Correlación: 0.31
    num_banos_completos_medio REAL,         -- Correlación: 0.61 (ALTA)
    num_aseos_medio REAL,
    tiene_cocina_americana_pct REAL,
    
    -- GARAJE Y ALMACENAMIENTO
    num_plazas_garaje_medio REAL,          -- Correlación: 0.64 (ALTA)
    tiene_trastero_pct REAL,
    superficie_garaje_media_m2 REAL,
    
    -- INSTALACIONES
    tiene_calefaccion_central_pct REAL,
    tiene_aire_acondicionado_pct REAL,
    tiene_calefaccion_suelo_radiante_pct REAL,
    tiene_piscina_comunitaria_pct REAL,
    tiene_gimnasio_pct REAL,
    tiene_zonas_infantiles_pct REAL,
    
    -- EFICIENCIA ENERGÉTICA (DETALLADA)
    calificacion_energetica_media TEXT,    -- A, B, C, D, E, F, G
    consumo_energetico_kwh_m2_ano REAL,
    emisiones_co2_kg_m2_ano REAL,
    tiene_paneles_solares_pct REAL,
    tiene_ventanas_doble_acristalamiento_pct REAL,
    
    -- TECNOLOGÍA Y DOMÓTICA
    tiene_fibra_optica_pct REAL,
    tiene_videoportero_pct REAL,
    tiene_sistema_seguridad_pct REAL,
    tiene_domotica_pct REAL,
    
    -- ACCESIBILIDAD
    tiene_rampa_acceso_pct REAL,
    ancho_puertas_accesible_pct REAL,
    tiene_ascensor_adaptado_pct REAL,
    
    -- Metadata
    source TEXT,
    cobertura_pct REAL,
    etl_created_at TEXT,
    etl_updated_at TEXT,
    
    FOREIGN KEY(barrio_id) REFERENCES dim_barrios(barrio_id),
    UNIQUE(barrio_id, anio)
);

CREATE INDEX IF NOT EXISTS idx_caracteristicas_tecnicas_barrio_anio 
    ON fact_caracteristicas_tecnicas(barrio_id, anio);

-- ============================================================================
-- 5. CONTEXTO ECONÓMICO (Impacto: Variable, macroeconómico)
-- Correlación: r = 0.4-0.6 con variables macroeconómicas
-- ============================================================================

CREATE TABLE IF NOT EXISTS fact_contexto_economico (
    contexto_id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER,                      -- NULL para datos a nivel ciudad/país
    anio INTEGER NOT NULL,
    trimestre INTEGER,
    
    -- MERCADO LABORAL
    tasa_paro_barrio_pct REAL,             -- Correlación INVERSA: -0.61 (MUY ALTA)
    tasa_actividad_pct REAL,
    pct_contratos_indefinidos REAL,
    pct_empleo_sector_servicios REAL,
    salario_medio_anual_eur REAL,
    
    -- TIPOS DE INTERÉS E HIPOTECAS
    tipo_interes_hipoteca_fijo_pct REAL,   -- Euribor, hipoteca fija
    tipo_interes_hipoteca_variable_pct REAL,
    num_hipotecas_concedidas INTEGER,
    importe_medio_hipoteca_eur REAL,
    
    -- INDICADORES ECONÓMICOS
    pib_per_capita_eur REAL,
    ipc_vivienda REAL,                     -- Índice precios consumo vivienda
    confianza_consumidor INTEGER,          -- Índice 0-100
    
    -- MERCADO INMOBILIARIO
    num_transacciones_vivienda INTEGER,
    dias_promedio_venta INTEGER,
    ratio_precio_venta_tasacion REAL,      -- Precio venta / precio tasación
    
    -- Metadata
    ambito TEXT,                           -- 'barrio', 'distrito', 'ciudad', 'nacional'
    source TEXT,
    etl_created_at TEXT,
    etl_updated_at TEXT,
    
    FOREIGN KEY(barrio_id) REFERENCES dim_barrios(barrio_id),
    UNIQUE(barrio_id, anio, trimestre)
);

CREATE INDEX IF NOT EXISTS idx_contexto_economico_barrio_anio 
    ON fact_contexto_economico(barrio_id, anio);

-- ============================================================================
-- 6. DESARROLLO URBANÍSTICO Y PLANIFICACIÓN (Impacto: +10% a +30%)
-- ============================================================================

CREATE TABLE IF NOT EXISTS fact_desarrollo_urbano (
    desarrollo_id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    
    -- PROYECTOS FUTUROS
    tiene_proyectos_infraestructura_futuros BOOLEAN,
    num_proyectos_planificados INTEGER,
    inversion_proyectos_millones_eur REAL,
    ano_estimado_finalizacion INTEGER,
    
    -- CAMBIOS URBANÍSTICOS
    tiene_reurbanizacion_en_curso BOOLEAN,  -- Ej: Eix Verd Consell de Cent
    pct_calles_peatonalizadas REAL,
    tiene_superilla BOOLEAN,                -- Supermanzana Barcelona
    tiene_zona_bajas_emisiones BOOLEAN,
    
    -- NUEVAS CONSTRUCCIONES
    num_viviendas_nueva_construccion INTEGER,
    num_licencias_obra_mayor INTEGER,
    num_rehabilitaciones_integrales INTEGER,
    
    -- CALIFICACIÓN SUELO
    calificacion_urbanistica TEXT,         -- 'residencial', 'comercial', 'mixto', 'protegido'
    edificabilidad_maxima REAL,            -- m²/m² permitidos
    altura_maxima_permitida_m REAL,
    
    -- EQUIPAMIENTOS PLANIFICADOS
    tiene_nuevos_parques_planificados BOOLEAN,
    tiene_nuevas_estaciones_metro_planificadas BOOLEAN,
    tiene_nuevos_colegios_planificados BOOLEAN,
    
    -- Metadata
    source TEXT,
    fecha_actualizacion DATE,
    etl_created_at TEXT,
    etl_updated_at TEXT,
    
    FOREIGN KEY(barrio_id) REFERENCES dim_barrios(barrio_id),
    UNIQUE(barrio_id, anio)
);

CREATE INDEX IF NOT EXISTS idx_desarrollo_urbano_barrio_anio 
    ON fact_desarrollo_urbano(barrio_id, anio);

-- ============================================================================
-- 7. TURISMO Y PRESIÓN TURÍSTICA (Impacto Barcelona: -5% a +10%)
-- ============================================================================

CREATE TABLE IF NOT EXISTS fact_turismo (
    turismo_id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    trimestre INTEGER,
    
    -- ALOJAMIENTO TURÍSTICO
    num_apartamentos_turisticos INTEGER,    -- Airbnb, Booking
    num_hoteles INTEGER,
    num_hostales INTEGER,
    num_camas_turisticas INTEGER,
    ratio_plazas_turisticas_habitantes REAL,  -- Presión turística
    
    -- ACTIVIDAD TURÍSTICA
    pernoctaciones_estimadas INTEGER,
    gasto_turistico_estimado_millones_eur REAL,
    
    -- IMPACTO EN VIVIENDA
    pct_viviendas_uso_turistico REAL,       -- % viviendas dedicadas a turismo
    precio_alquiler_turistico_noche_eur REAL,
    rentabilidad_alquiler_turistico_pct REAL,
    
    -- CONFLICTO RESIDENCIAL
    denuncias_actividad_turistica INTEGER,
    indice_saturacion_turistica REAL,       -- 0-100
    
    -- Metadata
    source TEXT,
    etl_created_at TEXT,
    etl_updated_at TEXT,
    
    FOREIGN KEY(barrio_id) REFERENCES dim_barrios(barrio_id),
    UNIQUE(barrio_id, anio, trimestre)
);

CREATE INDEX IF NOT EXISTS idx_turismo_barrio_anio 
    ON fact_turismo(barrio_id, anio);

-- ============================================================================
-- 8. CONECTIVIDAD DIGITAL (Impacto: +3% a +8%)
-- ============================================================================

CREATE TABLE IF NOT EXISTS fact_conectividad_digital (
    conectividad_id INTEGER PRIMARY KEY AUTOINCREMENT,
    barrio_id INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    
    -- INFRAESTRUCTURA
    tiene_fibra_optica_disponible BOOLEAN,
    velocidad_maxima_bajada_mbps INTEGER,
    velocidad_maxima_subida_mbps INTEGER,
    num_operadores_disponibles INTEGER,
    
    -- COBERTURA MÓVIL
    cobertura_5g_pct REAL,
    cobertura_4g_pct REAL,
    calidad_senal_promedio_dbm REAL,
    
    -- USO
    pct_hogares_con_internet REAL,
    pct_hogares_con_fibra REAL,
    
    -- Metadata
    source TEXT,
    etl_created_at TEXT,
    etl_updated_at TEXT,
    
    FOREIGN KEY(barrio_id) REFERENCES dim_barrios(barrio_id),
    UNIQUE(barrio_id, anio)
);

CREATE INDEX IF NOT EXISTS idx_conectividad_digital_barrio_anio 
    ON fact_conectividad_digital(barrio_id, anio);

-- ============================================================================
-- AMPLIACIONES A TABLAS EXISTENTES
-- ============================================================================

-- Ampliar fact_proximidad con transporte detallado
ALTER TABLE fact_proximidad ADD COLUMN num_lineas_metro_cercanas INTEGER;
ALTER TABLE fact_proximidad ADD COLUMN num_lineas_bus_cercanas INTEGER;
ALTER TABLE fact_proximidad ADD COLUMN frecuencia_media_transporte_min REAL;
ALTER TABLE fact_proximidad ADD COLUMN tiene_bicing_500m BOOLEAN;
ALTER TABLE fact_proximidad ADD COLUMN num_parkings_publicos_1km INTEGER;
ALTER TABLE fact_proximidad ADD COLUMN congestion_trafico_score REAL;  -- 0-100
ALTER TABLE fact_proximidad ADD COLUMN walkability_score REAL;  -- 0-100

-- Ampliar fact_demografia con tendencias
ALTER TABLE fact_demografia ADD COLUMN tasa_crecimiento_poblacional_pct REAL;
ALTER TABLE fact_demografia ADD COLUMN saldo_migratorio INTEGER;
ALTER TABLE fact_demografia ADD COLUMN edad_mediana REAL;
ALTER TABLE fact_demografia ADD COLUMN indice_envejecimiento REAL;  -- (>65 / <15) * 100
ALTER TABLE fact_demografia ADD COLUMN tamano_medio_hogar REAL;
ALTER TABLE fact_demografia ADD COLUMN pct_hogares_unipersonales REAL;
ALTER TABLE fact_demografia ADD COLUMN pct_hogares_con_menores REAL;
ALTER TABLE fact_demografia ADD COLUMN indice_dependencia REAL;  -- (no activos / activos) * 100

-- Ampliar fact_housing_master con índices calculados
ALTER TABLE fact_housing_master ADD COLUMN indice_calidad_aire REAL;  -- 0-100
ALTER TABLE fact_housing_master ADD COLUMN indice_seguridad REAL;  -- 0-100
ALTER TABLE fact_housing_master ADD COLUMN indice_educacion REAL;  -- 0-100
ALTER TABLE fact_housing_master ADD COLUMN indice_calidad_ambiental REAL;  -- 0-100

-- ============================================================================
-- VISTAS ANALÍTICAS ADICIONALES
-- ============================================================================

-- Vista: Calidad ambiental con alertas
CREATE VIEW IF NOT EXISTS vista_calidad_aire_alertas AS
SELECT 
    db.barrio_nombre,
    fca.anio,
    fca.concentracion_pm25,
    CASE 
        WHEN fca.concentracion_pm25 > 25 THEN 'ALERTA'
        WHEN fca.concentracion_pm25 > 15 THEN 'PRECAUCIÓN'
        ELSE 'BUENA'
    END as estado_aire,
    fca.dias_superacion_limites
FROM fact_calidad_ambiental fca
JOIN dim_barrios db ON fca.barrio_id = db.barrio_id
WHERE fca.concentracion_pm25 IS NOT NULL;

-- Vista: Impacto combinado de factores en precio
CREATE VIEW IF NOT EXISTS vista_impacto_factores_precio AS
SELECT 
    db.barrio_id,
    db.barrio_nombre,
    fhm.year,
    fhm.quarter,
    fhm.preu_venda_m2,
    
    -- Factores de impacto
    fs.indice_seguridad_total,
    fe.indice_calidad_educativa,
    fca.nivel_ruido_noche_promedio_db,
    fca.indice_calidad_aire,
    
    -- Score combinado (0-100)
    (COALESCE(fs.indice_seguridad_total, 50) * 0.3 +
     COALESCE(fe.indice_calidad_educativa, 50) * 0.25 +
     (100 - COALESCE(fca.nivel_ruido_noche_promedio_db, 50)) * 0.2 +
     COALESCE(fca.indice_calidad_aire, 50) * 0.15 +
     50 * 0.1) as score_entorno_total
    
FROM fact_housing_master fhm
JOIN dim_barrios db ON fhm.barrio_id = db.barrio_id
LEFT JOIN vista_indice_seguridad fs ON fhm.barrio_id = fs.barrio_id 
    AND fhm.year = fs.anio
LEFT JOIN vista_indice_educacion fe ON fhm.barrio_id = fe.barrio_id 
    AND fhm.year = fe.anio
LEFT JOIN fact_calidad_ambiental fca ON fhm.barrio_id = fca.barrio_id 
    AND fhm.year = fca.anio;

