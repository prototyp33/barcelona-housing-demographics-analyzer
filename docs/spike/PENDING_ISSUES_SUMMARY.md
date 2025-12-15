# Issues Pendientes - Fase 1

**Fecha**: 2025-12-14  
**Estado**: Issues creadas

---

## 📋 Issues Creadas

### 1. [FEAT] Mapear códigos INE para los 73 barrios

**Archivo**: `issues/database-architecture/04-map-ine-codes.md`

**Objetivo**: Completar mapeo de códigos INE (actualmente 0/73)

**Prioridad**: 🟡 Media  
**Estimación**: 3-4 horas

**Tareas**:
- Investigar fuente de códigos INE
- Crear mapeo manual inicial
- Actualizar script de migración
- Validar y documentar

---

### 2. [FEAT] Integrar scripts de migración en pipeline ETL

**Archivo**: `issues/database-architecture/05-integrate-scripts-in-etl.md`

**Objetivo**: Automatizar creación de `dim_tiempo`, migración de `dim_barrios`, y vistas

**Prioridad**: 🔴 Alta  
**Estimación**: 4-6 horas

**Tareas**:
- Refactorizar scripts a funciones reutilizables
- Integrar en `src/etl/pipeline.py`
- Asegurar idempotencia
- Tests de integración

---

### 3. [TEST] Crear tests unitarios para mejoras de Fase 1

**Archivo**: `issues/database-architecture/06-create-unit-tests.md`

**Objetivo**: Tests para todas las funcionalidades de Fase 1

**Prioridad**: 🟡 Media  
**Estimación**: 6-8 horas

**Tareas**:
- Tests para cálculo de centroides y áreas
- Tests para `dim_tiempo`
- Tests para vistas analíticas
- Tests de integración

---

## 📊 Resumen

| Issue | Tipo | Prioridad | Estimación | Estado |
|-------|------|-----------|------------|--------|
| #04 | FEAT | 🟡 Media | 3-4h | 📝 Creada |
| #05 | FEAT | 🔴 Alta | 4-6h | 📝 Creada |
| #06 | TEST | 🟡 Media | 6-8h | 📝 Creada |

**Total estimado**: 13-18 horas

---

## 🎯 Orden Recomendado de Implementación

1. **Issue #05** (Integrar en ETL) - 🔴 Alta prioridad
   - Automatiza todo el proceso
   - Reduce pasos manuales a 0

2. **Issue #04** (Mapear INE) - 🟡 Media prioridad
   - Puede hacerse en paralelo
   - No bloquea otras funcionalidades

3. **Issue #06** (Tests) - 🟡 Media prioridad
   - Asegura calidad
   - Puede hacerse después de #05

---

## 🔗 Relaciones

- **#05** facilita #04 y #06 (automatización)
- **#06** valida #04 y #05 (calidad)
- Todas dependen de Fase 1 completada ✅

---

**Estado**: ✅ Issues creadas y listas para implementación

