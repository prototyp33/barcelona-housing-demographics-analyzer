# Auditoría Completa del Proyecto Barcelona Housing Demographics Analyzer

**Fecha de auditoría:** 2025-12-02  
**Auditor:** Cursor Composer AI  
**Alcance:** Código fuente completo, documentación, issues existentes, commits recientes

---

## 📊 Resumen Ejecutivo

### Total de Issues Identificadas: **87**

#### Por Categoría:
- **A. Bugs Críticos:** 6
- **B. Bugs Menores:** 8
- **C. Mejoras de Calidad de Código:** 24
- **D. Refactorings Pendientes:** 5
- **E. Features Incompletas:** 7
- **F. Datos Faltantes:** 5
- **G. Testing:** 12
- **H. Documentación:** 8
- **I. DevOps/CI-CD:** 4
- **J. Performance:** 8

#### Por Prioridad:
- 🔴 **Crítica:** 6 issues
- 🟡 **Alta:** 18 issues
- 🟢 **Media:** 35 issues
- ⚪ **Baja:** 28 issues

### Issues Críticas que Bloquean Desarrollo:
1. **Código duplicado masivo** (`data_extraction.py` vs `extraction/`) - ~2000 líneas duplicadas
2. **SQL Injection potencial** en múltiples lugares
3. **IncasolSocrataExtractor no registrado** en `__init__.py`
4. **Validación de integridad referencial faltante** en ETL
5. **Manejo de errores genérico** en múltiples módulos críticos
6. **Hardcoding de año 2022** en múltiples lugares

### Quick Wins (Bajo Esfuerzo, Alto Impacto):
1. Registrar `IncasolSocrataExtractor` en `__init__.py` (15 min)
2. Reemplazar `print()` por logger en `data_extraction.py` (10 min)
3. Eliminar import no utilizado `json` en `enrichment.py` (5 min)
4. Añadir validación de tabla blanca en `data_loader.py` (20 min)
5. Corregir workflow `kpi-update.yml` bare except (10 min)

---

## 📋 Issues Detalladas

### A. Bugs Críticos (Priority: Critical)

#### A1. Código Duplicado Masivo: `data_extraction.py` vs `extraction/`
- **id:** A1
- **title:** "🔴 [BUG] Código duplicado: `data_extraction.py` legacy duplica funcionalidad de `extraction/`"
- **category:** A
- **priority:** critical
- **labels:** `bug`, `refactoring`, `code-quality`, `technical-debt`
- **affected_files:**
  - `src/data_extraction.py` (2547 líneas)
  - `src/extraction/opendata.py`
  - `src/extraction/idealista.py`
  - `src/extraction/portaldades.py`
- **description:** |
  Existe un módulo legacy `data_extraction.py` (2547 líneas) que duplica completamente la funcionalidad de los extractores modulares en `src/extraction/`. Esto genera:
  - Confusión sobre qué código usar
  - Mantenimiento duplicado
  - Riesgo de inconsistencias entre versiones
  - ~2000 líneas de código duplicado
- **current_behavior:** |
  Dos sistemas de extracción coexisten:
  - Sistema legacy: `src/data_extraction.py` con clases `OpenDataBCNExtractor`, `IdealistaExtractor`, `PortalDadesExtractor`
  - Sistema modular: `src/extraction/` con las mismas clases pero refactorizadas
- **expected_behavior:** |
  Un solo sistema de extracción modular en `src/extraction/`. El código legacy debe eliminarse o marcarse como deprecated con migración completa.
- **proposed_solution:** |
  1. Auditar qué código legacy aún se usa (buscar imports de `data_extraction`)
  2. Migrar todas las referencias a `extraction/`
  3. Eliminar `data_extraction.py` o marcarlo como deprecated con warnings
  4. Actualizar documentación y scripts que lo referencien
- **related_issues:** Issue #42, #43
- **related_docs:** `docs/CODE_AUDIT_ISSUES.md` #1
- **estimated_effort:** 8-12 horas
- **acceptance_criteria:**
  - [ ] No hay imports de `data_extraction` en código activo
  - [ ] Todas las referencias migradas a `extraction/`
  - [ ] `data_extraction.py` eliminado o marcado como deprecated
  - [ ] Tests pasan con código modular
  - [ ] Documentación actualizada
- **source:** `docs/CODE_AUDIT_ISSUES.md` #1

---

#### A2. SQL Injection Potencial en `data_loader.py`
- **id:** A2
- **title:** "🔴 [BUG] SQL Injection potencial: falta validación de tabla blanca en `data_loader.py`"
- **category:** A
- **priority:** critical
- **labels:** `bug`, `security`, `sql-injection`, `streamlit`
- **affected_files:**
  - `src/app/data_loader.py:80`
- **description:** |
  Uso de f-string con nombre de tabla sin validación explícita contra lista blanca. Aunque `table` viene de una lista controlada, es una mala práctica de seguridad.
- **current_behavior:** |
  ```python
  df = pd.read_sql(f"SELECT MIN(anio) as min_year, MAX(anio) as max_year FROM {table}", conn)
  ```
- **expected_behavior:** |
  Validar que `table` esté en una lista blanca antes de construir la query.
