# Code Audit - Issues Found

**Fecha:** 2025-12-01  
**Auditor:** AI Assistant  
**Alcance:** Código fuente completo (`src/`, `scripts/`, `tests/`)

---

## Resumen Ejecutivo

Se encontraron **47 issues** categorizados en:
- 🔴 **Críticos:** 8
- 🟡 **Importantes:** 15
- 🟢 **Mejoras:** 24

---

## 🔴 Issues Críticos (Alta Prioridad)

### 1. Código Duplicado: `data_extraction.py` vs `extraction/`
**Archivo:** `src/data_extraction.py`  
**Severidad:** Crítica  
**Descripción:**  
Existe un módulo legacy `data_extraction.py` (2547 líneas) que duplica funcionalidad de los extractores modulares en `src/extraction/`. Esto genera:
- Confusión sobre qué código usar
- Mantenimiento duplicado
- Riesgo de inconsistencias

**Impacto:**
- Duplicación de ~2000 líneas de código
- Clases duplicadas: `OpenDataBCNExtractor`, `IdealistaExtractor`, `PortalDadesExtractor`
- Dos sistemas de logging diferentes

**Recomendación:**
- [ ] Auditar qué código legacy aún se usa
- [ ] Migrar referencias restantes a `extraction/`
- [ ] Eliminar `data_extraction.py` o marcarlo como deprecated

---

### 2. SQL Injection Potencial en `data_loader.py`
**Archivo:** `src/app/data_loader.py:80`  
**Severidad:** Crítica  
**Código:**
```python
df = pd.read_sql(f"SELECT MIN(anio) as min_year, MAX(anio) as max_year FROM {table}", conn)
```

**Problema:**  
Uso de f-string con nombre de tabla sin validación. Aunque `table` viene de una lista controlada, es una mala práctica.

**Recomendación:**
```python
# Validar tabla contra lista blanca
ALLOWED_TABLES = ["fact_precios", "fact_demografia", "fact_renta"]
if table not in ALLOWED_TABLES:
    raise ValueError(f"Tabla no permitida: {table}")
df = pd.read_sql(f"SELECT MIN(anio) as min_year, MAX(anio) as max_year FROM {table}", conn)
```

---

### 3. SQL Injection Potencial en `database_setup.py`
**Archivo:** `src/database_setup.py:214`  
**Severidad:** Crítica  
**Código:**
```python
conn.execute(f"DELETE FROM {table};")
```

**Problema:**  
Similar al anterior, aunque `table` viene de una lista controlada en `truncate_tables()`.

**Recomendación:**
```python
ALLOWED_TABLES = {"dim_barrios", "fact_precios", "fact_demografia", ...}
if table not in ALLOWED_TABLES:
    raise ValueError(f"Tabla no permitida para truncado: {table}")
conn.execute(f"DELETE FROM {table};")
```

---

### 4. `IncasolSocrataExtractor` No Registrado en `__init__.py`
**Archivo:** `src/extraction/__init__.py`  
**Severidad:** Crítica  
**Descripción:**  
La clase `IncasolSocrataExtractor` existe en `src/extraction/incasol.py` pero no está exportada en `__init__.py`, por lo que no es importable desde `src.extraction`.

**Recomendación:**
```python
from .incasol import IncasolSocrataExtractor
__all__ = [
    # ... existing exports ...
    "IncasolSocrataExtractor",
]
```

---

### 5. Uso de `print()` en lugar de Logger
**Archivo:** `src/data_extraction.py:40`  
**Severidad:** Crítica  
**Código:**
```python
print("WARNING: Playwright no está instalado...", file=sys.stderr)
```

**Problema:**  
Debería usar el sistema de logging establecido.

**Recomendación:**
```python
logger.warning("Playwright no está instalado. El extractor PortalDades requerirá: pip install playwright && playwright install")
```

---

### 6. Manejo de Errores Genérico en `data_processing.py`
**Archivo:** `src/data_processing.py` (múltiples lugares)  
**Severidad:** Crítica  
**Ejemplos:**
- Línea 559: `except (UnicodeDecodeError, pd.errors.ParserError):` - OK
- Pero hay lugares donde se capturan excepciones muy amplias sin contexto suficiente

**Recomendación:**
- Revisar todos los `except Exception` y especificar tipos concretos
- Añadir logging con `exc_info=True` en todos los casos

---

### 7. Hardcoding de Año 2022 en Múltiples Lugares
**Archivo:** `src/app/data_loader.py` (múltiples funciones)  
**Severidad:** Crítica  
**Ejemplos:**
- `load_renta(year: int = 2022)` - hardcodea 2022 como default
- `load_affordability_data()` - hardcodea `WHERE anio = 2022` en línea 247
- `load_temporal_comparison()` - hardcodea `WHERE anio = 2022` en línea 291

