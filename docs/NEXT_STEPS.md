# Próximos Pasos - Roadmap de Desarrollo

Este documento detalla los próximos pasos recomendados para continuar el desarrollo del proyecto Barcelona Housing Demographics Analyzer.

## ✅ Estado Actual

**Completado**:
- ✅ **Milestone 1: Foundation & Data Infrastructure**
  - Extracción de datos (E) con mejoras avanzadas
  - Transformación (T) con esquema dimensional
  - Carga (L) en SQLite
  - Pipeline ETL completo y funcional

**Base de datos disponible**: `data/processed/database.db` con:
- `dim_barrios`: 73 barrios
- `fact_demografia`: 657 registros (2015-2023)
- `fact_precios`: 59 registros (venta 2015)
- `etl_runs`: Auditoría de ejecuciones

---

## 🎯 Próximos Pasos Recomendados

### **Paso 1: Documentación del Esquema de Base de Datos** (Prioridad Alta)

**Objetivo**: Documentar la estructura completa de la base de datos para facilitar análisis y desarrollo.

**Tareas**:
- [ ] Crear `docs/DATABASE_SCHEMA.md` con:
  - Descripción detallada de cada tabla
  - Relaciones entre tablas (diagrama ER)
  - Ejemplos de consultas SQL comunes
  - Convenciones de nombres y tipos de datos
- [ ] Agregar diagrama de relaciones (usando Mermaid o similar)
- [ ] Documentar índices y constraints

**Tiempo estimado**: 2-3 horas

---

### **Paso 2: EDA Inicial - Notebook de Exploración** (Prioridad Alta)

**Objetivo**: Completar `notebooks/01-eda-initial.ipynb` con análisis exploratorio de los datos cargados.

**Tareas**:
- [ ] Conectar a la base de datos SQLite
- [ ] Análisis descriptivo básico:
  - Resumen estadístico de `fact_demografia`
  - Resumen estadístico de `fact_precios`
  - Distribución de barrios y distritos
- [ ] Visualizaciones iniciales:
  - Evolución temporal de población por distrito
  - Distribución de precios de venta por barrio
  - Mapa de calor de precios vs población
- [ ] Identificar datos faltantes y outliers
- [ ] Documentar hallazgos iniciales

**Tiempo estimado**: 4-6 horas

**Ejemplo de código inicial**:
```python
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

conn = sqlite3.connect('../data/processed/database.db')

# Cargar datos
df_demo = pd.read_sql_query("""
    SELECT d.*, b.barrio_nombre, b.distrito_nombre
    FROM fact_demografia d
    JOIN dim_barrios b ON d.barrio_id = b.barrio_id
""", conn)

df_precios = pd.read_sql_query("""
    SELECT p.*, b.barrio_nombre, b.distrito_nombre
    FROM fact_precios p
    JOIN dim_barrios b ON p.barrio_id = b.barrio_id
""", conn)
```

---

### **Paso 3: Funciones de Análisis Básicas** (Prioridad Media)

**Objetivo**: Implementar funciones útiles en `src/analysis.py` para análisis reutilizables.

**Funciones sugeridas**:
- [ ] `get_demographics_by_district(district_name, year_start, year_end)`
- [ ] `get_housing_prices_by_barrio(barrio_name, year_start, year_end)`
- [ ] `calculate_population_growth(barrio_id, year_start, year_end)`
- [ ] `correlate_demographics_prices(district_name=None)`
- [ ] `get_top_barrios_by_metric(metric, top_n=10, year=None)`
- [ ] `compare_barrios(barrio_ids, metrics=['poblacion_total', 'precio_m2_venta'])`

**Tiempo estimado**: 4-6 horas

---

### **Paso 4: Visualizaciones Interactivas Básicas** (Prioridad Media)

**Objetivo**: Crear visualizaciones interactivas usando Plotly o Altair.

**Tareas**:
- [ ] Función para gráfico de evolución temporal (población/precios)
- [ ] Función para mapa de calor de correlaciones
- [ ] Función para comparación de barrios
- [ ] Guardar visualizaciones en `notebooks/visualizations/`

**Tiempo estimado**: 3-4 horas

---

### **Paso 5: Dashboard Streamlit Básico** (Prioridad Baja - Futuro)

