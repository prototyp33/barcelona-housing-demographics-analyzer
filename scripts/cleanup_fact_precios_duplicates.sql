-- Cleanup Script: Remove Duplicates from fact_precios
-- 
-- WARNING: Run the investigation query first to understand duplicates!
-- This script keeps the most recent record per (barrio_id, anio) group
-- based on etl_loaded_at timestamp and id.
--
-- Strategy: Keep the most recent record (highest etl_loaded_at, then highest id)
-- and delete older duplicates.

-- ============================================================================
-- STEP 1: BACKUP (Recommended - uncomment to create backup)
-- ============================================================================
-- CREATE TABLE fact_precios_backup AS SELECT * FROM fact_precios;

-- ============================================================================
-- STEP 2: IDENTIFY RECORDS TO DELETE (Preview - does not delete)
-- ============================================================================
-- This shows which records would be deleted
WITH ranked_duplicates AS (
    SELECT 
        id,
        barrio_id,
        anio,
        etl_loaded_at,
        ROW_NUMBER() OVER (
            PARTITION BY barrio_id, anio 
            ORDER BY etl_loaded_at DESC, id DESC
        ) as keep_rank
    FROM fact_precios
    WHERE EXISTS (
        SELECT 1 
        FROM fact_precios p2 
        WHERE p2.barrio_id = fact_precios.barrio_id 
          AND p2.anio = fact_precios.anio 
          AND p2.id != fact_precios.id
    )
)
SELECT 
    id,
    barrio_id,
    anio,
    etl_loaded_at,
    CASE 
        WHEN keep_rank = 1 THEN 'KEEP'
        ELSE 'DELETE'
    END as action
FROM ranked_duplicates
WHERE keep_rank > 1
ORDER BY barrio_id, anio, keep_rank;

-- ============================================================================
-- STEP 3: ACTUAL DELETION (Uncomment to execute)
-- ============================================================================
-- Delete duplicates, keeping only the most recent record per (barrio_id, anio)
-- 
-- WITH ranked_duplicates AS (
--     SELECT 
--         id,
--         ROW_NUMBER() OVER (
--             PARTITION BY barrio_id, anio 
--             ORDER BY etl_loaded_at DESC, id DESC
--         ) as keep_rank
--     FROM fact_precios
--     WHERE EXISTS (
--         SELECT 1 
--         FROM fact_precios p2 
--         WHERE p2.barrio_id = fact_precios.barrio_id 
--           AND p2.anio = fact_precios.anio 
--           AND p2.id != fact_precios.id
--     )
-- )
-- DELETE FROM fact_precios
-- WHERE id IN (
--     SELECT id FROM ranked_duplicates WHERE keep_rank > 1
-- );

-- ============================================================================
-- STEP 4: VERIFICATION (Run after deletion)
-- ============================================================================
-- Verify no duplicates remain
-- SELECT 
--     barrio_id,
--     anio,
--     COUNT(*) as count
-- FROM fact_precios
-- GROUP BY barrio_id, anio
-- HAVING COUNT(*) > 1;
-- 
-- Should return 0 rows if cleanup was successful

-- ============================================================================
-- ALTERNATIVE: More Conservative Cleanup
-- Only delete if dataset_id and source are also identical
-- ============================================================================
-- WITH ranked_duplicates AS (
--     SELECT 
--         id,
--         ROW_NUMBER() OVER (
--             PARTITION BY barrio_id, anio, COALESCE(dataset_id, ''), COALESCE(source, '')
--             ORDER BY etl_loaded_at DESC, id DESC
--         ) as keep_rank
--     FROM fact_precios
--     WHERE EXISTS (
--         SELECT 1 
--         FROM fact_precios p2 
--         WHERE p2.barrio_id = fact_precios.barrio_id 
--           AND p2.anio = fact_precios.anio 
--           AND COALESCE(p2.dataset_id, '') = COALESCE(fact_precios.dataset_id, '')
--           AND COALESCE(p2.source, '') = COALESCE(fact_precios.source, '')
--           AND p2.id != fact_precios.id
--     )
-- )
-- DELETE FROM fact_precios
-- WHERE id IN (
--     SELECT id FROM ranked_duplicates WHERE keep_rank > 1
-- );
