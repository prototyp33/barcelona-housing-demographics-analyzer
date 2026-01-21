# Sugerencias de Mejora para la Base de Datos
## Análisis Completo del Esquema y Estructura

**Fecha:** 2026-01-06  
**Base de Datos:** `data/processed/database.db`  
**Tipo:** SQLite (Star Schema / Data Warehouse)

---

## 📊 Resumen Ejecutivo

### Estado Actual
- **31 tablas** de hechos y dimensiones
- **15 vistas** materializadas
- **73 barrios** con cobertura completa
- **Rango temporal:** 2012-2025 (dependiendo de la tabla)
- **Arquitectura:** Star Schema bien estructurado

### Puntuación General: 7.5/10
- ✅ **Fortalezas:** Buen diseño dimensional, foreign keys, índices básicos
- ⚠️ **Áreas de mejora:** Índices faltantes, calidad de datos, optimizaciones

---

## 🔴 CRÍTICAS (Alta Prioridad)

### 1. Índices Faltantes en Consultas Frecuentes

**Problema:** Muchas tablas `fact_*` no tienen índices en columnas usadas frecuentemente en JOINs y filtros.

**Impacto:** Consultas lentas cuando se filtran por año o se hacen JOINs con múltiples tablas.

**Solución:**

```sql
-- Índices compuestos para consultas comunes
CREATE INDEX IF NOT EXISTS idx_fact_precios_anio_barrio 
ON fact_precios(anio, barrio_id);

CREATE INDEX IF NOT EXISTS idx_fact_demografia_anio_barrio 
ON fact_demografia(anio, barrio_id);

CREATE INDEX IF NOT EXISTS idx_fact_renta_anio_barrio 
ON fact_renta(anio, barrio_id);

-- Índice para búsquedas por distrito (usado en filtros del dashboard)
CREATE INDEX IF NOT EXISTS idx_dim_barrios_distrito 
ON dim_barrios(distrito_id, distrito_nombre);

-- Índice para búsquedas por código oficial
CREATE INDEX IF NOT EXISTS idx_dim_barrios_codi_barri 
ON dim_barrios(codi_barri);
```

**Prioridad:** 🔴 **ALTA** - Mejora inmediata del rendimiento

---

### 2. Tablas Vacías o con Datos Incompletos

**Problema Identificado:**

| Tabla | Registros | Cobertura | Estado |
|-------|-----------|-----------|--------|
| `fact_calidad_aire` | 0 | 0/73 (0%) | 🔴 Vacía |
| `fact_ruido` | Variable | Parcial | 🟡 Incompleta |
| `fact_soroll` | Variable | Parcial | 🟡 Incompleta |
| `fact_demografia` | Baja | Parcial | 🟡 Usar `fact_demografia_ampliada` |

**Solución:**

1. **Eliminar o poblar `fact_calidad_aire`:**
   ```sql
   -- Si no hay datos, considerar eliminar o crear vista que apunte a fact_medio_ambiente
   CREATE VIEW IF NOT EXISTS fact_calidad_aire AS
   SELECT 
       barrio_id, anio,
       no2_mean, pm25_mean, pm10_mean, o3_mean,
       stations_nearby, max_distance_m
   FROM fact_medio_ambiente
   WHERE no2_mean IS NOT NULL OR pm25_mean IS NOT NULL;
   ```

2. **Consolidar tablas de ruido:**
   - `fact_ruido` y `fact_soroll` parecen duplicadas
   - Considerar unificar en `fact_medio_ambiente` (ya tiene campos de ruido)

3. **Documentar tablas legacy:**
   - Marcar `fact_demografia` como deprecated si se usa `fact_demografia_ampliada`

**Prioridad:** 🔴 **ALTA** - Confusión en el código y consultas fallidas

---

### 3. Falta de Índices en Vistas Materializadas

**Problema:** Las vistas no pueden tener índices directamente, pero las tablas base deberían tenerlos.

**Solución:** Asegurar que todas las tablas base usadas en vistas tengan índices apropiados:

```sql
-- Para vw_gentrification_risk (usa fact_educacion, fact_precios, fact_calidad_aire, fact_ruido)
-- Ya existen índices únicos, pero agregar índices compuestos para JOINs:

CREATE INDEX IF NOT EXISTS idx_fact_educacion_barrio_anio 
ON fact_educacion(barrio_id, anio);

CREATE INDEX IF NOT EXISTS idx_fact_precios_barrio_anio 
ON fact_precios(barrio_id, anio);
```

**Prioridad:** 🔴 **ALTA** - Las vistas son consultadas frecuentemente