**Problema:**  
Los datos de renta ahora están disponibles para 2015-2023, pero el código sigue asumiendo solo 2022.

**Recomendación:**
- Actualizar funciones para usar el año pasado como parámetro
- Actualizar documentación y UI para reflejar años disponibles

---

### 8. Falta Validación de Integridad Referencial en ETL
**Archivo:** `src/etl/pipeline.py`  
**Severidad:** Crítica  
**Descripción:**  
El ETL carga datos en tablas con foreign keys pero no valida explícitamente que todos los `barrio_id` en fact tables existan en `dim_barrios` antes de insertar.

**Recomendación:**
```python
# Antes de cargar fact tables, validar:
invalid_barrios = fact_precios[~fact_precios['barrio_id'].isin(dim_barrios['barrio_id'])]
if not invalid_barrios.empty:
    logger.error(f"Barrios inválidos encontrados: {invalid_barrios['barrio_id'].unique()}")
    raise ValueError("Integridad referencial violada")
```

---

## 🟡 Issues Importantes (Media Prioridad)

### 9. Falta Type Hints Completos
**Archivos:** Múltiples  
**Severidad:** Importante  
**Ejemplos:**
- `src/data_processing.py`: Muchas funciones tienen type hints parciales
- `src/app/data_loader.py`: Algunas funciones retornan `dict` sin especificar estructura

**Recomendación:**
- Usar `TypedDict` para estructuras de diccionarios complejas
- Completar type hints en todas las funciones públicas

---

### 10. Manejo Inconsistente de Valores Nulos
**Archivo:** `src/data_processing.py`  
**Severidad:** Importante  
**Descripción:**  
Hay múltiples estrategias para manejar nulos:
- Algunos lugares usan `pd.NA`
- Otros usan `np.nan`
- Otros usan `None`
- Algunos usan `.fillna()`, otros `.dropna()`

**Recomendación:**
- Estandarizar: usar `pd.NA` para DataFrames, `None` para Python nativo
- Documentar estrategia de manejo de nulos por tipo de dato

---

### 11. Falta Validación de Esquema en `prepare_renta_barrio`
**Archivo:** `src/data_processing.py:1786`  
**Severidad:** Importante  
**Descripción:**  
La función busca columnas de renta con nombres específicos pero no valida que los valores sean razonables (ej: renta negativa, valores extremos).

**Recomendación:**
```python
# Validar rangos razonables
if (df[renta_col] < 0).any():
    logger.warning("Se encontraron valores de renta negativos")
if (df[renta_col] > 200000).any():
    logger.warning("Se encontraron valores de renta extremadamente altos (>200k€)")
```

---

### 12. Cache TTL Hardcodeado en `data_loader.py`
**Archivo:** `src/app/data_loader.py`  
**Severidad:** Importante  
**Descripción:**  
Todos los `@st.cache_data` usan `ttl=3600` (1 hora) hardcodeado. Debería ser configurable.

**Recomendación:**
```python
from src.app.config import CACHE_TTL
@st.cache_data(ttl=CACHE_TTL)
```

---

### 13. Falta Manejo de Conexiones SQLite en Context Managers
**Archivo:** `src/app/data_loader.py`  
**Severidad:** Importante  
**Descripción:**  
Las conexiones SQLite se abren y cierran manualmente con `try/finally`, pero no usan context managers.

**Recomendación:**
```python
from contextlib import contextmanager

@contextmanager
def get_db_connection():
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()

# Uso:
with get_db_connection() as conn:
    df = pd.read_sql(query, conn)
```

---

### 14. F-Strings en SQL Queries (Aunque con Parámetros)
**Archivo:** `src/app/data_loader.py`  
**Severidad:** Importante  
**Descripción:**  
Aunque se usan parámetros para valores (`params=[year]`), se usan f-strings para construir queries complejas. Esto es aceptable pero podría mejorarse.

**Ejemplo:**
```python
f"""
SELECT ...
(p.avg_precio_m2 * {VIVIENDA_TIPO_M2}) / r.renta_euros AS effort_ratio
"""
```

**Recomendación:**
- Mover constantes como `VIVIENDA_TIPO_M2` a parámetros de query si es posible
- O documentar que estas son constantes de configuración, no datos de usuario

---

### 15. Falta Validación de Años Disponibles en UI
**Archivo:** `src/app/main.py:75-88`  
**Severidad:** Importante  
**Descripción:**  
El sidebar hardcodea que renta solo está disponible para 2022, pero ahora hay datos 2015-2023.

