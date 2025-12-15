---
title: "[FEAT] Mapear códigos INE para los 73 barrios de Barcelona"
labels: feature, database, data-quality
assignees: ''
---

## 📌 Objetivo

Completar el mapeo de códigos INE para los 73 barrios de Barcelona en `dim_barrios.codigo_ine`. Actualmente todos los valores están en NULL (0/73).

**Por qué es importante**: 
- Facilita matching con datos del INE (Instituto Nacional de Estadística)
- Permite validación cruzada de datos demográficos
- Mejora la integridad y trazabilidad de datos

## 🔍 Descripción del Problema

**Estado actual:**
- Campo `codigo_ine` existe en `dim_barrios` pero está NULL para todos los barrios (0/73)
- No hay mapeo entre `barrio_id` y códigos INE oficiales
- Dificulta integración con datos del INE

**Estado deseado:**
- 73/73 barrios con código INE poblado
- Mapeo validado y documentado
- Script actualizado para poblar códigos automáticamente

**Archivos afectados:**
- `scripts/migrate_dim_barrios_add_fields.py` - Función `get_ine_codes()`
- `src/etl/pipeline.py` - Integrar mapeo en pipeline
- Nuevo archivo: `data/reference/barrio_ine_mapping.json` (mapeo de referencia)

## 📝 Pasos para Implementar

1. **Investigar fuente de códigos INE**
   - Consultar INE para códigos oficiales de barrios
   - Verificar si hay API o dataset disponible
   - Revisar documentación oficial del Ajuntament

2. **Crear mapeo manual inicial**
   - Crear archivo JSON con mapeo `barrio_id -> codigo_ine`
   - Validar cada código con fuente oficial
   - Documentar fuente de cada código

3. **Actualizar script de migración**
   - Completar función `get_ine_codes()` en `migrate_dim_barrios_add_fields.py`
   - Cargar mapeo desde archivo JSON
   - Validar que todos los códigos son válidos

4. **Ejecutar migración**
   - Ejecutar script para poblar códigos INE
   - Verificar que 73/73 barrios tienen código
   - Validar formato de códigos

5. **Integrar en pipeline ETL**
   - Añadir lógica para poblar `codigo_ine` en pipeline
   - Asegurar que se actualiza en cada carga

6. **Documentar y validar**
   - Documentar fuente de códigos
   - Crear tests de validación
   - Verificar matching con datos INE reales

## ✅ Definición de Hecho (Definition of Done)

- [ ] Archivo de mapeo creado (`data/reference/barrio_ine_mapping.json`)
- [ ] Función `get_ine_codes()` completada y validada
- [ ] Script de migración ejecutado exitosamente
- [ ] 73/73 barrios con código INE poblado (100%)
- [ ] Códigos validados contra fuente oficial
- [ ] Pipeline ETL actualizado para poblar códigos
- [ ] Tests creados y pasando
- [ ] Documentación actualizada con fuente de códigos

## 🎯 Impacto & KPI

- **KPI técnico**: Completitud de `codigo_ine` en `dim_barrios` (objetivo: 100%)
- **Objetivo**: 73/73 barrios con código INE válido
- **Fuente de datos**: INE (Instituto Nacional de Estadística) o mapeo oficial

## 🔗 Issues Relacionadas

- Depende de: Issue #01 (Mejorar dim_barrios) - ✅ Completada
- Bloquea: Integración con datos INE (futuro)
- Relacionada con: Arquitectura de Base de Datos (`docs/spike/DATABASE_ARCHITECTURE_DESIGN.md`)

## 🚧 Riesgos / Bloqueos

- **Riesgo**: Códigos INE pueden no estar disponibles públicamente
- **Mitigación**: 
  - Usar mapeo basado en nombres oficiales y códigos del Ajuntament
  - Consultar INE directamente si es necesario
  - Validar con datos reales del INE

- **Riesgo**: Códigos pueden cambiar con el tiempo
- **Mitigación**: Documentar versión/fecha de códigos usados

## 📚 Enlaces Relevantes

- [Arquitectura de BD](docs/spike/DATABASE_ARCHITECTURE_DESIGN.md)
- [Fase 1 Summary](docs/spike/FASE1_IMPLEMENTATION_SUMMARY.md)
- [Script de Migración](scripts/migrate_dim_barrios_add_fields.py)
- [INE - Instituto Nacional de Estadística](https://www.ine.es/)

## 💡 Notas de Implementación

- **Estimación**: 3-4 horas
- **Prioridad**: 🟡 Media
- **Sprint recomendado**: Sprint actual o siguiente
- **Dependencias**: Ninguna (puede hacerse en paralelo)

### Fuentes Potenciales

1. **INE Directo**: Consultar API o datasets del INE
2. **Ajuntament de Barcelona**: Códigos oficiales de barrios
3. **Mapeo Manual**: Basado en nombres y códigos `codi_barri` existentes

### Formato Esperado

```json
{
  "1": "08019001",  // barrio_id -> codigo_ine
  "2": "08019002",
  ...
}
```

