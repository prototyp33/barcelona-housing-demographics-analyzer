# Configuración de Logging para el Dashboard

Este documento explica cómo configurar y usar el sistema de logging mejorado del dashboard.

---

## 📋 Características

El sistema de logging incluye:

1. **Logging de rendimiento** - Tiempos de ejecución de funciones clave
2. **Logging de datos** - Información sobre qué datos se cargan (filas, columnas, etc.)
3. **Logging de consultas** - Tiempos de ejecución de queries SQL
4. **Logging de conexiones** - Estado de conexiones a la BD
5. **Logging a archivo** - Persistencia de logs para análisis posterior
6. **Componente de monitoreo** - Visualización de métricas en el dashboard

---

## 🚀 Configuración Rápida

### Opción 1: Habilitar logging básico (consola)

El logging básico ya está activo por defecto. Los logs aparecen en la consola donde ejecutas Streamlit.

### Opción 2: Habilitar logging a archivo

Crea o edita `.streamlit/secrets.toml`:

```toml
[logging]
enabled = true
level = "INFO"  # o "DEBUG" para más detalle
show_performance = true  # Muestra métricas en el sidebar
```

### Opción 3: Solo logging de consola (sin archivo)

No necesitas hacer nada. El logging básico ya está activo.

---

## 📊 Tipos de Logs

### 1. Logs de Rendimiento (`PERF`)

Miden el tiempo de ejecución de funciones:

```
PERF | load_kpis | 17.4ms | Keys: 12 | Args: () | Kwargs: {}
PERF | load_precios | 2.8ms | Rows: 73 | Cols: 5 | Args: (2024,) | Kwargs: {}
```

**Formato:**
- `PERF | <función> | <tiempo_ms>ms | <métricas> | Args: <args> | Kwargs: <kwargs>`

### 2. Logs de Carga de Datos (`DATA_LOAD`)

Información sobre qué datos se están cargando:

```
DATA_LOAD | load_precios | Year: 2024 | Distrito: All
DATA_LOAD | load_precios | Source: Local DB
DATA_LOAD | load_precios | Using optimized view: fact_precios_recent
DATA_LOAD | load_precios | Complete | Rows: 73 | Barrios: 73 | Avg precio: 3456.78€/m²
```

**Formato:**
- `DATA_LOAD | <función> | <información>`

### 3. Logs de Consultas SQL (`QUERY_START`, `QUERY_END`)

Tiempos de ejecución de queries (solo en modo DEBUG):

```
QUERY_START | load_kpis_stats | Params: None
QUERY_END | load_kpis_stats | 15.2ms | Success
```

### 4. Logs de Conexiones (`CONNECTION`)

Estado de conexiones a la base de datos:

```
CONNECTION | get_connection | Opening new connection
CONNECTION | get_connection | WAL mode: wal
CONNECTION | get_connection | DB locked, retry 1/3
```

### 5. Logs de Cache (`CACHE`)

Información sobre uso de cache (solo en modo DEBUG):

```
CACHE | load_kpis | HIT | 0.1ms
CACHE | load_precios | MISS | 52.0ms
```

---

## 🎛️ Niveles de Logging

### `INFO` (por defecto)

Muestra:
- Tiempos de ejecución de funciones principales
- Información sobre carga de datos
- Errores y advertencias
- Estado de conexiones

**Ejemplo:**
```
2026-01-15 18:54:09 | INFO | src.app.data_loader | DATA_LOAD | load_kpis | Starting
2026-01-15 18:54:09 | INFO | src.app.data_loader | PERF | load_kpis | 17.4ms | Keys: 12
```

### `DEBUG` (más detallado)

Incluye todo lo de INFO más:
- Consultas SQL individuales
- Cache hits/misses
- Detalles de conexiones
- Información de vistas optimizadas

**Ejemplo:**
```
2026-01-15 18:54:09 | DEBUG | src.app.data_loader | DATA_LOAD | load_distritos | Using optimized view: vw_resumen_por_distrito
2026-01-15 18:54:09 | DEBUG | CONNECTION | get_connection | WAL mode: wal
2026-01-15 18:54:09 | DEBUG | CACHE | load_kpis | HIT | 0.1ms
```

