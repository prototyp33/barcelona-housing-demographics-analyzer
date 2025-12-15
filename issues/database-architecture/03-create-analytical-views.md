---
title: "[FEAT] Crear vistas analíticas básicas para análisis comunes"
labels: feature, database, enhancement, analytics
assignees: ''
---

## 📌 Objetivo

Crear vistas SQL reutilizables para análisis comunes, facilitando queries complejas y mejorando la experiencia de análisis.

**Por qué es importante**: 
- Reduce duplicación de queries complejas
- Facilita análisis para usuarios no expertos en SQL
- Mejora rendimiento con vistas materializadas (futuro)
- Documenta patrones de análisis comunes

## 🔍 Descripción del Problema

**Estado actual:**
- Cada análisis requiere escribir queries complejas desde cero
- Queries de affordability, evolución de precios, etc. se duplican
- No hay abstracciones reutilizables

**Estado deseado:**
- Vistas SQL predefinidas para análisis comunes
- Documentación de uso de cada vista
- Fácil acceso desde notebooks y dashboards

**Vistas a crear:**
1. `v_affordability_quarterly` - Affordability por barrio y trimestre
2. `v_precios_evolucion_anual` - Evolución anual de precios
3. `v_demografia_resumen` - Resumen demográfico completo

**Archivos afectados:**
- Nuevo archivo: `src/database_setup.py` (añadir creación de vistas)
- O nuevo archivo: `src/database_views.py`
- Documentación: `docs/spike/DATABASE_ARCHITECTURE_DESIGN.md`

## 📝 Pasos para Implementar

1. **Diseñar vistas SQL**
   - Definir estructura de cada vista
   - Escribir queries SQL optimizadas
   - Validar queries manualmente

2. **Crear módulo de vistas**
   - Añadir funciones para crear vistas en `src/database_setup.py`
   - O crear `src/database_views.py` separado
   - Incluir en proceso de creación de esquema

3. **Crear script de creación**
   - Script para crear todas las vistas
   - Validar que vistas se crean correctamente
   - Tests de cada vista

4. **Documentar uso**
   - Ejemplos de queries usando vistas
   - Casos de uso de cada vista
   - Actualizar documentación

5. **Tests y validación**
   - Tests que verifican estructura de vistas
   - Tests que validan resultados esperados
   - Performance tests (opcional)

## ✅ Definición de Hecho (Definition of Done)

- [ ] 3 vistas SQL creadas y funcionando
- [ ] Vistas integradas en proceso de creación de esquema
- [ ] Script de creación de vistas ejecutado exitosamente
- [ ] Documentación con ejemplos de uso
- [ ] Tests creados y pasando
- [ ] Queries de ejemplo validadas manualmente
- [ ] Documentación actualizada

## 🎯 Impacto & KPI

- **KPI técnico**: Número de vistas creadas (objetivo: 3+)
- **Objetivo**: Reducir tiempo de escritura de queries complejas en 50%
- **Fuente de datos**: Tablas existentes (fact_housing_master, fact_precios, etc.)

## 🔗 Issues Relacionadas

- Relacionada con: Arquitectura de Base de Datos (`docs/spike/DATABASE_ARCHITECTURE_DESIGN.md`)
- Facilita: Análisis en notebooks y dashboards

## 🚧 Riesgos / Bloqueos

- **Riesgo**: Ninguno (vistas son read-only)
- **Nota**: Vistas pueden optimizarse más adelante como materializadas

## 📚 Enlaces Relevantes

- [Arquitectura de BD](docs/spike/DATABASE_ARCHITECTURE_DESIGN.md)
- [Database Setup](src/database_setup.py)
- [Master Table](docs/spike/IMPLEMENTATION_SUMMARY.md)

## 💡 Notas de Implementación

- **Estimación**: 2-3 horas
- **Prioridad**: 🟡 Media
- **Sprint recomendado**: Sprint actual o siguiente
- **Dependencias**: Ninguna (usa tablas existentes)