- **proposed_solution:** |
  ```python
  ALLOWED_TABLES = ["fact_precios", "fact_demografia", "fact_renta"]
  if table not in ALLOWED_TABLES:
      raise ValueError(f"Tabla no permitida: {table}")
  df = pd.read_sql(f"SELECT MIN(anio) as min_year, MAX(anio) as max_year FROM {table}", conn)
  ```
- **related_issues:** None
- **related_docs:** `docs/CODE_AUDIT_ISSUES.md` #2
- **estimated_effort:** 20 minutos
- **acceptance_criteria:**
  - [ ] Validación de tabla blanca implementada
  - [ ] Test que verifica rechazo de tablas no permitidas
  - [ ] Lista de tablas permitidas documentada
- **source:** `docs/CODE_AUDIT_ISSUES.md` #2

---

#### A3. SQL Injection Potencial en `database_setup.py`
- **id:** A3
- **title:** "🔴 [BUG] SQL Injection potencial: falta validación en `truncate_tables()`"
- **category:** A
- **priority:** critical
- **labels:** `bug`, `security`, `sql-injection`, `database`
- **affected_files:**
  - `src/database_setup.py:214`
- **description:** |
  Similar al anterior, aunque `table` viene de una lista controlada en `truncate_tables()`, falta validación explícita.
- **current_behavior:** |
  ```python
  conn.execute(f"DELETE FROM {table};")
  ```
- **expected_behavior:** |
  Validar explícitamente contra lista blanca antes de ejecutar DELETE.
- **proposed_solution:** |
  ```python
  ALLOWED_TABLES = {"dim_barrios", "fact_precios", "fact_demografia", ...}
  if table not in ALLOWED_TABLES:
      raise ValueError(f"Tabla no permitida para truncado: {table}")
  conn.execute(f"DELETE FROM {table};")
  ```
- **related_issues:** A2
- **related_docs:** `docs/CODE_AUDIT_ISSUES.md` #3
- **estimated_effort:** 15 minutos
- **acceptance_criteria:**
  - [ ] Validación de tabla blanca implementada
  - [ ] Test que verifica rechazo de tablas no permitidas
- **source:** `docs/CODE_AUDIT_ISSUES.md` #3

---

#### A4. IncasolSocrataExtractor No Registrado en `__init__.py`
- **id:** A4
- **title:** "🔴 [BUG] `IncasolSocrataExtractor` no exportado en `extraction/__init__.py`"
- **category:** A
- **priority:** critical
- **labels:** `bug`, `import-error`, `extraction`
- **affected_files:**
  - `src/extraction/incasol.py`
  - `src/extraction/__init__.py`
- **description:** |
  La clase `IncasolSocrataExtractor` existe en `src/extraction/incasol.py` pero no está exportada en `__init__.py`, por lo que no es importable desde `src.extraction`.
- **current_behavior:** |
  ```python
  from src.extraction import IncasolSocrataExtractor  # ❌ ImportError
  ```
- **expected_behavior:** |
  ```python
  from src.extraction import IncasolSocrataExtractor  # ✅ Funciona
  ```
- **proposed_solution:** |
  Añadir en `src/extraction/__init__.py`:
  ```python
  from .incasol import IncasolSocrataExtractor
  __all__ = [
      # ... existing exports ...
      "IncasolSocrataExtractor",
  ]
  ```
- **related_issues:** None
- **related_docs:** `docs/CODE_AUDIT_ISSUES.md` #4
- **estimated_effort:** 5 minutos
- **acceptance_criteria:**
  - [ ] `IncasolSocrataExtractor` añadido a `__all__`
  - [ ] Import funciona correctamente
  - [ ] Test de import añadido
- **source:** `docs/CODE_AUDIT_ISSUES.md` #4

---

#### A5. Uso de `print()` en lugar de Logger
- **id:** A5
- **title:** "🔴 [BUG] Uso de `print()` en lugar de logger en `data_extraction.py`"
- **category:** A
- **priority:** critical
- **labels:** `bug`, `logging`, `code-quality`
- **affected_files:**
  - `src/data_extraction.py:40`
- **description:** |
  Uso de `print()` para warnings cuando debería usarse el sistema de logging establecido.
- **current_behavior:** |
  ```python
  print("WARNING: Playwright no está instalado...", file=sys.stderr)
  ```
- **expected_behavior:** |
  Usar logger una vez inicializado o inicializar logger antes si es necesario.
- **proposed_solution:** |
  ```python
  logger.warning("Playwright no está instalado. El extractor PortalDades requerirá: pip install playwright && playwright install")
  ```
- **related_issues:** None
- **related_docs:** `docs/CODE_AUDIT_ISSUES.md` #5
- **estimated_effort:** 10 minutos
- **acceptance_criteria:**
  - [ ] `print()` reemplazado por logger
  - [ ] Logger inicializado correctamente
- **source:** `docs/CODE_AUDIT_ISSUES.md` #5

---

#### A6. Falta Validación de Integridad Referencial en ETL
- **id:** A6
- **title:** "🔴 [BUG] Falta validación de integridad referencial antes de insertar en fact tables"
- **category:** A
- **priority:** critical
- **labels:** `bug`, `database`, `etl`, `data-integrity`
- **affected_files:**
  - `src/etl/pipeline.py`
  - `src/etl/transformations/market.py`
  - `src/etl/transformations/demographics.py`
- **description:** |
  El ETL carga datos en tablas con foreign keys pero no valida explícitamente que todos los `barrio_id` en fact tables existan en `dim_barrios` antes de insertar.
