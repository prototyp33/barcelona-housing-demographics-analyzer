# 🏠 Dashboard Scripts - Barcelona Housing Analytics

Scripts útiles para gestionar y ejecutar el dashboard Streamlit.

## 📋 Scripts Disponibles

### 0. `fix_demografia_warning.sh` - Corrector de Advertencias

Script interactivo para corregir la advertencia de `fact_demografia` vacía.

**Uso:**
```bash
./scripts/dashboard/fix_demografia_warning.sh
```

**Características:**
- ✅ Detecta si `fact_demografia` está vacía
- ✅ Verifica disponibilidad de datos raw
- ✅ Ofrece múltiples opciones de carga:
  - ETL completo (recomendado)
  - Solo procesamiento de demografía
  - Enriquecimiento de datos existentes
- ✅ Guía interactiva paso a paso
- ✅ Verifica el resultado después de la carga

**Cuándo usarlo:**
- Cuando el health check muestra: `⚠️ Tabla fact_demografia: existe pero está vacía`
- Después de una extracción de datos demográficos
- Para enriquecer datos demográficos existentes

---

### 1. `run_dashboard.sh` - Lanzador Principal

Script mejorado para ejecutar el dashboard con verificaciones y opciones.

**Uso básico:**
```bash
./scripts/dashboard/run_dashboard.sh
```

**Opciones:**
```bash
# Modo desarrollo (auto-reload habilitado)
./scripts/dashboard/run_dashboard.sh --dev

# Puerto personalizado
./scripts/dashboard/run_dashboard.sh --port 8502

# Solo verificar dependencias
./scripts/dashboard/run_dashboard.sh --check

# Ver ayuda
./scripts/dashboard/run_dashboard.sh --help
```

**Características:**
- ✅ Verificación automática de dependencias
- ✅ Liberación automática del puerto si está ocupado
- ✅ Configuración automática de PYTHONPATH
- ✅ Modo desarrollo con auto-reload
- ✅ Mensajes informativos con colores

---

### 2. `check_dashboard.sh` - Health Check Exhaustivo

Verificación exhaustiva de **todos** los componentes del dashboard.

**Uso:**
```bash
./scripts/dashboard/check_dashboard.sh
```

**Verifica (10 secciones completas):**

1. **Entorno y Dependencias**
   - Python 3 y versión
   - Todas las dependencias críticas (streamlit, pandas, plotly, geopandas, etc.)
   - Versiones de paquetes

2. **Estructura de Directorios y Archivos**
   - Directorios críticos del proyecto
   - Archivos principales del dashboard
   - **Todas las 13 vistas del dashboard** (market_cockpit, overview, map_analysis, etc.)

3. **Base de Datos - Estructura**
   - Existencia y tamaño de la base de datos
   - **8 tablas críticas** (dim_barrios, fact_precios, fact_demografia, etc.)
   - **Vistas optimizadas** (vw_gentrification_risk, vw_resumen_por_distrito, etc.)

4. **Integridad de Datos**
   - **73 barrios** completos
   - **GeoJSON** en barrios (para mapas)
   - **Rango de años** disponible
   - **Datos recientes** (últimos 2 años)
   - **Cobertura de datos** por tabla (%)

5. **Funciones de Carga de Datos**
   - Verifica que las **22 funciones de carga** sean importables
   - Valida que sean callables
   - Prueba imports sin errores

6. **Configuración y Estilos**
   - Configuración Streamlit (.streamlit/config.toml)
   - Funciones de estilos críticas (inject_global_css, render_kpi_card)

7. **Componentes Personalizados**
   - card_standard
   - render_breadcrumbs
   - render_empty_state

8. **API Client (Opcional)**
   - Verifica disponibilidad de API backend
   - Modo offline si no está disponible

9. **Puerto y Recursos**
   - Puerto 8501 disponible
   - Espacio en disco

10. **Verificación de Sintaxis**
    - Compila archivos Python críticos
    - Detecta errores de sintaxis antes de ejecutar

**Salida:**
- ✅ Verde: Todo correcto
- ⚠️ Amarillo: Advertencias (dashboard debería funcionar)
- ❌ Rojo: Errores (corregir antes de ejecutar)

