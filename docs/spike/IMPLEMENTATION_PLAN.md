# Plan de Implementación - Arquitectura de Base de Datos

**Fecha**: 2025-12-14  
**Basado en**: `docs/spike/DATABASE_ARCHITECTURE_DESIGN.md`

---

## 📊 Resumen Ejecutivo

Este plan prioriza la implementación de mejoras a la arquitectura de base de datos en 3 fases:

- **Fase 1 (Corto Plazo)**: Mejoras incrementales a tablas existentes
- **Fase 2 (Medio Plazo)**: Nuevas dimensiones y tablas de hechos
- **Fase 3 (Largo Plazo)**: Integraciones avanzadas y optimizaciones

---

## 🎯 Fase 1: Mejoras Incrementales (Corto Plazo)

**Duración estimada**: 1-2 semanas  
**Prioridad**: 🔴 Alta  
**Impacto**: Mejora inmediata sin romper compatibilidad

### 1.1 Mejorar `dim_barrios` con campos adicionales

**Objetivo**: Añadir campos para matching y análisis geográfico.

**Campos a añadir**:
- `codigo_ine` TEXT - Código INE para matching
- `centroide_lat` REAL - Latitud del centroide
- `centroide_lon` REAL - Longitud del centroide
- `area_km2` REAL - Área en km²

**Implementación**:
1. Crear migración SQL para añadir columnas
2. Actualizar `src/database_setup.py` con nuevos campos
3. Script para calcular centroides desde `geometry_json`
4. Script para calcular áreas desde geometrías
5. Actualizar ETL para poblar nuevos campos

**Estimación**: 4-6 horas

---

### 1.2 Crear tabla `dim_tiempo`

**Objetivo**: Tabla de tiempo para análisis temporal y normalización.

**Implementación**:
1. Crear tabla `dim_tiempo` con períodos 2015-2024
2. Generar registros para todos los períodos (anual, quarterly, mensual)
3. Actualizar `src/database_setup.py`
4. Crear script de población inicial
5. Actualizar queries de ejemplo para usar `dim_tiempo`

**Estimación**: 3-4 horas

---

### 1.3 Crear vistas analíticas básicas

**Objetivo**: Vistas SQL para análisis comunes.

**Vistas a crear**:
1. `v_affordability_quarterly` - Affordability por trimestre
2. `v_precios_evolucion_anual` - Evolución anual de precios
3. `v_demografia_resumen` - Resumen demográfico

**Implementación**:
1. Crear archivo SQL con definiciones de vistas
2. Script para crear vistas en la BD
3. Documentar uso de cada vista
4. Tests para validar vistas

**Estimación**: 2-3 horas

---

## 🚀 Fase 2: Nuevas Dimensiones y Hechos (Medio Plazo)

**Duración estimada**: 3-4 semanas  
**Prioridad**: 🟡 Media  
**Impacto**: Nuevas capacidades analíticas

### 2.1 Crear `dim_servicios` y `fact_proximidad`

**Objetivo**: Análisis de proximidad a servicios y POIs.

**Implementación**:
1. Diseñar esquema de `dim_servicios`
2. Integrar con Google Maps API / Overpass OSM
3. Crear extractor de servicios
4. Calcular métricas de proximidad
5. Crear `fact_proximidad` con agregaciones
6. Crear vista `v_barrios_mejor_conectados`

**Estimación**: 8-12 horas

**Dependencias**:
- API keys de Google Maps (si se usa)
- Acceso a Overpass API (OSM)

---

### 2.2 Crear `dim_fuentes_datos`

**Objetivo**: Catálogo de fuentes para trazabilidad.

**Implementación**:
1. Crear tabla `dim_fuentes_datos`
2. Poblar con fuentes actuales
3. Actualizar ETL para registrar fuente en cada carga
4. Crear vista de calidad por fuente

**Estimación**: 2-3 horas

---

### 2.3 Implementar Framework de Data Quality

**Objetivo**: Sistema automatizado de validación de calidad.

**Implementación**:
1. Crear clase `DataQualityChecker` en `src/quality/`
2. Implementar checks: completitud, validez, unicidad
3. Integrar en pipeline ETL
4. Generar reportes de calidad
5. Crear dashboard de calidad (opcional)

**Estimación**: 6-8 horas

---

## 🔮 Fase 3: Integraciones Avanzadas (Largo Plazo)

**Duración estimada**: 2-3 meses  
**Prioridad**: 🟢 Baja  
**Impacto**: Capacidades avanzadas

### 3.1 Integración con Catastro API

**Objetivo**: Datos de edificios y uso del suelo.

**Implementación**:
1. Investigar API del Catastro
2. Crear extractor de Catastro
3. Crear tabla `fact_catastro`
4. Integrar en pipeline ETL

