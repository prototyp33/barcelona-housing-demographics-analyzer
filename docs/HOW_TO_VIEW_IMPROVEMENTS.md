# Cómo Ver las Mejoras de la Base de Datos

Esta guía te muestra diferentes formas de visualizar y verificar las mejoras aplicadas a la base de datos.

---

## 🚀 Forma Rápida: Script Visualizador

La forma más fácil de ver todas las mejoras es ejecutar el script visualizador:

```bash
python3 scripts/view_database_improvements.py
```

Este script muestra:
- ✅ Todos los índices creados (15 nuevos)
- ✅ Todas las vistas creadas (16 nuevas)
- ✅ Estado del sistema de validación
- ✅ Estadísticas de tablas
- ✅ Comparación de rendimiento
- ✅ Ejemplos de uso

---

## 📊 Ver Mejoras de Rendimiento

### Ejecutar Benchmark

Para ver las mejoras de rendimiento en acción:

```bash
python3 scripts/benchmark_query_performance.py
```

Este script compara:
- Consultas originales vs optimizadas
- Tiempos de ejecución antes/después
- Mejora porcentual de cada función

**Resultados esperados:**
- `load_kpis_by_barrio`: **94.3% más rápido** ⚡
- `load_distrito_summary`: Nueva función (0.03ms)
- `load_distritos`: 0.4% mejora
- `load_precios`: 1.1% mejora

---

## 🔍 Ver Índices Creados

### Desde Python

```python
from src.database import DatabaseManager
import pandas as pd

db = DatabaseManager()
conn = db.get_connection()

# Ver todos los índices nuevos
query = """
    SELECT name, tbl_name 
    FROM sqlite_master 
    WHERE type = 'index' 
    AND name LIKE 'idx_%'
    ORDER BY name
"""
df = pd.read_sql(query, conn)
print(df)

conn.close()
```

### Desde SQLite CLI

```bash
sqlite3 data/processed/database.db

# Ver todos los índices
.schema

# Ver índices específicos
SELECT name, tbl_name 
FROM sqlite_master 
WHERE type = 'index' 
AND name LIKE 'idx_%'
ORDER BY name;
```

---

## 📋 Ver Vistas Creadas

### Desde Python

```python
from src.database import DatabaseManager
import pandas as pd

db = DatabaseManager()
conn = db.get_connection()

# Ver todas las vistas nuevas
query = """
    SELECT name, sql 
    FROM sqlite_master 
    WHERE type = 'view' 
    AND (name LIKE '%_recent' OR name LIKE '%_historical' OR name LIKE 'vw_%')
    ORDER BY name
"""
df = pd.read_sql(query, conn)
print(df)

# Probar una vista
df_kpis = pd.read_sql("SELECT * FROM vw_kpis_por_barrio_anio WHERE anio = 2025 LIMIT 5", conn)
print(df_kpis)

conn.close()
```

### Desde SQLite CLI

```bash
sqlite3 data/processed/database.db

# Ver todas las vistas
SELECT name FROM sqlite_master WHERE type = 'view';

# Ver estructura de una vista
.schema vw_kpis_por_barrio_anio

# Consultar una vista
SELECT * FROM vw_kpis_por_barrio_anio WHERE anio = 2025 LIMIT 5;
```

---

## 🔒 Ver Sistema de Validación

### Verificar Checks de Integridad

```python
from src.database import DatabaseManager
import pandas as pd

db = DatabaseManager()
conn = db.get_connection()

# Ver todos los checks
df = pd.read_sql("""
    SELECT check_date, table_name, issue_type, affected_rows, resolved
    FROM integrity_checks
    ORDER BY check_date DESC
""", conn)

print(df)

# Ver solo issues pendientes
df_pending = pd.read_sql("""
    SELECT * FROM integrity_checks
    WHERE resolved = 0
    ORDER BY check_date DESC
""", conn)

print(f"Issues pendientes: {len(df_pending)}")

conn.close()
```

---

## ⚡ Probar Funciones Optimizadas

### Probar load_kpis_by_barrio_optimized

```python
from src.app.data_loader_optimized import load_kpis_by_barrio_optimized
import time

# Medir tiempo
start = time.perf_counter()
df = load_kpis_by_barrio_optimized(2025)
elapsed = (time.perf_counter() - start) * 1000

print(f"Tiempo: {elapsed:.2f}ms")
print(f"Registros: {len(df)}")
print(df.head())
```

### Probar load_distrito_summary_optimized

```python
from src.app.data_loader_optimized import load_distrito_summary_optimized

df = load_distrito_summary_optimized()
print(df)
```

### Comparar Rendimiento