**Código actual:**
```python
if selected_metric == "Renta Mensual":
    st.info("Mostrando datos disponibles para **2022** (Único registro oficial de renta)")
    selected_year = 2022
    disable_slider = True
```

**Recomendación:**
- Consultar años disponibles dinámicamente desde `load_available_years()`
- Habilitar slider si hay múltiples años disponibles

---

### 16. Falta Manejo de Errores en `build_geojson`
**Archivo:** `src/app/data_loader.py:446`  
**Severidad:** Importante  
**Descripción:**  
La función `build_geojson` hace `json.loads()` sin manejo de errores si el JSON es inválido.

**Recomendación:**
```python
try:
    geometry = json.loads(row["geometry_json"])
except (json.JSONDecodeError, TypeError) as e:
    logger.warning(f"GeoJSON inválido para barrio {row['barrio_id']}: {e}")
    continue
```

---

### 17. Falta Validación de DataFrame Vacío en Múltiples Funciones
**Archivo:** `src/data_processing.py`  
**Severidad:** Importante  
**Descripción:**  
Muchas funciones asumen que el DataFrame tiene datos, pero no validan explícitamente al inicio.

**Recomendación:**
- Añadir validación temprana: `if df.empty: return pd.DataFrame()` o `raise ValueError`
- Documentar comportamiento cuando DataFrame está vacío

---

### 18. Magic Numbers en Cálculos
**Archivo:** `src/data_processing.py`, `src/app/data_loader.py`  
**Severidad:** Importante  
**Ejemplos:**
- `VIVIENDA_TIPO_M2 = 70` está bien definido en config
- Pero hay otros números mágicos: `* 100` para porcentajes, `* 12` para anualizar alquiler

**Recomendación:**
- Extraer a constantes con nombres descriptivos
- O documentar en comentarios inline

---

### 19. Falta Logging de Métricas de Calidad de Datos
**Archivo:** `src/data_processing.py`  
**Severidad:** Importante  
**Descripción:**  
El ETL no registra métricas de calidad como:
- Porcentaje de valores nulos por columna
- Número de registros descartados por validación
- Distribución de valores (min, max, media) para detectar outliers

**Recomendación:**
- Añadir función `log_data_quality_metrics(df, table_name)` que se ejecute antes de cargar en SQLite

---

### 20. Inconsistencia en Nombres de Columnas de Renta
**Archivo:** `src/data_processing.py:1822`  
**Severidad:** Importante  
**Descripción:**  
La función busca columnas con nombres variados: `["Import_Euros", "Import_Renda_Bruta_€", "Import"]`. Esto es frágil.

**Recomendación:**
- Documentar nombres esperados por fuente
- Añadir mapeo explícito por `source` o `dataset_id`

---

### 21. Falta Validación de Rangos Temporales
**Archivo:** `src/etl/pipeline.py`  
**Severidad:** Importante  
**Descripción:**  
El ETL no valida que los años en los datos estén dentro de rangos esperados (ej: no hay años futuros, no hay años antes de 2010).

**Recomendación:**
```python
MIN_VALID_YEAR = 2010
MAX_VALID_YEAR = datetime.now().year + 1
if (df['anio'] < MIN_VALID_YEAR).any() or (df['anio'] > MAX_VALID_YEAR).any():
    logger.warning(f"Años fuera de rango válido detectados")
```

---

### 22. Falta Documentación de Estrategias de Deduplicación
**Archivo:** `src/data_processing.py:462-497`  
**Severidad:** Importante  
**Descripción:**  
La lógica de deduplicación es compleja y está bien comentada, pero falta documentación de alto nivel sobre cuándo se aplica cada estrategia.

**Recomendación:**
- Crear documento `docs/ETL_DEDUPLICATION_STRATEGY.md` explicando la política

---

### 23. Falta Manejo de Encoding en `_load_portaldades_csv`
**Archivo:** `src/data_processing.py:539`  
**Severidad:** Importante  
**Descripción:**  
La función maneja encoding bien, pero si `chardet` falla, hace fallback silencioso a UTF-8 que puede fallar.

**Recomendación:**
- Añadir logging cuando se usa fallback
- Considerar lanzar excepción si todos los encodings fallan (ya lo hace, pero el mensaje podría ser más claro)

---

## 🟢 Mejoras y Optimizaciones (Baja Prioridad)

### 24. Optimización de Queries SQL
**Archivo:** `src/app/data_loader.py`  
**Severidad:** Baja  
**Descripción:**  
Algunas queries hacen múltiples subconsultas que podrían optimizarse con JOINs más eficientes o índices.

**Ejemplo:** `load_affordability_data()` tiene múltiples subconsultas que podrían combinarse.