**Estimación**: 12-16 horas

**Dependencias**:
- Acceso a API del Catastro
- Documentación de la API

---

### 3.2 Sistema de Auditoría

**Objetivo**: Tracking de cambios en datos críticos.

**Implementación**:
1. Crear tabla `audit_housing_changes`
2. Crear triggers para capturar cambios
3. Sistema de versionado de datos
4. Dashboard de auditoría

**Estimación**: 6-8 horas

---

### 3.3 Migración a PostgreSQL + PostGIS (Opcional)

**Objetivo**: Mejor soporte geoespacial y escalabilidad.

**Implementación**:
1. Diseñar esquema PostgreSQL
2. Scripts de migración desde SQLite
3. Actualizar código para PostgreSQL
4. Tests de migración
5. Documentación de migración

**Estimación**: 20-30 horas

**Nota**: Solo si se requiere escalabilidad o funcionalidades PostGIS avanzadas.

---

## 📋 Issues a Crear

### Fase 1 (Corto Plazo)

1. **[FEAT] Mejorar dim_barrios con campos adicionales**
   - Añadir codigo_ine, centroide, area_km2
   - Prioridad: 🔴 Alta
   - Estimación: 4-6 horas

2. **[FEAT] Crear tabla dim_tiempo**
   - Tabla de tiempo para análisis temporal
   - Prioridad: 🔴 Alta
   - Estimación: 3-4 horas

3. **[FEAT] Crear vistas analíticas básicas**
   - 3 vistas SQL para análisis comunes
   - Prioridad: 🟡 Media
   - Estimación: 2-3 horas

### Fase 2 (Medio Plazo)

4. **[FEAT] Integrar dim_servicios y fact_proximidad**
   - Análisis de proximidad a servicios
   - Prioridad: 🟡 Media
   - Estimación: 8-12 horas

5. **[FEAT] Crear dim_fuentes_datos**
   - Catálogo de fuentes para trazabilidad
   - Prioridad: 🟢 Baja
   - Estimación: 2-3 horas

6. **[FEAT] Implementar Framework de Data Quality**
   - Sistema automatizado de validación
   - Prioridad: 🟡 Media
   - Estimación: 6-8 horas

### Fase 3 (Largo Plazo)

7. **[FEAT] Integración con Catastro API**
   - Datos de edificios y uso del suelo
   - Prioridad: 🟢 Baja
   - Estimación: 12-16 horas

8. **[FEAT] Sistema de Auditoría de Datos**
   - Tracking de cambios en datos críticos
   - Prioridad: 🟢 Baja
   - Estimación: 6-8 horas

---

## 🎯 Métricas de Éxito

### Fase 1
- ✅ `dim_barrios` con 4 campos adicionales poblados
- ✅ `dim_tiempo` con períodos 2015-2024
- ✅ 3 vistas analíticas funcionando

### Fase 2
- ✅ `dim_servicios` con >100 servicios catalogados
- ✅ `fact_proximidad` con métricas para 73 barrios
- ✅ Framework DQ generando reportes automáticos

### Fase 3
- ✅ `fact_catastro` con datos de edificios
- ✅ Sistema de auditoría capturando cambios
- ✅ (Opcional) Migración a PostgreSQL completada

---

## 📅 Timeline Sugerido

### Semana 1-2: Fase 1
- Día 1-2: Mejorar `dim_barrios`
- Día 3-4: Crear `dim_tiempo`
- Día 5: Crear vistas analíticas

### Semana 3-6: Fase 2
- Semana 3-4: `dim_servicios` y `fact_proximidad`
- Semana 5: `dim_fuentes_datos`
- Semana 6: Framework DQ

### Mes 2-3: Fase 3
- Mes 2: Integración Catastro
- Mes 3: Sistema de auditoría (y migración PostgreSQL si aplica)

---

## 🔗 Dependencias

### Fase 1
- ✅ Ninguna (mejoras incrementales)

### Fase 2
- ⚠️ API keys de Google Maps (opcional)
- ⚠️ Acceso a Overpass API (OSM)

### Fase 3
- ⚠️ Acceso a API del Catastro
- ⚠️ Decisión sobre migración PostgreSQL

---

## 📚 Referencias

- **Arquitectura**: `docs/spike/DATABASE_ARCHITECTURE_DESIGN.md`
- **Estado Actual**: `src/database_setup.py`
- **ETL Pipeline**: `src/etl/pipeline.py`
- **Master Table**: `docs/spike/IMPLEMENTATION_SUMMARY.md`

---

**Estado**: ✅ Plan creado  
**Siguiente**: Crear issues en GitHub y comenzar Fase 1