---

### 4. Validación de Foreign Keys Inconsistente

**Problema:** Aunque se habilitan foreign keys (`PRAGMA foreign_keys = ON`), no hay validación automática de integridad.

**Solución:**

```sql
-- Script de validación periódica
CREATE TABLE IF NOT EXISTS integrity_checks (
    check_id INTEGER PRIMARY KEY AUTOINCREMENT,
    check_date TEXT NOT NULL,
    table_name TEXT NOT NULL,
    issue_type TEXT NOT NULL,
    issue_description TEXT,
    affected_rows INTEGER
);

-- Función para validar foreign keys (ejecutar periódicamente)
-- Verificar barrio_id huérfanos
INSERT INTO integrity_checks (check_date, table_name, issue_type, issue_description, affected_rows)
SELECT 
    datetime('now'),
    'fact_precios',
    'orphaned_fk',
    'Registros con barrio_id inexistente',
    COUNT(*)
FROM fact_precios p
LEFT JOIN dim_barrios b ON p.barrio_id = b.barrio_id
WHERE b.barrio_id IS NULL;
```

**Prioridad:** 🔴 **ALTA** - Integridad referencial es crítica

---

## 🟡 IMPORTANTES (Prioridad Media)

### 5. Optimización de Consultas con COALESCE en Índices Únicos

**Problema:** Los índices únicos usan `COALESCE(trimestre, -1)` que puede ser ineficiente.

**Ejemplo actual:**
```sql
CREATE UNIQUE INDEX idx_fact_precios_unique
ON fact_precios (
    barrio_id,
    anio,
    COALESCE(trimestre, -1),
    COALESCE(dataset_id, ''),
    COALESCE(source, '')
);
```

**Solución:** Considerar normalizar valores NULL antes de insertar:

```python
# En el código ETL, normalizar antes de insertar
df['trimestre'] = df['trimestre'].fillna(-1)
df['dataset_id'] = df['dataset_id'].fillna('')
df['source'] = df['source'].fillna('')
```

Luego simplificar el índice:
```sql
CREATE UNIQUE INDEX idx_fact_precios_unique
ON fact_precios (barrio_id, anio, trimestre, dataset_id, source);
```

**Prioridad:** 🟡 **MEDIA** - Mejora de rendimiento moderada

---

### 6. Particionamiento Temporal (Consideración Futura)

**Problema:** Con datos desde 2012-2025, las tablas crecen y las consultas pueden ser lentas.

**Solución:** Para SQLite, considerar tablas separadas por rango de años o usar vistas:

```sql
-- Vista para datos recientes (últimos 3 años)
CREATE VIEW IF NOT EXISTS fact_precios_recent AS
SELECT * FROM fact_precios
WHERE anio >= (SELECT MAX(anio) - 2 FROM fact_precios);

-- Vista para datos históricos
CREATE VIEW IF NOT EXISTS fact_precios_historical AS
SELECT * FROM fact_precios
WHERE anio < (SELECT MAX(anio) - 2 FROM fact_precios);
```

**Prioridad:** 🟡 **MEDIA** - Solo necesario si el rendimiento se degrada

---

### 7. Normalización de Metadatos ETL

**Problema:** Columnas `source`, `dataset_id`, `etl_loaded_at` se repiten en todas las tablas `fact_*`.

**Solución:** Considerar tabla de metadatos separada (aunque esto rompería el star schema):

```sql
-- Alternativa: Tabla de metadatos por registro
CREATE TABLE IF NOT EXISTS fact_metadata (
    fact_table TEXT NOT NULL,
    fact_id INTEGER NOT NULL,
    dataset_id TEXT,
    source TEXT,
    etl_loaded_at TEXT,
    PRIMARY KEY (fact_table, fact_id)
);
```

**Nota:** Esto es una decisión de diseño. El enfoque actual (columnas en cada tabla) es más simple y eficiente para consultas.

**Prioridad:** 🟡 **BAJA** - Solo si se necesita auditoría detallada

---

### 8. Índices para Búsquedas de Texto

**Problema:** Búsquedas por `barrio_nombre` o `barrio_nombre_normalizado` pueden ser lentas.

**Solución:**

```sql
-- Índice para búsquedas por nombre (ya existe UNIQUE, pero agregar para búsquedas LIKE)
-- SQLite no soporta índices FULLTEXT directamente, pero podemos optimizar:

-- Para búsquedas exactas (ya existe)
-- idx_dim_barrios_nombre (UNIQUE)

-- Para búsquedas por distrito + nombre
CREATE INDEX IF NOT EXISTS idx_dim_barrios_distrito_nombre 
ON dim_barrios(distrito_nombre, barrio_nombre);
```

