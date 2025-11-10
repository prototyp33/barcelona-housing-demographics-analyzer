# 1.1 Visión y Objetivos de Datos

## Objetivo Principal

Consolidar datos demográficos dispersos y precios de vivienda de múltiples fuentes públicas en una base única, limpia y normalizada que permita análisis integrado, correlaciones estadísticas y visualizaciones interactivas sin fricción.

## Objetivos Específicos

### 1. Integración de Fuentes de Datos

**Objetivo**: Integrar 3+ fuentes de datos públicas en un sistema unificado.

**Fuentes Identificadas**:
- **INE (Instituto Nacional de Estadística)**: Datos demográficos oficiales, censos, padrones municipales
- **Open Data BCN**: Datos abiertos del Ayuntamiento de Barcelona (demografía, vivienda, servicios)
- **Idealista**: Precios de vivienda y mercado inmobiliario (con prácticas éticas de scraping)

**Criterios de Éxito**:
- [ ] Extracción automatizada de datos de las 3 fuentes principales
- [ ] Normalización de esquemas de datos heterogéneos
- [ ] Mapeo de identificadores geográficos (barrios, distritos, códigos postales)
- [ ] Documentación de fuentes y metodología de extracción

### 2. Calidad de Datos

**Objetivo**: Asegurar calidad de datos mínima con métricas cuantificables.

**Métricas de Calidad**:
- **Completitud**: ≥ 95% de campos requeridos completos
- **Validez**: ≥ 98% de registros válidos según reglas de negocio
- **Consistencia**: Coherencia entre fuentes y períodos temporales
- **Precisión**: Validación de rangos, formatos y relaciones referenciales

**Criterios de Éxito**:
- [ ] Sistema de validación automática de datos
- [ ] Reportes de calidad de datos (data quality reports)
- [ ] Procesos de limpieza y normalización documentados
- [ ] Manejo de valores faltantes y outliers
- [ ] Logs de errores y advertencias de calidad

### 3. Cobertura Temporal

**Objetivo**: Mantener histórico completo desde 2015 hasta 2025 (10 años de datos).

**Requisitos Temporales**:
- **Período**: 2015-2025 (10 años)
- **Granularidad**: 
  - Datos demográficos: Anual y trimestral (cuando esté disponible)
  - Precios de vivienda: Trimestral y mensual (cuando esté disponible)
- **Histórico**: Preservación de todas las versiones de datos para análisis de tendencias

**Criterios de Éxito**:
- [ ] Base de datos con cobertura completa 2015-2025
- [ ] Sistema de versionado de datos históricos
- [ ] Capacidad de análisis de series temporales
- [ ] Documentación de disponibilidad de datos por fuente y período

### 4. Granularidad Geográfica y Temporal

**Objetivo**: Permitir análisis por barrio/distrito con granularidad temporal (trimestral/anual).

**Dimensiones de Análisis**:
- **Geográfica**:
  - Nivel 1: Distrito (10 distritos de Barcelona)
  - Nivel 2: Barrio (73 barrios de Barcelona)
  - Nivel 3: Código postal (cuando esté disponible)
- **Temporal**:
  - Anual: Para análisis de tendencias a largo plazo
  - Trimestral: Para análisis de estacionalidad y cambios más frecuentes
  - Mensual: Para precios de vivienda (cuando esté disponible)

**Criterios de Éxito**:
- [ ] Esquema de base de datos que soporte agregación por barrio/distrito
- [ ] Funciones de análisis que permitan filtrar por geografía y tiempo
- [ ] Visualizaciones interactivas con selección de granularidad
- [ ] Comparaciones entre barrios/distritos

### 5. Actualización Periódica

**Objetivo**: Establecer sistema de actualización periódica (trimestral) automatizable en el futuro.

**Requisitos de Actualización**:
- **Frecuencia**: Trimestral (cada 3 meses)
- **Automatización**: Pipeline automatizable para actualizaciones futuras
- **Procesamiento**: ETL (Extract, Transform, Load) automatizado
- **Notificaciones**: Alertas de actualizaciones exitosas/fallidas

**Criterios de Éxito**:
- [ ] Scripts de extracción reutilizables y parametrizables
- [ ] Pipeline ETL documentado y versionado
- [ ] Sistema de logging y monitoreo de actualizaciones
- [ ] Capacidad de ejecución manual y programada (cron/scheduler)
- [ ] Documentación para automatización futura (Airflow, Prefect, etc.)

## Arquitectura de Datos Propuesta

### Estructura de Base de Datos

```
barcelona_housing_demographics/
├── raw_data/              # Datos sin procesar de fuentes originales
├── processed_data/        # Datos limpios y normalizados
├── analytics/             # Datos agregados para análisis
└── metadata/              # Metadatos, esquemas, documentación
```

### Esquema de Datos Unificado

**Tablas Principales**:
- `demographics`: Datos demográficos por barrio/distrito/año/trimestre
- `housing_prices`: Precios de vivienda por barrio/distrito/año/trimestre
- `geographic_reference`: Mapeo de barrios, distritos, códigos postales
- `data_sources`: Metadatos de fuentes y versiones de datos
- `data_quality_metrics`: Métricas de calidad por fuente y período

## Métricas de Éxito del Proyecto

### KPIs Técnicos
- **Cobertura de datos**: ≥ 95% de barrios con datos completos
- **Tiempo de actualización**: < 2 horas para actualización trimestral completa
- **Disponibilidad**: 99% uptime de base de datos
- **Rendimiento**: Consultas de análisis < 5 segundos

### KPIs de Calidad
- **Completitud**: ≥ 95%
- **Validez**: ≥ 98%
- **Consistencia**: 0 inconsistencias críticas entre fuentes
- **Documentación**: 100% de funciones y procesos documentados

## Próximos Pasos

1. **Fase 1**: Diseño de esquema de base de datos y normalización
2. **Fase 2**: Implementación de extracción de datos de INE
3. **Fase 3**: Implementación de extracción de datos de Open Data BCN
4. **Fase 4**: Implementación de extracción de datos de Idealista
5. **Fase 5**: Pipeline de procesamiento y validación de calidad
6. **Fase 6**: Carga histórica de datos 2015-2025
7. **Fase 7**: Sistema de actualización periódica

## Referencias

- [INE - Instituto Nacional de Estadística](https://www.ine.es/)
- [Open Data BCN](https://opendata-ajuntament.barcelona.cat/)
- [Idealista](https://www.idealista.com/)
- [Barcelona - División Administrativa](https://www.barcelona.cat/bcnmes/)