**Objetivo**: Crear un dashboard interactivo básico en `src/app.py`.

**Funcionalidades iniciales**:
- [ ] Selector de barrio/distrito
- [ ] Visualización de evolución temporal
- [ ] Tabla de datos filtrados
- [ ] Métricas resumen (población, precios)

**Tiempo estimado**: 6-8 horas

---

### **Paso 6: Mejoras al Pipeline ETL** (Prioridad Baja)

**Tareas opcionales**:
- [ ] Agregar validación de integridad referencial
- [ ] Implementar incremental loads (solo nuevos datos)
- [ ] Agregar tests unitarios para ETL
- [ ] Optimizar consultas SQL

**Tiempo estimado**: 4-6 horas

---

## 📋 Plan de Acción Inmediato (Esta Semana)

### Día 1-2: Documentación
1. Crear `docs/DATABASE_SCHEMA.md`
2. Actualizar README con instrucciones de uso del ETL

### Día 3-4: EDA
1. Completar `notebooks/01-eda-initial.ipynb`
2. Generar visualizaciones iniciales
3. Documentar hallazgos

### Día 5: Funciones de Análisis
1. Implementar 3-4 funciones básicas en `analysis.py`
2. Probar funciones con datos reales

---

## 🔧 Comandos Útiles para Empezar

### Verificar datos en la base de datos:
```bash
python -c "
import sqlite3
import pandas as pd
conn = sqlite3.connect('data/processed/database.db')
print('Barrios:', pd.read_sql_query('SELECT COUNT(*) FROM dim_barrios', conn).iloc[0,0])
print('Demografía:', pd.read_sql_query('SELECT COUNT(*) FROM fact_demografia', conn).iloc[0,0])
print('Precios:', pd.read_sql_query('SELECT COUNT(*) FROM fact_precios', conn).iloc[0,0])
"
```

### Regenerar base de datos después de nueva extracción:
```bash
# 1. Extraer datos actualizados
python scripts/extract_data.py --sources opendatabcn --year-start 2015 --year-end 2023

# 2. Ejecutar ETL
python scripts/process_and_load.py --raw-dir data/raw --processed-dir data/processed
```

### Explorar datos en Jupyter:
```python
# En notebooks/01-eda-initial.ipynb
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

conn = sqlite3.connect('../data/processed/database.db')

# Ver estructura
tables = pd.read_sql_query(
    "SELECT name FROM sqlite_master WHERE type='table'", 
    conn
)
print(tables)

# Cargar datos combinados
query = """
SELECT 
    d.anio,
    d.poblacion_total,
    d.poblacion_hombres,
    d.poblacion_mujeres,
    p.precio_m2_venta,
    b.barrio_nombre,
    b.distrito_nombre
FROM fact_demografia d
LEFT JOIN fact_precios p ON d.barrio_id = p.barrio_id AND d.anio = p.anio
JOIN dim_barrios b ON d.barrio_id = b.barrio_id
ORDER BY d.anio, b.barrio_nombre
"""

df = pd.read_sql_query(query, conn)
print(df.head())
print(df.info())
```

---

## 📊 Métricas de Éxito

Para considerar completado cada paso:

- **Paso 1 (Documentación)**: 
  - ✅ Documento completo con ejemplos
  - ✅ Diagrama ER incluido
  
- **Paso 2 (EDA)**:
  - ✅ Notebook ejecutable sin errores
  - ✅ Al menos 5 visualizaciones
  - ✅ Hallazgos documentados
  
- **Paso 3 (Funciones)**:
  - ✅ Al menos 5 funciones implementadas
  - ✅ Funciones documentadas con docstrings
  - ✅ Ejemplos de uso incluidos

---

## 🚀 Siguiente Hito

**Objetivo**: Completar Milestone 2 (Initial Analysis & EDA)

**Fecha objetivo**: 1-2 semanas

**Entregables**:
- Documentación del esquema
- Notebook EDA completo
- Funciones de análisis básicas
- Visualizaciones iniciales

---

## 💡 Notas

- Priorizar calidad sobre cantidad: mejor tener pocas funciones bien documentadas
- Mantener el código DRY (Don't Repeat Yourself)
- Documentar decisiones y hallazgos en los notebooks
- Commits frecuentes con mensajes descriptivos

