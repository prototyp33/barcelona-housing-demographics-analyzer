# GitHub Issues - Audit de Archivos Recientes

**Fecha:** 2025-12-01  
**Alcance:** Archivos recientes del proyecto (transformaciones ETL, pipeline, extracción, workflows)

---

## Issues Nuevos Identificados

### Issue 1: Bug en regex de `_parse_household_size` (utils.py)

**Severidad:** 🟡 Media  
**Etiquetas:** `bug`, `etl`, `data-processing`, `priority-medium`

**Descripción:**

La función `_parse_household_size` en `src/etl/transformations/utils.py` usa un regex con doble backslash (`r"\\d+"`) cuando debería usar un solo backslash (`r"\d+"`). En Python raw strings, el doble backslash puede causar que el regex no funcione correctamente.

**Archivo afectado:**
- `src/etl/transformations/utils.py:46, 52, 58`

**Código problemático:**
```python
if normalized.startswith(">"):
    digits = re.findall(r"\\d+", normalized)  # ❌ Doble backslash
```

**Impacto:**
- Puede fallar al parsear tamaños de hogar que contengan números
- Afecta el cálculo de métricas de hogares en `enrich_fact_demografia`

**Solución propuesta:**
```python
if normalized.startswith(">"):
    digits = re.findall(r"\d+", normalized)  # ✅ Backslash simple
```

**Pasos para resolver:**
- [ ] Corregir regex en línea 46
- [ ] Corregir regex en línea 52  
- [ ] Corregir regex en línea 58
- [ ] Añadir test unitario que verifique parsing de tamaños de hogar con números

---

### Issue 2: Manejo de errores genérico en `enrichment.py`

**Severidad:** 🟡 Media  
**Etiquetas:** `code-quality`, `etl`, `priority-medium`

**Descripción:**

Múltiples bloques `except Exception` en `src/etl/transformations/enrichment.py` capturan excepciones muy amplias sin especificar tipos concretos, lo que dificulta el debugging y puede ocultar errores inesperados.

**Archivos afectados:**
- `src/etl/transformations/enrichment.py:52` (carga de metadatos)
- `src/etl/transformations/enrichment.py:164` (procesamiento de CSV)

**Código problemático:**
```python
except Exception as exc:  # noqa: BLE001
    logger.warning("Error cargando metadatos: %s", exc)
```