**Prioridad:** 🟡 **MEDIA** - Mejora UX del dashboard

---

## 🟢 MEJORAS ADICIONALES (Prioridad Baja)

### 9. Estadísticas de Tablas (ANALYZE)

**Problema:** SQLite no actualiza estadísticas automáticamente, lo que puede afectar el plan de ejecución.

**Solución:** Ejecutar periódicamente:

```sql
-- Actualizar estadísticas para optimizador de consultas
ANALYZE dim_barrios;
ANALYZE fact_precios;
ANALYZE fact_demografia;
ANALYZE fact_renta;
-- ... para todas las tablas principales

-- O analizar toda la base de datos
ANALYZE;
```

**Script recomendado:** Ejecutar después de cada carga ETL importante.

**Prioridad:** 🟢 **BAJA** - Mejora marginal

---

### 10. Compresión de geometry_json

**Problema:** `geometry_json` almacena GeoJSON completo como TEXT, puede ser grande.

**Solución:** Considerar compresión o almacenamiento externo:

```python
# En el código ETL, comprimir antes de almacenar
import gzip
import json

geometry_compressed = gzip.compress(
    json.dumps(geojson_data).encode('utf-8')
).hex()

# Al leer, descomprimir
geometry_json = json.loads(
    gzip.decompress(bytes.fromhex(geometry_compressed))
)
```

**Nota:** Esto añade complejidad. Solo necesario si el tamaño de la BD es un problema.

**Prioridad:** 🟢 **BAJA** - Solo si hay problemas de tamaño

---

### 11. Tabla de Agregaciones Pre-calculadas

**Problema:** Consultas agregadas complejas se ejecutan en tiempo real.

**Solución:** Crear tabla de agregaciones para KPIs comunes:

```sql
CREATE TABLE IF NOT EXISTS fact_kpis_aggregated (
    barrio_id INTEGER NOT NULL,
    anio INTEGER NOT NULL,
    precio_m2_promedio REAL,
    precio_m2_mediano REAL,
    variacion_precio_anual REAL,
    poblacion_total INTEGER,
    renta_promedio REAL,
    indice_gentrificacion REAL,
    updated_at TEXT,
    PRIMARY KEY (barrio_id, anio),
    FOREIGN KEY (barrio_id) REFERENCES dim_barrios(barrio_id)
);

-- Poblar con trigger o proceso ETL separado
```

**Prioridad:** 🟢 **BAJA** - Solo si las consultas son muy lentas

---

### 12. Documentación de Esquema en la BD

**Problema:** No hay documentación del esquema almacenada en la base de datos.

**Solución:**

```sql
-- Tabla de documentación
CREATE TABLE IF NOT EXISTS schema_documentation (
    table_name TEXT NOT NULL,
    column_name TEXT NOT NULL,
    description TEXT,
    data_type TEXT,
    constraints TEXT,
    examples TEXT,
    last_updated TEXT,
    PRIMARY KEY (table_name, column_name)
);

-- Poblar con información del esquema
INSERT INTO schema_documentation VALUES
('dim_barrios', 'barrio_id', 'Identificador único del barrio (1-73)', 'INTEGER', 'PRIMARY KEY', '1, 2, 3...', datetime('now')),
('dim_barrios', 'codi_barri', 'Código oficial del barrio según Ayuntamiento de Barcelona', 'TEXT', 'UNIQUE', '01.001, 01.002', datetime('now'));
-- ... etc
```

**Prioridad:** 🟢 **BAJA** - Mejora mantenibilidad

---

## 📋 Plan de Implementación Recomendado

### Fase 1: Críticas (Semana 1)
1. ✅ Crear índices faltantes (Item 1)
2. ✅ Resolver tablas vacías (Item 2)
3. ✅ Validar foreign keys (Item 4)

### Fase 2: Importantes (Semana 2-3)
4. ✅ Optimizar índices con COALESCE (Item 5)
5. ✅ Índices para búsquedas de texto (Item 8)
6. ✅ Índices para vistas (Item 3)

### Fase 3: Mejoras (Oportunista)
7. ⏳ Particionamiento temporal si es necesario (Item 6)
8. ⏳ Estadísticas ANALYZE (Item 9)
9. ⏳ Documentación en BD (Item 12)

---

## 🔧 Scripts de Implementación

### Script 1: Crear Índices Faltantes

