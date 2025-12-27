-- SCHEMA_V2_EDUCATION_ENVIRONMENTAL.sql
-- New tables for Issue #217: Schema Design for Education & Environmental Quality

-- Fact table for education levels (Barrio-level, annual)
CREATE TABLE fact_educacion (
    barrio_id INTEGER,
    year INTEGER,
    pct_sin_estudios REAL,
    pct_primaria REAL,
    pct_secundaria REAL,
    pct_universitarios REAL,  -- Key gentrification proxy
    poblacion_16plus INTEGER,
    source_id INTEGER,
    PRIMARY KEY (barrio_id, year),
    FOREIGN KEY (barrio_id) REFERENCES dim_barrios(barrio_id)
);

-- Fact table for air quality (Barrio-level via IDW, annual)
CREATE TABLE fact_calidad_aire (
    barrio_id INTEGER,
    year INTEGER,
    no2_mean REAL,      -- µg/m³
    pm25_mean REAL,     -- Critical for hedonic pricing
    pm10_mean REAL,
    o3_mean REAL,
    stations_nearby INTEGER,  -- Quality indicator (number of stations used in IDW)
    max_distance_m REAL,      -- IDW validation metric (furthest station distance)
    PRIMARY KEY (barrio_id, year),
    FOREIGN KEY (barrio_id) REFERENCES dim_barrios(barrio_id)
);

-- Fact table for noise (Barrio-level via spatial join, quinquennial)
CREATE TABLE fact_soroll (
    barrio_id INTEGER,
    year INTEGER,          -- 2012, 2017, 2022 only
    lden_mean REAL,        -- Ambient noise: day-evening-night equivalent level in dB(A)
    pct_exposed_65db REAL, -- % population exposed to levels over 65dB
    area_covered_m2 REAL,
    PRIMARY KEY (barrio_id, year),
    FOREIGN KEY (barrio_id) REFERENCES dim_barrios(barrio_id)
);

-- View for cross-variable gentrification and quality of life analysis
CREATE VIEW vw_gentrification_risk AS
SELECT 
    b.nom_barri,
    e.year,
    e.pct_universitarios,
    p.precio_venta_medio_m2,
    a.pm25_mean,
    s.pct_exposed_65db
FROM dim_barrios b
LEFT JOIN fact_educacion e ON b.barrio_id = e.barrio_id
LEFT JOIN fact_precios p ON b.barrio_id = p.barrio_id AND e.year = p.year
LEFT JOIN fact_calidad_aire a ON b.barrio_id = a.barrio_id AND e.year = a.year
LEFT JOIN fact_soroll s ON b.barrio_id = s.barrio_id AND e.year = s.year;

-- Create indexes for performance on typical query patterns
CREATE INDEX idx_fact_educacion_year ON fact_educacion(year);
CREATE INDEX idx_fact_calidad_aire_year ON fact_calidad_aire(year);
CREATE INDEX idx_fact_soroll_year ON fact_soroll(year);