**Ejemplo de salida:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🔍 Dashboard Comprehensive Health Check
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1. Entorno y Dependencias
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Python 3.11.5
✅ streamlit (1.28.0)
✅ pandas (2.1.0)
...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  3. Base de Datos - Estructura
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Base de datos existe (45M)
✅   Tabla dim_barrios: 73 registros
✅   Tabla fact_precios: 1247 registros
...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  4. Integridad de Datos
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Barrios: 73/73 (completo)
✅ Barrios con GeoJSON: 73/73
✅ Rango de años: 2015 - 2024 (10 años)
✅ Datos más recientes: 2024
✅   fact_precios: 73/73 barrios (100%)
...
```

---

### 3. `dashboard_helper.sh` - Helper Interactivo

Menú interactivo con múltiples opciones para gestionar el dashboard.

**Uso:**
```bash
./scripts/dashboard/dashboard_helper.sh
```

**Opciones del menú:**
1. 🚀 Iniciar dashboard (modo normal)
2. 🔧 Iniciar dashboard (modo desarrollo)
3. 🔍 Verificar estado del dashboard
4. 🛑 Detener dashboard (puerto 8501)
5. 📊 Ver logs del dashboard
6. 🧹 Limpiar cache de Streamlit
7. 📦 Verificar dependencias
8. 🌐 Abrir dashboard en navegador
9. 📝 Ver configuración
0. ❌ Salir

---

## 🚀 Inicio Rápido

### Opción 1: Script Simple (Recomendado)
```bash
./scripts/dashboard/run_dashboard.sh
```

### Opción 2: Helper Interactivo
```bash
./scripts/dashboard/dashboard_helper.sh
```

### Opción 3: Script Legacy (Compatibilidad)
```bash
./run_dashboard.sh
```

---

## 🔧 Requisitos Previos

1. **Python 3.11+** instalado
2. **Dependencias Python** instaladas:
   ```bash
   pip install -r requirements.txt
   ```
3. **Base de datos** generada:
   ```bash
   python src/etl/pipeline.py
   ```

---

## 📝 Ejemplos de Uso

### Desarrollo con Auto-reload
```bash
./scripts/dashboard/run_dashboard.sh --dev
```
El dashboard se recargará automáticamente cuando cambies archivos.

### Verificar Antes de Ejecutar (Recomendado)
```bash
# Verificación exhaustiva de todos los componentes
./scripts/dashboard/check_dashboard.sh
```

El script verifica:
- ✅ 13 vistas del dashboard
- ✅ 22 funciones de carga de datos
- ✅ 8 tablas críticas + vistas optimizadas
- ✅ Integridad de datos (73 barrios, GeoJSON, años)
- ✅ Sintaxis de archivos Python
- ✅ Y mucho más...

### Ejecutar en Puerto Diferente
```bash
./scripts/dashboard/run_dashboard.sh --port 8502
```

### Limpiar Cache y Reiniciar
```bash
# Usar helper interactivo
./scripts/dashboard/dashboard_helper.sh
# Seleccionar opción 6 (Limpiar cache)
# Luego opción 1 (Iniciar dashboard)
```

---

## 🐛 Troubleshooting

### Puerto ya en uso
```bash
# El script intenta liberar el puerto automáticamente
# Si falla, detén manualmente:
lsof -ti:8501 | xargs kill -9
```

### Dependencias faltantes
```bash
# Verificar qué falta
./scripts/dashboard/check_dashboard.sh

# Instalar dependencias
pip install -r requirements.txt
```

### Base de datos no encontrada
```bash
# Generar base de datos
python src/etl/pipeline.py
```

### Cache corrupto
```bash
# Limpiar cache
./scripts/dashboard/dashboard_helper.sh
# Opción 6: Limpiar cache
```

### fact_demografia vacía
```bash
# Script interactivo para cargar datos demográficos
./scripts/dashboard/fix_demografia_warning.sh
```

Este script:
- Verifica si `fact_demografia` está vacía
- Detecta si hay datos raw disponibles
- Ofrece opciones para cargar datos (ETL completo, solo demografía, enriquecimiento)
- Guía paso a paso para resolver la advertencia

---

## 📚 Estructura de Archivos

```
scripts/dashboard/
├── README.md              # Esta documentación
├── run_dashboard.sh       # Lanzador principal
├── check_dashboard.sh     # Health check
└── dashboard_helper.sh    # Helper interactivo
```

---

## 🔗 Enlaces Útiles

- **Dashboard URL**: http://localhost:8501
- **Documentación Streamlit**: https://docs.streamlit.io
- **Configuración**: `.streamlit/config.toml`
- **Logs**: `data/logs/dashboard.log`

---

## 💡 Tips

1. **Modo Desarrollo**: Usa `--dev` cuando estés desarrollando para auto-reload
2. **Health Check**: Ejecuta `check_dashboard.sh` antes de hacer deploy
3. **Helper Interactivo**: Útil cuando no recuerdas los comandos exactos
4. **Puerto Personalizado**: Útil si tienes múltiples dashboards corriendo

---

## 📝 Notas

- Todos los scripts son ejecutables (`chmod +x`)
- Los scripts verifican automáticamente el entorno
- Los mensajes usan colores para mejor legibilidad
- Compatible con macOS, Linux y WSL