- **current_behavior:** |
  El ETL inserta directamente en fact tables sin validar referencias. SQLite puede fallar silenciosamente o generar errores de foreign key constraint.
- **expected_behavior:** |
  Validar explícitamente que todos los `barrio_id` existen en `dim_barrios` antes de insertar.
- **proposed_solution:** |
  ```python
  # Antes de cargar fact tables, validar:
  invalid_barrios = fact_precios[~fact_precios['barrio_id'].isin(dim_barrios['barrio_id'])]
  if not invalid_barrios.empty:
      logger.error(f"Barrios inválidos encontrados: {invalid_barrios['barrio_id'].unique()}")
      raise ValueError("Integridad referencial violada")
  ```
- **related_issues:** None
- **related_docs:** `docs/CODE_AUDIT_ISSUES.md` #8
- **estimated_effort:** 2-3 horas
- **acceptance_criteria:**
  - [ ] Validación implementada para todas las fact tables
  - [ ] Logging claro cuando se detectan violaciones
  - [ ] Tests que verifican rechazo de datos inválidos
- **source:** `docs/CODE_AUDIT_ISSUES.md` #8

---

### B. Bugs Menores (Priority: Medium-High)

#### B1. Hardcoding de Año 2022 en Múltiples Lugares
- **id:** B1
- **title:** "🟡 [BUG] Hardcoding de año 2022 en funciones de `data_loader.py` y `main.py`"
- **category:** B
- **priority:** high
- **labels:** `bug`, `hardcoding`, `streamlit`, `data-quality`
- **affected_files:**
  - `src/app/data_loader.py` (múltiples funciones)
  - `src/app/main.py:75-88`
- **description:** |
  Los datos de renta ahora están disponibles para 2015-2023, pero el código sigue asumiendo solo 2022.
- **current_behavior:** |
  - `load_renta(year: int = 2022)` - hardcodea 2022 como default
  - `load_affordability_data()` - hardcodea `WHERE anio = 2022`
  - `load_temporal_comparison()` - hardcodea `WHERE anio = 2022`
  - UI muestra "Mostrando datos disponibles para **2022**"
- **expected_behavior:** |
  Usar años disponibles dinámicamente desde la base de datos.
- **proposed_solution:** |
  1. Consultar años disponibles dinámicamente desde `load_available_years()`
  2. Actualizar funciones para usar año pasado como parámetro
  3. Habilitar slider si hay múltiples años disponibles
- **related_issues:** None
- **related_docs:** `docs/CODE_AUDIT_ISSUES.md` #7, #15
- **estimated_effort:** 2-3 horas
- **acceptance_criteria:**
  - [ ] Funciones usan años dinámicos
  - [ ] UI muestra años disponibles correctamente
  - [ ] Slider habilitado cuando hay múltiples años
- **source:** `docs/CODE_AUDIT_ISSUES.md` #7, #15

---

#### B2. Validación Faltante en `prepare_fact_precios` para Pipes Duplicados
- **id:** B2
- **title:** "🟡 [BUG] `prepare_fact_precios` detecta pipes duplicados pero no los corrige automáticamente"
- **category:** B
- **priority:** medium
- **labels:** `bug`, `etl`, `data-quality`
- **affected_files:**
  - `src/etl/transformations/market.py:243-252`
- **description:** |
  La función detecta pipes duplicados (`|`) en las columnas `source` y `dataset_id` pero solo loguea un error sin corregir el problema. Aunque existe `_normalize_pipe_tags`, no se aplica automáticamente.
- **current_behavior:** |
  ```python
  if fact["source"].astype(str).str.contains(r"\\|").any():
      logger.error("⚠️ ALERTA: Se detectaron pipes '|' en columna 'source'...")
  # Solo loguea error, no corrige
  ```
- **expected_behavior:** |
  Aplicar `_normalize_pipe_tags` automáticamente cuando se detecten pipes duplicados.
- **proposed_solution:** |
  ```python
  if fact["source"].astype(str).str.contains(r"\\|").any():
      logger.warning("Se detectaron pipes duplicados en 'source'. Normalizando automáticamente.")
      fact["source"] = fact["source"].apply(_normalize_pipe_tags)
  ```
- **related_issues:** Issue #13 (deduplicación en fact_precios)
- **related_docs:** `docs/GITHUB_ISSUES_AUDIT_RECIENTE.md` #4
- **estimated_effort:** 30 minutos
- **acceptance_criteria:**
  - [ ] Normalización automática implementada
  - [ ] Log level cambiado a WARNING si se corrige automáticamente
  - [ ] Test que verifica corrección automática
- **source:** `docs/GITHUB_ISSUES_AUDIT_RECIENTE.md` #4

---

#### B3. Falta Validación de Años en Datos de Portal de Dades
- **id:** B3
- **title:** "🟡 [BUG] Falta validación de años None antes de agrupar en transformaciones"
- **category:** B
- **priority:** medium
- **labels:** `bug`, `etl`, `data-quality`
- **affected_files:**
  - `src/etl/transformations/enrichment.py:112`
  - `src/etl/transformations/utils.py:114-120`
- **description:** |
  `_extract_year_from_temps` puede retornar `None` cuando falla el parsing, pero este valor no siempre se valida antes de agrupar.
