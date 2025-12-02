#!/usr/bin/env bash

set -euo pipefail

# Script para crear GitHub Issues desde el audit de archivos recientes
# Basado en sync_issues.sh del proyecto

current_user="@me"

#
# Issue 1: Bug en regex de _parse_household_size
#
gh issue create \
  --title "🐛 Bug en regex de _parse_household_size (utils.py)" \
  --label "bug" \
  --label "etl" \
  --label "data-processing" \
  --label "priority-medium" \
  --assignee "${current_user}" \
  --body '
### 📌 Descripción

La función `_parse_household_size` en `src/etl/transformations/utils.py` usa un regex con doble backslash (`r"\\d+"`) cuando debería usar un solo backslash (`r"\d+"`). En Python raw strings, el doble backslash puede causar que el regex no funcione correctamente.

### 🔍 Archivos Afectados

- `src/etl/transformations/utils.py:46, 52, 58`

### 💻 Código Problemático

```python
if normalized.startswith(">"):
    digits = re.findall(r"\\d+", normalized)  # ❌ Doble backslash
```

### ⚠️ Impacto

- Puede fallar al parsear tamaños de hogar que contengan números
- Afecta el cálculo de métricas de hogares en `enrich_fact_demografia`

### ✅ Solución Propuesta

```python
if normalized.startswith(">"):
    digits = re.findall(r"\d+", normalized)  # ✅ Backslash simple
```

### 📝 Pasos para Resolver

- [ ] Corregir regex en línea 46
- [ ] Corregir regex en línea 52  
- [ ] Corregir regex en línea 58
- [ ] Añadir test unitario que verifique parsing de tamaños de hogar con números

### 🔗 Issues Relacionadas

- Relacionada con: cálculo de métricas demográficas y enriquecimiento de datos
- Conecta con: Issue #14 "Feature: Completar campos demográficos faltantes"
'

#
# Issue 2: Manejo de errores genérico en enrichment.py
#
gh issue create \
  --title "🔧 Mejorar manejo de errores genérico en enrichment.py" \
  --label "code-quality" \
  --label "etl" \
  --label "priority-medium" \
  --assignee "${current_user}" \
  --body '
### 📌 Descripción

Múltiples bloques `except Exception` en `src/etl/transformations/enrichment.py` capturan excepciones muy amplias sin especificar tipos concretos, lo que dificulta el debugging y puede ocultar errores inesperados.

### 🔍 Archivos Afectados

- `src/etl/transformations/enrichment.py:52` (carga de metadatos)
- `src/etl/transformations/enrichment.py:164` (procesamiento de CSV)

### 💻 Código Problemático

```python
except Exception as exc:  # noqa: BLE001
    logger.warning("Error cargando metadatos: %s", exc)
```

### ⚠️ Impacto

