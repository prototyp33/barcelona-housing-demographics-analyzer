# Mejoras Sugeridas para `src/app/main.py`

## Resumen Ejecutivo

Este documento detalla las mejoras sugeridas para el archivo principal del dashboard Streamlit. Las mejoras están organizadas por categoría y prioridad.

---

## 🔴 Críticas (Alta Prioridad)

### 1. Eliminar Código de Debug
**Ubicación:** Líneas 185-188  
**Problema:** Código de logging de debug que no debería estar en producción.

```python
# #region agent log
import json, time; from pathlib import Path; log_path = Path('/Users/adrianiraeguialvear/Projects/barcelona-housing-demographics-analyzer/.cursor/debug.log'); log_entry = {"id": "log_" + str(time.time()), "timestamp": int(time.time() * 1000), "location": "src/app/main.py:main", "message": "Entering main()", "sessionId": "debug-syntax-check", "runId": "run1", "hypothesisId": "A"}; 
with log_path.open("a") as f: f.write(json.dumps(log_entry) + "\n")
# #endregion
```

**Solución:** Eliminar completamente este bloque de código.

---

### 2. Corregir Posición del Docstring
**Ubicación:** Línea 189  
**Problema:** El docstring está después del código de debug, debería estar al inicio de la función.

**Solución:** Mover el docstring a la línea 184, justo después de `def main() -> None:`.

---

### 3. Eliminar Imports No Utilizados
**Ubicación:** Líneas 29-30, 35, 39-40  
**Problema:** Varios imports que no se usan en el archivo.

**Imports no utilizados:**
- `VIVIENDA_TIPO_M2` (línea 29)
- `METRIC_METADATA` (línea 29) - aunque se usa en `get_dynamic_metric_metadata()`, no se usa directamente aquí
- `format_smart_currency` (línea 30)
- `load_precios` (línea 35)
- `card_standard, card_chart, card_snapshot, card_metric, render_skeleton_kpi` (línea 39)
- `render_responsive_kpi_grid, render_ranking_item, KPIMetric` (línea 40)

**Solución:** Eliminar estos imports para mantener el código limpio.

---

## 🟡 Importantes (Prioridad Media)

### 4. Mejorar Manejo de Excepciones
**Ubicación:** Líneas 229-248, 156-157, 276-277  
**Problema:** Uso de `except Exception:` genérico que captura todos los errores sin distinción.

**Solución:** Usar excepciones más específicas y agregar logging:

```python
import logging

logger = logging.getLogger(__name__)

# En lugar de:
except Exception as e:
    st.error(f"⚠️ Error loading Investment Analysis view: {str(e)}")

# Usar:
except (FileNotFoundError, KeyError, ValueError) as e:
    logger.error(f"Error loading Investment Analysis view: {e}", exc_info=True)
    st.error(f"⚠️ Error loading Investment Analysis view: {str(e)}")
except Exception as e:
    logger.critical(f"Unexpected error in Investment Analysis: {e}", exc_info=True)
    st.error(f"⚠️ Error inesperado. Por favor, contacta al soporte.")
```

---

### 5. Extraer Constantes Mágicas
**Ubicación:** Varias líneas  
**Problema:** Strings hardcodeados que deberían ser constantes.

**Constantes a extraer:**
- `"Todos"` (línea 99)
- `"Home"`, `"Dashboard"`, `"Global BCN"` (líneas 199-203)
- Nombres de tabs (líneas 208-216)
- Rutas de reportes: `"stakeholder_report_*.html"` (líneas 142, 262)
- Mensajes de error repetidos

**Solución:** Crear constantes en `config.py` o al inicio del módulo:

```python
# Constantes de navegación
DISTRITO_FILTER_ALL = "Todos"
BREADCRUMB_HOME = "Home"
BREADCRUMB_DASHBOARD = "Dashboard"
BREADCRUMB_GLOBAL = "Global BCN"

# Patrones de archivos
REPORT_FILE_PATTERN = "stakeholder_report_*.html"
REPORTS_DIR = "docs/reports"
```

---

### 6. Mejorar Type Hints
**Ubicación:** Línea 66  
**Problema:** El tipo de retorno usa `str | None` que es Python 3.10+, pero podría ser más explícito.

**Solución:** Usar `Optional[str]` para compatibilidad o mantener `str | None` si se garantiza Python 3.10+:

```python
from typing import Optional, Tuple

def render_sidebar() -> Tuple[int, Optional[str], str]:
    """
    Renderiza el sidebar estilo cockpit con identidad, filtros y metadatos.
    
    Returns:
        Tupla con (año seleccionado, filtro de distrito, métrica seleccionada).
    """
```

---

### 7. Simplificar Configuración de Path
**Ubicación:** Líneas 14-25  
**Problema:** Código complejo para configurar el path que podría simplificarse.

**Solución:** Extraer a una función helper o simplificar:

```python
def _setup_project_path() -> Path:
    """
    Configura el path del proyecto y lo añade a sys.path si es necesario.
    
    Returns:
        Path del directorio raíz del proyecto.
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    project_root_str = str(project_root)
    
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)
    
    # Actualizar PYTHONPATH si es necesario
    pythonpath = os.environ.get('PYTHONPATH', '')
    if project_root_str not in pythonpath:
        separator = ':' if pythonpath else ''
        os.environ['PYTHONPATH'] = f"{project_root_str}{separator}{pythonpath}"
    
    return project_root

# Al inicio del archivo:
PROJECT_ROOT = _setup_project_path()
```

