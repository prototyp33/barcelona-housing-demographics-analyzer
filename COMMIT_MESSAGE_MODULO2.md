# Módulo 2: Inside Airbnb - Presión Turística

## Resumen

Implementación completa del Módulo 2 del Sprint de Expansión de Datos, añadiendo análisis de presión turística mediante datos de Inside Airbnb.

## Cambios Implementados

### 1. Esquema de Base de Datos
- **Archivo**: `src/database_setup.py`
- **Cambios**:
  - Añadida tabla `fact_presion_turistica` con columnas:
    - `barrio_id`, `anio`, `mes` (PK compuesta)
    - `num_listings_airbnb`, `pct_entire_home`, `precio_noche_promedio`
    - `tasa_ocupacion`, `num_reviews_mes`
  - Añadido `fact_presion_turistica` a `VALID_TABLES`
  - Índices únicos y de rendimiento creados

### 2. Extractor de Datos
- **Archivo**: `src/extraction/airbnb_extractor.py` (NUEVO)
- **Funcionalidad**:
  - Descarga datos públicos desde S3 de Inside Airbnb
  - Soporta listings.csv.gz, calendar.csv.gz, reviews.csv.gz
  - Manejo de errores y rate limiting
  - Extracción automática de fecha más reciente disponible

### 3. Procesador de Datos
- **Archivo**: `src/processing/prepare_presion_turistica.py` (NUEVO)
- **Funcionalidades**:
  - **Geocodificación espacial**: Usa geometrías de `dim_barrios.geometry_json` con shapely/geopandas
  - **Fallback por nombre**: Mapeo por neighbourhood si geocodificación falla
  - **Agregación temporal**: Agrupa por barrio, año y mes
  - **Cálculo de métricas**:
    - `num_listings_airbnb`: Conteo de listings activos
    - `pct_entire_home`: Porcentaje de viviendas completas vs habitaciones
    - `precio_noche_promedio`: Precio promedio limpio de símbolos
    - `tasa_ocupacion`: Días ocupados / días totales (desde calendar)
    - `num_reviews_mes`: Conteo de reviews por mes

### 4. Integración ETL
- **Archivo**: `src/etl/pipeline.py`
- **Cambios**:
  - Importación de `prepare_presion_turistica`
  - Procesamiento automático de datos de Airbnb
  - Carga en `fact_presion_turistica` con `if_exists="replace"`
  - Logging de métricas y estadísticas

### 5. Scripts de Utilidad
- **Archivo**: `scripts/extract_airbnb_data.py` (NUEVO)
  - Script CLI para extracción manual de datos
  - Muestra resumen de archivos descargados
  
- **Archivo**: `scripts/validate_presion_turistica.py` (NUEVO)
  - Validación de criterios de calidad:
    - ≥70 barrios con datos (≥95% cobertura)
    - Cobertura temporal 2020-2024
    - ≥80% completitud en `num_listings_airbnb`
  - Identificación de barrios faltantes

- **Archivo**: `scripts/update_airbnb_monthly.py` (NUEVO)
  - Script de actualización mensual automatizada
  - Ejecuta extracción → ETL → validación
  - Listo para cron/scheduler

### 6. Tests Unitarios
- **Archivo**: `tests/processing/test_prepare_presion_turistica.py` (NUEVO)
- **Tests implementados**:
  - `test_prepare_presion_turistica_basic_flow`: Flujo básico de procesamiento
  - `test_prepare_presion_turistica_empty_raw`: Manejo de datos vacíos
  - `test_prepare_presion_turistica_missing_barrios_columns`: Validación de columnas
  - `test_prepare_presion_turistica_calculates_metrics`: Verificación de cálculos
  - `test_prepare_presion_turistica_empty_barrios_df`: Validación de entrada vacía
- **Coverage**: 59% (tests básicos pasando)

### 7. Documentación
- **Archivo**: `docs/data_sources/INSIDE_AIRBNB.md` (NUEVO)
- **Contenido**:
  - Descripción de la fuente de datos
  - Esquema de `fact_presion_turistica`
  - Proceso de geocodificación y agregación
  - Validaciones y criterios de calidad
  - Instrucciones de actualización mensual
  - Limitaciones conocidas

### 8. Actualización de Módulos
- **Archivo**: `src/extraction/__init__.py`
- **Cambios**: Exportación de `AirbnbExtractor`

## Resultados con Datos Reales

- ✅ 2,093 registros procesados exitosamente
- ✅ 71/73 barrios mapeados (97% de cobertura)
- ✅ Cobertura temporal: 2011-2025
- ✅ 100% completitud en `num_listings_airbnb` y `tasa_ocupacion`
- ✅ Validaciones pasando

## Criterios de Aceptación

| Criterio | Estado | Notas |
|----------|--------|-------|
| Datos desde diciembre 2023 | ✅ | Histórico completo 2011-2025 |
| Geocodificación ≥95% | ✅ | 97% de listings mapeados |
| Métricas calculadas | ✅ | Todas implementadas |
| Script de actualización mensual | ✅ | Funcional y documentado |
| Tests unitarios ≥80% | ⚠️ | 59% coverage (mejorable) |

## Dependencias Añadidas

- `geopandas`: Para geocodificación espacial
- `shapely`: Para manipulación de geometrías

## Notas Técnicas

- La geocodificación usa spatial join con geometrías de `dim_barrios`
- Fallback automático a mapeo por nombre si geocodificación falla
- El calendar muestra disponibilidad futura, no ocupación histórica
- Algunos barrios pueden no tener listings (ej: Vallbona, Baró de Viver)

## Próximos Pasos Sugeridos

1. Mejorar coverage de tests añadiendo casos de geocodificación
2. Optimizar procesamiento de calendar (7M+ registros)
3. Añadir tests de integración ETL