- **current_behavior:** |
  Aunque hay `dropna(subset=["anio"])` en algunos lugares, puede haber agrupaciones que fallen si hay None.
- **expected_behavior:** |
  Validar explícitamente que `anio` no sea None antes de agrupar en todos los lugares.
- **proposed_solution:** |
  Asegurar que siempre se valida `dropna(subset=["anio"])` antes de agrupar y añadir logging cuando se descarten registros.
- **related_issues:** Issue #15 (mapeo de territorios)
- **related_docs:** `docs/GITHUB_ISSUES_AUDIT_RECIENTE.md` #7
- **estimated_effort:** 1 hora
- **acceptance_criteria:**
  - [ ] Validación de años en todos los lugares de agrupación
  - [ ] Logging cuando se descartan registros por año inválido
  - [ ] Test que verifica manejo de años inválidos
- **source:** `docs/GITHUB_ISSUES_AUDIT_RECIENTE.md` #7

---

#### B4. Falta Validación de Estructura de manifest.json
- **id:** B4
- **title:** "🟡 [BUG] `_load_manifest` no valida estructura de manifest.json"
- **category:** B
- **priority:** medium
- **labels:** `bug`, `etl`, `data-quality`
- **affected_files:**
  - `src/etl/pipeline.py:45-67`
- **description:** |
  La función carga el JSON pero no valida que tenga la estructura esperada (lista de diccionarios con campos específicos).
- **current_behavior:** |
  ```python
  manifest = json.load(f)  # ❌ No valida estructura
  return manifest
  ```
- **expected_behavior:** |
  Validar que sea una lista y que cada entrada tenga campos mínimos requeridos.
- **proposed_solution:** |
  Añadir validación de tipo (debe ser lista) y campos requeridos en cada entrada, con logging claro cuando el manifest tiene estructura incorrecta.
- **related_issues:** None
- **related_docs:** `docs/GITHUB_ISSUES_AUDIT_RECIENTE.md` #10
- **estimated_effort:** 1 hora
- **acceptance_criteria:**
  - [ ] Validación de tipo implementada
  - [ ] Validación de campos requeridos
  - [ ] Logging claro cuando el manifest es inválido
  - [ ] Test que verifica validación de manifest inválido
- **source:** `docs/GITHUB_ISSUES_AUDIT_RECIENTE.md` #10

---

#### B5. Función `prepare_idealista_oferta` con Lógica Incompleta
- **id:** B5
- **title:** "🟡 [BUG] `prepare_idealista_oferta` calcula `num_anuncios_tipologia` pero no lo incluye en resultado"
- **category:** B
- **priority:** medium
- **labels:** `bug`, `etl`, `code-quality`
- **affected_files:**
  - `src/etl/transformations/enrichment.py:277-283`
- **description:** |
  La función calcula `num_anuncios_tipologia` pero lo asigna a `_` (descartado), lo que es código muerto.
- **current_behavior:** |
  ```python
  if "tipologia" in df.columns:
      _ = (  # ❌ Resultado descartado
          df.groupby(group_cols + ["tipologia"])
          .size()
          .reset_index(name="num_anuncios_tipologia")
      )
  ```
- **expected_behavior:** |
  Incluir `num_anuncios_tipologia` en el resultado agregado si es útil, o eliminar el código si no se necesita.
- **proposed_solution:** |
  Evaluar si es información útil. Si sí, incluir en el DataFrame agregado (pivot o agregación adicional). Si no, eliminar código muerto.
- **related_issues:** None
- **related_docs:** `docs/GITHUB_ISSUES_AUDIT_RECIENTE.md` #11
- **estimated_effort:** 1 hora
- **acceptance_criteria:**
  - [ ] Decisión documentada sobre si incluir o eliminar
  - [ ] Código implementado según decisión
  - [ ] Test actualizado
- **source:** `docs/GITHUB_ISSUES_AUDIT_RECIENTE.md` #11

---

#### B6. Falta Manejo de Errores en `build_geojson`
- **id:** B6
- **title:** "🟡 [BUG] `build_geojson` hace `json.loads()` sin manejo de errores"
- **category:** B
- **priority:** medium
- **labels:** `bug`, `streamlit`, `error-handling`
- **affected_files:**
  - `src/app/data_loader.py:446`
- **description:** |
  La función hace `json.loads()` sin manejo de errores si el JSON es inválido.
- **current_behavior:** |
  ```python
  geometry = json.loads(row["geometry_json"])  # ❌ Puede fallar
  ```
- **expected_behavior:** |
  Manejar `json.JSONDecodeError` y `TypeError` con logging apropiado.
- **proposed_solution:** |
  ```python
  try:
      geometry = json.loads(row["geometry_json"])
  except (json.JSONDecodeError, TypeError) as e:
      logger.warning(f"GeoJSON inválido para barrio {row['barrio_id']}: {e}")
      continue
  ```
- **related_issues:** None
- **related_docs:** `docs/CODE_AUDIT_ISSUES.md` #16
- **estimated_effort:** 20 minutos
- **acceptance_criteria:**
  - [ ] Manejo de errores implementado
  - [ ] Logging apropiado
  - [ ] Test que verifica manejo de JSON inválido
- **source:** `docs/CODE_AUDIT_ISSUES.md` #16

---