**Impacto:**
- Errores críticos pueden ser tratados como warnings
- Dificulta identificar la causa raíz de fallos
- No sigue las mejores prácticas del proyecto (ver CODE_AUDIT_ISSUES.md #6)

**Solución propuesta:**
```python
except (FileNotFoundError, pd.errors.ParserError, json.JSONDecodeError) as exc:
    logger.warning("Error cargando metadatos: %s", exc, exc_info=True)
except Exception as exc:
    logger.error("Error inesperado cargando metadatos: %s", exc, exc_info=True)
    raise
```

**Pasos para resolver:**
- [ ] Identificar tipos de excepciones específicos para cada bloque try/except
- [ ] Reemplazar `except Exception` por tipos concretos donde sea posible
- [ ] Añadir `exc_info=True` a logs de errores
- [ ] Evaluar si algunos errores deberían detener el pipeline en lugar de continuar

---

### Issue 3: Import no utilizado en `enrichment.py`

**Severidad:** 🟢 Baja  
**Etiquetas:** `code-quality`, `cleanup`, `priority-low`

**Descripción:**

El módulo `src/etl/transformations/enrichment.py` importa `json` pero está marcado como no utilizado (`# noqa: F401`) con el comentario "se mantiene por compatibilidad si se usa en futuras extensiones". Esto es código muerto que debería eliminarse o documentarse mejor.

**Archivo afectado:**
- `src/etl/transformations/enrichment.py:38`

**Código problemático:**
```python
import json  # noqa: F401  # se mantiene por compatibilidad si se usa en futuras extensiones
```

**Impacto:**
- Código muerto que confunde a linters y desarrolladores
- Import innecesario aumenta tiempo de carga del módulo

**Solución propuesta:**
- Opción 1: Eliminar el import si realmente no se usa
- Opción 2: Si se planea usar en el futuro, moverlo a donde se necesite cuando se implemente

**Pasos para resolver:**
- [ ] Verificar que `json` no se usa en ninguna parte del módulo
- [ ] Eliminar el import si no se necesita
- [ ] Si se necesita en el futuro, añadirlo cuando se implemente la funcionalidad

---

### Issue 4: Validación faltante en `prepare_fact_precios` para pipes duplicados

**Severidad:** 🟡 Media  
**Etiquetas:** `bug`, `etl`, `data-quality`, `priority-medium`

**⚠️ Relacionada con:** Issue #13 "Fix: Deduplicación agresiva en fact_precios"

**Descripción:**

La función `prepare_fact_precios` detecta pipes duplicados (`|`) en las columnas `source` y `dataset_id` pero solo loguea un error sin corregir el problema. Aunque existe la función `_normalize_pipe_tags` que puede normalizar estos valores, no se aplica automáticamente cuando se detecta el problema.

**Archivo afectado:**
- `src/etl/transformations/market.py:243-252`

**Código problemático:**
```python
if fact["source"].astype(str).str.contains(r"\\|").any():
    logger.error(
        "⚠️ ALERTA: Se detectaron pipes '|' en columna 'source'. "
        "Esto indica un problema de agregación upstream.",
    )
# Solo loguea error, no corrige
```

**Impacto:**
- Datos con pipes duplicados pueden persistir en la base de datos
- Puede causar problemas en consultas y análisis posteriores
- La función `_normalize_pipe_tags` ya existe pero no se aplica aquí

**Solución propuesta:**
```python
# Aplicar normalización automáticamente después de detectar el problema
if fact["source"].astype(str).str.contains(r"\\|").any():
    logger.warning(
        "Se detectaron pipes duplicados en 'source'. Normalizando automáticamente."
    )
    fact["source"] = fact["source"].apply(_normalize_pipe_tags)
```

**Pasos para resolver:**
- [ ] Aplicar `_normalize_pipe_tags` automáticamente cuando se detecten pipes duplicados
- [ ] Cambiar log level de ERROR a WARNING si se corrige automáticamente
- [ ] Añadir test que verifique la corrección automática de pipes duplicados
- [ ] Documentar el comportamiento en docstring de la función

---

### Issue 5: Tests marcados como skip en `test_pipeline.py`

**Severidad:** 🟡 Media  
**Etiquetas:** `testing`, `etl`, `priority-medium`

**⚠️ Relacionada con:** Issue #20 "Task: Testing - Unit e Integration Tests", Issue #40 "Tests de integración para pipeline ETL"

**Descripción:**

Múltiples tests en `tests/test_pipeline.py` están marcados con `@pytest.mark.skip` porque requieren datos con estructura exacta del esquema real. Esto reduce la cobertura de tests y puede ocultar regresiones.

**Archivo afectado:**
- `tests/test_pipeline.py:117, 141, 179, 209, 249`

**Tests afectados:**
- `test_etl_creates_database` (línea 117)
- `test_etl_creates_dim_barrios` (línea 141)
- `test_etl_creates_fact_precios` (línea 179)
- `test_etl_creates_fact_demografia` (línea 209)
- `test_etl_registers_run` (línea 249)

**Problema:**
```python
@pytest.mark.skip(reason="Requiere datos con estructura exacta del esquema real.")
def test_etl_creates_database(raw_data_structure: Dict[str, Path]) -> None:
```

**Impacto:**
- Cobertura de tests reducida para el pipeline ETL crítico
- Regresiones pueden pasar desapercibidas
- Fixtures de prueba no son suficientemente robustos

**Solución propuesta:**
- Crear fixtures más robustos que generen datos con estructura válida
- O documentar claramente cómo generar datos de prueba válidos
- O crear tests de integración separados que usen datos reales (más lentos pero más completos)

**Pasos para resolver:**
- [ ] Revisar fixtures existentes en `test_pipeline.py`
- [ ] Crear fixtures que generen datos con estructura exacta del esquema
- [ ] Actualizar tests para usar fixtures mejorados
- [ ] Remover `@pytest.mark.skip` cuando los tests pasen
- [ ] Documentar cómo generar datos de prueba válidos si es necesario

---

### Issue 6: Manejo de errores silencioso en `pipeline.py`

**Severidad:** 🟡 Media  
**Etiquetas:** `code-quality`, `etl`, `error-handling`, `priority-medium`

**⚠️ Relacionada con:** Issue #43 "Refactor: Limpiar orquestador Pipeline"

**Descripción:**

Múltiples bloques `try/except` en `src/etl/pipeline.py` solo loguean warnings pero continúan la ejecución del pipeline, incluso cuando algunos errores podrían ser críticos y deberían detener el proceso.

**Archivo afectado:**
- `src/etl/pipeline.py` (múltiples ubicaciones)

**Ubicaciones problemáticas:**
- Línea 252: Error cargando datos de renta
- Línea 310: Error procesando demografía ampliada
- Línea 363: Error procesando Portal de Dades
- Línea 394: Error procesando renta
- Línea 410: Error cargando Idealista venta
- Línea 421: Error cargando Idealista alquiler
- Línea 438: Error procesando oferta Idealista

**Código problemático:**
```python
try:
    renta_df = _safe_read_csv(renta_path)
    logger.info("✓ Datos de renta cargados: %s", renta_path.name)
except Exception as e:
    logger.warning("Error cargando datos de renta: %s", e)
    # Continúa ejecución sin datos de renta
```

**Impacto:**
- Errores críticos pueden pasar desapercibidos
- Pipeline puede completarse "exitosamente" con datos incompletos
- Dificulta debugging de problemas de datos

**Solución propuesta:**
- Clasificar errores en críticos vs. opcionales
- Errores críticos (ej: demografía base) deberían detener el pipeline
- Errores opcionales (ej: Idealista, Portal de Dades) pueden continuar con warning
- Añadir flag `--strict` para pipeline que falle en cualquier error

**Pasos para resolver:**
- [ ] Clasificar cada fuente de datos como crítica u opcional
- [ ] Modificar manejo de errores para fuentes críticas (raise en lugar de warning)
- [ ] Mantener warnings para fuentes opcionales pero mejorar logging
- [ ] Añadir `exc_info=True` a todos los logs de errores
- [ ] Documentar qué fuentes son críticas vs. opcionales

---

### Issue 7: Falta validación de años en datos de Portal de Dades

**Severidad:** 🟡 Media  
**Etiquetas:** `bug`, `etl`, `data-quality`, `priority-medium`

**⚠️ Relacionada con:** Issue #15 "Improvement: Mejorar mapeo de territorios Portal de Dades"

**Descripción:**

La función `_extract_year_from_temps` puede retornar `None` cuando falla el parsing de fechas, pero este valor no se valida antes de usarse en agrupaciones y operaciones que requieren años válidos.

**Archivo afectado:**
- `src/etl/transformations/enrichment.py:112`
- `src/etl/transformations/utils.py:114-120` (función `_extract_year_from_temps`)

**Código problemático:**
```python
df["anio"] = df["Dim-00:TEMPS"].apply(_extract_year_from_temps)
df = df.dropna(subset=["anio", "VALUE"])  # ✅ Esto está bien
# Pero en otros lugares puede no validarse:
df.groupby(["anio", ...])  # ❌ Puede fallar si hay None
```

**Impacto:**
- Puede causar errores en agrupaciones por año si hay valores None
- Datos con fechas inválidas pueden ser procesados incorrectamente
- Puede causar errores silenciosos en cálculos temporales

**Solución propuesta:**
- Validar que `anio` no sea None antes de agrupar
- Añadir logging cuando se descarten registros por año inválido
- Documentar comportamiento esperado cuando `_extract_year_from_temps` retorna None

**Pasos para resolver:**
- [ ] Revisar todos los usos de `_extract_year_from_temps`
- [ ] Asegurar que siempre se valida `dropna(subset=["anio"])` antes de agrupar
- [ ] Añadir logging cuando se descarten registros por año inválido
- [ ] Añadir test que verifique manejo de años inválidos

---

### Issue 8: Workflow de dashboard-demo sin validación de puerto

**Severidad:** 🟢 Baja  
**Etiquetas:** `ci-cd`, `workflow`, `priority-low`

**Descripción:**

El workflow `.github/workflows/dashboard-demo.yml` acepta un puerto como input string pero no valida que esté en un rango válido (1024-65535) antes de usarlo.

**Archivo afectado:**
- `.github/workflows/dashboard-demo.yml:10-14, 38`

**Código problemático:**
```yaml
inputs:
  port:
    description: 'Streamlit port (default 8501)'
    required: false
    default: '8501'
    type: string  # ❌ No valida rango
```

**Impacto:**
- Puertos inválidos pueden causar fallos en el workflow
- Puertos privilegiados (<1024) pueden causar errores de permisos
- Puertos fuera de rango pueden causar errores de conexión

**Solución propuesta:**
```yaml
- name: Validate port
  run: |
    PORT="${{ inputs.port }}"
    if ! [[ "$PORT" =~ ^[0-9]+$ ]] || [ "$PORT" -lt 1024 ] || [ "$PORT" -gt 65535 ]; then
      echo "Error: Port must be between 1024 and 65535"
      exit 1
    fi
```

**Pasos para resolver:**
- [ ] Añadir step de validación de puerto antes de iniciar Streamlit
- [ ] Validar que el puerto sea numérico y esté en rango válido
- [ ] Añadir mensaje de error claro si el puerto es inválido
- [ ] Documentar rango válido en la descripción del input

---

### Issue 9: Workflow kpi-update con manejo de errores genérico

**Severidad:** 🟢 Baja  
**Etiquetas:** `ci-cd`, `workflow`, `code-quality`, `priority-low`

**Descripción:**

El workflow `.github/workflows/kpi-update.yml` usa `except:` sin especificar tipo de excepción, lo que es una mala práctica y puede ocultar errores inesperados.

**Archivo afectado:**
- `.github/workflows/kpi-update.yml:48`

**Código problemático:**
```python
try:
    with open('$FILE', 'r') as f:
        data = json.load(f)
except:  # ❌ Bare except
    data = {"kpis": []}
```

**Impacto:**
- Puede capturar excepciones críticas (KeyboardInterrupt, SystemExit)
- Dificulta debugging de errores reales
- No sigue mejores prácticas de Python

**Solución propuesta:**
```python
except (json.JSONDecodeError, FileNotFoundError) as e:
    logger.warning("Error cargando KPI progress, inicializando vacío: %s", e)
    data = {"kpis": []}
```

**Pasos para resolver:**
- [ ] Especificar tipos de excepciones concretos (`json.JSONDecodeError`, `FileNotFoundError`)
- [ ] Añadir logging del error para debugging
- [ ] Evaluar si otros errores deberían propagarse

---

### Issue 10: Falta validación de estructura de manifest.json

**Severidad:** 🟡 Media  
**Etiquetas:** `bug`, `etl`, `data-quality`, `priority-medium`

**Descripción:**

La función `_load_manifest` en `src/etl/pipeline.py` carga el archivo JSON pero no valida que tenga la estructura esperada (lista de diccionarios con campos específicos). Esto puede causar fallos silenciosos si el manifest tiene estructura incorrecta.

**Archivo afectado:**
- `src/etl/pipeline.py:45-67`

**Código problemático:**
```python
def _load_manifest(raw_dir: Path) -> List[Dict[str, object]]:
    manifest_path = raw_dir / "manifest.json"
    if not manifest_path.exists():
        return []
    
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)  # ❌ No valida estructura
        return manifest
```

**Impacto:**
- Manifest con estructura incorrecta puede causar errores en tiempo de ejecución
- Errores pueden ser difíciles de debuggear si el manifest está malformado
- Puede causar fallos silenciosos en descubrimiento de archivos

**Solución propuesta:**
```python
def _load_manifest(raw_dir: Path) -> List[Dict[str, object]]:
    manifest_path = raw_dir / "manifest.json"
    if not manifest_path.exists():
        return []
    
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        # Validar estructura
        if not isinstance(manifest, list):
            logger.error("Manifest debe ser una lista, encontrado: %s", type(manifest))
            return []
        
        # Validar que cada entrada tenga campos mínimos
        required_fields = {"file_path", "type"}
        for i, entry in enumerate(manifest):
            if not isinstance(entry, dict):
                logger.warning("Entrada %d del manifest no es un diccionario", i)
                continue
            missing = required_fields - set(entry.keys())
            if missing:
                logger.warning("Entrada %d del manifest falta campos: %s", i, missing)
        
        return manifest
    except json.JSONDecodeError as e:
        logger.error("Error parseando manifest.json: %s", e)
        return []
```

**Pasos para resolver:**
- [ ] Añadir validación de tipo (debe ser lista)
- [ ] Validar campos requeridos en cada entrada del manifest
- [ ] Añadir logging claro cuando el manifest tiene estructura incorrecta
- [ ] Añadir test que verifique validación de manifest inválido

---

### Issue 11: Función `prepare_idealista_oferta` con lógica incompleta

**Severidad:** 🟡 Media  
**Etiquetas:** `bug`, `etl`, `code-quality`, `priority-medium`

**Descripción:**

La función `prepare_idealista_oferta` calcula `num_anuncios_tipologia` agrupando por tipología pero no incluye este resultado en el DataFrame final. El resultado se asigna a `_` (descartado), lo que es código muerto.

**Archivo afectado:**
- `src/etl/transformations/enrichment.py:277-283`

**Código problemático:**
```python
if "tipologia" in df.columns:
    _ = (  # ❌ Resultado descartado
        df.groupby(group_cols + ["tipologia"])
        .size()
        .reset_index(name="num_anuncios_tipologia")
    )

aggregated = df.groupby(group_cols).agg(agg_dict).reset_index()
# num_anuncios_tipologia no se incluye en aggregated
```

**Impacto:**
- Código muerto que confunde a desarrolladores
- Información útil (distribución por tipología) se calcula pero no se usa
- Puede indicar funcionalidad incompleta o abandonada

**Solución propuesta:**
- Opción 1: Eliminar el código si no se necesita
- Opción 2: Incluir `num_anuncios_tipologia` en el resultado agregado si es útil

**Pasos para resolver:**
- [ ] Evaluar si `num_anuncios_tipologia` es información útil para análisis
- [ ] Si es útil: incluir en el DataFrame agregado (pivot o agregación adicional)
- [ ] Si no es útil: eliminar el código muerto
- [ ] Documentar decisión en comentario o docstring

---

## Issues Ya Documentados (Referencias)

Los siguientes issues ya están documentados en `docs/CODE_AUDIT_ISSUES.md` y no requieren nuevas issues:

- **Issue 5 del plan:** Hardcoding de año 2022 en `main.py` → Ver CODE_AUDIT_ISSUES.md #7 y #15
- **Issue 6 del plan:** Falta validación de integridad referencial → Ver CODE_AUDIT_ISSUES.md #8
- **Issue 10 del plan:** Lógica de deduplicación sin documentación → Ver CODE_AUDIT_ISSUES.md #22
- **Issue 11 del plan:** Falta manejo de encoding fallback → Ver CODE_AUDIT_ISSUES.md #23

## Issues Relacionadas en GitHub

Los siguientes issues existentes en GitHub están relacionadas con algunos de los problemas identificados:

- **Issue #13:** "Fix: Deduplicación agresiva en fact_precios" → Relacionada con Issue 4 (validación de pipes)
- **Issue #14:** "Feature: Completar campos demográficos faltantes" → Relacionada con enriquecimiento de datos
- **Issue #15:** "Improvement: Mejorar mapeo de territorios Portal de Dades" → Relacionada con Issue 7 (validación de años)
- **Issue #20:** "Task: Testing - Unit e Integration Tests" → Relacionada con Issue 5 (tests marcados como skip)
- **Issue #40, #37:** "Tests de integración para pipeline ETL" → Relacionada con Issue 5
- **Issue #43:** "Refactor: Limpiar orquestador Pipeline" → Relacionada con Issue 6 (manejo de errores)

---

## Resumen de Priorización

### 🔴 Alta Prioridad
- Ninguno (todos los críticos ya están documentados)

### 🟡 Media Prioridad
1. Issue 1: Bug en regex de `_parse_household_size`
2. Issue 2: Manejo de errores genérico en `enrichment.py`
3. Issue 4: Validación faltante en `prepare_fact_precios`
4. Issue 5: Tests marcados como skip
5. Issue 6: Manejo de errores silencioso en `pipeline.py`
6. Issue 7: Falta validación de años en Portal de Dades
7. Issue 10: Falta validación de estructura de manifest.json
8. Issue 11: Función `prepare_idealista_oferta` con lógica incompleta

### 🟢 Baja Prioridad
1. Issue 3: Import no utilizado en `enrichment.py`
2. Issue 8: Workflow dashboard-demo sin validación de puerto
3. Issue 9: Workflow kpi-update con manejo de errores genérico

---

## Próximos Pasos

1. Crear GitHub Issues para cada issue nuevo usando `gh issue create`
2. Asignar etiquetas y prioridades según la clasificación
3. Referenciar issues relacionadas cuando aplique
4. Actualizar este documento cuando los issues sean creados