```sql
-- scripts/add_missing_indexes.sql

-- Índices para consultas por año + barrio
CREATE INDEX IF NOT EXISTS idx_fact_precios_anio_barrio 
ON fact_precios(anio, barrio_id);

CREATE INDEX IF NOT EXISTS idx_fact_demografia_anio_barrio 
ON fact_demografia(anio, barrio_id);

CREATE INDEX IF NOT EXISTS idx_fact_renta_anio_barrio 
ON fact_renta(anio, barrio_id);

CREATE INDEX IF NOT EXISTS idx_fact_educacion_barrio_anio 
ON fact_educacion(barrio_id, anio);

CREATE INDEX IF NOT EXISTS idx_fact_comercio_barrio_anio 
ON fact_comercio(barrio_id, anio);

-- Índices para búsquedas por distrito
CREATE INDEX IF NOT EXISTS idx_dim_barrios_distrito 
ON dim_barrios(distrito_id, distrito_nombre);

CREATE INDEX IF NOT EXISTS idx_dim_barrios_codi_barri 
ON dim_barrios(codi_barri);

CREATE INDEX IF NOT EXISTS idx_dim_barrios_distrito_nombre 
ON dim_barrios(distrito_nombre, barrio_nombre);

-- Verificar índices creados
SELECT name, tbl_name, sql 
FROM sqlite_master 
WHERE type = 'index' 
AND name LIKE 'idx_%'
ORDER BY name;
```

### Script 2: Validación de Integridad

```sql
-- scripts/validate_integrity.sql

-- Crear tabla de checks si no existe
CREATE TABLE IF NOT EXISTS integrity_checks (
    check_id INTEGER PRIMARY KEY AUTOINCREMENT,
    check_date TEXT NOT NULL,
    table_name TEXT NOT NULL,
    issue_type TEXT NOT NULL,
    issue_description TEXT,
    affected_rows INTEGER
);

-- Verificar foreign keys huérfanos
INSERT INTO integrity_checks (check_date, table_name, issue_type, issue_description, affected_rows)
SELECT 
    datetime('now'),
    'fact_precios',
    'orphaned_fk',
    'Registros con barrio_id inexistente',
    COUNT(*)
FROM fact_precios p
LEFT JOIN dim_barrios b ON p.barrio_id = b.barrio_id
WHERE b.barrio_id IS NULL;

-- Repetir para otras tablas fact_*
-- fact_demografia, fact_renta, fact_educacion, etc.

-- Ver resultados
SELECT * FROM integrity_checks 
ORDER BY check_date DESC 
LIMIT 20;
```

### Script 3: Actualizar Estadísticas

```sql
-- scripts/update_statistics.sql

ANALYZE dim_barrios;
ANALYZE fact_precios;
ANALYZE fact_demografia;
ANALYZE fact_renta;
ANALYZE fact_educacion;
ANALYZE fact_comercio;
ANALYZE fact_servicios_salud;
ANALYZE fact_presion_turistica;

-- Verificar tamaño de tablas
SELECT 
    name as table_name,
    (SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=m.name) as exists,
    (SELECT COUNT(*) FROM pragma_table_info(m.name)) as column_count
FROM sqlite_master m
WHERE type = 'table'
AND name LIKE 'fact_%' OR name LIKE 'dim_%'
ORDER BY name;
```

---

## 📊 Métricas de Éxito

### Antes de las Mejoras
- Tiempo promedio de consulta: [Medir]
- Tamaño de la base de datos: [Medir]
- Consultas con tiempo > 1s: [Contar]

### Después de las Mejoras (Objetivos)
- ⬇️ Reducción del 50% en tiempo de consulta promedio
- ⬇️ Reducción del 30% en consultas lentas (>1s)
- ✅ 100% de foreign keys válidos
- ✅ Todas las tablas con índices apropiados

---

## 🎯 Conclusión

La base de datos tiene una **arquitectura sólida** (star schema bien diseñado), pero necesita:

1. **Índices adicionales** para optimizar consultas frecuentes
2. **Resolución de tablas vacías** para evitar confusión
3. **Validación de integridad** para asegurar calidad de datos
4. **Optimizaciones menores** para mejorar rendimiento

**Priorizar las mejoras críticas** (Fase 1) dará el mayor impacto con el menor esfuerzo.

---

## 📚 Referencias

- [SQLite Indexing Best Practices](https://www.sqlite.org/queryplanner.html)
- [Star Schema Design Patterns](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/)
- Documentación del proyecto: `docs/DATABASE_SCHEMA.md`
- Reporte de esquema: `docs/DATABASE_SCHEMA_REPORT.md`
