---
name: 🚀 Feature / Mejora
about: Dashboard de monitoreo de calidad de datos
title: "[FEATURE] Data Quality Monitoring Dashboard"
labels: enhancement, dashboard, streamlit, data-quality, priority-medium
assignees: ''
---

## 📌 Objetivo

Crear un dashboard interactivo en Streamlit para visualizar métricas de calidad de datos en tiempo real, permitiendo la detección temprana de problemas de datos y el seguimiento de KPIs de calidad.

**Valor de Negocio:**
- Detección temprana de problemas de datos antes de que afecten análisis
- Visibilidad continua del estado de calidad de datos
- Facilita el mantenimiento proactivo del pipeline ETL
- Mejora la confianza en los datos para toma de decisiones

## 🔍 Descripción del Problema

**Estado actual:**
- No hay visibilidad en tiempo real de la calidad de los datos
- Las métricas de calidad solo se verifican manualmente ejecutando scripts
- No hay alertas automáticas cuando la calidad cae por debajo de umbrales
- Los problemas de datos se detectan tarde, afectando análisis y visualizaciones

**Estado deseado:**
- Dashboard interactivo que muestre métricas de calidad en tiempo real
- Visualización histórica de la evolución de calidad
- Lista de issues detectados con severidad y fecha
- Capacidad de ejecutar validaciones manuales desde el dashboard
- Alertas visuales cuando métricas caen por debajo de objetivos

**Archivos afectados:**
- `src/app/pages/05_Data_Quality.py` (nuevo)
- `src/database.py` (posible extensión para métricas)
- `scripts/verify_integrity.py` (integración con dashboard)

## 📝 Pasos para Implementar

### 1. Crear página de Streamlit

```python
# src/app/pages/05_Data_Quality.py
"""
Dashboard de Quality Assurance de Datos.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from src.database import DatabaseManager

st.set_page_config(page_title="Data Quality", page_icon="🔍", layout="wide")

st.title("🔍 Data Quality Monitor")

# Cargar métricas
db = DatabaseManager()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Completeness", 
        "96.2%", 
        "+2.1%",
        help="Porcentaje de campos no nulos"
    )

with col2:
    st.metric(
        "Validity", 
        "98.5%", 
        "+0.5%",
        help="Datos dentro de rangos esperados"
    )

with col3:
    st.metric(
        "Consistency", 
        "94.8%", 
        "-1.2%",
        help="Coherencia entre fuentes"
    )

with col4:
    st.metric(
        "Timeliness", 
        "2 días", 
        delta_color="inverse",
        help="Antigüedad del dato más reciente"
    )

# Gráfico de evolución temporal
st.subheader("📈 Evolución de Calidad de Datos")

quality_history = pd.DataFrame({
    'fecha': pd.date_range('2024-01-01', '2025-12-01', freq='M'),
    'completeness': [92, 93, 94, 95, 95.5, 96, 96.2] + [96.2] * 17,
    'validity': [95, 96, 97, 97.5, 98, 98.2, 98.5] + [98.5] * 17,
})

fig = px.line(
    quality_history.melt(id_vars='fecha'),
    x='fecha',
    y='value',
    color='variable',
    title='Métricas de Calidad (Últimos 24 Meses)'
)
fig.add_hline(y=95, line_dash="dash", annotation_text="Target: 95%")
st.plotly_chart(fig, use_container_width=True)

# Tabla de issues detectados
st.subheader("⚠️ Issues Detectados")

issues_df = pd.DataFrame({
    'Barrio': ['Poblenou', 'Gràcia', 'Sant Martí'],
    'Issue': ['Missing precio_m2', 'Outlier edad_media', 'Duplicate entry'],
    'Severidad': ['High', 'Medium', 'Low'],
    'Detectado': ['2025-12-01', '2025-11-28', '2025-11-25']
})

st.dataframe(
    issues_df,
    use_container_width=True,
    column_config={
        "Severidad": st.column_config.SelectboxColumn(
            "Severidad",
            options=["Low", "Medium", "High"],
        ),
    }
)

# Botón para ejecutar validación manual
if st.button("🔄 Ejecutar Validación Manual"):
    with st.spinner("Validando datos..."):
        # Llamar a scripts/verify_integrity.py
        import subprocess
        result = subprocess.run(
            ["python", "scripts/verify_integrity.py"],
            capture_output=True,
            text=True
        )
        st.success("✅ Validación completada")
        st.code(result.stdout)
```