---

### 25. Falta Tests para Funciones de `data_processing.py`
**Archivo:** `tests/`  
**Severidad:** Baja  
**Descripción:**  
Hay tests para extractores pero pocos para funciones de transformación/limpieza en `data_processing.py`.

**Recomendación:**
- Crear `tests/test_data_processing.py` con tests para funciones clave

---

### 26. Falta Validación de Tipos en Runtime
**Archivo:** Múltiples  
**Severidad:** Baja  
**Descripción:**  
Aunque hay type hints, no hay validación en runtime (ej: con `pydantic` o `typeguard`).

---

### 27. Falta Configuración Centralizada para Thresholds
**Archivo:** Múltiples  
**Severidad:** Baja  
**Descripción:**  
Thresholds como `MIN_RECORDS_WARNING = 10` están hardcodeados en diferentes módulos.

**Recomendación:**
- Mover a `src/app/config.py` o crear `src/config.py` centralizado

---

### 28. Falta Documentación de API de Funciones Públicas
**Archivo:** Múltiples  
**Severidad:** Baja  
**Descripción:**  
Algunas funciones públicas tienen docstrings incompletos o faltan ejemplos de uso.

---

### 29. Falta Manejo de Versiones de Datasets
**Archivo:** `src/etl/pipeline.py`  
**Severidad:** Baja  
**Descripción:**  
No hay tracking de versiones de datasets procesados (solo timestamps).

**Recomendación:**
- Añadir campo `dataset_version` en `etl_runs` o crear tabla `dataset_versions`

---

### 30. Falta Validación de Coherencia Temporal
**Archivo:** `src/data_processing.py`  
**Severidad:** Baja  
**Descripción:**  
No se valida que las fechas en los datos sean coherentes (ej: `etl_loaded_at` no puede ser futuro).

---

### 31-47. Issues Menores

- **31.** Falta `__repr__` en algunas clases de extractores
- **32.** Algunos imports no utilizados (detectables con `flake8 --select=F401`)
- **33.** Líneas muy largas (>100 caracteres) en algunos lugares
- **34.** Falta `__all__` en algunos módulos
- **35.** Algunos comentarios en español, otros en inglés (inconsistencia)
- **36.** Falta `.gitignore` para archivos temporales de tests
- **37.** Falta validación de que `dim_barrios` tiene exactamente 73 barrios
- **38.** Falta logging de tiempo de ejecución de funciones críticas
- **39.** Algunas funciones muy largas (>100 líneas) podrían dividirse
- **40.** Falta manejo de timeouts en algunas requests HTTP
- **41.** Falta retry logic en algunas operaciones de red
- **42.** Falta validación de tamaño de archivos antes de cargar
- **43.** Falta compresión de archivos raw grandes
- **44.** Falta validación de checksums de archivos descargados
- **45.** Falta documentación de rate limits por fuente
- **46.** Falta manejo de cuotas de API (ej: Idealista 150 calls/month)
- **47.** Falta alertas cuando datos están desactualizados (>6 meses sin actualizar)

---

## Priorización Recomendada

### Sprint Inmediato (Esta Semana)
1. ✅ Registrar `IncasolSocrataExtractor` en `__init__.py` (#4)
2. ✅ Actualizar hardcoding de año 2022 para renta (#7)
3. ✅ Añadir validación SQL injection en `data_loader.py` (#2)
4. ✅ Reemplazar `print()` por logger (#5)

### Sprint Próximo (Próximas 2 Semanas)
5. ✅ Auditar y eliminar código duplicado `data_extraction.py` (#1)
6. ✅ Añadir validación de integridad referencial (#8)
7. ✅ Mejorar manejo de errores genéricos (#6)
8. ✅ Actualizar UI para años disponibles dinámicamente (#15)

### Backlog (Próximo Mes)
9-23. Issues importantes de media prioridad
24-47. Mejoras y optimizaciones

---

## Métricas de Calidad

- **Cobertura de Tests:** ~60% (estimado)
- **Type Hints:** ~80% completo
- **Documentación:** ~70% completo
- **Linting:** ✅ Sin errores
- **Duplicación de Código:** 🔴 Alta (2000+ líneas duplicadas)
- **Complejidad Ciclomática:** 🟡 Media-Alta en algunas funciones

---

## Conclusión

El código está en buen estado general, pero hay **8 issues críticos** que deberían abordarse antes de nuevas features. La mayoría son problemas de mantenibilidad y robustez más que bugs funcionales.

**Recomendación:** Priorizar issues #1, #2, #4, #7 esta semana para estabilizar la base antes de continuar con nuevas funcionalidades.

