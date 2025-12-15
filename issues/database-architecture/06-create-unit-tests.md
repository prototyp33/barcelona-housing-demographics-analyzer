---
title: "[TEST] Crear tests unitarios para mejoras de Fase 1"
labels: test, database, quality-assurance
assignees: ''
---

## 📌 Objetivo

Crear tests unitarios e integración para las mejoras implementadas en Fase 1: `dim_barrios` mejorada, `dim_tiempo`, y vistas analíticas.

**Por qué es importante**: 
- Asegura que las funcionalidades funcionan correctamente
- Previene regresiones en futuras modificaciones
- Valida cálculos de centroides y áreas
- Verifica que vistas retornan datos correctos

## 🔍 Descripción del Problema

**Estado actual:**
- Funcionalidades implementadas pero sin tests
- Cálculos de centroides y áreas no tienen validación automatizada
- Vistas analíticas no tienen tests de validación
- Riesgo de regresiones en futuras modificaciones

**Estado deseado:**
- Tests unitarios para cálculo de centroides
- Tests unitarios para cálculo de áreas
- Tests de integración para `dim_tiempo`
- Tests de validación para vistas analíticas
- Cobertura de tests >80% para nuevos módulos

**Archivos afectados:**
- Nuevo: `tests/test_dim_barrios_migration.py`
- Nuevo: `tests/test_dim_tiempo.py`
- Nuevo: `tests/test_database_views.py`
- `tests/test_database_setup.py` - Actualizar tests existentes

## 📝 Pasos para Implementar

1. **Tests para cálculo de centroides**
   - Test con GeoJSON Polygon simple
   - Test con GeoJSON MultiPolygon
   - Test con geometría inválida
   - Test con geometría NULL
   - Validar precisión de cálculos

2. **Tests para cálculo de áreas**
   - Test con polígono conocido (área calculable manualmente)
   - Test con MultiPolygon
   - Test con geometría inválida
   - Validar conversión a km²

3. **Tests para `dim_tiempo`**
   - Test de creación de tabla
   - Test de población de registros
   - Test de períodos generados (2015-2024)
   - Test de atributos temporales (estación, es_verano)
   - Test de índices

4. **Tests para vistas analíticas**
   - Test que vistas se crean correctamente
   - Test que vistas retornan datos (no vacías)
   - Test de estructura de columnas
   - Test de joins correctos
   - Test de filtros aplicados

5. **Tests de integración**
   - Test de migración completa de `dim_barrios`
   - Test de creación completa de `dim_tiempo` y vistas
   - Test de idempotencia (ejecutar múltiples veces)
   - Test con base de datos real

6. **Tests de validación de datos**
   - Test que centroides están en rango válido (Barcelona)
   - Test que áreas son razonables (0.1 - 20 km²)
   - Test que períodos temporales son correctos
   - Test que vistas no tienen duplicados

## ✅ Definición de Hecho (Definition of Done)

- [ ] Tests para cálculo de centroides creados y pasando
- [ ] Tests para cálculo de áreas creados y pasando
- [ ] Tests para `dim_tiempo` creados y pasando
- [ ] Tests para vistas analíticas creados y pasando
- [ ] Tests de integración creados y pasando
- [ ] Tests de validación de datos creados y pasando
- [ ] Cobertura de tests >80% para nuevos módulos
- [ ] Todos los tests pasan en CI/CD
- [ ] Documentación de tests actualizada

## 🎯 Impacto & KPI

- **KPI técnico**: Cobertura de tests para módulos nuevos (objetivo: >80%)
- **Objetivo**: 100% de funcionalidades críticas con tests
- **Fuente de datos**: Funcionalidades implementadas en Fase 1

## 🔗 Issues Relacionadas

- Depende de: 
  - Issue #01 (Mejorar dim_barrios) - ✅ Completada
  - Issue #02 (Crear dim_tiempo) - ✅ Completada
  - Issue #03 (Crear vistas analíticas) - ✅ Completada
- Relacionada con: Quality Assurance, Fase 1 Summary

## 🚧 Riesgos / Bloqueos

- **Riesgo**: Tests pueden ser frágiles si dependen de datos específicos
- **Mitigación**: 
  - Usar fixtures y datos de prueba
  - Tests independientes de datos de producción
  - Mock de base de datos cuando sea posible

- **Riesgo**: Cálculos de área pueden variar según implementación
- **Mitigación**: 
  - Usar polígonos de prueba con área conocida
  - Validar con tolerancia razonable (±5%)

## 📚 Enlaces Relevantes

- [Fase 1 Summary](docs/spike/FASE1_IMPLEMENTATION_SUMMARY.md)
- [Scripts de Migración](scripts/migrate_dim_barrios_add_fields.py)
- [Database Views](src/database_views.py)
- [Test Structure](tests/)

## 💡 Notas de Implementación

- **Estimación**: 6-8 horas
- **Prioridad**: 🟡 Media
- **Sprint recomendado**: Sprint actual o siguiente
- **Dependencias**: Issues #01, #02, #03 completadas

### Estructura de Tests Sugerida

```python
tests/
├── test_dim_barrios_migration.py
│   ├── test_calculate_centroid()
│   ├── test_calculate_area()
│   ├── test_migrate_dim_barrios()
│   └── test_validation_centroids_areas()
│
├── test_dim_tiempo.py
│   ├── test_create_dim_tiempo()
│   ├── test_populate_periods()
│   ├── test_temporal_attributes()
│   └── test_indexes()
│
└── test_database_views.py
    ├── test_create_views()
    ├── test_v_affordability_quarterly()
    ├── test_v_precios_evolucion_anual()
    ├── test_v_demografia_resumen()
    └── test_v_gentrificacion_tendencias()
```

### Datos de Prueba

- GeoJSON de prueba para cálculos
- Polígonos con área conocida para validación
- Datos sintéticos para vistas

