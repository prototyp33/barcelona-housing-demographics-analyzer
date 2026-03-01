#!/usr/bin/env bash

set -euo pipefail

# Script para sincronizar issues técnicas en GitHub siguiendo el estilo del proyecto.
# Nota: Ajusta --project y --milestone si es necesario antes de ejecutar.

current_user="@me"

#
# Issue 1: Integrar geometrías de barrios en dim_barrios.geometry_json
#
gh issue create \
  --title "📋 [S1] Integrar geometrías de barrios en dim_barrios.geometry_json" \
  --label "sprint-1" \
  --label "database" \
  --label "visualization" \
  --label "priority-high" \
  --assignee "${current_user}" \
  --body '
### 📌 Objetivo

Integrar de forma robusta las geometrías de los 73 barrios de Barcelona en la columna `geometry_json` de `dim_barrios`, garantizando que el pipeline ETL deje la tabla lista para visualizaciones geoespaciales (Mapbox, choropleths, etc.).

### 🔍 Descripción del Problema

Aunque existe el script `scripts/load_geometries.py` y `prepare_dim_barrios()` soporta un `geojson_path` opcional, el estado actual de la base de datos indica que `geometry_json` sigue en NULL para la mayoría (o todos) los barrios. Esto implica que la carga de geometrías no está integrada ni automatizada dentro del pipeline ETL principal, y no hay una verificación sistemática de cobertura (73/73 barrios) ni de validez de los GeoJSON cargados.

### 📝 Pasos para Implementar

1. Definir fuente canónica de geometrías (archivo(s) GeoJSON en `data/raw/geometries/`), documentando su procedencia (Open Data BCN u otra).  
2. Conectar `scripts/load_geometries.py` con el pipeline principal (`scripts/process_and_load.py` o equivalente) para que la carga de geometrías forme parte del ETL estándar.  
3. Asegurar que `prepare_dim_barrios()` reciba `geojson_path` cuando existan geometrías y que el mapeo `barrio_id` ↔ geometría sea consistente con `codi_barri`.  
4. Implementar verificación posterior a la carga: consulta a `dim_barrios` para comprobar que 73/73 barrios tienen `geometry_json` no nulo.  
5. Añadir logs detallados (INFO/WARNING) sobre barrios sin geometría, features saltadas y tipos de geometría inválidos.  
6. Actualizar o crear notebook de validación (p.ej. `04-eda-precios.ipynb` o uno nuevo) con un mapa simple que consuma `geometry_json` para validar visualmente.  
7. Documentar el flujo en `docs/DATA_STRUCTURE.md` y/o un documento específico de geometrías (fuentes, supuestos, limitaciones).

### ✅ Definición de Hecho (Definition of Done)

- [ ] `dim_barrios.geometry_json` poblado para 73/73 barrios con GeoJSON válido.  
- [ ] Pipeline ETL (`scripts/process_and_load.py`) ejecuta la carga de geometrías sin pasos manuales adicionales.  
- [ ] Logs claros indicando número de barrios actualizados, skippeados y con errores.  
- [ ] Existe un check automatizado (script o test) que falla si `geometry_json` está vacío o incompleto.  
- [ ] Notebook de validación con un mapa funcionando usando `geometry_json`.  
- [ ] Documentación actualizada describiendo la fuente de geometrías y el proceso de carga.

### 🎯 Impacto & KPI

- **KPI afectado:** % de barrios con geometría válida (objetivo: 100% = 73/73).  
- **Impacto directo:** Habilita mapas coropléticos y análisis espaciales (densidad, renta, precios) en notebooks y dashboard futuro.  
- **Riesgo mitigado:** Evitar inconsistencias entre nombres/códigos de barrios y sus polígonos geográficos.

### 🔗 Issues Relacionadas

- Relacionada con: tareas de visualización y futuro dashboard Streamlit.  
- Conecta con: enriquecimiento de `fact_demografia` y `fact_precios` para mapas temáticos.

### 🚧 Riesgos / Bloqueos

- Posibles discrepancias entre los nombres/códigos de barrios en el GeoJSON y en `dim_barrios`.  
- Cambios futuros en la fuente de datos geográficos (nuevos límites administrativos).  
- Tamaño de los GeoJSON y rendimiento en consultas si no se optimizan correctamente.