#### B7. Falta Validación de DataFrame Vacío en Múltiples Funciones
- **id:** B7
- **title:** "🟡 [BUG] Múltiples funciones no validan DataFrame vacío al inicio"
- **category:** B
- **priority:** medium
- **labels:** `bug`, `data-processing`, `validation`
- **affected_files:**
  - `src/data_processing.py` (múltiples funciones)
  - `src/etl/transformations/*.py`
- **description:** |
  Muchas funciones asumen que el DataFrame tiene datos pero no validan explícitamente al inicio.
- **current_behavior:** |
  Funciones pueden fallar con errores crípticos si reciben DataFrame vacío.
- **expected_behavior:** |
  Validar temprano: `if df.empty: return pd.DataFrame()` o `raise ValueError` según el caso.
- **proposed_solution:** |
  Añadir validación temprana en todas las funciones de transformación y documentar comportamiento cuando DataFrame está vacío.
- **related_issues:** None
- **related_docs:** `docs/CODE_AUDIT_ISSUES.md` #17
- **estimated_effort:** 2-3 horas
- **acceptance_criteria:**
  - [ ] Validación añadida en funciones críticas
  - [ ] Comportamiento documentado
  - [ ] Tests que verifican manejo de DataFrames vacíos
- **source:** `docs/CODE_AUDIT_ISSUES.md` #17

---

#### B8. Falta Validación de Rangos Temporales en ETL
- **id:** B8
- **title:** "🟡 [BUG] ETL no valida que años estén en rangos esperados"
- **category:** B
- **priority:** medium
- **labels:** `bug`, `etl`, `data-quality`
- **affected_files:**
  - `src/etl/pipeline.py`
  - `src/etl/transformations/*.py`
- **description:** |
  El ETL no valida que los años en los datos estén dentro de rangos esperados (ej: no hay años futuros, no hay años antes de 2010).
- **current_behavior:** |
  Años inválidos pueden pasar al ETL sin detección.
- **expected_behavior:** |
  Validar rangos temporales y loguear warnings cuando se detecten años fuera de rango.
- **proposed_solution:** |
  ```python
  MIN_VALID_YEAR = 2010
  MAX_VALID_YEAR = datetime.now().year + 1
  if (df['anio'] < MIN_VALID_YEAR).any() or (df['anio'] > MAX_VALID_YEAR).any():
      logger.warning(f"Años fuera de rango válido detectados")
  ```
- **related_issues:** None
- **related_docs:** `docs/CODE_AUDIT_ISSUES.md` #21
- **estimated_effort:** 1 hora
- **acceptance_criteria:**
  - [ ] Validación de rangos implementada
  - [ ] Logging cuando se detectan años inválidos
  - [ ] Tests que verifican validación
- **source:** `docs/CODE_AUDIT_ISSUES.md` #21

---

### C. Mejoras de Calidad de Código (Priority: Medium-Low)

#### C1. Manejo de Errores Genérico en `enrichment.py`
- **id:** C1
- **title:** "🟢 [QUALITY] Manejo de errores genérico: múltiples `except Exception` en `enrichment.py`"
- **category:** C
- **priority:** medium
- **labels:** `code-quality`, `etl`, `error-handling`
- **affected_files:**
  - `src/etl/transformations/enrichment.py:52, 164`
- **description:** |
  Múltiples bloques `except Exception` capturan excepciones muy amplias sin especificar tipos concretos.
- **current_behavior:** |
  ```python
  except Exception as exc:  # noqa: BLE001
      logger.warning("Error cargando metadatos: %s", exc)
  ```
- **expected_behavior:** |
  Especificar tipos de excepciones concretos y añadir `exc_info=True` a logs de errores.
- **proposed_solution:** |
  ```python
  except (FileNotFoundError, pd.errors.ParserError, json.JSONDecodeError) as exc:
      logger.warning("Error cargando metadatos: %s", exc, exc_info=True)
  except Exception as exc:
      logger.error("Error inesperado: %s", exc, exc_info=True)
      raise
  ```
- **related_issues:** None
- **related_docs:** `docs/GITHUB_ISSUES_AUDIT_RECIENTE.md` #2
- **estimated_effort:** 1-2 horas
- **acceptance_criteria:**
  - [ ] Tipos específicos identificados para cada bloque
  - [ ] `except Exception` reemplazado por tipos concretos donde sea posible
  - [ ] `exc_info=True` añadido a logs de errores
- **source:** `docs/GITHUB_ISSUES_AUDIT_RECIENTE.md` #2

---

#### C2. Manejo de Errores Silencioso en `pipeline.py`
- **id:** C2
- **title:** "🟢 [QUALITY] Manejo de errores silencioso: múltiples bloques try/except solo loguean warnings"
- **category:** C
- **priority:** medium
- **labels:** `code-quality`, `etl`, `error-handling`
- **affected_files:**
  - `src/etl/pipeline.py` (múltiples ubicaciones: 252, 310, 363, 394, 410, 421, 438)
- **description:** |
  Múltiples bloques `try/except` solo loguean warnings pero continúan la ejecución, incluso cuando algunos errores podrían ser críticos.
- **current_behavior:** |
  ```python
  try:
      renta_df = _safe_read_csv(renta_path)
  except Exception as e:
      logger.warning("Error cargando datos de renta: %s", e)
      # Continúa ejecución sin datos de renta
  ```
