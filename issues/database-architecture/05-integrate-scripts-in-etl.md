---
title: "[FEAT] Integrar scripts de migración en pipeline ETL"
labels: feature, database, etl, automation
assignees: ''
---

## 📌 Objetivo

Integrar los scripts de migración y creación de tablas (`dim_tiempo`, mejoras a `dim_barrios`, vistas analíticas) en el pipeline ETL principal para que se ejecuten automáticamente.

**Por qué es importante**: 
- Automatiza la creación y actualización de tablas y vistas
- Asegura consistencia en cada ejecución del ETL
- Elimina pasos manuales adicionales
- Garantiza que nuevas bases de datos tengan todas las mejoras

## 🔍 Descripción del Problema

**Estado actual:**
- Scripts de migración existen pero se ejecutan manualmente:
  - `scripts/migrate_dim_barrios_add_fields.py`
  - `scripts/create_dim_tiempo.py`
  - `scripts/create_analytical_views.py`
- Pipeline ETL no crea `dim_tiempo` automáticamente
- Pipeline ETL no actualiza campos adicionales de `dim_barrios`
- Vistas analíticas no se crean automáticamente

**Estado deseado:**
- Pipeline ETL crea `dim_tiempo` si no existe
- Pipeline ETL actualiza campos adicionales de `dim_barrios` automáticamente
- Pipeline ETL crea vistas analíticas después de cargar datos
- Todo funciona sin pasos manuales

**Archivos afectados:**
- `src/etl/pipeline.py` - Integrar llamadas a scripts
- `src/database_setup.py` - Añadir creación de `dim_tiempo`
- `src/database_views.py` - Integrar creación de vistas

## 📝 Pasos para Implementar

1. **Refactorizar scripts a funciones reutilizables**
   - Convertir scripts a funciones en módulos reutilizables
   - Crear `src/etl/migrations.py` para migraciones
   - Mover lógica de `create_dim_tiempo.py` a función
   - Mover lógica de vistas a `src/database_views.py`

2. **Integrar creación de `dim_tiempo`**
   - Añadir función `ensure_dim_tiempo()` en `src/database_setup.py`
   - Llamar desde `create_database_schema()`
   - Asegurar que se crea antes de fact tables

3. **Integrar migración de `dim_barrios`**
   - Añadir función `migrate_dim_barrios_if_needed()` en `src/etl/migrations.py`
   - Llamar desde pipeline después de crear esquema
   - Verificar si columnas existen antes de migrar

4. **Integrar creación de vistas**
   - Añadir llamada a `create_analytical_views()` en pipeline
   - Ejecutar después de cargar todas las fact tables
   - Manejar errores gracefully (vistas pueden fallar si tablas no tienen datos)

5. **Actualizar `create_database_schema()`**
   - Añadir creación de `dim_tiempo` al esquema base
   - Añadir migración de `dim_barrios` si es necesario
   - Mantener compatibilidad con bases de datos existentes

6. **Tests y validación**
   - Tests que verifican creación automática
   - Tests de idempotencia (ejecutar múltiples veces sin errores)
   - Validar que funciona en bases de datos nuevas y existentes

## ✅ Definición de Hecho (Definition of Done)

- [ ] Scripts refactorizados a funciones reutilizables
- [ ] `dim_tiempo` se crea automáticamente en pipeline ETL
- [ ] Campos adicionales de `dim_barrios` se actualizan automáticamente
- [ ] Vistas analíticas se crean automáticamente después de cargar datos
- [ ] Pipeline ETL ejecuta sin pasos manuales
- [ ] Tests creados y pasando
- [ ] Documentación actualizada
- [ ] Validado en base de datos nueva y existente

## 🎯 Impacto & KPI

- **KPI técnico**: Reducción de pasos manuales (objetivo: 0 pasos manuales)
- **Objetivo**: Pipeline ETL completamente automatizado
- **Fuente de datos**: Scripts existentes refactorizados

## 🔗 Issues Relacionadas

- Depende de: 
  - Issue #01 (Mejorar dim_barrios) - ✅ Completada
  - Issue #02 (Crear dim_tiempo) - ✅ Completada
  - Issue #03 (Crear vistas analíticas) - ✅ Completada
- Bloquea: Automatización completa del pipeline
- Relacionada con: ETL Automation (`docs/spike/ETL_AUTOMATION_MASTER_TABLE.md`)

## 🚧 Riesgos / Bloqueos

- **Riesgo**: Migraciones pueden fallar en bases de datos existentes
- **Mitigación**: 
  - Verificar existencia de columnas antes de añadir
  - Usar `IF NOT EXISTS` en todas las operaciones
  - Manejar errores gracefully

- **Riesgo**: Vistas pueden fallar si tablas no tienen datos
- **Mitigación**: 
  - Crear vistas después de cargar datos
  - Manejar errores y continuar si vistas fallan
  - Log warnings en lugar de fallar pipeline

## 📚 Enlaces Relevantes

- [ETL Pipeline](src/etl/pipeline.py)
- [Database Setup](src/database_setup.py)
- [Database Views](src/database_views.py)
- [Fase 1 Summary](docs/spike/FASE1_IMPLEMENTATION_SUMMARY.md)
- [ETL Automation](docs/spike/ETL_AUTOMATION_MASTER_TABLE.md)

## 💡 Notas de Implementación

- **Estimación**: 4-6 horas
- **Prioridad**: 🔴 Alta
- **Sprint recomendado**: Sprint actual
- **Dependencias**: Issues #01, #02, #03 completadas

### Orden de Ejecución en Pipeline

```
1. create_database_schema()
   ├─ Crear tablas base (dim_barrios, fact_*)
   └─ ensure_dim_tiempo()  # 🆕

2. migrate_dim_barrios_if_needed()  # 🆕
   └─ Añadir campos adicionales si no existen

3. Cargar datos en fact tables
   └─ (proceso existente)

4. create_analytical_views()  # 🆕
   └─ Crear vistas después de cargar datos
```

### Consideraciones de Idempotencia

- Todas las operaciones deben ser idempotentes
- Verificar existencia antes de crear/añadir
- Usar `IF NOT EXISTS` en SQL
- No fallar si ya existe

