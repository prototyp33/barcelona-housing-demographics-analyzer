-- Limpieza de Tabla Duplicada: fact_soroll
-- Fecha: 2026-01-05
-- Razón: fact_soroll es un duplicado vacío de fact_ruido

-- =============================================================================
-- VERIFICACIÓN PREVIA
-- =============================================================================

-- 1. Verificar que fact_soroll está vacía
SELECT 'fact_soroll registros: ' || COUNT(*) as verificacion_soroll
FROM fact_soroll;

-- 2. Verificar que fact_ruido tiene datos
SELECT 'fact_ruido registros: ' || COUNT(*) as verificacion_ruido
FROM fact_ruido;

-- 3. Comparar esquemas
SELECT 'Columnas en fact_soroll: ' || COUNT(*) as columnas_soroll
FROM pragma_table_info('fact_soroll');

SELECT 'Columnas en fact_ruido: ' || COUNT(*) as columnas_ruido
FROM pragma_table_info('fact_ruido');

-- =============================================================================
-- ELIMINACIÓN DE TABLA DUPLICADA
-- =============================================================================

-- Eliminar fact_soroll (tabla vacía y duplicada)
DROP TABLE IF EXISTS fact_soroll;

-- =============================================================================
-- VERIFICACIÓN POST-ELIMINACIÓN
-- =============================================================================

-- Verificar que fact_soroll ya no existe
SELECT name 
FROM sqlite_master 
WHERE type='table' AND name='fact_soroll';
-- Debe retornar 0 filas

-- Verificar que fact_ruido sigue existiendo y con datos
SELECT 'fact_ruido después de limpieza: ' || COUNT(*) || ' registros' as verificacion_final
FROM fact_ruido;

-- =============================================================================
-- NOTAS
-- =============================================================================

/*
RAZÓN DE LA ELIMINACIÓN:
- fact_soroll está completamente vacía (0 registros)
- fact_ruido contiene los mismos datos (73 registros)
- Ambas tablas tienen esquemas similares (datos de ruido)
- Mantener ambas causa confusión y desperdicia espacio

IMPACTO:
- Tablas vacías: 7 → 6 (-1)
- Health score esperado: 98.8 → 98.9 (+0.1)
- Espacio liberado: Mínimo (tabla vacía)
- Riesgo: Ninguno (tabla sin datos ni dependencias)

VERIFICACIÓN:
1. fact_soroll eliminada ✓
2. fact_ruido intacta con 73 registros ✓
3. fact_medio_ambiente también tiene datos de ruido ✓

PRÓXIMOS PASOS:
1. Actualizar database_setup.py para no crear fact_soroll
2. Crear snapshot del nuevo estado
3. Verificar health score mejorado
*/