### 📚 Enlaces Relevantes

- `scripts/load_geometries.py`  
- `src/transform/cleaners.py` (`prepare_dim_barrios` y helpers de GeoJSON)  
- `src/database_setup.py` (definición de `dim_barrios`)  
- `docs/PROJECT_STATUS.md` (sección Geometry JSON vacío)  

### ⏱️ Tiempo Estimado

**4-6 horas**
'


#
# Issue 2: Endurecer verificación de integridad de datos (scripts/verify_integrity.py)
#
gh issue create \
  --title "📋 [S1] Endurecer verificación de integridad de datos (verify_integrity.py)" \
  --label "sprint-1" \
  --label "testing" \
  --label "quality-assurance" \
  --label "etl" \
  --label "priority-medium" \
  --assignee "${current_user}" \
  --body '
### 📌 Objetivo

Convertir `scripts/verify_integrity.py` en una herramienta robusta de verificación de integridad de datos que cubra las tablas principales (`fact_precios`, `fact_demografia`, `fact_renta`, `fact_oferta_idealista`, `dim_barrios`) y se integre fácilmente en el flujo de desarrollo (CLI y CI).

### 🔍 Descripción del Problema

El script actual `scripts/verify_integrity.py` realiza algunas comprobaciones básicas usando `print()` y se centra principalmente en duplicados de `fact_precios` y nulls simples en `fact_demografia`. No sigue los estándares de logging del proyecto, no valida tablas nuevas (como `fact_renta`, `fact_oferta_idealista` ni las métricas ampliadas de edad), y no está pensado para ejecutarse automáticamente en CI o como parte del pipeline ETL.

### 📝 Pasos para Implementar

1. Refactorizar `verify_integrity.py` para usar `logging` en lugar de `print()`, siguiendo el formato y niveles del resto del proyecto.  
2. Añadir checks estructurados para:
   - Duplicados en `fact_precios` usando la clave única real (incluyendo `dataset_id` y `source`).  
   - Nulls críticos en `fact_demografia` (edad_media, densidad_hab_km2, hogares_totales, nuevas métricas de edad).  
   - Rango razonable de valores (p.ej. precios > 0, densidades positivas, porcentajes entre 0 y 100).  
   - Integridad referencial entre `fact_*` y `dim_barrios`.  
3. Incorporar métricas de resumen (conteos por tabla, % de nulls por columna crítica) en un pequeño reporte legible.  
4. Exponer una interfaz CLI clara (por ejemplo `python scripts/verify_integrity.py --db data/processed/database.db`) con códigos de salida apropiados (0=OK, 1=warnings/errores).  
5. Documentar el uso del script en `docs/PROJECT_STATUS.md` o en un documento específico de calidad de datos.  
6. (Opcional) Añadir una job de CI futura que ejecute este script tras el ETL.

### ✅ Definición de Hecho (Definition of Done)

- [ ] `verify_integrity.py` usa `logging` y no `print()`.  
- [ ] Existen checks para todas las tablas principales y campos críticos definidos en el sprint de integridad.  
- [ ] El script devuelve un código de salida no cero cuando hay problemas graves de integridad.  
- [ ] Hay ejemplos de salida/documentación para interpretar los resultados.  
- [ ] La ejecución local del script sobre la base de datos actual produce un resumen claro y accionable.

### 🎯 Impacto & KPI

- **KPI afectado:** % de ejecuciones ETL que pasan los checks de integridad sin errores graves.  
- **Impacto directo:** Reduce riesgo de degradación silenciosa de datos y facilita debugging de problemas en pipelines futuros.  
- **Facilita:** Integración con CI/CD y validaciones previas a releases.

### 🔗 Issues Relacionadas

- Relacionada con: sprint de integridad de datos (deduplicación `fact_precios`, enriquecimiento `fact_demografia`).  
- Puede alimentar futuras issues de testing y calidad de datos.

### 🚧 Riesgos / Bloqueos

- Posible necesidad de ajustar umbrales de aceptación (p.ej. % máximo de nulls) a medida que se incorporan nuevas fuentes.  
- Riesgo de falsos positivos si los checks no tienen en cuenta casos especiales documentados.

