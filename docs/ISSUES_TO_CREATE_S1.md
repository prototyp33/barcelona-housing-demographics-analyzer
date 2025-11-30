# Issues a Crear - Sprint 1 (Post-Implementación)

**Fecha:** 30 de Noviembre 2025  
**Estado:** Issue #24 parcialmente completada

---

## 📋 Issues Sugeridas

### Issue #24.1: [S1] Investigar ID del indicador de renta en API IDESCAT

**Tipo:** 🔍 Investigación / Task  
**Prioridad:** 🔴 Alta  
**Depende de:** Issue #24 (parcialmente completada)  
**Estimación:** 2-4 horas

**Descripción:**
El `IDESCATExtractor` está implementado y funcional, pero requiere identificar el ID específico del indicador de renta disponible en la API de IDESCAT para poder extraer datos reales.

**Contexto:**
- ✅ Extractor base implementado con 3 estrategias
- ✅ Tests unitarios completos (12/12 pasando)
- ✅ Integración con manifest lista
- ⏳ Falta: ID del indicador específico de renta

**Tareas:**
- [ ] Explorar API de indicadores: `https://api.idescat.cat/indicadors/v1/nodes.json?lang=es`
- [ ] Buscar indicadores relacionados con "renta", "renda", "income", "disponible"
- [ ] Identificar estructura de respuesta de la API
- [ ] Probar endpoint `dades.json` con el ID encontrado
- [ ] Verificar cobertura temporal (2015-2023)
- [ ] Verificar cobertura geográfica (barrios de Barcelona)
- [ ] Documentar hallazgos en `docs/sources/idescat.md`
- [ ] Actualizar `_try_api_indicators()` con el ID encontrado

**Criterios de Aceptación:**
- [ ] ID del indicador identificado y documentado
- [ ] Endpoint funcional probado con datos reales
- [ ] Documentación actualizada en `docs/sources/idescat.md`
- [ ] Código actualizado para usar el ID correcto

**Enlaces:**
- API IDESCAT: https://www.idescat.cat/dev/api/v1/?lang=es
- Extractor: `src/extraction/idescat.py`
- Progreso: `docs/SPRINT_1_PROGRESS.md`

**Labels:** `sprint-1`, `investigation`, `data-extraction`, `idescat`

---

### Issue #24.2: [S1] Completar estrategias alternativas IDESCATExtractor

**Tipo:** 🚀 Feature  
**Prioridad:** 🟡 Media  
**Depende de:** Issue #24.1 (si API no funciona)  
**Estimación:** 1-2 días

**Descripción:**
Si la API de IDESCAT no proporciona datos de renta directamente, completar las estrategias alternativas (web scraping y archivos públicos) para obtener los datos necesarios.

**Tareas:**
- [ ] Investigar estructura del sitio web de IDESCAT para datos de renta
- [ ] Implementar scraping específico en `_try_web_scraping()`
- [ ] Identificar URLs de archivos CSV/Excel públicos
- [ ] Implementar descarga y parsing en `_try_public_files()`
- [ ] Probar con datos reales (2015-2023)
- [ ] Validar mapeo de barrios
- [ ] Actualizar tests con casos reales

**Criterios de Aceptación:**
- [ ] Al menos una estrategia alternativa funcional
- [ ] Datos extraídos y guardados en `data/raw/idescat/`
- [ ] Cobertura >=80% para 2015-2023
- [ ] Tests actualizados

**Labels:** `sprint-1`, `feature`, `data-extraction`, `web-scraping`

---

### Issue #24.3: [S1] Documentar IDESCATExtractor

**Tipo:** 📚 Documentation  
**Prioridad:** 🟡 Media  
**Depende de:** Issue #24.1 o #24.2 (cuando haya datos reales)  
**Estimación:** 1-2 horas

**Descripción:**
Crear documentación completa del extractor de IDESCAT siguiendo el formato de otras fuentes.

**Tareas:**
- [ ] Crear `docs/sources/idescat.md`
- [ ] Documentar endpoints y estructura de la API
- [ ] Documentar estrategias de extracción
- [ ] Incluir ejemplos de uso
- [ ] Documentar limitaciones y rate limits
- [ ] Agregar diagramas de flujo si aplica

**Criterios de Aceptación:**
- [ ] Documentación completa en `docs/sources/idescat.md`
- [ ] Ejemplos de uso incluidos
- [ ] Referencias actualizadas en README

**Labels:** `sprint-1`, `documentation`, `idescat`

---

### Issue #25: [S2] Pipeline renta histórica

**Tipo:** 🚀 Feature  
**Prioridad:** 🔴 Alta  
**Depende de:** Issue #24 (completada con datos reales)  
**Estimación:** 1-1.5 semanas  
**Estado:** ⏳ Pendiente (bloqueada hasta Issue #24)

**Descripción:**
Crear el pipeline ETL completo para cargar datos de renta histórica en la tabla `fact_renta_hist`.

**Tareas:**
- [ ] Crear migración SQLite para tabla `fact_renta_hist`
- [ ] Implementar `prepare_fact_renta_hist()` en `src/data_processing.py`
- [ ] Integrar en pipeline ETL (`src/etl/pipeline.py`)
- [ ] Validar cobertura >=80% (2015-2023)
- [ ] Crear notebook QA (`notebooks/renta_historica.ipynb`)
- [ ] Actualizar `src/app/data_loader.py` para exponer datos
- [ ] Tests de integración

**Criterios de Aceptación:**
- [ ] Tabla `fact_renta_hist` creada con >=80% cobertura 2015-2023
- [ ] Pipeline ETL ejecuta sin errores
- [ ] Notebook QA completado
- [ ] `data_loader.py` actualizado
- [ ] Tests pasando

**Labels:** `sprint-1`, `feature`, `etl`, `database`

---

## 🎯 Priorización Recomendada

1. **Inmediato:** Issue #24.1 (investigación del ID del indicador)
2. **Si API no funciona:** Issue #24.2 (estrategias alternativas)
3. **En paralelo:** Issue #24.3 (documentación)
4. **Después de #24:** Issue #25 (pipeline ETL)

---

## 📝 Notas

- El Issue #24 original está **parcialmente completado**:
  - ✅ Extractor funcional
  - ✅ Tests unitarios
  - ✅ Integración manifest
  - ⏳ Pendiente: datos reales + documentación

- Se recomienda crear issues separadas para las tareas pendientes para mejor tracking.

- Issue #25 puede comenzar en paralelo una vez tengamos datos de prueba, pero requiere datos reales para completarse.