```python
from src.app.data_loader import load_distritos
from src.app.data_loader_optimized import load_distritos_optimized
import time

# Original
start = time.perf_counter()
result1 = load_distritos()
time1 = (time.perf_counter() - start) * 1000

# Optimizada
start = time.perf_counter()
result2 = load_distritos_optimized()
time2 = (time.perf_counter() - start) * 1000

print(f"Original: {time1:.2f}ms")
print(f"Optimizada: {time2:.2f}ms")
print(f"Mejora: {((time1 - time2) / time1 * 100):.1f}%")
```

---

## 📈 Ver Estadísticas de Uso

### Verificar Uso de Vistas Recent

```python
from src.database import DatabaseManager
import pandas as pd

db = DatabaseManager()
conn = db.get_connection()

# Ver cuántos registros hay en vista recent vs tabla completa
df_recent = pd.read_sql("SELECT COUNT(*) as total FROM fact_precios_recent", conn)
df_all = pd.read_sql("SELECT COUNT(*) as total FROM fact_precios", conn)

print(f"Vista recent: {df_recent['total'].iloc[0]} registros")
print(f"Tabla completa: {df_all['total'].iloc[0]} registros")
print(f"Reducción: {((df_all['total'].iloc[0] - df_recent['total'].iloc[0]) / df_all['total'].iloc[0] * 100):.1f}%")

conn.close()
```

---

## 📚 Ver Documentación

### Documentos Disponibles

1. **Análisis y Sugerencias:**
   ```bash
   cat docs/DATABASE_IMPROVEMENTS_SUGGESTIONS.md
   ```

2. **Mejoras Críticas Aplicadas:**
   ```bash
   cat docs/CRITICAL_DB_IMPROVEMENTS_APPLIED.md
   ```

3. **Mejoras de Prioridad Media:**
   ```bash
   cat docs/MEDIUM_PRIORITY_DB_IMPROVEMENTS_APPLIED.md
   ```

4. **Resumen de Integración:**
   ```bash
   cat docs/VIEWS_INTEGRATION_SUMMARY.md
   ```

5. **Reporte Final:**
   ```bash
   cat docs/FINAL_INTEGRATION_REPORT.md
   ```

---

## 🎯 Ver Mejoras en el Dashboard

### Verificar que las Funciones Usan Vistas

Las funciones en `src/app/data_loader.py` ya usan las vistas automáticamente:

1. **`load_distritos()`** - Usa `vw_resumen_por_distrito` automáticamente
2. **`load_precios()`** - Usa `fact_precios_recent` para años recientes automáticamente

Para verificar en el código:

```python
# Ver el código actualizado
grep -n "vw_resumen_por_distrito\|fact_precios_recent" src/app/data_loader.py
```

### Probar en el Dashboard

1. Ejecutar el dashboard:
   ```bash
   streamlit run src/app/main.py
   ```

2. Observar tiempos de carga:
   - Los KPIs deberían cargar más rápido
   - Los filtros de distrito deberían ser más rápidos
   - Las consultas de datos recientes deberían ser más eficientes

---

## 🔧 Verificar desde SQLite Directamente

### Conectarse a la Base de Datos

```bash
sqlite3 data/processed/database.db
```

### Comandos Útiles

```sql
-- Ver todas las tablas y vistas
.tables

-- Ver estructura de una vista
.schema vw_kpis_por_barrio_anio

-- Ver todos los índices
SELECT name, tbl_name FROM sqlite_master WHERE type = 'index';

-- Consultar una vista optimizada
SELECT * FROM vw_kpis_por_barrio_anio WHERE anio = 2025 LIMIT 5;

-- Ver estadísticas de una tabla
SELECT COUNT(*) FROM fact_precios;
SELECT COUNT(*) FROM fact_precios_recent;

-- Verificar integridad
SELECT * FROM integrity_checks ORDER BY check_date DESC LIMIT 10;
```

---

## 📊 Resumen de Comandos Rápidos

```bash
# Ver todas las mejoras (recomendado)
python3 scripts/view_database_improvements.py

# Ver benchmark de rendimiento
python3 scripts/benchmark_query_performance.py

# Ver documentación completa
ls -la docs/*IMPROVEMENTS*.md docs/*INTEGRATION*.md

# Conectarse a la BD
sqlite3 data/processed/database.db
```

---

## ✅ Checklist de Verificación

- [ ] Ejecutar `view_database_improvements.py` - Ver todas las mejoras
- [ ] Ejecutar `benchmark_query_performance.py` - Ver mejoras de rendimiento
- [ ] Probar funciones optimizadas en Python
- [ ] Verificar vistas en SQLite
- [ ] Revisar documentación en `docs/`
- [ ] Probar dashboard y observar tiempos de carga

---

**¡Todas las mejoras están aplicadas y funcionando!** 🎉