- **expected_behavior:** |
  Clasificar errores en críticos vs. opcionales. Errores críticos deberían detener el pipeline, opcionales pueden continuar con warning.
- **proposed_solution:** |
  Clasificar cada fuente como crítica u opcional. Modificar manejo de errores para fuentes críticas (raise en lugar de warning). Añadir flag `--strict` para pipeline que falle en cualquier error.
- **related_issues:** Issue #43
- **related_docs:** `docs/GITHUB_ISSUES_AUDIT_RECIENTE.md` #6
- **estimated_effort:** 3-4 horas
- **acceptance_criteria:**
  - [ ] Fuentes clasificadas como críticas vs. opcionales
  - [ ] Manejo de errores actualizado según clasificación
  - [ ] `exc_info=True` añadido a todos los logs de errores
  - [ ] Documentación de qué fuentes son críticas
- **source:** `docs/GITHUB_ISSUES_AUDIT_RECIENTE.md` #6

---

#### C3. Import No Utilizado en `enrichment.py`
- **id:** C3
- **title:** "🟢 [QUALITY] Import no utilizado: `json` marcado como `# noqa: F401`"
- **category:** C
- **priority:** low
- **labels:** `code-quality`, `cleanup`
- **affected_files:**
  - `src/etl/transformations/enrichment.py:38`
- **description:** |
  El módulo importa `json` pero está marcado como no utilizado con comentario "se mantiene por compatibilidad si se usa en futuras extensiones". Esto es código muerto.
- **current_behavior:** |
  ```python
  import json  # noqa: F401  # se mantiene por compatibilidad si se usa en futuras extensiones
  ```
- **expected_behavior:** |
  Eliminar el import si realmente no se usa, o moverlo a donde se necesite cuando se implemente la funcionalidad.
- **proposed_solution:** |
  Verificar que `json` no se usa en ninguna parte del módulo. Eliminar si no se necesita. Si se necesita en el futuro, añadirlo cuando se implemente.
- **related_issues:** None
- **related_docs:** `docs/GITHUB_ISSUES_AUDIT_RECIENTE.md` #3
- **estimated_effort:** 5 minutos
- **acceptance_criteria:**
  - [ ] Import eliminado o justificado
  - [ ] Código limpio sin `# noqa` innecesarios
- **source:** `docs/GITHUB_ISSUES_AUDIT_RECIENTE.md` #3

---

#### C4-C24. Otros Issues de Calidad de Código
*(Ver `docs/CODE_AUDIT_ISSUES.md` para detalles completos de issues C4-C24)*

- **C4:** Falta Type Hints Completos
- **C5:** Manejo Inconsistente de Valores Nulos
- **C6:** Falta Validación de Esquema en `prepare_renta_barrio`
- **C7:** Cache TTL Hardcodeado en `data_loader.py`
- **C8:** Falta Manejo de Conexiones SQLite en Context Managers
- **C9:** F-Strings en SQL Queries (Aunque con Parámetros)
- **C10:** Falta Validación de Años Disponibles en UI
- **C11:** Magic Numbers en Cálculos
- **C12:** Falta Logging de Métricas de Calidad de Datos
- **C13:** Inconsistencia en Nombres de Columnas de Renta
- **C14:** Falta Documentación de Estrategias de Deduplicación
- **C15:** Falta Manejo de Encoding en `_load_portaldades_csv`
- **C16-C24:** Issues menores de calidad (ver `docs/CODE_AUDIT_ISSUES.md`)

---

### D. Refactorings Pendientes (Priority: Medium)

#### D1. Refactor: Eliminar Código Legacy `data_extraction.py`
- **id:** D1
- **title:** "🟡 [REFACTOR] Eliminar código legacy `data_extraction.py` después de migración completa"
- **category:** D
- **priority:** medium
- **labels:** `refactoring`, `technical-debt`, `cleanup`
- **related_issues:** A1
- **estimated_effort:** 2-3 horas
- **source:** `docs/CODE_AUDIT_ISSUES.md` #1

---

#### D2-D5. Otros Refactorings
*(Ver `docs/CODE_AUDIT_ISSUES.md` y `docs/GITHUB_ISSUES.md` para detalles)*