### 📚 Enlaces Relevantes

- `scripts/verify_integrity.py`  
- `src/data_processing.py` y `src/transform/cleaners.py`  
- `docs/PROJECT_STATUS.md` (sección Issues Identificados y Próximos Pasos)  

### ⏱️ Tiempo Estimado

**3-5 horas**
'


#
# Issue 3: Tests de integración para pipeline ETL (fact_precios y fact_demografia)
#
gh issue create \
  --title "📋 [S1] Tests de integración para pipeline ETL (fact_precios y fact_demografia)" \
  --label "sprint-1" \
  --label "testing" \
  --label "etl" \
  --label "data-processing" \
  --label "priority-high" \
  --assignee "${current_user}" \
  --body '
### 📌 Objetivo

Cubrir con tests de integración el pipeline ETL que construye `fact_precios` y `fact_demografia`, incluyendo las funciones de enriquecimiento (`enrich_fact_demografia`) y la integración de Portal de Dades, para garantizar que las regresiones en deduplicación y enriquecimiento se detectan automáticamente.

### 🔍 Descripción del Problema

El módulo `src/data_processing.py` y los helpers en `src/transform/cleaners.py` ya implementan lógica avanzada de deduplicación, normalización de barrios y enriquecimiento de campos demográficos usando Portal de Dades. Sin embargo, la cobertura de tests de integración sobre el pipeline completo sigue siendo limitada, lo que deja espacio a regresiones silenciosas (por ejemplo, cambios en estructura de CSV, nuevos indicadores, variaciones de nombres de territorios o ajustes en deduplicación semántica).

### 📝 Pasos para Implementar

1. Diseñar datasets mínimos de prueba (fixtures en `tests/fixtures/`) que representen:
   - Múltiples fuentes de precios (Open Data BCN + Portal de Dades) con potencial solapamiento.  
   - Casos con barrios difíciles de mapear y alias.  
   - Series demográficas con huecos que deban rellenarse vía `enrich_fact_demografia`.  
2. Crear tests de integración para:
   - `prepare_fact_precios()` verificando que:
     - Se preserva la granularidad multi-fuente (no se pierden registros válidos).  
     - La deduplicación solo elimina duplicados exactos (`dataset_id`, `source`, `trimestre`).  
   - `prepare_fact_demografia()` y `enrich_fact_demografia()` verificando:
     - Relleno de `hogares_totales`, `edad_media`, `porc_inmigracion`, `densidad_hab_km2`.  
     - Nuevas métricas de edad (`pct_mayores_65`, etc.) cuando hay datos raw disponibles.  
3. Añadir asserts sobre:
   - Número esperado de filas en tablas de hechos.  
   - % máximo de nulls permitido en campos clave (<10% según criterios de integridad).  
   - Rango razonable de valores (sin negativos, porcentajes 0-100).  
4. Integrar estos tests en `tests/test_pipeline.py` o crear un nuevo módulo dedicado.  
5. Documentar los supuestos de los fixtures y la intención de los tests en un breve README dentro de `tests/fixtures/`.

### ✅ Definición de Hecho (Definition of Done)

- [ ] Existen tests que ejecutan de extremo a extremo las funciones clave del pipeline ETL para precios y demografía.  
- [ ] Los tests fallan de forma clara si se rompe la deduplicación semántica o el enriquecimiento de campos.  
- [ ] La ejecución de `pytest` incluye estos tests sin aumentar excesivamente el tiempo total.  
- [ ] Los fixtures de datos de prueba están documentados y versionados junto con el código.

### 🎯 Impacto & KPI

- **KPI afectado:** Cobertura de tests del pipeline ETL y % de regresiones detectadas antes de producción.  
- **Impacto directo:** Mayor confianza en cambios futuros de deduplicación, mapeo de territorios y enriquecimiento demográfico.  
- **Facilita:** Refactors seguros y experimentación con nuevas fuentes de datos.

### 🔗 Issues Relacionadas

- Relacionada con: sprint de integridad de datos (`fact_precios`, `fact_demografia`).  
- Conecta con futuras issues de CI/CD y métricas de calidad.

### 🚧 Riesgos / Bloqueos

