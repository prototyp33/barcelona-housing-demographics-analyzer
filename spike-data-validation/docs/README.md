# Documentación del Spike de Validación - Gràcia

Este directorio contiene toda la documentación técnica y de referencia para el spike de validación de datos de Gràcia (Issues #199, #200, #201).

---

## 📚 Documentos Principales

### Reportes Técnicos

1. **[OBJETIVOS_WEB_SCRAPER.md](./OBJETIVOS_WEB_SCRAPER.md)** ⭐ **NUEVO**
   - **Objetivos detallados del web scraper de Idealista**
   - Qué datos buscamos y por qué
   - Cómo se integra en el pipeline MICRO
   - Resultado esperado y métricas de éxito
   - **Recomendado para entender el propósito del scraper**

2. **[DATA_SOURCES_COMPLETE_REPORT.md](./DATA_SOURCES_COMPLETE_REPORT.md)** ⭐
   - **Reporte completo de todas las fuentes de datos**
   - Análisis técnico detallado de URLs, métodos de extracción y estructuras de datasets
   - Incluye: Catastro, Portal Dades, Idealista, Idescat, Incasòl, Agencia Tributaria
   - Validación de accesos y rate limits
   - **Recomendado para consulta técnica completa**

2. **[CATASTRO_DATA_SOURCES.md](./CATASTRO_DATA_SOURCES.md)**
   - Comparación de opciones para obtener datos catastrales
   - Opción 1: catastro-api.es (recomendada para spike)
   - Opción 2: Servicio oficial D.G. del Catastro
   - Instrucciones de uso para ambas opciones

3. **[ISSUE_199_CLOSURE_SUMMARY.md](./ISSUE_199_CLOSURE_SUMMARY.md)**
   - Resumen de completación de Issue #199
   - Métricas de validación DoD
   - Archivos generados y estadísticas
   - Próximos pasos para Issue #200

4. **[CATASTRO_MASIVO_STATUS.md](./CATASTRO_MASIVO_STATUS.md)** ⭐ **ACTUALIZADO**
   - Estado actual de la consulta masiva Catastro (Issue #202, Fase 2)
   - XML enviado a Sede Electrónica (19/12/2025)
   - Próximos pasos: Parsear XML de salida cuando esté disponible

5. **[GITHUB_UPDATE_SNIPPETS.md](./GITHUB_UPDATE_SNIPPETS.md)** 📋 **NUEVO**
   - Snippets listos para copiar/pegar en GitHub Issues
   - 4 opciones: comentario completo, update corto, checklist, etc.
   - **Usar**: Cada vez que quieras actualizar Issue #202 en GitHub

6. **[GITHUB_DOCUMENTATION_GUIDE.md](./GITHUB_DOCUMENTATION_GUIDE.md)** 📖 **NUEVO**
   - Guía completa: cómo mantener docs locales sincronizadas con GitHub
   - Checklist de actualización por escenario
   - Buenas prácticas y flujo de trabajo recomendado

---

## 🎯 Guía Rápida por Issue

### Issue #199: Extract INE/Portal Dades Price Data

**Estado**: ✅ Completado

**Documentación**:
- Resumen: [ISSUE_199_CLOSURE_SUMMARY.md](./ISSUE_199_CLOSURE_SUMMARY.md)
- Fuentes: [DATA_SOURCES_COMPLETE_REPORT.md](./DATA_SOURCES_COMPLETE_REPORT.md#2-portal-dades-barcelona)

**Resultados**:
- 1,268 registros extraídos (2020-2025, 5 barrios Gràcia)
- Archivo: `data/raw/ine_precios_gracia_notebook.csv`

---

### Issue #200: Extract Catastro/Open Data Attributes

**Estado**: ✅ Debugging completo + workaround por coordenadas disponible

**Fase 2 - Consulta Masiva**:
- Estado: ⏳ XML enviado a Sede Electrónica (19/12/2025)
- Ver: [CATASTRO_MASIVO_STATUS.md](./CATASTRO_MASIVO_STATUS.md) para detalles completos

**Documentación**:
- Fuentes Catastro: [CATASTRO_DATA_SOURCES.md](./CATASTRO_DATA_SOURCES.md)
- Reporte completo: [DATA_SOURCES_COMPLETE_REPORT.md](./DATA_SOURCES_COMPLETE_REPORT.md#1-catastro-fuente-primaria-características-físicas)
 - Debugging (error 12): [ISSUE_200_DEBUG_SUMMARY.md](./ISSUE_200_DEBUG_SUMMARY.md)
 - Estado: [ISSUE_200_STATUS_UPDATE.md](./ISSUE_200_STATUS_UPDATE.md)

**Opciones (Prioridad: Fuentes Oficiales y Gratuitas)**:
1. **⭐ API SOAP Oficial** (RECOMENDADA): 100% gratuita, oficial, sin API key
2. **Consulta Masiva Oficial**: Fuente oficial, procesamiento asíncrono
3. **catastro-api.es** (NO recomendada): Servicio de terceros, requiere API key

**Scripts**:
- `scripts/catastro_soap_client.py` - ⭐ Cliente SOAP oficial (NUEVO)
- `scripts/generate_gracia_seed.py` - Genera seed por coordenadas (RC+dirección+lat/lon)
- `scripts/generate_gracia_seed_by_barrio.py` - Genera seed equilibrado (12 refs por barrio 28-32)
- `scripts/validate_seed_csv.py` - Valida seed (incluye longitudes 14/20 y coords)
- `scripts/extract_catastro_gracia.py` - Extracción principal (incluye fallback por coordenadas)
- `scripts/generate_catastro_xml.py` - Generador XML para consulta masiva
- `scripts/inspect_catastro_masivo_xml.py` - Inspección de XML masivo (descubre estructura real)
- `scripts/parse_catastro_masivo_output.py` - Parser de XML masivo (cliente + heurísticas)
- `scripts/filter_gracia_real.py` - Filtra dataset real a RC del seed (genera catastro_gracia_real.csv)
- `scripts/compare_imputed_vs_real.py` - Genera/actualiza ANALISIS_IMPUTADO_VS_REAL.md
- `scripts/download_catastro_barcelona.py` - Diagnóstico programático (ConsultaMunicipio; actualmente devuelve error 12)
- `scripts/check_issue_200_ready.py` - Verificación de requisitos

**Workaround actual (mientras `Consulta_DNPRC` falle con error 12)**:
- Generar seed por coordenadas (`Consulta_RCCOOR`) y ejecutar extracción en modo coordenadas.
- Output: `spike-data-validation/data/raw/catastro_gracia_coords.csv` (RC + dirección + lat/lon; sin superficie/año).

**Nota de ejecución (importante)**:
- Ejecutar con `.venv-spike/bin/python` (en algunos entornos `python3` del sistema puede fallar por segfault al importar numpy/pandas).

---

### Issue #201: Data Linking & Cleaning

**Estado**: ✅ v0.1 (macro) listo con imputación Fase 1; v1.0 (micro) depende de Fase 2

**Documentación**:
- Reporte completo: [DATA_SOURCES_COMPLETE_REPORT.md](./DATA_SOURCES_COMPLETE_REPORT.md#-resumen-técnico-para-implementación)

**Script**:
- `scripts/link_and_clean_gracia.py` - Matching jerárquico y limpieza

**Outputs (claridad macro vs micro)**:
- **Macro (baseline v0.1, coherente con Portal Dades agregado)**:
  - `spike-data-validation/data/processed/gracia_merged_agg_barrio_anio_dataset.csv`
  - Nivel: `barrio_id × anio × dataset_id`
  - Variables: `precio_m2_mean`, `precio_m2_std`, `n_obs` + features imputadas por barrio
- **Merged fila-a-fila (portal dades, no micro-hedonic)**:
  - `spike-data-validation/data/processed/gracia_merged.csv`
  - Nota: contiene múltiples filas por barrio-año-dataset; los atributos estructurales siguen siendo barrio-constantes en Fase 1.
- **Micro (atributos por edificio, imputados Fase 1)**:
  - `spike-data-validation/data/processed/catastro_gracia_imputado_micro.csv`
  - Nota: útil cuando exista un `y` micro (precios por edificio) o para Fase 2 con Catastro real.

---

## 🔍 Búsqueda Rápida

### Por Fuente de Datos

- **Catastro**: [DATA_SOURCES_COMPLETE_REPORT.md#1-catastro](./DATA_SOURCES_COMPLETE_REPORT.md#1-catastro-fuente-primaria-características-físicas)
- **Portal Dades**: [DATA_SOURCES_COMPLETE_REPORT.md#2-portal-dades](./DATA_SOURCES_COMPLETE_REPORT.md#2-portal-dades-barcelona-fuente-secundaria-validación)
- **Idealista**: [DATA_SOURCES_COMPLETE_REPORT.md#3-idealista](./DATA_SOURCES_COMPLETE_REPORT.md#3-idealista-fuente-mercado--oferta)
- **Idescat/Incasòl**: [DATA_SOURCES_COMPLETE_REPORT.md#4-fuentes-complementarias](./DATA_SOURCES_COMPLETE_REPORT.md#4-fuentes-complementarias-contexto-demográfico)

### Por Método de Extracción

- **REST API**: Ver secciones correspondientes en [DATA_SOURCES_COMPLETE_REPORT.md](./DATA_SOURCES_COMPLETE_REPORT.md)
- **CSV Directo**: Portal Dades, Open Data BCN
- **XML/GML**: Catastro oficial, WFS INSPIRE
- **Scraping**: Idealista (no recomendado para spike)

---

## 📊 Resumen Ejecutivo

## 🎯 Estado del Spike (19 Dic 2025)

### ✅ Completado

#### Issue #199: Extracción Precios Portal Dades
- Dataset: 1,241 registros (2020-2025, 5 barrios Gràcia)
- CSV: `spike-data-validation/data/processed/gracia_merged_agg_barrio_anio_dataset.csv`
- Completitud: 100% en `precio_m2_mean`

#### Issue #200: Extracción Catastro Gràcia
- Modo: Coordenadas (workaround por error SOAP)
- Dataset: 60 edificios con coords + referencia catastral
- Limitación: Features estructurales agregados por barrio (no micro)

#### Issue #201: Linking Precios ↔ Edificios
- Match method: `barrio_id` (nivel macro)
- Dataset merged: 175 observaciones (`barrio_id × anio × dataset_id`)
- Match rate: 100% (pero nivel agregado)

#### Issue #203: Baseline MACRO v0.1 ⭐
- Modelo: Structural-only (`anio_num` + estructurales + dummies dataset)
- R² (test 2025): 0.710
- RMSE: 323.47 €/m²
- Sesgo: +203.28 €/m² (subestima 2025)
- Artefactos: CSV pred/coefs + PNG scatter + JSON summary

#### Issue #204: Validación OLS
- Resultado: 2/5 checks passed (criterio ≥4/5 **NO** cumplido)
- Limitaciones: heterocedasticidad, autocorrelación temporal, outliers influyentes
- Recomendación: No usar OLS “puro” en producción; preferir errores estándar robustos / modelos robustos.

### ⏳ Pendiente (Fase 2)

#### Issue #202: Modelo Hedonic Pricing MICRO ✅ **COMPLETADO - NO-GO**

**Estado**: ✅ Investigación completada (21/12/2025)  
**Decisión**: ❌ **NO-GO para MICRO con modelo lineal**

**Resumen**:
- ✅ 4 estrategias de matching implementadas (geográfico, edificio, cuadrícula, heurístico)
- ✅ Investigación exhaustiva de datos (precios, características, correlaciones)
- ✅ **Causa raíz identificada**: Curva de demanda no-lineal en mercado de Gràcia
- ❌ Modelo lineal OLS inadecuado para estructura no-lineal

**Resultados**:
- MACRO baseline: R² = 0.71 ✅ (mantener como modelo operativo)
- MICRO mejor intento: R² = 0.21 ❌ (no cumple target ≥0.75)
- Correlaciones negativas persisten incluso con datos limpios

**Documentación**:
- `INVESTIGACION_RESUMEN_FINAL.md` - Resumen completo
- `GITHUB_ISSUE_202_CIERRE.md` - Comentario de cierre
- `ESTRATEGIAS_MATCHING_NIVEL_DIFERENTE.md` - Comparación de estrategias
- `MATCHING_GEOGRAFICO_RESULTADOS.md` - Resultados matching geográfico

**Recomendación**: Mantener MACRO v0.1 como modelo operativo. MICRO v0.2 requeriría modelos no-lineales (Random Forest, XGBoost) - ver `ISSUE_FUTURO_MICRO_V02.md` para futuras iteraciones.

### 📊 Métricas Clave

| Métrica      | Baseline MACRO v0.1 ✅ | MICRO v0.1 ❌ | Target MICRO v1.0 |
|--------------|----------------------|---------------|-------------------|
| **R²**       | 0.710                | 0.21          | ≥0.75             |
| **RMSE**     | 323.47 €/m²          | 2,113 €/m²    | ≤250 €/m²         |
| **Sesgo**    | +203.28 €/m²         | N/A           | <±100 €/m²        |
| **Granularidad** | Barrio×Año       | Edificio      | Edificio individual |
| **Estado**   | ✅ Operativo         | ❌ NO-GO      | -                 |

**Decisión**: Mantener MACRO v0.1 como modelo operativo. MICRO requiere modelos no-lineales (futuro).

### 🚀 Próximos Pasos

1. ✅ **Descarga masiva Catastro Barcelona**: XML enviado (19/12/2025), pendiente respuesta ≤24h
2. ⏳ **Parser XML**: Implementar cuando llegue el XML de salida (`ECLTI250200147801.XML`)
3. ⏳ **Filtrar edificios Gràcia**: Usar `filter_gracia_real.py` con datos reales del Catastro
4. ⏳ **Scraping Idealista**: 50–100 anuncios Gràcia (pendiente de Catastro real)
5. ⏳ **Matching micro**: Ref catastral + fuzzy dirección
6. ⏳ **Entrenar modelo MICRO v1.0**: Comparar contra baseline MACRO v0.1
7. ⏳ **Decisión Go/No-Go**: ¿La mejora en R²/RMSE/sesgo justifica producción?

### Ruta Recomendada para Spike

**CartoBCN (Seed) → Catastro API (Enriquecimiento) → Portal Dades (Validación)**

### Estado de Implementación

| Fuente | Estado | Script | Documentación |
| :-- | :-- | :-- | :-- |
| Portal Dades | ✅ Completado | `extract_precios_gracia.py` | [ISSUE_199_CLOSURE_SUMMARY.md](./ISSUE_199_CLOSURE_SUMMARY.md) |
| Catastro SOAP Oficial | ✅ Implementado (gratuito) | `catastro_soap_client.py` | [CATASTRO_DATA_SOURCES.md](./CATASTRO_DATA_SOURCES.md) |
| Catastro API (Terceros) | ⚠️ No recomendada | `catastro_client.py` | [CATASTRO_DATA_SOURCES.md](./CATASTRO_DATA_SOURCES.md) |
| Catastro Masiva Oficial | 🔧 Implementado | `catastro_oficial_client.py` | [CATASTRO_DATA_SOURCES.md](./CATASTRO_DATA_SOURCES.md) |
| Linking | ⏳ Pendiente | `link_and_clean_gracia.py` | [DATA_SOURCES_COMPLETE_REPORT.md](./DATA_SOURCES_COMPLETE_REPORT.md) |

---

## 🔗 Referencias Externas

### Documentación Oficial

- **Catastro API**: https://catastro-api.es
- **Sede Electrónica Catastro**: https://www1.sedecatastro.gob.es
- **Portal Dades Barcelona**: https://opendata-ajuntament.barcelona.cat
- **Open Data BCN API**: https://opendata-ajuntament.barcelona.cat/es/desenvolupadors
- **Idescat API**: https://www.idescat.cat/dev/api/pob/?lang=en

### Artículos y Referencias

Ver sección completa en [DATA_SOURCES_COMPLETE_REPORT.md](./DATA_SOURCES_COMPLETE_REPORT.md#-referencias-y-documentación)

---

**Última actualización**: 2025-12-19  
**Mantenido por**: Equipo A - Data Infrastructure

