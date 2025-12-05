# 🎯 Próximos Pasos - Plan de Acción Concreto

**Fecha de actualización**: 5 de diciembre de 2025  
**Estado actual**: Sprint de Integridad completado ✅  
**Cobertura actual**: 37% (objetivo: ≥80%)

---

## 📊 Estado Actual del Proyecto

### ✅ Completado
- ✅ Sprint de Integridad de Datos (PR #99)
- ✅ `fact_precios`: 6,358 registros preservados
- ✅ `dim_barrios`: 73/73 geometrías GeoJSON
- ✅ `fact_demografia`: 0% nulls críticos
- ✅ Validación de integridad referencial implementada (Issues #67, #81, #82 cerradas)
- ✅ Tests para `cleaners.py` (100% cobertura)
- ✅ Tests para `database_setup.py` (97% cobertura)
- ✅ Tests para `dimensions.py` (80% cobertura)
- ✅ Tests para `pipeline.py` (78% cobertura) - **PR #111 completado**
- ✅ Tests para `demographics.py` (58% cobertura) - **PR #110 completado**
- ✅ Tests para `validators.py` (80% cobertura)

### 📈 Métricas Actuales
- **Cobertura de tests**: **37%** (mejora desde 24.88%, objetivo: ≥80%)
- **Módulos con ≥60% cobertura**: 6 módulos ✅
- **Módulos pendientes**:
  - `market.py`: 37% ⚠️ (siguiente prioridad)
  - `orchestrator.py`: 4% ⚠️
  - `opendata.py`: 22% ⚠️
  - `enrichment.py`: 5% ⚠️

---

## 🚀 Opciones de Próximos Pasos (Priorizadas)

### Opción 1: Mejorar Cobertura de Tests (Recomendado) 🔴

**Objetivo**: Llevar cobertura de 37% a ≥60% (módulos críticos) y ≥80% (total)  
**Progreso**: 2 de 4 módulos críticos completados ✅  
**Tiempo estimado restante**: 1-2 semanas  
**Impacto**: Alta calidad de código, menos bugs

#### Paso 1.1: Tests para `demographics.py` ✅ COMPLETADO
**Estado anterior**: 3% cobertura  
**Estado actual**: **58% cobertura** ✅  
**PR**: #110

**Logros**:
- ✅ 43 tests creados (22 iniciales + 21 adicionales)
- ✅ Tests para `prepare_fact_demografia()` - 8 tests
- ✅ Tests para `enrich_fact_demografia()` - 9 tests
- ✅ Tests para `prepare_demografia_ampliada()` - 7 tests
- ✅ Tests para funciones auxiliares privadas - 19 tests
- ✅ Objetivo de ≥60% cumplido

**Comando para verificar**:
```bash
python3 -m pytest tests/test_demographics.py \
  --cov=src.etl.transformations.demographics \
  --cov-report=term-missing
```

---

#### Paso 1.2: Tests para `pipeline.py` ✅ COMPLETADO
**Estado anterior**: 34% cobertura  
**Estado actual**: **78% cobertura** ✅  
**PR**: #111

**Logros**:
- ✅ 30 tests totales (7 anteriores + 23 nuevos)
- ✅ Tests para funciones auxiliares (100% cobertura):
  - `_find_latest_file()` - 3 tests
  - `_load_metadata()` - 2 tests
  - `_load_manifest()` - 3 tests
  - `_get_latest_file_from_manifest()` - 4 tests
  - `_safe_read_csv()` - 3 tests
- ✅ Tests para `run_etl()` - 8 tests
- ✅ Objetivo de ≥60% superado (78%)

**Comando para verificar**:
```bash
python3 -m pytest tests/test_pipeline.py \
  --cov=src.etl.pipeline \
  --cov-report=term-missing
```

---

#### Paso 1.3: Tests para `market.py` (Prioridad Media)
**Estado actual**: 37% cobertura  
**Objetivo**: ≥60% cobertura

**Áreas a cubrir**:
- `prepare_fact_precios()`
- `prepare_renta_barrio()`
- Lógica de deduplicación
- Validación de datos de mercado

**Estimación**: 3-4 horas

---

### Opción 2: Completar Documentación 📚

**Objetivo**: Llevar documentación de ~50% a ≥70%  
**Tiempo estimado**: 1-2 semanas  
**Impacto**: Mejor onboarding, código más mantenible

#### Paso 2.1: Documentar funciones principales del ETL
**Archivos prioritarios**:
- `src/etl/pipeline.py`: Documentar flujo completo
- `src/etl/transformations/*`: Docstrings detallados
- `src/extraction/*`: Documentar extractores

**Estructura sugerida**:
```python
def prepare_fact_demografia(...) -> pd.DataFrame:
    """
    Prepara la tabla fact_demografia con datos demográficos básicos.
    
    Args:
        df_raw: DataFrame con datos brutos de demografía
        conn: Conexión a la base de datos
    
    Returns:
        DataFrame con datos preparados para fact_demografia
    
    Raises:
        ValueError: Si faltan columnas requeridas
        sqlite3.Error: Si hay problemas con la base de datos
    
    Example:
        >>> df = prepare_fact_demografia(df_raw, conn)
        >>> df.head()
    """
```

**Estimación**: 8-10 horas

---

#### Paso 2.2: Crear guías de usuario
**Archivos a crear**:
- `docs/USER_GUIDE.md`: Guía completa para usuarios
- `docs/DEVELOPER_GUIDE.md`: Guía para desarrolladores
- `docs/API_REFERENCE.md`: Referencia de API

**Estimación**: 6-8 horas

---

#### Paso 2.3: Ejemplos prácticos
**Archivos a crear**:
- `docs/examples/extract_data.md`
- `docs/examples/run_etl.md`
- `docs/examples/verify_data.md`
- `docs/examples/query_database.md`

**Estimación**: 4-6 horas

---

### Opción 3: Optimizar Pipeline ETL ⚡

**Objetivo**: Mejorar rendimiento y robustez  
**Tiempo estimado**: 1-2 semanas  
**Impacto**: Pipeline más rápido y confiable

#### Paso 3.1: Mejorar manejo de errores
**Mejoras**:
- Logging más detallado
- Recovery automático cuando sea posible
- Mejores mensajes de error
- Retry logic para APIs externas

**Archivos a modificar**:
- `src/etl/pipeline.py`
- `src/extraction/base.py`
- `src/extraction/opendata.py`

**Estimación**: 4-6 horas

---

#### Paso 3.2: Añadir validaciones de calidad
**Validaciones a añadir**:
- Validación de rangos de valores (precios, población)
- Validación de consistencia temporal
- Validación de integridad de datos
- Detección de outliers

**Archivos a crear/modificar**:
- `src/etl/validators.py` (expandir)
- Nuevos validadores específicos

**Estimación**: 6-8 horas

---

#### Paso 3.3: Optimizar consultas SQL
**Mejoras**:
- Índices adicionales si es necesario
- Optimizar queries complejas
- Batch processing para grandes volúmenes

**Estimación**: 3-4 horas

---

### Opción 4: Dashboard Streamlit - Mejoras 🎨

**Objetivo**: Dashboard más completo y funcional  
**Tiempo estimado**: 2-3 semanas  
**Impacto**: Mejor experiencia de usuario

#### Paso 4.1: Visualizaciones Geográficas
**Funcionalidades**:
- Integrar GeoJSON cargado en `dim_barrios`
- Mapas interactivos con Plotly Mapbox
- Choropleth maps por barrio
- Visualización de precios en mapa

**Archivos a modificar**:
- `src/app/main.py`
- Crear `src/app/components/map.py`

**Estimación**: 8-10 horas

---

#### Paso 4.2: Filtros Avanzados
**Funcionalidades**:
- Filtro por rango de años
- Filtro por distrito
- Filtro por tipo de operación (venta/alquiler)
- Búsqueda por nombre de barrio

**Estimación**: 4-6 horas

---

#### Paso 4.3: Mejoras de UX
**Mejoras**:
- Loading states
- Mejor manejo de errores
- Tooltips informativos
- Mejor diseño responsive

**Estimación**: 6-8 horas

---

### Opción 5: Features Nuevas 🆕

**Objetivo**: Añadir funcionalidades nuevas  
**Tiempo estimado**: Variable  
**Impacto**: Valor añadido al proyecto

#### Paso 5.1: Calculadora de Inversión
**Descripción**: Calculadora para evaluar inversiones inmobiliarias  
**Archivo**: `docs/features/feature-02-calculator.md`  
**Estimación**: 10-12 horas

---

#### Paso 5.2: Sistema de Alertas
**Descripción**: Alertas cuando cambian precios o demografía  
**Archivo**: `docs/features/feature-05-alertas.md`  
**Estimación**: 8-10 horas

---

#### Paso 5.3: Clustering de Barrios
**Descripción**: Agrupar barrios por similitud demográfica/precio  
**Archivo**: `docs/features/feature-13-clustering.md`  
**Estimación**: 12-15 horas

---

## 📅 Plan Recomendado (2-3 Semanas)

### Semana 1: Tests y Documentación
**Día 1-2**: Tests para `demographics.py`
- Crear `tests/test_demographics.py`
- Añadir tests para todas las funciones principales
- Objetivo: Llevar cobertura de 3% a ≥60%

**Día 3-4**: Tests para `pipeline.py`
- Expandir `tests/test_pipeline.py`
- Tests de integración end-to-end
- Objetivo: Llevar cobertura de 34% a ≥60%

**Día 5-7**: Documentación
- Documentar funciones principales del ETL
- Crear guías de usuario
- Añadir ejemplos prácticos

**Resultado esperado**: Cobertura ≥60%, Documentación ≥50%

---

### Semana 2-3: Optimización y Dashboard
**Día 8-10**: Optimización del Pipeline
- Mejorar manejo de errores
- Añadir validaciones
- Optimizar consultas SQL

**Día 11-14**: Dashboard Streamlit
- Integrar visualizaciones geográficas
- Añadir filtros avanzados
- Mejorar UX

---

## 🎯 Métricas de Éxito

### Cobertura de Tests
- **Actual**: 24.88%
- **Objetivo Sprint 1**: ≥60%
- **Objetivo Final**: ≥80%

### Documentación
- **Actual**: ~50% (estimado)
- **Objetivo Sprint 1**: ≥60%
- **Objetivo Final**: ≥70%

### Calidad de Código
- **Tests pasando**: 100% ✅
- **Linting**: Sin errores ✅
- **Type hints**: En todas las funciones públicas ⚠️

---

## 🛠️ Comandos Útiles

### Verificar Estado Actual
```bash
# Verificar estado del sprint
python3 scripts/verify_sprint_status.py

# Ejecutar todos los tests
python3 -m pytest tests/ -v

# Verificar cobertura
python3 -m pytest tests/ --cov=src --cov-report=term-missing

# Ver cobertura de un módulo específico
python3 -m pytest tests/test_demographics.py \
  --cov=src.etl.transformations.demographics \
  --cov-report=term-missing
```

### Desarrollo
```bash
# Crear nueva rama para tests
git checkout -b test/add-demographics-tests

# Ejecutar tests específicos
python3 -m pytest tests/test_demographics.py -v

# Ejecutar con coverage
python3 -m pytest tests/ --cov=src --cov-report=html
# Abrir htmlcov/index.html en el navegador
```

---

## 📝 Issues a Crear en GitHub

### Alta Prioridad
1. **`test: Añadir tests para demographics.py`**
   - Tipo: `enhancement`
   - Labels: `testing`, `high-priority`
   - Estimación: 4-6 horas
   - Objetivo: Llevar cobertura de 3% a ≥60%

2. **`test: Añadir tests para pipeline.py`**
   - Tipo: `enhancement`
   - Labels: `testing`, `high-priority`
   - Estimación: 6-8 horas
   - Objetivo: Tests de integración end-to-end

3. **`docs: Completar documentación del ETL`**
   - Tipo: `documentation`
   - Labels: `documentation`, `high-priority`
   - Estimación: 8-10 horas
   - Objetivo: Documentación completa de funciones principales

### Media Prioridad
4. **`refactor: Optimizar pipeline ETL`**
   - Tipo: `enhancement`
   - Labels: `refactoring`, `medium-priority`
   - Estimación: 6-8 horas

5. **`feat: Mejorar dashboard Streamlit`**
   - Tipo: `enhancement`
   - Labels: `dashboard`, `medium-priority`
   - Estimación: 10-12 horas

---

## 🚀 Recomendación Final

**Para empezar ahora mismo**, te recomiendo:

1. **Opción 1 - Paso 1.1**: Crear tests para `demographics.py`
   - Mayor impacto en calidad de código
   - Relativamente rápido (4-6 horas)
   - Base sólida para futuras mejoras

2. **Opción 2 - Paso 2.1**: Documentar funciones principales
   - Mejora mantenibilidad
   - Facilita onboarding
   - Puede hacerse en paralelo con tests

**Comando para empezar**:
```bash
# Crear rama para tests
git checkout -b test/add-demographics-tests

# Crear archivo de tests
touch tests/test_demographics.py

# Empezar a escribir tests
# (ver estructura sugerida arriba)
```

---

## 📚 Recursos

- **Documentación del Sprint**: `docs/SPRINT_STATUS_DEC_2025.md`
- **Estado del Proyecto**: `docs/PROJECT_STATUS.md`
- **Resumen Ejecutivo**: `docs/PROJECT_STATUS_SUMMARY.md`
- **Plan de Acción Anterior**: `docs/NEXT_STEPS_ACTION_PLAN.md`
- **Guía de Contribución**: `CONTRIBUTING.md`

---

**Última actualización**: 3 de diciembre de 2025

