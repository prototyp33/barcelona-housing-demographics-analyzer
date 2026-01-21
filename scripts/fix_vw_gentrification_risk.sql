-- Fix Script: vw_gentrification_risk View
-- 
-- Issue: View may reference non-existent column pct_universitarios
-- Solution: Recreate view using only columns that exist in fact_educacion
--
-- Run: sqlite3 data/processed/database.db < scripts/fix_vw_gentrification_risk.sql

-- ============================================================================
-- STEP 1: Drop existing view (if it exists)
-- ============================================================================
DROP VIEW IF EXISTS vw_gentrification_risk;

-- ============================================================================
-- STEP 2: Recreate view with safe column references
-- ============================================================================
-- Using only columns that exist in fact_educacion:
-- - total_centros_educativos (exists)
-- - num_centros_universidad (exists, can be used as proxy for education level)
-- 
-- Removed: pct_universitarios (doesn't exist in actual table)
CREATE VIEW vw_gentrification_risk AS
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

-- ============================================================================
-- STEP 3: Verify view works
-- ============================================================================
-- Test query (should return count without errors)
SELECT 
    'View created successfully' AS status,
    COUNT(*) AS record_count
FROM vw_gentrification_risk;

-- Show sample data
SELECT 
    nom_barri,
    barrio_id,
    year,
    num_centros_educativos,
    num_universidades,
    precio_venta_medio_m2,
    pm25_mean,
    pct_exposed_65db
FROM vw_gentrification_risk
LIMIT 10;