- Errores críticos pueden ser tratados como warnings
- Dificulta identificar la causa raíz de fallos
- No sigue las mejores prácticas del proyecto (ver CODE_AUDIT_ISSUES.md #6)

### ✅ Solución Propuesta

```python
except (FileNotFoundError, pd.errors.ParserError, json.JSONDecodeError) as exc:
    logger.warning("Error cargando metadatos: %s", exc, exc_info=True)
except Exception as exc:
    logger.error("Error inesperado cargando metadatos: %s", exc, exc_info=True)
    raise
```

### 📝 Pasos para Resolver

- [ ] Identificar tipos de excepciones específicos para cada bloque try/except
- [ ] Reemplazar `except Exception` por tipos concretos donde sea posible
- [ ] Añadir `exc_info=True` a logs de errores
- [ ] Evaluar si algunos errores deberían detener el pipeline en lugar de continuar

### 🔗 Issues Relacionadas

- Relacionada con: CODE_AUDIT_ISSUES.md #6 (Manejo de Errores Genérico)
- Conecta con: Issue #43 "Refactor: Limpiar orquestador Pipeline"
'

#
# Issue 3: Import no utilizado en enrichment.py
#
gh issue create \
  --title "🧹 Limpiar import no utilizado en enrichment.py" \
  --label "code-quality" \
  --label "cleanup" \
  --label "priority-low" \
  --assignee "${current_user}" \
  --body '
### 📌 Descripción

El módulo `src/etl/transformations/enrichment.py` importa `json` pero está marcado como no utilizado (`# noqa: F401`) con el comentario "se mantiene por compatibilidad si se usa en futuras extensiones". Esto es código muerto que debería eliminarse o documentarse mejor.

### 🔍 Archivos Afectados

- `src/etl/transformations/enrichment.py:38`

### 💻 Código Problemático

```python
import json  # noqa: F401  # se mantiene por compatibilidad si se usa en futuras extensiones
```

### ⚠️ Impacto

- Código muerto que confunde a linters y desarrolladores
- Import innecesario aumenta tiempo de carga del módulo

### ✅ Solución Propuesta

- Opción 1: Eliminar el import si realmente no se usa
- Opción 2: Si se planea usar en el futuro, moverlo a donde se necesite cuando se implemente

### 📝 Pasos para Resolver

- [ ] Verificar que `json` no se usa en ninguna parte del módulo
- [ ] Eliminar el import si no se necesita
- [ ] Si se necesita en el futuro, añadirlo cuando se implemente la funcionalidad
'

#
# Issue 4: Validación faltante en prepare_fact_precios
#
gh issue create \
  --title "🐛 Validación faltante en prepare_fact_precios para pipes duplicados" \
  --label "bug" \
  --label "etl" \
  --label "data-quality" \
  --label "priority-medium" \
  --assignee "${current_user}" \
  --body '
### 📌 Descripción

La función `prepare_fact_precios` detecta pipes duplicados (`|`) en las columnas `source` y `dataset_id` pero solo loguea un error sin corregir el problema. Aunque existe la función `_normalize_pipe_tags` que puede normalizar estos valores, no se aplica automáticamente cuando se detecta el problema.

### 🔍 Archivos Afectados

- `src/etl/transformations/market.py:243-252`

### 💻 Código Problemático

```python
if fact["source"].astype(str).str.contains(r"\\|").any():
    logger.error(
        "⚠️ ALERTA: Se detectaron pipes \"|\" en columna \"source\". "
        "Esto indica un problema de agregación upstream.",
    )
# Solo loguea error, no corrige
```

### ⚠️ Impacto

- Datos con pipes duplicados pueden persistir en la base de datos
- Puede causar problemas en consultas y análisis posteriores
- La función `_normalize_pipe_tags` ya existe pero no se aplica aquí

### ✅ Solución Propuesta

```python
# Aplicar normalización automáticamente después de detectar el problema
if fact["source"].astype(str).str.contains(r"\\|").any():
    logger.warning(
        "Se detectaron pipes duplicados en \"source\". Normalizando automáticamente."
    )
    fact["source"] = fact["source"].apply(_normalize_pipe_tags)
```

### 📝 Pasos para Resolver

- [ ] Aplicar `_normalize_pipe_tags` automáticamente cuando se detecten pipes duplicados
- [ ] Cambiar log level de ERROR a WARNING si se corrige automáticamente
- [ ] Añadir test que verifique la corrección automática de pipes duplicados
- [ ] Documentar el comportamiento en docstring de la función

### 🔗 Issues Relacionadas

- Relacionada con: Issue #13 "Fix: Deduplicación agresiva en fact_precios"
- Conecta con: problemas de deduplicación y calidad de datos en fact_precios
'

#
# Issue 5: Tests marcados como skip
#
gh issue create \
  --title "🧪 Habilitar tests marcados como skip en test_pipeline.py" \
  --label "testing" \
  --label "etl" \
  --label "priority-medium" \
  --assignee "${current_user}" \
  --body '
### 📌 Descripción

Múltiples tests en `tests/test_pipeline.py` están marcados con `@pytest.mark.skip` porque requieren datos con estructura exacta del esquema real. Esto reduce la cobertura de tests y puede ocultar regresiones.

### 🔍 Archivos Afectados

- `tests/test_pipeline.py:117, 141, 179, 209, 249`

### 📋 Tests Afectados

- `test_etl_creates_database` (línea 117)
- `test_etl_creates_dim_barrios` (línea 141)
- `test_etl_creates_fact_precios` (línea 179)
- `test_etl_creates_fact_demografia` (línea 209)
- `test_etl_registers_run` (línea 249)

### 💻 Código Problemático

```python
@pytest.mark.skip(reason="Requiere datos con estructura exacta del esquema real.")
def test_etl_creates_database(raw_data_structure: Dict[str, Path]) -> None:
```

### ⚠️ Impacto

- Cobertura de tests reducida para el pipeline ETL crítico
- Regresiones pueden pasar desapercibidas
- Fixtures de prueba no son suficientemente robustos

### ✅ Solución Propuesta

- Crear fixtures más robustos que generen datos con estructura válida
- O documentar claramente cómo generar datos de prueba válidos
- O crear tests de integración separados que usen datos reales (más lentos pero más completos)

### 📝 Pasos para Resolver

- [ ] Revisar fixtures existentes en `test_pipeline.py`
- [ ] Crear fixtures que generen datos con estructura exacta del esquema
- [ ] Actualizar tests para usar fixtures mejorados
- [ ] Remover `@pytest.mark.skip` cuando los tests pasen
- [ ] Documentar cómo generar datos de prueba válidos si es necesario

### 🔗 Issues Relacionadas

- Relacionada con: Issue #20 "Task: Testing - Unit e Integration Tests"
- Relacionada con: Issue #40 "Tests de integración para pipeline ETL"
- Conecta con: mejoras generales en cobertura de tests del proyecto
'

#
# Issue 6: Manejo de errores silencioso en pipeline.py
#
gh issue create \
  --title "🔧 Mejorar manejo de errores silencioso en pipeline.py" \
  --label "code-quality" \
  --label "etl" \
  --label "error-handling" \
  --label "priority-medium" \
  --assignee "${current_user}" \
  --body '
### 📌 Descripción

Múltiples bloques `try/except` en `src/etl/pipeline.py` solo loguean warnings pero continúan la ejecución del pipeline, incluso cuando algunos errores podrían ser críticos y deberían detener el proceso.

### 🔍 Archivos Afectados

- `src/etl/pipeline.py` (múltiples ubicaciones)

### 📍 Ubicaciones Problemáticas

- Línea 252: Error cargando datos de renta
- Línea 310: Error procesando demografía ampliada
- Línea 363: Error procesando Portal de Dades
- Línea 394: Error procesando renta
- Línea 410: Error cargando Idealista venta
- Línea 421: Error cargando Idealista alquiler
- Línea 438: Error procesando oferta Idealista

### 💻 Código Problemático

```python
try:
    renta_df = _safe_read_csv(renta_path)
    logger.info("✓ Datos de renta cargados: %s", renta_path.name)
except Exception as e:
    logger.warning("Error cargando datos de renta: %s", e)
    # Continúa ejecución sin datos de renta
```

### ⚠️ Impacto

- Errores críticos pueden pasar desapercibidos
- Pipeline puede completarse "exitosamente" con datos incompletos
- Dificulta debugging de problemas de datos

### ✅ Solución Propuesta

- Clasificar errores en críticos vs. opcionales
- Errores críticos (ej: demografía base) deberían detener el pipeline
- Errores opcionales (ej: Idealista, Portal de Dades) pueden continuar con warning
- Añadir flag `--strict` para pipeline que falle en cualquier error

### 📝 Pasos para Resolver

- [ ] Clasificar cada fuente de datos como crítica u opcional
- [ ] Modificar manejo de errores para fuentes críticas (raise en lugar de warning)
- [ ] Mantener warnings para fuentes opcionales pero mejorar logging
- [ ] Añadir `exc_info=True` a todos los logs de errores
- [ ] Documentar qué fuentes son críticas vs. opcionales

### 🔗 Issues Relacionadas

- Relacionada con: Issue #43 "Refactor: Limpiar orquestador Pipeline"
- Conecta con: mejoras generales en robustez y manejo de errores del pipeline ETL
'

#
# Issue 7: Falta validación de años en Portal de Dades
#
gh issue create \
  --title "🐛 Falta validación de años en datos de Portal de Dades" \
  --label "bug" \
  --label "etl" \
  --label "data-quality" \
  --label "priority-medium" \
  --assignee "${current_user}" \
  --body '
### 📌 Descripción

La función `_extract_year_from_temps` puede retornar `None` cuando falla el parsing de fechas, pero este valor no se valida antes de usarse en agrupaciones y operaciones que requieren años válidos.

### 🔍 Archivos Afectados

- `src/etl/transformations/enrichment.py:112`
- `src/etl/transformations/utils.py:114-120` (función `_extract_year_from_temps`)

### 💻 Código Problemático

```python
df["anio"] = df["Dim-00:TEMPS"].apply(_extract_year_from_temps)
df = df.dropna(subset=["anio", "VALUE"])  # ✅ Esto está bien
# Pero en otros lugares puede no validarse:
df.groupby(["anio", ...])  # ❌ Puede fallar si hay None
```

### ⚠️ Impacto

- Puede causar errores en agrupaciones por año si hay valores None
- Datos con fechas inválidas pueden ser procesados incorrectamente
- Puede causar errores silenciosos en cálculos temporales

### ✅ Solución Propuesta

- Validar que `anio` no sea None antes de agrupar
- Añadir logging cuando se descarten registros por año inválido
- Documentar comportamiento esperado cuando `_extract_year_from_temps` retorna None

### 📝 Pasos para Resolver

- [ ] Revisar todos los usos de `_extract_year_from_temps`
- [ ] Asegurar que siempre se valida `dropna(subset=["anio"])` antes de agrupar
- [ ] Añadir logging cuando se descarten registros por año inválido
- [ ] Añadir test que verifique manejo de años inválidos

### 🔗 Issues Relacionadas

- Relacionada con: Issue #15 "Improvement: Mejorar mapeo de territorios Portal de Dades"
- Conecta con: mejoras en procesamiento y validación de datos del Portal de Dades
'

#
# Issue 8: Workflow dashboard-demo sin validación de puerto
#
gh issue create \
  --title "🔧 Añadir validación de puerto en workflow dashboard-demo" \
  --label "ci-cd" \
  --label "workflow" \
  --label "priority-low" \
  --assignee "${current_user}" \
  --body '
### 📌 Descripción

El workflow `.github/workflows/dashboard-demo.yml` acepta un puerto como input string pero no valida que esté en un rango válido (1024-65535) antes de usarlo.

### 🔍 Archivos Afectados

- `.github/workflows/dashboard-demo.yml:10-14, 38`

### 💻 Código Problemático

```yaml
inputs:
  port:
    description: \"Streamlit port (default 8501)\"
    required: false
    default: \"8501\"
    type: string  # ❌ No valida rango
```

### ⚠️ Impacto

- Puertos inválidos pueden causar fallos en el workflow
- Puertos privilegiados (<1024) pueden causar errores de permisos
- Puertos fuera de rango pueden causar errores de conexión

### ✅ Solución Propuesta

Añadir step de validación antes de iniciar Streamlit:

```yaml
- name: Validate port
  run: |
    PORT=\"\${{ inputs.port }}\"
    if ! [[ \"\$PORT\" =~ ^[0-9]+\$ ]] || [ \"\$PORT\" -lt 1024 ] || [ \"\$PORT\" -gt 65535 ]; then
      echo \"Error: Port must be between 1024 and 65535\"
      exit 1
    fi
```

### 📝 Pasos para Resolver

- [ ] Añadir step de validación de puerto antes de iniciar Streamlit
- [ ] Validar que el puerto sea numérico y esté en rango válido
- [ ] Añadir mensaje de error claro si el puerto es inválido
- [ ] Documentar rango válido en la descripción del input
'

#
# Issue 9: Workflow kpi-update con manejo de errores genérico
#
gh issue create \
  --title "🔧 Mejorar manejo de errores en workflow kpi-update" \
  --label "ci-cd" \
  --label "workflow" \
  --label "code-quality" \
  --label "priority-low" \
  --assignee "${current_user}" \
  --body '
### 📌 Descripción

El workflow `.github/workflows/kpi-update.yml` usa `except:` sin especificar tipo de excepción, lo que es una mala práctica y puede ocultar errores inesperados.

### 🔍 Archivos Afectados

- `.github/workflows/kpi-update.yml:48`

### 💻 Código Problemático

```python
try:
    with open(\"\$FILE\", \"r\") as f:
        data = json.load(f)
except:  # ❌ Bare except
    data = {\"kpis\": []}
```

### ⚠️ Impacto

- Puede capturar excepciones críticas (KeyboardInterrupt, SystemExit)
- Dificulta debugging de errores reales
- No sigue mejores prácticas de Python

### ✅ Solución Propuesta

```python
except (json.JSONDecodeError, FileNotFoundError) as e:
    logger.warning(\"Error cargando KPI progress, inicializando vacío: %s\", e)
    data = {\"kpis\": []}
```

### 📝 Pasos para Resolver

- [ ] Especificar tipos de excepciones concretos (`json.JSONDecodeError`, `FileNotFoundError`)
- [ ] Añadir logging del error para debugging
- [ ] Evaluar si otros errores deberían propagarse
'

#
# Issue 10: Falta validación de estructura de manifest.json
#
gh issue create \
  --title "🐛 Añadir validación de estructura de manifest.json" \
  --label "bug" \
  --label "etl" \
  --label "data-quality" \
  --label "priority-medium" \
  --assignee "${current_user}" \
  --body '
### 📌 Descripción

La función `_load_manifest` en `src/etl/pipeline.py` carga el archivo JSON pero no valida que tenga la estructura esperada (lista de diccionarios con campos específicos). Esto puede causar fallos silenciosos si el manifest tiene estructura incorrecta.

### 🔍 Archivos Afectados

- `src/etl/pipeline.py:45-67`

### 💻 Código Problemático

```python
def _load_manifest(raw_dir: Path) -> List[Dict[str, object]]:
    manifest_path = raw_dir / \"manifest.json\"
    if not manifest_path.exists():
        return []
    
    try:
        with open(manifest_path, \"r\", encoding=\"utf-8\") as f:
            manifest = json.load(f)  # ❌ No valida estructura
        return manifest
```

### ⚠️ Impacto

- Manifest con estructura incorrecta puede causar errores en tiempo de ejecución
- Errores pueden ser difíciles de debuggear si el manifest está malformado
- Puede causar fallos silenciosos en descubrimiento de archivos

### ✅ Solución Propuesta

Añadir validación de estructura:

```python
# Validar estructura
if not isinstance(manifest, list):
    logger.error(\"Manifest debe ser una lista, encontrado: %s\", type(manifest))
    return []

# Validar que cada entrada tenga campos mínimos
required_fields = {\"file_path\", \"type\"}
for i, entry in enumerate(manifest):
    if not isinstance(entry, dict):
        logger.warning(\"Entrada %d del manifest no es un diccionario\", i)
        continue
    missing = required_fields - set(entry.keys())
    if missing:
        logger.warning(\"Entrada %d del manifest falta campos: %s\", i, missing)
```

### 📝 Pasos para Resolver

- [ ] Añadir validación de tipo (debe ser lista)
- [ ] Validar campos requeridos en cada entrada del manifest
- [ ] Añadir logging claro cuando el manifest tiene estructura incorrecta
- [ ] Añadir test que verifique validación de manifest inválido
'

#
# Issue 11: Función prepare_idealista_oferta con lógica incompleta
#
gh issue create \
  --title "🐛 Lógica incompleta en prepare_idealista_oferta" \
  --label "bug" \
  --label "etl" \
  --label "code-quality" \
  --label "priority-medium" \
  --assignee "${current_user}" \
  --body '
### 📌 Descripción

La función `prepare_idealista_oferta` calcula `num_anuncios_tipologia` agrupando por tipología pero no incluye este resultado en el DataFrame final. El resultado se asigna a `_` (descartado), lo que es código muerto.

### 🔍 Archivos Afectados

- `src/etl/transformations/enrichment.py:277-283`

### 💻 Código Problemático

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

### ⚠️ Impacto

- Código muerto que confunde a desarrolladores
- Información útil (distribución por tipología) se calcula pero no se usa
- Puede indicar funcionalidad incompleta o abandonada

### ✅ Solución Propuesta

- Opción 1: Eliminar el código si no se necesita
- Opción 2: Incluir `num_anuncios_tipologia` en el resultado agregado si es útil

### 📝 Pasos para Resolver

- [ ] Evaluar si `num_anuncios_tipologia` es información útil para análisis
- [ ] Si es útil: incluir en el DataFrame agregado (pivot o agregación adicional)
- [ ] Si no es útil: eliminar el código muerto
- [ ] Documentar decisión en comentario o docstring
'

echo "✅ Todos los issues han sido creados exitosamente"