---

## 🟢 Mejoras Adicionales (Prioridad Baja)

### 8. Agregar Logging para Errores
**Problema:** No hay logging cuando ocurren errores en las vistas.

**Solución:** Agregar logging antes de mostrar errores al usuario:

```python
import logging

logger = logging.getLogger(__name__)

# En cada try/except:
try:
    investment_analysis.render(year=selected_year)
except Exception as e:
    logger.error(
        f"Error rendering Investment Analysis view: {e}",
        exc_info=True,
        extra={"year": selected_year}
    )
    st.error(f"⚠️ Error loading Investment Analysis view: {str(e)}")
```

---

### 9. Extraer Lógica de Reportes a Función Helper
**Ubicación:** Líneas 140-157, 261-277  
**Problema:** Código duplicado para buscar y descargar reportes.

**Solución:** Crear función helper:

```python
def _get_latest_report() -> Optional[Path]:
    """
    Busca el reporte ejecutivo más reciente.
    
    Returns:
        Path del reporte más reciente o None si no se encuentra.
    """
    try:
        reports_dir = PROJECT_ROOT / "docs" / "reports"
        report_files = list(reports_dir.glob(REPORT_FILE_PATTERN))
        if report_files:
            return sorted(report_files)[-1]
    except Exception as e:
        logger.warning(f"Error buscando reportes: {e}")
    return None

def _render_report_download(report_path: Path) -> None:
    """Renderiza el botón de descarga de reporte."""
    with open(report_path, "rb") as f:
        st.download_button(
            label="📥 Descargar Reporte Ejecutivo",
            data=f,
            file_name=report_path.name,
            mime="text/html",
            help="Descarga el último reporte ejecutivo generado en formato HTML."
        )
```

---

### 10. Mejorar Documentación de Funciones
**Problema:** Algunas funciones no tienen docstrings completos.

**Solución:** Agregar docstrings completos siguiendo el estándar Google:

```python
def render_sidebar() -> Tuple[int, Optional[str], str]:
    """
    Renderiza el sidebar estilo cockpit con identidad, filtros y metadatos.
    
    El sidebar incluye:
    - Logo e identidad de la aplicación
    - Selector de métrica principal
    - Filtro por distrito
    - Selector de año (dinámico según métrica)
    - Información sobre los datos
    - Botones de descarga
    
    Returns:
        Tupla con:
        - selected_year: Año seleccionado para el análisis
        - distrito_filter: Nombre del distrito filtrado o None si es "Todos"
        - selected_metric: Nombre de la métrica principal seleccionada
    
    Raises:
        ValueError: Si no hay métricas disponibles en los metadatos.
    """
```

---

### 11. Validar Datos de Entrada
**Problema:** No hay validación de los valores retornados por `render_sidebar()`.

**Solución:** Agregar validación antes de usar los valores:

```python
selected_year, distrito_filter, selected_metric = render_sidebar()

# Validar valores
if not selected_metric:
    st.error("⚠️ No se pudo cargar la métrica seleccionada.")
    st.stop()

if selected_year < 2015 or selected_year > 2025:
    st.warning(f"⚠️ Año fuera del rango esperado: {selected_year}")
```

---

### 12. Mejorar Mensajes de Error al Usuario
**Problema:** Algunos mensajes de error están en inglés cuando deberían estar en español.

**Solución:** Traducir todos los mensajes al español:

```python
# En lugar de:
st.info("This view is temporarily unavailable. Please try another view.")

# Usar:
st.info("Esta vista no está disponible temporalmente. Por favor, prueba otra vista.")
```

---

## 📋 Checklist de Implementación

- [ ] Eliminar código de debug (líneas 185-188)
- [ ] Mover docstring de `main()` a posición correcta
- [ ] Eliminar imports no utilizados
- [ ] Mejorar manejo de excepciones con tipos específicos
- [ ] Agregar logging para errores
- [ ] Extraer constantes mágicas
- [ ] Simplificar configuración de path
- [ ] Extraer lógica de reportes a función helper
- [ ] Mejorar docstrings de funciones
- [ ] Agregar validación de datos de entrada
- [ ] Traducir mensajes de error al español
- [ ] Ejecutar linter y corregir warnings
- [ ] Ejecutar tests para verificar que no se rompió nada

---

## 🎯 Priorización Recomendada

1. **Fase 1 (Crítica):** Items 1-3 (debug, docstring, imports)
2. **Fase 2 (Importante):** Items 4-7 (excepciones, constantes, type hints, path)
3. **Fase 3 (Mejoras):** Items 8-12 (logging, helpers, documentación, validación)

---

## 📝 Notas Adicionales

- Todas las mejoras mantienen la funcionalidad existente
- Se recomienda implementar en orden de prioridad
- Después de cada fase, ejecutar tests para verificar que todo funciona
- Considerar crear un archivo de constantes separado si el número de constantes crece
