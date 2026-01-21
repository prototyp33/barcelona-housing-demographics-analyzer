-- Investigation Query: fact_precios Duplicates
-- This query identifies duplicate records that violate the intended uniqueness constraint
-- Run this to understand duplicate patterns before cleanup

-- ============================================================================
-- 1. OVERVIEW: Total records and potential duplicates
-- ============================================================================
SELECT 
    COUNT(*) as total_records,
    COUNT(DISTINCT barrio_id) as unique_barrios,
    COUNT(DISTINCT anio) as unique_years,
    MIN(anio) as min_year,
    MAX(anio) as max_year
FROM fact_precios;

-- ============================================================================
-- 2. DUPLICATES BY KEY FIELDS (barrio_id + anio)
-- This shows records that share the same barrio_id and anio
-- ============================================================================
WITH duplicates AS (
    SELECT 
        barrio_id,
        anio,
        COUNT(*) as duplicate_count,
        COUNT(DISTINCT dataset_id) as unique_datasets,
        COUNT(DISTINCT source) as unique_sources,
        COUNT(DISTINCT trimestre) as unique_trimestres,
        GROUP_CONCAT(DISTINCT dataset_id) as all_dataset_ids,
        GROUP_CONCAT(DISTINCT source) as all_sources
    FROM fact_precios
    GROUP BY barrio_id, anio
    HAVING COUNT(*) > 1
)
SELECT 
    d.*,
    b.barrio_nombre,
    b.distrito_nombre,
    COUNT(*) as total_duplicate_groups
FROM duplicates d
JOIN dim_barrios b ON d.barrio_id = b.barrio_id
GROUP BY d.barrio_id, d.anio
ORDER BY d.duplicate_count DESC, d.barrio_id, d.anio
LIMIT 50;

-- ============================================================================
-- 3. DETAILED DUPLICATE RECORDS
-- Shows the actual duplicate rows with all their fields
-- ============================================================================
WITH ranked_duplicates AS (
    SELECT 
        p.*,
        b.barrio_nombre,
        b.distrito_nombre,
        ROW_NUMBER() OVER (
            PARTITION BY p.barrio_id, p.anio 
            ORDER BY p.etl_loaded_at DESC, p.id DESC
        ) as dup_rank
    FROM fact_precios p
    JOIN dim_barrios b ON p.barrio_id = b.barrio_id
    WHERE EXISTS (
        SELECT 1 
        FROM fact_precios p2 
        WHERE p2.barrio_id = p.barrio_id 
          AND p2.anio = p.anio 
          AND p2.id != p.id
    )
)
SELECT 
    id,
    barrio_id,
    barrio_nombre,
    distrito_nombre,
    anio,
    trimestre,
    periodo,
    precio_m2_venta,
    precio_mes_alquiler,
    dataset_id,
    source,
    etl_loaded_at,
    dup_rank,
    CASE 
        WHEN dup_rank = 1 THEN 'KEEP (most recent)'
        ELSE 'CANDIDATE FOR DELETION'
    END as action
FROM ranked_duplicates
ORDER BY barrio_id, anio, dup_rank
LIMIT 100;

-- ============================================================================
-- 4. DUPLICATES BY SOURCE/DATASET COMBINATION
-- Shows which sources are creating duplicates
-- ============================================================================
SELECT 
    source,
    dataset_id,
    COUNT(*) as total_records,
    COUNT(DISTINCT barrio_id) as unique_barrios,
    COUNT(DISTINCT anio) as unique_years,
    COUNT(*) - COUNT(DISTINCT barrio_id || '|' || anio || '|' || COALESCE(trimestre, -1) || '|' || COALESCE(dataset_id, '')) as duplicate_count
FROM fact_precios
GROUP BY source, dataset_id
ORDER BY duplicate_count DESC, total_records DESC;

