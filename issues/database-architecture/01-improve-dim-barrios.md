---
title: "[FEAT] Mejorar dim_barrios con campos adicionales"
labels: feature, database, enhancement
assignees: ''
---

## 📌 Objetivo

Añadir campos adicionales a `dim_barrios` para mejorar matching con otras fuentes de datos y habilitar análisis geográficos más precisos. Los campos propuestos son: `codigo_ine`, `centroide_lat/lon`, y `area_km2`.

**Por qué es importante**: 
- Facilita matching con datos del INE
- Permite cálculos de proximidad más precisos
- Habilita normalizaciones por área

## 🔍 Descripción del Problema

**Estado actual:**
- `dim_barrios` tiene información básica (nombre, distrito, geometría JSON)
- No hay código INE para matching con datos del INE
- No hay centroides calculados para cálculos de distancia
- No hay área calculada para normalizaciones

**Estado deseado:**
- `dim_barrios` incluye `codigo_ine` para matching
- Centroides calculados automáticamente desde `geometry_json`
- Área en km² calculada desde geometrías
- Todos los campos poblados para los 73 barrios

**Archivos afectados:**
- `src/database_setup.py` - Esquema de tabla
- `src/etl/pipeline.py` - Lógica de población
- Scripts de migración (nuevo)

## 📝 Pasos para Implementar

1. **Crear migración SQL**
   - Añadir columnas: `codigo_ine TEXT`, `centroide_lat REAL`, `centroide_lon REAL`, `area_km2 REAL`
   - Actualizar `src/database_setup.py` con nuevos campos

2. **Crear script de cálculo de centroides**
   - Leer `geometry_json` de cada barrio
   - Calcular centroide usando GeoJSON
   - Actualizar `centroide_lat` y `centroide_lon`

3. **Crear script de cálculo de áreas**
   - Calcular área desde geometrías GeoJSON
   - Convertir a km²
   - Actualizar `area_km2`

4. **Crear script de matching INE**
   - Mapear nombres de barrios a códigos INE
   - Actualizar `codigo_ine` para cada barrio

5. **Integrar en pipeline ETL**
   - Añadir lógica para poblar nuevos campos
   - Validar que todos los barrios tienen valores

6. **Tests y validación**
   - Verificar que todos los barrios tienen centroides
   - Verificar que áreas son razonables (0.1 - 10 km²)
   - Verificar matching de códigos INE

## ✅ Definición de Hecho (Definition of Done)

- [ ] Columnas añadidas a `dim_barrios` en `src/database_setup.py`
- [ ] Script de migración creado y ejecutado
- [ ] Centroides calculados para 73/73 barrios
- [ ] Áreas calculadas para 73/73 barrios
- [ ] Códigos INE mapeados para 73/73 barrios
- [ ] Pipeline ETL actualizado para poblar nuevos campos
- [ ] Tests creados y pasando
- [ ] Documentación actualizada (`docs/spike/DATABASE_ARCHITECTURE_DESIGN.md`)
- [ ] Script de verificación confirma 100% de completitud

## 🎯 Impacto & KPI

- **KPI técnico**: Completitud de campos en `dim_barrios` (objetivo: 100%)
- **Objetivo**: 73/73 barrios con todos los campos poblados
- **Fuente de datos**: GeoJSON existente, mapeo manual INE

## 🔗 Issues Relacionadas

- Relacionada con: Arquitectura de Base de Datos (`docs/spike/DATABASE_ARCHITECTURE_DESIGN.md`)
- Bloquea: Creación de `fact_proximidad` (necesita centroides)

## 🚧 Riesgos / Bloqueos

- **Riesgo**: Códigos INE pueden no estar disponibles para todos los barrios
- **Mitigación**: Usar mapeo manual basado en nombres y códigos oficiales
- **Riesgo**: Cálculo de áreas puede variar según proyección
- **Mitigación**: Usar EPSG:4326 (WGS84) estándar

## 📚 Enlaces Relevantes

- [Arquitectura de BD](docs/spike/DATABASE_ARCHITECTURE_DESIGN.md)
- [Database Setup](src/database_setup.py)
- [ETL Pipeline](src/etl/pipeline.py)

## 💡 Notas de Implementación

- **Estimación**: 4-6 horas
- **Prioridad**: 🔴 Alta
- **Sprint recomendado**: Sprint actual
- **Dependencias**: Ninguna (mejora incremental)