- **D2:** Refactor: Modularización de `data_processing.py` → `src/etl/transformations/` (Issue #42, #43)
- **D3:** Refactor: Limpiar orquestador Pipeline (Issue #43)
- **D4:** Refactor: Dividir funciones muy largas (>100 líneas)
- **D5:** Refactor: Reducir acoplamiento entre componentes

---

### E. Features Incompletas (Priority: Varies)

#### E1. INEExtractor Incompleto
- **id:** E1
- **title:** "🟡 [FEATURE] Completar implementación de `INEExtractor`"
- **category:** E
- **priority:** medium
- **labels:** `feature`, `extraction`, `ine`
- **description:** |
  `INEExtractor` sigue en versión base. No se han automatizado las descargas de precios históricos nacionales.
- **related_issues:** Issue #9 (ISSUES_TO_CREATE.md)
- **estimated_effort:** 4-6 horas
- **source:** `docs/PROJECT_STATUS.md` #5, `docs/ISSUES_TO_CREATE.md` #9

---

#### E2-E7. Otras Features Incompletas
*(Ver documentación existente)*

- **E2:** Idealista scraping completo (Issue #10)
- **E3:** Sistema de actualización periódica automatizada (Issue #11)
- **E4:** Paralelización de extracción (Issue #12)
- **E5:** Dashboard Streamlit completo (Issue #9, #7)
- **E6:** Funciones de análisis básicas (Issue #6)
- **E7:** Case studies por barrios (Issue #8)

---

### F. Datos Faltantes (Priority: High-Medium)

#### F1. fact_oferta_idealista Vacía
- **id:** F1
- **title:** "🔴 [DATA] `fact_oferta_idealista` está completamente vacía (0 registros)"
- **category:** F
- **priority:** high
- **labels:** `data`, `idealista`, `extraction`
- **description:** |
  Tabla existe pero está completamente vacía. Requiere ejecutar discovery script y extracción.
- **related_issues:** Issue #38 (Sprint 1)
- **estimated_effort:** 2-3 horas
- **source:** `docs/DATOS_FALTANTES.md` #1

---

#### F2-F5. Otros Datos Faltantes
*(Ver `docs/DATOS_FALTANTES.md` para detalles)*

- **F2:** Cobertura temporal limitada de `fact_renta` (solo 1 año)
- **F3:** Datos de alquiler incompletos en `fact_precios` (17.4% de registros)
- **F4:** Campos NULL menores en `fact_demografia` (`porc_inmigracion`: 3.0%)
- **F5:** Geometrías faltantes (aunque según PROJECT_STATUS.md ya están cargadas)

---

### G. Testing (Priority: High)

#### G1. Tests Marcados como Skip en `test_pipeline.py`
- **id:** G1
- **title:** "🟡 [TEST] 5 tests marcados como skip en `test_pipeline.py`"
- **category:** G
- **priority:** high
- **labels:** `testing`, `etl`, `coverage`
- **affected_files:**
  - `tests/test_pipeline.py:117, 141, 179, 209, 249`
- **description:** |
  Múltiples tests están marcados con `@pytest.mark.skip` porque requieren datos con estructura exacta del esquema real.
- **related_issues:** Issue #20, #40, #37
- **estimated_effort:** 4-6 horas
- **source:** `docs/GITHUB_ISSUES_AUDIT_RECIENTE.md` #5

---

#### G2-G12. Otros Issues de Testing
*(Ver `docs/CODE_AUDIT_ISSUES.md` y `docs/GITHUB_ISSUES.md`)*

- **G2:** Cobertura baja en módulos críticos (~60% estimado)
- **G3:** Tests de integración faltantes para pipeline ETL
- **G4:** Falta tests para funciones de `data_processing.py`
- **G5-G12:** Otros issues de testing (ver documentación)

---

### H. Documentación (Priority: Low-Medium)

#### H1-H8. Issues de Documentación
*(Ver `docs/CODE_AUDIT_ISSUES.md` y `docs/NEXT_STEPS.md`)*

- **H1:** Docstrings faltantes en algunas funciones
- **H2:** README incompleto
- **H3:** Documentación desactualizada
- **H4:** Ejemplos de uso faltantes
- **H5:** Falta documentación de API de funciones públicas
- **H6:** Falta documentación de estrategias de deduplicación
- **H7:** Falta documentación de rate limits por fuente
- **H8:** Documentación de esquema de base de datos incompleta

---

### I. DevOps/CI-CD (Priority: Medium)

#### I1. Workflow dashboard-demo sin Validación de Puerto
- **id:** I1
- **title:** "🟢 [CI-CD] Workflow `dashboard-demo.yml` sin validación de puerto"
- **category:** I
- **priority:** low
- **labels:** `ci-cd`, `workflow`, `validation`
- **affected_files:**
  - `.github/workflows/dashboard-demo.yml:10-14, 38`
- **description:** |
  El workflow acepta un puerto como input string pero no valida que esté en un rango válido (1024-65535).
- **estimated_effort:** 20 minutos
- **source:** `docs/GITHUB_ISSUES_AUDIT_RECIENTE.md` #8

---

#### I2. Workflow kpi-update con Manejo de Errores Genérico
- **id:** I2
- **title:** "🟢 [CI-CD] Workflow `kpi-update.yml` usa bare `except:`"
- **category:** I
- **priority:** low
- **labels:** `ci-cd`, `workflow`, `code-quality`
- **affected_files:**
  - `.github/workflows/kpi-update.yml:48`
- **description:** |
  El workflow usa `except:` sin especificar tipo de excepción, lo que es una mala práctica.
- **estimated_effort:** 15 minutos
- **source:** `docs/GITHUB_ISSUES_AUDIT_RECIENTE.md` #9

---

#### I3-I4. Otros Issues de DevOps
- **I3:** Falta validaciones de puerto/parámetros en workflows
- **I4:** Scripts de deployment faltantes

---

### J. Performance (Priority: Low)

#### J1-J8. Issues de Performance
*(Ver `docs/CODE_AUDIT_ISSUES.md`)*

- **J1:** Optimización de queries SQL
- **J2:** Falta compresión de archivos raw grandes
- **J3:** Falta validación de tamaño de archivos antes de cargar
- **J4-J8:** Otros issues de performance menores

---

## 🗺️ Roadmap Sugerido

### Sprint 1 (Próximas 2 Semanas) - Quick Wins y Bugs Críticos

**Objetivo:** Estabilizar base del proyecto y resolver issues críticas

#### Semana 1:
1. ✅ **A4:** Registrar `IncasolSocrataExtractor` (15 min)
2. ✅ **A5:** Reemplazar `print()` por logger (10 min)
3. ✅ **A2:** Validación SQL injection en `data_loader.py` (20 min)
4. ✅ **A3:** Validación SQL injection en `database_setup.py` (15 min)
5. ✅ **I2:** Corregir workflow `kpi-update.yml` (15 min)
6. ✅ **C3:** Eliminar import no utilizado (5 min)
7. ✅ **B2:** Corregir pipes duplicados automáticamente (30 min)
8. ✅ **B6:** Manejo de errores en `build_geojson` (20 min)

**Total estimado:** ~2 horas

#### Semana 2:
1. ✅ **A6:** Validación de integridad referencial (2-3 horas)
2. ✅ **B1:** Eliminar hardcoding de año 2022 (2-3 horas)
3. ✅ **B3:** Validación de años en Portal de Dades (1 hora)
4. ✅ **B4:** Validación de estructura manifest.json (1 hora)
5. ✅ **B7:** Validación de DataFrame vacío (2-3 horas)

**Total estimado:** ~8-11 horas

---

### Sprint 2 (Siguientes 2 Semanas) - Refactoring y Testing

**Objetivo:** Mejorar calidad de código y cobertura de tests

1. ✅ **A1:** Auditar y eliminar código duplicado `data_extraction.py` (8-12 horas)
2. ✅ **C1:** Mejorar manejo de errores en `enrichment.py` (1-2 horas)
3. ✅ **C2:** Clasificar errores críticos vs. opcionales en pipeline (3-4 horas)
4. ✅ **G1:** Habilitar tests skipeados en `test_pipeline.py` (4-6 horas)
5. ✅ **B5:** Completar lógica de `prepare_idealista_oferta` (1 hora)
6. ✅ **B8:** Validación de rangos temporales (1 hora)

**Total estimado:** ~18-26 horas

---

### Backlog (Resto) - Features y Mejoras

#### Prioridad Alta:
- **F1:** Completar `fact_oferta_idealista` (2-3 horas)
- **F2:** Ampliar cobertura temporal de `fact_renta` (1-2 horas)
- **E1:** Completar `INEExtractor` (4-6 horas)
- **G2-G4:** Mejorar cobertura de tests (8-12 horas)

#### Prioridad Media:
- **E5:** Dashboard Streamlit completo (6-8 horas)
- **E6:** Funciones de análisis básicas (4-6 horas)
- **H1-H8:** Mejorar documentación (6-8 horas)
- **C4-C24:** Mejoras de calidad de código (10-15 horas)

#### Prioridad Baja:
- **J1-J8:** Optimizaciones de performance (8-12 horas)
- **E2-E4:** Features futuras (12-20 horas)

---

## 📈 Métricas de Salud del Proyecto

### Código
- **Líneas de código:** ~15,000+ (estimado)
- **Código duplicado:** ~2000 líneas (🔴 Alto)
- **Complejidad ciclomática:** 🟡 Media-Alta en algunas funciones
- **% de funciones con docstrings:** ~70% (🟡 Medio)
- **% de funciones con type hints:** ~80% (🟢 Bueno)

### Testing
- **Cobertura de tests:** ~60% (🟡 Medio)
- **Tests skipeados:** 5 tests críticos
- **Tests de integración:** ⚠️ Faltantes para pipeline ETL

### Calidad
- **TODOs/FIXMEs en código:** ~20+ (🟡 Medio)
- **Bare exceptions:** ~147 instancias (🔴 Alto)
- **Imports no utilizados:** ~5-10 (🟢 Bajo)
- **Linter errors:** ✅ Sin errores

### Deuda Técnica
- **Estimada:** ~150-200 horas
- **Crítica:** ~40 horas (bugs críticos y código duplicado)
- **Importante:** ~60 horas (refactorings y testing)
- **Mejoras:** ~50-100 horas (features y optimizaciones)

---

## 🎯 Conclusiones y Recomendaciones

### Prioridades Inmediatas:
1. **Resolver bugs críticos** (A1-A6) antes de nuevas features
2. **Eliminar código duplicado** para reducir confusión y mantenimiento
3. **Mejorar manejo de errores** para facilitar debugging
4. **Aumentar cobertura de tests** para prevenir regresiones

### Quick Wins Recomendados:
- Registrar `IncasolSocrataExtractor` (5 min)
- Eliminar import no utilizado (5 min)
- Corregir workflows CI-CD (30 min)
- Validaciones SQL injection (35 min)

**Total Quick Wins:** ~1.5 horas para resolver 4 issues críticas

### Riesgos Identificados:
1. **Código duplicado:** Alto riesgo de inconsistencias
2. **Manejo de errores genérico:** Dificulta debugging
3. **Tests skipeados:** Regresiones pueden pasar desapercibidas
4. **Datos faltantes:** Limita análisis y funcionalidades

### Próximos Pasos:
1. Crear GitHub Issues para todas las issues identificadas
2. Priorizar según roadmap sugerido
3. Asignar a sprints según capacidad del equipo
4. Actualizar este documento cuando se resuelvan issues

---

**Última actualización:** 2025-12-02  
**Próxima revisión recomendada:** 2025-12-16 (después de Sprint 1)

