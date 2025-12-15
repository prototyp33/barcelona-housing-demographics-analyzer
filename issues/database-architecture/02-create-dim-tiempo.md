---
title: "[FEAT] Crear tabla dim_tiempo para análisis temporal"
labels: feature, database, enhancement
assignees: ''
---

## 📌 Objetivo

Crear tabla de dimensión `dim_tiempo` para normalizar y facilitar análisis temporales. Esta tabla contendrá períodos desde 2015 hasta 2024 con granularidades anual, quarterly y mensual.

**Por qué es importante**: 
- Normaliza información temporal en un solo lugar
- Facilita agregaciones temporales
- Permite análisis de estacionalidad y tendencias
- Reduce duplicación de datos temporales en fact tables

## 🔍 Descripción del Problema

**Estado actual:**
- Cada fact table tiene su propia columna `anio` (y opcionalmente `trimestre`, `mes`)
- No hay normalización de períodos temporales
- Difícil hacer análisis comparativos entre diferentes granularidades

**Estado deseado:**
- Tabla `dim_tiempo` con todos los períodos 2015-2024
- Soporte para granularidades: anual, quarterly, mensual
- Atributos temporales: estación, día de semana, etc.
- Fact tables referencian `time_id` en lugar de duplicar datos

**Archivos afectados:**
- `src/database_setup.py` - Esquema de tabla
- Script de población inicial (nuevo)
- `src/etl/pipeline.py` - Actualizar para usar `dim_tiempo`

## 📝 Pasos para Implementar

1. **Crear esquema de `dim_tiempo`**
   - Definir columnas: `time_id`, `anio`, `trimestre`, `mes`, `periodo`, etc.
   - Añadir atributos temporales: `estacion`, `es_verano`, etc.
   - Actualizar `src/database_setup.py`

2. **Crear script de población inicial**
   - Generar registros para 2015-2024
   - Crear registros anuales, quarterly (Q1-Q4), y mensuales
   - Calcular atributos temporales (estación, etc.)

3. **Crear índices**
   - Índice único en `periodo`
   - Índice en `(anio, trimestre)`
   - Índice en `anio`

4. **Actualizar queries de ejemplo**
   - Documentar uso de `dim_tiempo` en joins
   - Crear ejemplos de agregaciones temporales

5. **Tests y validación**
   - Verificar que todos los períodos están presentes
   - Validar atributos temporales
   - Tests de joins con fact tables

## ✅ Definición de Hecho (Definition of Done)

- [ ] Tabla `dim_tiempo` creada en `src/database_setup.py`
- [ ] Script de población inicial creado y ejecutado
- [ ] Registros generados para 2015-2024 (anual, quarterly, mensual)
- [ ] Atributos temporales calculados correctamente
- [ ] Índices creados y validados
- [ ] Queries de ejemplo documentadas
- [ ] Tests creados y pasando
- [ ] Documentación actualizada

## 🎯 Impacto & KPI

- **KPI técnico**: Número de períodos en `dim_tiempo` (objetivo: ~120 períodos)
- **Objetivo**: Cobertura completa 2015-2024 con múltiples granularidades
- **Fuente de datos**: Generación sintética basada en fechas

## 🔗 Issues Relacionadas

- Relacionada con: Arquitectura de Base de Datos (`docs/spike/DATABASE_ARCHITECTURE_DESIGN.md`)
- Facilita: Análisis temporales y agregaciones

## 🚧 Riesgos / Bloqueos

- **Riesgo**: Ninguno (tabla independiente)
- **Nota**: No requiere cambios inmediatos en fact tables (puede usarse gradualmente)

## 📚 Enlaces Relevantes

- [Arquitectura de BD](docs/spike/DATABASE_ARCHITECTURE_DESIGN.md)
- [Database Setup](src/database_setup.py)

## 💡 Notas de Implementación

- **Estimación**: 3-4 horas
- **Prioridad**: 🔴 Alta
- **Sprint recomendado**: Sprint actual
- **Dependencias**: Ninguna (tabla independiente)