### 2. Integrar con DatabaseManager

```python
# Extender src/database.py para obtener métricas
def get_quality_metrics(self) -> dict:
    """Calcula métricas de calidad de datos."""
    # Implementar cálculo de completeness, validity, etc.
    pass
```

### 3. Conectar con verify_integrity.py

```python
# Modificar scripts/verify_integrity.py para retornar resultados estructurados
# que puedan ser consumidos por el dashboard
```

### 4. Añadir a navegación del dashboard

```python
# Asegurar que la página aparece en el menú lateral de Streamlit
```

## ✅ Definición de Hecho (Definition of Done)

- [ ] Página `05_Data_Quality.py` creada y funcional
- [ ] 4 métricas principales visibles (Completeness, Validity, Consistency, Timeliness)
- [ ] Gráfico de evolución temporal funcionando con datos reales
- [ ] Tabla de issues detectados muestra problemas reales de la base de datos
- [ ] Botón de validación manual ejecuta `verify_integrity.py` y muestra resultados
- [ ] Métricas se calculan desde la base de datos real (no hardcoded)
- [ ] Código sigue estilo del proyecto (black, type hints, docstrings)
- [ ] Tests unitarios para funciones de cálculo de métricas
- [ ] Documentación actualizada en `docs/` sobre el dashboard
- [ ] Dashboard accesible desde el menú principal de Streamlit

## 🎯 Impacto & KPI

- **KPI técnico:** 
  - Tiempo de detección de problemas de datos: De días → minutos
  - Visibilidad de calidad: 0% → 100% (dashboard siempre disponible)
  
- **Objetivo:** 
  - Detectar problemas de calidad antes de que afecten análisis
  - Mantener métricas de calidad ≥95% completeness, ≥98% validity
  
- **Métrica de éxito:** 
  - Dashboard muestra métricas reales calculadas desde DB
  - Issues detectados se reflejan en < 1 hora
  - Usuarios pueden ejecutar validaciones manuales exitosamente
  
- **Fuente de datos:** 
  - Base de datos SQLite (`data/processed/database.db`)
  - Scripts de validación (`scripts/verify_integrity.py`)

## 🔗 Issues Relacionadas

- Relacionada con: #67 (Validación de integridad referencial)
- Bloquea: - (no bloquea otras features)
- Depende de: - (puede implementarse independientemente)

## 🚧 Riesgos / Bloqueos

- **Riesgo:** Cálculo de métricas puede ser lento con datasets grandes
  - **Mitigación:** Implementar caching y cálculos incrementales
  
- **Riesgo:** `verify_integrity.py` puede no retornar formato estructurado
  - **Mitigación:** Modificar script para retornar JSON o crear wrapper
  
- **Dependencias externas:** 
  - Plotly para gráficos interactivos (ya en requirements.txt)
  
- **Accesos/credenciales pendientes:** Ninguno
  
- **Datos faltantes:** 
  - Necesitamos datos históricos de calidad para el gráfico temporal
  - Solución: Empezar a registrar métricas desde ahora, usar datos sintéticos inicialmente

## 📚 Enlaces Relevantes

- [Documentación Streamlit Pages](https://docs.streamlit.io/develop/api-reference/app-structure/st.set_page_config)
- [Plotly Express Documentation](https://plotly.com/python/plotly-express/)
- [Código relacionado: DatabaseManager](src/database.py)
- [Script de validación: verify_integrity.py](scripts/verify_integrity.py)

## 💡 Notas de Implementación

- **Estimación:** 4-5 horas
  - Implementación página Streamlit: 2 horas
  - Integración con DatabaseManager: 1 hora
  - Cálculo de métricas reales: 1 hora
  - Tests y documentación: 1 hora
  
- **Prioridad:** 🟡 Media
  
- **Sprint recomendado:** Sprint 3 (después de resolver issues críticas de calidad)
  
- **Consideraciones técnicas:**
  - Usar `st.cache_data` para cachear cálculos de métricas
  - Considerar usar `st.rerun()` para actualización automática periódica
  - Implementar alertas visuales cuando métricas < umbrales

