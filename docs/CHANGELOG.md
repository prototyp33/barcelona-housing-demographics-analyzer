# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

## [2025-12-05] - Mejoras de Testing y Cierre de Issues

### ✅ Testing
- **PR #110**: Añadidos 43 tests para `demographics.py` (cobertura: 3% → 58%)
  - Tests para `prepare_fact_demografia()`, `enrich_fact_demografia()`, `prepare_demografia_ampliada()`
  - Tests para funciones auxiliares privadas
- **PR #111**: Añadidos 23 tests para `pipeline.py` (cobertura: 34% → 78%)
  - Tests para funciones auxiliares (100% cobertura)
  - Tests para `run_etl()` con diferentes escenarios
- **Cobertura total**: Mejorada de 24.88% a 37%

### 🐛 Issues Cerradas
- **#67**: Validación de integridad referencial implementada
- **#81**: Validación para `fact_precios` implementada
- **#82**: Validación para `fact_demografia` implementada
- **#75**: Cerrada como duplicada de #53

### 📝 Issues Actualizadas
- **#53**: Actualizada con progreso de PR #111

### 📊 Métricas Actualizadas
- Cobertura total: 37% (objetivo: ≥80%)
- Módulos con ≥60% cobertura: 6 módulos
- Tests totales: 73 tests nuevos añadidos en últimos commits