- Diseño de fixtures demasiado complejos que hagan difíciles de mantener los tests.  
- Posible necesidad de refactorizar funciones para hacerlas más fácilmente testeables.

### 📚 Enlaces Relevantes

- `src/data_processing.py`  
- `src/transform/cleaners.py`  
- `tests/test_pipeline.py`, `tests/test_cleaners.py`  
- `docs/PROJECT_STATUS.md` (secciones de integridad y próximos pasos)  

### ⏱️ Tiempo Estimado

**4-6 horas**
'


#
# Issue 4: Implementar extractor completo para INE
#
gh issue create \
  --title "📋 [S1] Implementar extractor completo para INE (series históricas de referencia)" \
  --label "sprint-1" \
  --label "data-extraction" \
  --label "priority-medium" \
  --assignee "${current_user}" \
  --body '
### 📌 Objetivo

Implementar un extractor completo para el INE que obtenga series históricas de precios y/o indicadores demográficos a nivel municipal/nacional, para usarlos como benchmark y contexto frente a los datos de barrios/distritos de Barcelona.

### 🔍 Descripción del Problema

Según `docs/PROJECT_STATUS.md`, el `INEExtractor` sigue en versión base y no se han automatizado las descargas de precios históricos nacionales. Actualmente el proyecto depende principalmente del Portal de Dades y Open Data BCN para series largas, lo que limita la capacidad de comparar la evolución de Barcelona frente a tendencias más amplias (Cataluña, España). Contar con un extractor de INE robusto permitiría enriquecer análisis de contexto y validar la coherencia de las series locales.

### 📝 Pasos para Implementar

1. Revisar el diseño actual de extractores en `src/data_extraction.py` y `src/extraction/` para alinear el `INEExtractor` con el patrón `BaseExtractor`.  
2. Investigar los endpoints relevantes del INE (precios de vivienda, renta, demografía) y documentar los IDs de serie necesarios.  
3. Implementar el `INEExtractor` con:
   - Manejo de paginación/rate limits.  
   - Guardado de respuestas raw en `data/raw/ine/` con timestamp.  
   - Logs claros de cobertura temporal y tamaño de datos.  
4. Crear funciones de procesamiento inicial (pueden ser simples) para transformar los datos raw en un formato compatible con el esquema actual o en tablas auxiliares.  
5. Añadir tests unitarios y, si es posible, un pequeño test de integración con datos mockeados para evitar depender de la API real en CI.  
6. Documentar el extractor en `docs/sources/ine.md` (similar a IDESCAT) y enlazarlo desde la documentación general de fuentes.

### ✅ Definición de Hecho (Definition of Done)

- [ ] `INEExtractor` implementado siguiendo el patrón `BaseExtractor` y probado localmente.  
- [ ] Datos raw guardados en `data/raw/ine/` con estructura consistente.  
- [ ] Al menos una serie histórica relevante (precios o renta) descargada y disponible para análisis.  
- [ ] Tests unitarios básicos pasando (incluyendo manejo de errores y de respuestas vacías).  
- [ ] Documentación de la fuente y de los endpoints utilizada.

### 🎯 Impacto & KPI

- **KPI afectado:** Número de fuentes externas integradas (objetivo: 3/4 a corto plazo).  
- **Impacto directo:** Mejora la capacidad de contextualizar los datos de Barcelona comparándolos con tendencias nacionales/municipales.  
- **Facilita:** Análisis posteriores de convergencia/divergencia de precios y renta.

### 🔗 Issues Relacionadas

- Relacionada con: análisis de correlaciones y EDA avanzada.  
- Conecta con futuras issues de análisis comparativo (`src/analysis.py`).

### 🚧 Riesgos / Bloqueos

- Complejidad de la API del INE (documentación, autenticación, formatos de respuesta heterogéneos).  
- Cambios de estructura/IDs de serie con el tiempo.  
- Posibles límites de peticiones o ventanas de mantenimiento del servicio.

### 📚 Enlaces Relevantes

- `src/data_extraction.py`, `src/extraction/`  
- `docs/PROJECT_STATUS.md` (sección Datos de INE pendientes)  
- Documentación oficial del INE (API)  

### ⏱️ Tiempo Estimado

**1-2 días**
'