---

## 📁 Ubicación de Logs

Los logs se guardan en:

```
data/logs/dashboard.log
```

**Formato del archivo:**
```
2026-01-15 18:54:09 | INFO | src.app.data_loader | DATA_LOAD | load_kpis | Starting
2026-01-15 18:54:09 | INFO | src.app.data_loader | PERF | load_kpis | 17.4ms | Keys: 12
```

---

## 📊 Componente de Monitoreo en el Dashboard

Si `show_performance = true` en `secrets.toml`, verás una sección expandible en el sidebar con:

- **Métricas básicas**: Cache hits, conexiones DB, tiempo promedio de carga
- **Logs recientes**: Últimas 10 líneas del archivo de log
- **Resumen de rendimiento**: Errores, advertencias, tiempo promedio de queries

---

## 🔍 Ejemplos de Uso

### Ver logs en tiempo real

```bash
# Terminal 1: Ejecutar dashboard
streamlit run src/app/main.py

# Terminal 2: Ver logs en tiempo real
tail -f data/logs/dashboard.log
```

### Buscar errores

```bash
grep "ERROR" data/logs/dashboard.log
```

### Analizar tiempos de carga

```bash
grep "PERF" data/logs/dashboard.log | grep "load_kpis"
```

### Ver uso de vistas optimizadas

```bash
grep "optimized view" data/logs/dashboard.log
```

---

## 🛠️ Funciones con Logging

Las siguientes funciones incluyen logging detallado:

- ✅ `load_kpis()` - KPIs globales
- ✅ `load_precios()` - Precios de vivienda
- ✅ `load_distritos()` - Lista de distritos
- ✅ `get_connection()` - Conexiones a BD
- ✅ `load_available_years()` - Años disponibles
- ✅ `load_price_trends()` - Tendencias de precios

---

## 📈 Análisis de Logs

### Script de análisis básico

```python
import re
from pathlib import Path

log_file = Path("data/logs/dashboard.log")

# Leer logs
with open(log_file, "r") as f:
    lines = f.readlines()

# Extraer tiempos de load_kpis
kpis_times = []
for line in lines:
    if "PERF | load_kpis" in line:
        match = re.search(r'(\d+\.?\d*)\s*ms', line)
        if match:
            kpis_times.append(float(match.group(1)))

if kpis_times:
    print(f"Tiempo promedio load_kpis: {sum(kpis_times)/len(kpis_times):.1f}ms")
    print(f"Tiempo mínimo: {min(kpis_times):.1f}ms")
    print(f"Tiempo máximo: {max(kpis_times):.1f}ms")
```

---

## ⚙️ Configuración Avanzada

### Cambiar formato de logs

Edita `src/app/components/performance_monitor.py`:

```python
formatter = logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
```

### Agregar logging a nuevas funciones

Usa el decorator `@log_performance`:

```python
from src.app.data_loader import log_performance

@st.cache_data(ttl=3600)
@log_performance
def mi_nueva_funcion():
    # Tu código aquí
    pass
```

---

## 🐛 Troubleshooting

### Los logs no aparecen

1. Verifica que `logging.enabled = true` en `secrets.toml`
2. Verifica que el directorio `data/logs/` existe y tiene permisos de escritura
3. Revisa la consola donde ejecutas Streamlit (los logs básicos siempre aparecen ahí)

### Los logs son demasiado verbosos

1. Cambia `level = "INFO"` en lugar de `"DEBUG"`
2. O elimina `show_performance = true` del sidebar

### El componente de monitoreo no aparece

1. Verifica que `show_performance = true` en `secrets.toml`
2. Recarga el dashboard (F5)

---

## 📚 Referencias

- [Python Logging Documentation](https://docs.python.org/3/library/logging.html)
- [Streamlit Secrets Management](https://docs.streamlit.io/develop/concepts/configuration/secrets-management)

---

**Última actualización:** 2026-01-15