-- ============================================================================
-- 5. DUPLICATES WHERE PRICE VALUES DIFFER
-- Critical: These are duplicates with different price values (data quality issue)
-- ============================================================================
WITH price_duplicates AS (
    SELECT 
        barrio_id,
        anio,
        COUNT(*) as dup_count,
        COUNT(DISTINCT precio_m2_venta) as unique_venta_prices,
        COUNT(DISTINCT precio_mes_alquiler) as unique_alquiler_prices,
        MIN(precio_m2_venta) as min_venta,
        MAX(precio_m2_venta) as max_venta,
        MIN(precio_mes_alquiler) as min_alquiler,
        MAX(precio_mes_alquiler) as max_alquiler,
        AVG(precio_m2_venta) as avg_venta,
        AVG(precio_mes_alquiler) as avg_alquiler
    FROM fact_precios
    WHERE precio_m2_venta IS NOT NULL OR precio_mes_alquiler IS NOT NULL
    GROUP BY barrio_id, anio
    HAVING COUNT(*) > 1
)
SELECT 
    pd.*,
    b.barrio_nombre,
    b.distrito_nombre,
    CASE 
        WHEN pd.unique_venta_prices > 1 THEN '⚠️ Different venta prices'
        ELSE 'OK'
    END as venta_status,
    CASE 
        WHEN pd.unique_alquiler_prices > 1 THEN '⚠️ Different alquiler prices'
        ELSE 'OK'
    END as alquiler_status,
    ABS(pd.max_venta - pd.min_venta) as venta_variance,
    ABS(pd.max_alquiler - pd.min_alquiler) as alquiler_variance
FROM price_duplicates pd
JOIN dim_barrios b ON pd.barrio_id = b.barrio_id
WHERE pd.unique_venta_prices > 1 OR pd.unique_alquiler_prices > 1
ORDER BY venta_variance DESC, alquiler_variance DESC
LIMIT 50;

-- ============================================================================
-- 6. DUPLICATES BY TRIMESTRE (NULL vs non-NULL)
-- Shows cases where same barrio/year has both NULL and non-NULL trimestre
-- ============================================================================
SELECT 
    p.barrio_id,
    b.barrio_nombre,
    p.anio,
    COUNT(*) as total_records,
    COUNT(CASE WHEN trimestre IS NULL THEN 1 END) as null_trimestre_count,
    COUNT(CASE WHEN trimestre IS NOT NULL THEN 1 END) as nonnull_trimestre_count,
    GROUP_CONCAT(DISTINCT trimestre) as all_trimestres,
    GROUP_CONCAT(DISTINCT dataset_id) as all_datasets,
    GROUP_CONCAT(DISTINCT source) as all_sources
FROM fact_precios p
JOIN dim_barrios b ON p.barrio_id = b.barrio_id
GROUP BY p.barrio_id, p.anio
HAVING COUNT(*) > 1 
   AND (COUNT(CASE WHEN trimestre IS NULL THEN 1 END) > 0 
        AND COUNT(CASE WHEN trimestre IS NOT NULL THEN 1 END) > 0)
ORDER BY total_records DESC
LIMIT 50;

-- ============================================================================
-- 7. SUMMARY STATISTICS FOR CLEANUP PLANNING
-- ============================================================================
WITH duplicate_groups AS (
    SELECT 
        barrio_id,
        anio,
        COUNT(*) as dup_count
    FROM fact_precios
    GROUP BY barrio_id, anio
    HAVING COUNT(*) > 1
),
duplicate_records AS (
    SELECT 
        p.id,
        p.barrio_id,
        p.anio,
        ROW_NUMBER() OVER (
            PARTITION BY p.barrio_id, p.anio 
            ORDER BY p.etl_loaded_at DESC, p.id DESC
        ) as keep_rank
    FROM fact_precios p
    WHERE EXISTS (
        SELECT 1 FROM duplicate_groups dg
        WHERE dg.barrio_id = p.barrio_id AND dg.anio = p.anio
    )
)
SELECT 
    'Total duplicate groups' as metric,
    COUNT(DISTINCT barrio_id || '|' || anio) as value
FROM duplicate_groups
UNION ALL
SELECT 
    'Total duplicate records to delete',
    COUNT(*) - COUNT(CASE WHEN keep_rank = 1 THEN 1 END)
FROM duplicate_records
UNION ALL
SELECT 
    'Records to keep (most recent per group)',
    COUNT(CASE WHEN keep_rank = 1 THEN 1 END)
FROM duplicate_records
UNION ALL
SELECT 
    'Total records in fact_precios',
    COUNT(*)
FROM fact_precios;
