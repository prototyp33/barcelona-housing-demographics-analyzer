# Especificación Técnica: Dashboard Streamlit Barcelona Housing Analytics

**Versión:** 1.0  
**Fecha:** Enero 2026  
**Estado:** SSOT (Single Source of Truth)  
**Audiencia:** Desarrolladores Frontend, Diseñadores UX/UI, Arquitectos de Software

---

## 1. Introducción y Propósito

### 1.1 Visión Estratégica

El **Dashboard de Barcelona Housing Analytics** no es simplemente un visualizador de datos, sino un **Cockpit de Inteligencia de Mercado** diseñado para facilitar la toma de decisiones basada en datos (Data-Driven Decision Making) para dos perfiles principales:

- **Inversores inmobiliarios**: Necesitan identificar oportunidades de rentabilidad, evaluar el riesgo y comparar barrios según métricas financieras.
- **Urbanistas y analistas de políticas públicas**: Requieren entender la relación entre demografía, precios de vivienda y calidad de vida en los 73 barrios de Barcelona.

### 1.2 Principios de Diseño

El dashboard se fundamenta en tres pilares arquitectónicos:

1. **Modularidad**: Cada vista (tab) es independiente y puede evolucionar sin afectar otras secciones.
2. **Claridad Visual**: Prioriza la legibilidad y la jerarquía de información sobre efectos decorativos.
3. **Performance**: Optimizado para cargar grandes volúmenes de datos geográficos sin comprometer la experiencia del usuario.

### 1.3 Alcance del Documento

Este documento establece:

- La arquitectura de información y navegación del dashboard.
- Los protocolos técnicos para el manejo de datos geográficos y estadísticos.
- Las directrices de diseño visual y UX.
- La estructura de archivos y organización del código.
- Los estándares de implementación para componentes reutilizables.

---

## 2. Arquitectura de Información

### 2.1 Estructura de Navegación Principal

El dashboard utiliza un sistema de **Tabs de alto nivel** para organizar las funcionalidades principales. Esta estructura permite a los usuarios cambiar de contexto sin perder el estado de los filtros globales.

#### 2.1.1 Tabs Principales

```
🏘️ Market          → Vista táctica del mercado actual
📊 Insights        → Análisis avanzado y correlaciones
💰 Inversión       → Métricas de rentabilidad y scoring
🚨 Alertas         → Detección automática de anomalías
💡 Recomendaciones → Sugerencias basadas en ML
📄 Reportes        → Exportación y documentación
```

**Implementación técnica:**

```python
# src/app/main.py
tab1, tab2, tab_inv, tab3, tab4, tab5 = st.tabs([
    "🏘️ Market",
    "📊 Insights",
    "💰 Inversión",
    "🚨 Alertas",
    "💡 Recomendaciones",
    "📄 Reportes",
])
```

#### 2.1.2 Jerarquía Visual

```
┌─────────────────────────────────────────────────────────┐
│  Sidebar (Filtros Globales)  │  Contenido Principal     │
│                             │                          │
│  • Identidad Visual         │  • Breadcrumbs           │
│  • Configuración de Vista   │  • Tabs de Navegación    │
│  • Filtros Temporales       │  • Visualizaciones       │
│  • Metadatos                │  • KPIs                  │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Componentes de Navegación

#### 2.2.1 Sidebar (Panel Lateral)

**Propósito**: Proporcionar contexto global y controles de filtrado que afectan a todas las vistas.

**Elementos obligatorios**:

1. **Identidad Visual**:
   - Logo o icono del proyecto (44x44px)
   - Nombre del proyecto: "Barcelona Housing Analytics"
   - Subtítulo: "Housing Analytics"

2. **Configuración de Vista**:
   - Selector de **Métrica Principal**: `["Precio Venta", "Renta Mensual", "Esfuerzo Compra", "Demografía"]`
   - Filtro de **Distrito**: `["Todos"] + lista_distritos`
   - Slider de **Año de Análisis**: Rango dinámico basado en datos disponibles

3. **Metadatos de Datos**:
   - Fecha de última actualización
   - Fuentes de datos (OpenData BCN, Idealista, IDESCAT)
   - Contador de registros totales
   - Versión del dashboard

**Implementación de referencia**: `src/app/main.py` líneas 44-153

#### 2.2.2 Breadcrumbs (Migas de Pan)

**Propósito**: Facilitar la navegación profunda y mostrar la ubicación actual del usuario.

**Estructura estándar**:

```
Home > Dashboard > [Distrito/Global] > [Vista Actual]
```

**Implementación técnica**:

```python
# src/app/components.py
def render_breadcrumbs(crumbs: list[dict[str, str]]) -> None:
    """
    Renderiza breadcrumbs navegables.
    
    Args:
        crumbs: Lista de diccionarios con 'label' y 'path'
    """
    # Ver implementación en src/app/components.py
```

#### 2.2.3 Header Dinámico

**Propósito**: Mostrar el contexto actual de forma clara y concisa.

**Contenido**:

- Título principal que refleja el filtro de distrito activo
- Subtítulo con la métrica seleccionada y el año
- Campo de búsqueda de barrios (opcional, fase futura)

**Ejemplo de renderizado**:

```python
# src/app/main.py líneas 156-177
def render_custom_header(distrito_filter: str | None, metric_name: str, year: int) -> None:
    if distrito_filter:
        display_title = f"Monitor de Mercado: {distrito_filter}"
    else:
        display_title = "Monitor de Mercado: Global BCN"
```

---

## 3. Especificaciones Técnicas de Datos

### 3.1 Integridad Territorial: Sistema de Identificadores

#### 3.1.1 Uso Mandatorio de `barrio_id`

**Regla crítica**: Todos los componentes que trabajen con datos geográficos DEBEN usar `barrio_id` (entero 1-73) como identificador único. Este identificador es el enlace entre:

- Las tablas de hechos (`fact_precios`, `fact_demografia`)
- La dimensión geográfica (`dim_barrios`)
- Los archivos GeoJSON para visualización en mapas

**Optimización de Carga (v1.1)**: 
Para evitar latencia innecesaria en el renderizado de mapas, el GeoJSON de los 73 barrios debe considerarse un recurso estático.
- **Recomendación**: Almacenar el GeoJSON pre-procesado en un archivo `data/processed/barrios_geo.json`.
- **Implementación**: Cargar una sola vez al inicio de la aplicación y almacenar en `st.session_state` o usar `@st.cache_resource`.

**Implementación correcta**:

```python
# ✅ CORRECTO: Usar barrio_id para enlace con GeoJSON
import plotly.express as px

@st.cache_resource
def get_geojson():
    with open("data/processed/barrios_geo.json") as f:
        return json.load(f)

geojson_data = get_geojson()

fig = px.choropleth_mapbox(
    df,
    geojson=geojson_data,
    locations="barrio_id",      # Columna del DataFrame
    featureidkey="id",          # Propiedad 'id' en GeoJSON (DEBE ser el barrio_id)
    color="precio_m2_venta",
    # ... otros parámetros
)
```

**Estructura GeoJSON requerida**:

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "id": 1,  // ← DEBE coincidir con barrio_id del DataFrame
      "geometry": { /* geometría del barrio */ }
    }
  ]
}
```

**Carga de geometrías desde la base de datos**:

```python
# Cargar geometrías desde dim_barrios.geometry_json
import sqlite3
import json
import pandas as pd

conn = sqlite3.connect("data/processed/database.db")
df_geometries = pd.read_sql_query("""
    SELECT barrio_id, geometry_json 
    FROM dim_barrios 
    WHERE geometry_json IS NOT NULL
""", conn)

# Parsear JSON strings a diccionarios
geometries = {}
for _, row in df_geometries.iterrows():
    geometries[row['barrio_id']] = json.loads(row['geometry_json'])

# Crear FeatureCollection
geojson_data = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "id": barrio_id,  # CRÍTICO: Debe ser entero 1-73
            "geometry": geom
        }
        for barrio_id, geom in geometries.items()
    ]
}
```

**Referencia**: `.cursor/rules/300-visualization.mdc` líneas 44-117

#### 3.1.2 Validación de Datos Geográficos

Antes de renderizar cualquier mapa, se DEBE validar:

```python
# Validación obligatoria antes de visualizar
assert len(df) > 0, "DataFrame vacío"
assert df['barrio_id'].notna().all(), "Valores NULL en barrio_id"
assert df['barrio_id'].between(1, 73).all(), "barrio_id fuera de rango válido (1-73)"

# Validar geometrías disponibles
df_geometries = pd.read_sql_query("""
    SELECT barrio_id, geometry_json 
    FROM dim_barrios 
    WHERE geometry_json IS NOT NULL
""", conn)
assert len(df_geometries) == 73, f"Esperadas 73 geometrías, encontradas {len(df_geometries)}"
```

### 3.2 Tratamiento Estadístico: Manejo de Outliers

#### 3.2.1 Clipping de Outliers mediante Cuantiles

**Problema**: Barcelona tiene outliers extremos que distorsionan las escalas cromáticas:
- **Pedralbes**: Precios muy altos (>6,000 €/m²)
- **Ciutat Vella**: Precios muy bajos (<2,000 €/m²)

**Solución**: Aplicar clipping estadístico usando cuantiles 0.05 y 0.95 en todas las escalas de color para mapas y gráficos de distribución.

**Implementación obligatoria**:

```python
# Calcular rango de color con clipping de outliers
q05 = df['precio_m2_venta'].quantile(0.05)
q95 = df['precio_m2_venta'].quantile(0.95)

fig = px.choropleth_mapbox(
    df,
    geojson=geojson_data,
    locations="barrio_id",
    featureidkey="id",
    color="precio_m2_venta",
    range_color=[q05, q95],  # ← OBLIGATORIO: Clipping de outliers
    color_continuous_scale="Viridis",
    # ... otros parámetros
)
```

**Excepciones**: Los gráficos de distribución (box plots, histogramas) pueden mostrar outliers sin clipping para análisis estadístico completo.

**Referencia**: `.cursor/rules/300-visualization.mdc` líneas 136-158

### 3.3 Estándares de Visualización Mapbox

#### 3.3.1 Configuración Fija de Mapas

Todos los mapas DEBEN usar la siguiente configuración estándar:

```python
MAPBOX_CONFIG = {
    "mapbox_style": "carto-positron",  # Estilo neutro, legible
    "zoom": 10.5,                      # Zoom óptimo para Barcelona
    "center": {"lat": 41.39, "lon": 2.17},  # Centro de Barcelona
    "opacity": 0.7                     # Transparencia para superposición
}
```

**Implementación en Plotly**:

```python
import plotly.express as px

fig = px.choropleth_mapbox(
    df,
    geojson=geojson_data,
    locations="barrio_id",
    featureidkey="id",
    color="precio_m2_venta",
    mapbox_style="carto-positron",  # ← OBLIGATORIO
    zoom=10.5,                      # ← OBLIGATORIO
    center={"lat": 41.39, "lon": 2.17},  # ← OBLIGATORIO
    opacity=0.7,                    # ← OBLIGATORIO
    # ... otros parámetros
)

# Eliminar márgenes para aprovechar todo el espacio
fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
```

**Justificación**:
- `carto-positron`: Estilo minimalista que no compite con los datos.
- Zoom 10.5: Muestra todos los 73 barrios sin requerir scroll excesivo.
- Centro (41.39, 2.17): Punto geográfico central de Barcelona.

**Referencia**: `.cursor/rules/300-visualization.mdc` líneas 9-42

### 3.4 Semántica del Color: Escalas Cromáticas

#### 3.4.1 Reglas de Selección de Escalas (v1.1: Accesibilidad)

La elección de la escala de color DEBE seguir la semántica de los datos y garantizar la accesibilidad para usuarios con daltonismo.

| Tipo de Dato | Escala Recomendada | Justificación |
|--------------|-------------------|---------------|
| **Neutral/Volumen** (Precios, Población, Densidad) | `Viridis` | Perceptualmente uniforme, óptima para daltonismo |
| **Positivo/Negativo** (Rentabilidad, Ingresos, Crecimiento) | `Spectral` o `RdYlBu` | Más accesible que RdYlGn para protanopia/deuteranopia |
| **Riesgo/Esfuerzo** (Esfuerzo de compra, Índice de riesgo) | `RdYlBu_r` | Invertido: Rojo/Cálido = alto riesgo/esfuerzo |
| **Correlación** (Matrices de correlación) | `PuOr` | Divergente púrpura-naranja, alto contraste |

**Nota sobre Accesibilidad**: Evitar el uso estricto de `RdYlGn` (Rojo-Verde) a menos que se implemente un "Modo Accesible" que lo sustituya por escalas divergentes seguras.

**Implementación**:

```python
# Precios de vivienda (neutral)
fig = px.choropleth_mapbox(
    df,
    color="precio_m2_venta",
    color_continuous_scale="Viridis",  # ← Neutral
    # ...
)

# Rentabilidad (positivo/negativo)
fig = px.choropleth_mapbox(
    df,
    color="yield_pct",
    color_continuous_scale="RdYlGn",  # ← Verde = alto yield
    # ...
)

# Esfuerzo de compra (riesgo)
fig = px.choropleth_mapbox(
    df,
    color="esfuerzo_compra",
    color_continuous_scale="RdYlGn_r",  # ← Rojo = alto esfuerzo
    # ...
)
```

**Referencia**: `src/app/config.py` líneas 40-47 y `.cursor/rules/300-visualization.mdc` líneas 119-134

---

## 4. Componentes Visuales Principales

### 4.1 KPIs (Key Performance Indicators)

#### 4.1.1 Definición de Estructura (v1.1: Tipado Fuerte)

Para asegurar la integridad de los componentes visuales, se recomienda el uso de `Dataclasses` para definir las métricas. Esto evita errores de claves faltantes en diccionarios.

```python
from dataclasses import dataclass
from typing import Optional, Literal

@dataclass
class KPIMetric:
    title: str
    value: float | str
    style: Literal["white", "warm", "cool"] = "white"
    delta: Optional[str] = None
    delta_color: Literal["green", "red", "normal"] = "normal"
    unit: Optional[str] = None
    is_currency: bool = False
```

El dashboard DEBE mostrar al menos estos cuatro KPIs principales en la vista Market:

1. **Rentabilidad Bruta (Yield)**:
   - Fórmula: `(Alquiler Mensual × 12) / (Precio_m² × 70) × 100`
   - Unidad: Porcentaje (%)
   - Estilo: Gradiente "cool" (azul)
   - Delta: "Retorno Anual"

2. **Registros de Precios**:
   - Descripción: Total de registros históricos disponibles
   - Unidad: Número entero (formato: 1,234)
   - Estilo: Gradiente "warm" (naranja)
   - Delta: Rango de años (ej: "2015-2023")

3. **Precio Medio Venta**:
   - Descripción: Precio promedio por metro cuadrado
   - Unidad: €/m²
   - Estilo: Gradiente "cool" (azul)
   - Delta: Variación interanual (ej: "+5.2% vs 2021")

4. **Renta Media Anual**:
   - Descripción: Renta disponible promedio por hogar
   - Unidad: € (formato: 25,000)
   - Estilo: Fondo blanco
   - Delta: Año de referencia (ej: "Dato 2022")

**Implementación técnica**:

```python
# src/app/main.py líneas 183-237
kpi_data = [
    {
        "title": "Rentabilidad Bruta",
        "value": f"{yield_pct:.1f}%",
        "style": "white",
        "delta": "Retorno Anual",
        "delta_color": "green",
    },
    # ... más KPIs
]

render_responsive_kpi_grid(kpi_data)
```

**Componente de referencia**: `src/app/styles.py` función `render_responsive_kpi_grid()` líneas 671-701

#### 4.1.2 Grid Responsive de KPIs

Los KPIs DEBEN renderizarse en un grid CSS que se adapta automáticamente al ancho de la pantalla:

```css
.bh-kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 24px;
}

@media (max-width: 640px) {
    .bh-kpi-grid {
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    }
}
```

**Implementación**: `src/app/styles.py` líneas 202-213

### 4.2 Visualizaciones Principales

#### 4.2.1 Gráfico de Evolución Temporal

**Propósito**: Mostrar la tendencia histórica de precios por año.

**Tipo**: Gráfico de líneas (Plotly Line Chart)

**Características**:
- Marcadores en cada punto de datos
- Hover interactivo con información detallada
- Eje X: Años (dtick=1 para mostrar todos los años)
- Eje Y: Precio medio (€/m²)

**Implementación de referencia**: `src/app/views/overview.py` función `render_price_evolution()` líneas 60-116

#### 4.2.2 Mapa de Coropletas (Choropleth Map)

**Propósito**: Visualizar la distribución geográfica de una métrica (precios, rentabilidad, etc.) sobre los 73 barrios.

**Tipo**: Plotly Choropleth Mapbox

**Características obligatorias**:
- GeoJSON cargado desde `dim_barrios.geometry_json`
- Enlace mediante `barrio_id` y `featureidkey="id"`
- Clipping de outliers (cuantiles 0.05 y 0.95)
- Estilo `carto-positron`
- Zoom 10.5, centro (41.39, 2.17)

**Implementación de referencia**: `.cursor/rules/300-visualization.mdc` líneas 209-250

#### 4.2.3 Comparativa de Distritos/Barrios

**Propósito**: Ranking visual de distritos o barrios según una métrica.

**Tipo**: Gráfico de barras horizontales (Plotly Bar Chart)

**Características**:
- Orientación horizontal para legibilidad de nombres
- Ordenamiento ascendente o descendente según contexto
- Etiquetas de valor fuera de las barras
- Altura dinámica según número de elementos

**Implementación de referencia**: `src/app/views/overview.py` función `render_distrito_comparison()` líneas 119-206

### 4.3 Componentes de Filtrado

#### 4.3.1 Selector de Métrica Principal

**Ubicación**: Sidebar

**Opciones**:
- `"Precio Venta"`: Enfoque en precios de compra
- `"Renta Mensual"`: Enfoque en mercado de alquiler
- `"Esfuerzo Compra"`: Ratio precio/renta
- `"Demografía"`: Variables poblacionales

**Efecto**: Cambia la variable principal mostrada en KPIs y mapas.

#### 4.3.2 Filtro de Distrito

**Ubicación**: Sidebar

**Opciones**: `["Todos"] + lista_distritos`

**Efecto**:
- Si `"Todos"`: Vista global de Barcelona
- Si distrito específico: Vista local con ranking de barrios dentro del distrito

**Implementación**: `src/app/main.py` líneas 81-84

#### 4.3.3 Slider de Año

**Comportamiento Dinámico (v1.1)**:
- Rango dinámico basado en datos disponibles en `fact_precios`.
- **Lógica de Año Máximo por Métrica**: Algunas métricas tienen una ventana temporal limitada (ej: Renta Mensual solo disponible para 2022).
- **Implementación**: El Slider debe ajustar su `max_value` y `value` según la métrica seleccionada en el sidebar para evitar estados inconsistentes o errores de "Data Not Found".

**Ejemplo de Configuración en `config.py`**:
```python
METRIC_METADATA = {
    "Precio Venta": {"max_year": 2023, "min_year": 2015},
    "Renta Mensual": {"max_year": 2022, "min_year": 2022},  # Bloqueado a 2022
    "Demografía": {"max_year": 2025, "min_year": 2015}
}
```

---

## 5. Guía de Estilo y UX

### 5.1 Design System: Tokens de Color

El dashboard utiliza el Design System "Kristin" adaptado, definido en `src/app/styles.py`.

#### 5.1.1 Paleta de Colores Base

```python
COLOR_TOKENS = {
    "bg_canvas": "#F4F5F7",      # Fondo general (Light Grey)
    "bg_card": "#FFFFFF",        # Fondo de tarjetas
    "text_primary": "#1A1A1A",   # Títulos y cifras principales
    "text_secondary": "#8E92BC", # Subtítulos y metadatos
    "accent_blue": "#2F80ED",    # Botones y estados activos
    "accent_red": "#EB5757",     # Alertas y tendencias negativas
    "accent_green": "#27AE60",   # Éxito y tendencias positivas
}
```

**Uso**:
- `bg_canvas`: Fondo de la aplicación (con gradiente mesh sutil)
- `bg_card`: Fondo de todas las tarjetas y contenedores
- `text_primary`: Texto principal (títulos H1, H2, valores de KPIs)
- `text_secondary`: Texto secundario (subtítulos, etiquetas, metadatos)
- `accent_blue`: Color primario de acción (botones, tabs activos, enlaces)
- `accent_red`: Indicadores de riesgo o tendencias negativas
- `accent_green`: Indicadores de éxito o tendencias positivas

**Referencia**: `src/app/styles.py` líneas 16-28

#### 5.1.2 Gradientes Mesh para KPIs

```python
GRADIENTS = {
    "warm": "linear-gradient(135deg, #FF9966 0%, #FF5E62 100%)",
    "cool": "linear-gradient(135deg, #56CCF2 0%, #2F80ED 100%)",
}
```

**Uso**:
- `warm`: KPIs relacionados con volumen o actividad (registros, transacciones)
- `cool`: KPIs relacionados con valor o rentabilidad (precios, yield)

**Referencia**: `src/app/styles.py` líneas 30-34

### 5.2 Tipografía

#### 5.2.1 Familia de Fuentes

**Fuente principal**: `Inter` (Google Fonts)

**Fallbacks**: `'Inter', 'DM Sans', 'Roboto', sans-serif`

**Justificación**: Inter es una fuente sans-serif moderna, optimizada para legibilidad en pantallas y con excelente soporte para números.

**Implementación**:

```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

font-family: 'Inter', 'DM Sans', 'Roboto', sans-serif !important;
```

**Referencia**: `src/app/styles.py` líneas 46-47

#### 5.2.2 Escala Tipográfica

| Elemento | Tamaño | Peso | Uso |
|----------|--------|------|-----|
| H1 (Page Title) | 32px | 700 (Bold) | Títulos principales de página |
| H2 (Card Title) | 18px | 600 (Semi-Bold) | Títulos de tarjetas |
| H3 | 16px | 600 (Semi-Bold) | Subtítulos de sección |
| Body | 14px | 400 (Regular) | Texto de párrafo |
| Caption | 14px | 400 (Regular) | Metadatos, etiquetas |

**Referencia**: `src/app/styles.py` líneas 133-174

### 5.3 Componentes de UI Reutilizables

#### 5.3.1 Tarjetas (Cards)

**Componente**: `card_standard()` (context manager)

**Características**:
- Fondo blanco (`bg_card`)
- Border radius: 24px
- Sombra suave (`shadow_elevation_1`)
- Padding: 24px (configurable)
- Header opcional con título, subtítulo y badge

**Uso**:

```python
from src.app.components import card_standard

with card_standard(
    title="Evolución del Mercado",
    subtitle="Datos 2015-2023",
    badge="Nuevo",
    badge_color="blue"
):
    st.plotly_chart(fig)
```

**Referencia**: `src/app/components.py` líneas 15-100

#### 5.3.2 Skeletons de Carga

**Propósito**: Mostrar placeholders durante la carga de datos pesados para mejorar la percepción de performance.

**Implementación**:

```python
# src/app/styles.py líneas 475-492
.skeleton {
    background: linear-gradient(
        90deg,
        #F0F2F5 0%,
        #E0E0E0 20%,
        #F0F2F5 40%,
        #F0F2F5 100%
    );
    background-size: 1000px 100%;
    animation: shimmer 1.5s infinite linear;
    border-radius: 12px;
}
```

**Uso**:

```python
# src/app/main.py líneas 234-237
if st.session_state.get("loading_kpis", False):
    render_skeleton_kpi(4)
else:
    render_responsive_kpi_grid(kpi_data)
```

#### 5.3.3 Estados Vacíos (Empty States)

**Propósito**: Informar al usuario cuando no hay datos disponibles en lugar de mostrar gráficos vacíos.

**Componente**: `render_empty_state()`

**Características**:
- Icono descriptivo
- Título claro
- Descripción de la causa (opcional)
- Acción sugerida (opcional)

**Uso**:

```python
from src.app.components import render_empty_state

if df.empty:
    render_empty_state(
        title="Sin datos de precios",
        description="No hay datos históricos para el filtro seleccionado.",
        icon="📉"
    )
    return
```

**Referencia**: `src/app/components.py` (buscar función `render_empty_state`)

### 5.4 Micro-interacciones y Feedback

#### 5.4.1 Hover States

**KPIs**: Elevación sutil y aumento de sombra al pasar el mouse.

```css
.bh-kpi-card:hover {
    transform: translateY(-4px) scale(1.01);
    box-shadow: 0px 20px 50px rgba(29, 22, 23, 0.15);
}
```

**Referencia**: `src/app/styles.py` líneas 466-473

#### 5.4.2 Transiciones

**Duración estándar**: 0.3s con easing `cubic-bezier(0.4, 0, 0.2, 1)`

**Aplicación**: Transformaciones, cambios de color, cambios de sombra.

### 5.5 Responsive Design

#### 5.5.1 Breakpoints

| Dispositivo | Ancho Máximo | Ajustes |
|-------------|--------------|---------|
| Mobile | 640px | Grid de KPIs: 1 columna, Tabs: scroll horizontal |
| Tablet | 1024px | Grid de KPIs: 2 columnas |
| Desktop | >1024px | Grid de KPIs: 4 columnas (auto-fit) |

#### 5.5.2 Grid Adaptativo de KPIs

```css
.bh-kpi-grid {
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
}

@media (max-width: 640px) {
    .bh-kpi-grid {
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    }
}
```

**Referencia**: `src/app/styles.py` líneas 202-213

---

## 6. Estructura de Archivos y Organización

### 6.1 Arquitectura de Módulos

```
src/app/
├── main.py              # Punto de entrada, orquestación de tabs
├── config.py            # Constantes y configuración global
├── styles.py            # Design System, CSS injection, componentes visuales
├── components.py        # Componentes reutilizables (cards, breadcrumbs, etc.)
├── data_loader.py       # Funciones de carga de datos desde BD
├── utils.py             # Utilidades (formateo de moneda, etc.)
└── views/               # Módulos de vista por tab
    ├── overview.py      # Vista Market (legacy, en transición)
    ├── market_cockpit.py # Vista Market (nueva implementación)
    ├── advanced_analytics.py  # Vista Insights
    ├── investment_analysis.py # Vista Inversión
    ├── alerts.py        # Vista Alertas
    ├── recommendations.py # Vista Recomendaciones
    ├── map_analysis.py  # Componente de mapas reutilizable
    ├── demographics.py  # Análisis demográfico
    ├── correlations.py # Análisis de correlaciones
    ├── data_quality.py  # Métricas de calidad de datos
    └── data_dictionary.py # Diccionario de datos
```

### 6.2 Responsabilidades por Módulo

#### 6.2.1 `src/app/main.py`

**Responsabilidades**:
- Configuración inicial de la página (`configure_page()`)
- Renderizado del sidebar con filtros globales (`render_sidebar()`)
- Orquestación de tabs principales
- Renderizado del header dinámico (`render_custom_header()`)
- Gestión del estado de sesión (filtros, métricas seleccionadas)

**NO debe contener**:
- Lógica de visualización específica (delegar a `views/`)
- Consultas SQL directas (usar `data_loader.py`)
- Estilos CSS inline (usar `styles.py`)

**Referencia**: `src/app/main.py` completo

#### 6.2.2 `src/app/styles.py`

**Responsabilidades**:
- Inyección de CSS global (`inject_global_css()`)
- Definición de tokens de color y gradientes
- Funciones de renderizado de componentes visuales (KPIs, rankings)
- Aplicación de tema Plotly (`apply_plotly_theme()`)

**NO debe contener**:
- Lógica de negocio
- Consultas a base de datos
- Cálculos de métricas

**Referencia**: `src/app/styles.py` completo

#### 6.2.3 `src/app/views/`

**Responsabilidades**:
- Implementación de la lógica de visualización específica de cada tab
- Carga de datos necesarios para la vista (usando `data_loader.py`)
- Renderizado de gráficos y tablas específicos
- Manejo de estados vacíos y errores

**Estructura estándar de un módulo de vista**:

```python
"""
Vista: [Nombre de la Vista]

Descripción breve de la funcionalidad.
"""

from __future__ import annotations

import streamlit as st
import plotly.express as px
from src.app.data_loader import load_*
from src.app.components import card_standard, render_empty_state
from src.app.styles import apply_plotly_theme, COLOR_TOKENS

def render(year: int, distrito_filter: str | None = None, key_prefix: str = "view_name") -> None:
    """
    Renderiza la vista completa.
    
    Args:
        year: Año seleccionado
        distrito_filter: Filtro de distrito (None = todos)
        key_prefix: Prefijo para claves únicas de componentes Plotly
    """
    st.header("Título de la Vista")
    
    # Cargar datos
    df = load_datos_especificos(year, distrito_filter)
    
    if df.empty:
        render_empty_state(
            title="Sin datos",
            description="No hay datos disponibles para los filtros seleccionados.",
            icon="📊"
        )
        return
    
    # Renderizar visualizaciones
    with card_standard(title="Gráfico Principal"):
        fig = crear_grafico(df)
        apply_plotly_theme(fig)
        st.plotly_chart(fig, key=f"{key_prefix}_main_chart")
```

**Referencia**: `src/app/views/overview.py` como ejemplo

#### 6.2.4 `src/app/data_loader.py`

**Responsabilidades**:
- Abstracción de consultas SQL a funciones Python reutilizables
- Validación de datos antes de retornar
- Manejo de errores de conexión a BD
- Caché de consultas frecuentes (usando `@st.cache_data`)

**Estructura estándar**:

```python
@st.cache_data(ttl=3600)  # Cache por 1 hora
def load_precios(year: int, distrito_filter: str | None = None) -> pd.DataFrame:
    """
    Carga datos de precios para un año y distrito específicos.
    
    Args:
        year: Año a cargar
        distrito_filter: Nombre del distrito (None = todos)
    
    Returns:
        DataFrame con columnas: barrio_id, barrio_nombre, distrito_nombre, avg_precio_m2
    
    Raises:
        ValueError: Si el año está fuera del rango válido
    """
    # Validación
    if year < 2015 or year > 2025:
        raise ValueError(f"Año {year} fuera del rango válido (2015-2025)")
    
    # Consulta SQL
    query = """
        SELECT 
            b.barrio_id,
            b.barrio_nombre,
            b.distrito_nombre,
            AVG(p.precio_m2_venta) as avg_precio_m2
        FROM fact_precios p
        JOIN dim_barrios b ON p.barrio_id = b.barrio_id
        WHERE p.anio = ?
    """
    params = [year]
    
    if distrito_filter:
        query += " AND b.distrito_nombre = ?"
        params.append(distrito_filter)
    
    query += " GROUP BY b.barrio_id, b.barrio_nombre, b.distrito_nombre"
    
    # Ejecutar y retornar
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    return df
```

**Referencia**: `src/app/data_loader.py` completo

### 6.3 Convenciones de Nomenclatura

#### 6.3.1 Funciones de Renderizado

**Patrón**: `render_*` para funciones que renderizan componentes visuales.

**Ejemplos**:
- `render_sidebar()`
- `render_kpi_card()`
- `render_price_evolution()`
- `render_distrito_comparison()`

#### 6.3.2 Funciones de Carga de Datos

**Patrón**: `load_*` para funciones que cargan datos desde la BD.

**Ejemplos**:
- `load_precios()`
- `load_kpis()`
- `load_distritos()`
- `load_available_years()`

#### 6.3.3 Claves de Componentes Plotly

**Patrón**: `{key_prefix}_{component_name}` para evitar conflictos cuando el mismo gráfico se renderiza múltiples veces.

**Ejemplos**:
- `"dashboard_price_evolution"`
- `"overview_distrito_comparison"`
- `"market_cockpit_map"`

---

## 7. Ejemplo de Implementación Completa

### 7.1 Vista Market: Estructura Recomendada

```python
"""
Vista Market - Cockpit de Mercado Inmobiliario

Muestra una visión táctica del mercado actual con KPIs, evolución temporal
y mapa de distribución geográfica.
"""

from __future__ import annotations

import streamlit as st
import plotly.express as px
import pandas as pd
from src.app.data_loader import load_precios, load_kpis, load_available_years
from src.app.components import card_standard, card_chart, render_empty_state
from src.app.styles import render_responsive_kpi_grid, apply_plotly_theme, COLOR_TOKENS

def render(year: int, distrito_filter: str | None = None, key_prefix: str = "market") -> None:
    """
    Renderiza la vista Market completa.
    
    Args:
        year: Año seleccionado
        distrito_filter: Filtro de distrito (None = todos)
        key_prefix: Prefijo para claves únicas
    """
    st.header("🏘️ Market Cockpit")
    
    # Sección 1: KPIs Principales
    kpis = load_kpis()
    kpi_data = [
        {
            "title": "Rentabilidad Bruta",
            "value": calcular_yield(kpis),
            "style": "cool",
            "delta": "Retorno Anual",
        },
        {
            "title": "Precio Medio Venta",
            "value": kpis.get('precio_medio_actual', 0),
            "is_currency": True,
            "unit": "€/m²",
            "style": "cool",
            "delta": f"vs {year-1}: {calcular_variacion(kpis)}%",
        },
        # ... más KPIs
    ]
    render_responsive_kpi_grid(kpi_data)
    
    # Sección 2: Evolución Temporal y Mapa
    col_main, col_map = st.columns([2, 1])
    
    with col_main:
        with card_chart(title="📈 Evolución del Mercado"):
            render_price_evolution(year, distrito_filter, key=f"{key_prefix}_evolution")
    
    with col_map:
        with card_chart(title="🗺️ Distribución Geográfica"):
            render_map_snapshot(year, distrito_filter, key=f"{key_prefix}_map")
    
    # Sección 3: Ranking de Barrios/Distritos
    st.markdown("### 📋 Ranking por Precio")
    render_ranking(year, distrito_filter, key=f"{key_prefix}_ranking")


def render_price_evolution(
    year: int,
    distrito_filter: str | None,
    key: str
) -> None:
    """Renderiza gráfico de evolución temporal."""
    years_info = load_available_years()
    min_year = years_info["fact_precios"]["min"] or 2015
    max_year = years_info["fact_precios"]["max"] or 2023
    
    data = []
    for y in range(min_year, max_year + 1):
        df = load_precios(y, distrito_filter)
        if not df.empty:
            avg_precio = df["avg_precio_m2"].mean()
            data.append({"año": y, "precio_medio": avg_precio})
    
    if not data:
        render_empty_state(
            title="Sin datos históricos",
            description="No hay datos disponibles para el período seleccionado.",
            icon="📉"
        )
        return
    
    df_evolution = pd.DataFrame(data)
    
    fig = px.line(
        df_evolution,
        x="año",
        y="precio_medio",
        markers=True,
        title="Evolución del Precio Medio (€/m²)",
        labels={"año": "Año", "precio_medio": "Precio Medio (€/m²)"},
    )
    
    fig.update_traces(
        line=dict(color=COLOR_TOKENS["accent_blue"], width=3),
        marker=dict(size=10, color=COLOR_TOKENS["accent_blue"]),
    )
    
    apply_plotly_theme(fig)
    fig.update_layout(hovermode="x unified", xaxis=dict(dtick=1))
    
    st.plotly_chart(fig, key=key, use_container_width=True)


def render_map_snapshot(
    year: int,
    distrito_filter: str | None,
    key: str
) -> None:
    """Renderiza mapa de coropletas."""
    df = load_precios(year, distrito_filter)
    
    if df.empty:
        render_empty_state(
            title="Sin datos geográficos",
            description="No hay datos disponibles para visualizar en el mapa.",
            icon="🗺️"
        )
        return
    
    # Cargar geometrías (ver sección 3.1.1)
    geojson_data = load_geometries()
    
    # Clipping de outliers
    q05 = df['avg_precio_m2'].quantile(0.05)
    q95 = df['avg_precio_m2'].quantile(0.95)
    
    fig = px.choropleth_mapbox(
        df,
        geojson=geojson_data,
        locations="barrio_id",
        featureidkey="id",
        color="avg_precio_m2",
        range_color=[q05, q95],
        color_continuous_scale="Viridis",
        mapbox_style="carto-positron",
        zoom=10.5,
        center={"lat": 41.39, "lon": 2.17},
        opacity=0.7,
        labels={"avg_precio_m2": "Precio (€/m²)"},
    )
    
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    
    st.plotly_chart(fig, key=key, use_container_width=True)


def render_ranking(
    year: int,
    distrito_filter: str | None,
    key: str
) -> None:
    """Renderiza ranking de barrios o distritos."""
    df = load_precios(year)
    
    if df.empty:
        render_empty_state(
            title="Sin datos para ranking",
            description="No hay datos disponibles para generar el ranking.",
            icon="📋"
        )
        return
    
    if distrito_filter:
        # Ranking de barrios dentro del distrito
        df_filtered = df[df["distrito_nombre"] == distrito_filter]
        ranking_data = (
            df_filtered.groupby("barrio_nombre")["avg_precio_m2"]
            .mean()
            .sort_values(ascending=True)
            .reset_index()
        )
        title = f"Ranking de Barrios: {distrito_filter} ({year})"
        y_col = "barrio_nombre"
    else:
        # Ranking de distritos
        ranking_data = (
            df.groupby("distrito_nombre")["avg_precio_m2"]
            .mean()
            .sort_values(ascending=True)
            .reset_index()
        )
        title = f"Precio Medio por Distrito ({year})"
        y_col = "distrito_nombre"
    
    fig = px.bar(
        ranking_data,
        x="avg_precio_m2",
        y=y_col,
        orientation="h",
        title=title,
        labels={"avg_precio_m2": "Precio (€/m²)", y_col: "Barrio" if distrito_filter else "Distrito"},
        text="avg_precio_m2",
    )
    
    fig.update_traces(
        marker_color=COLOR_TOKENS["accent_blue"],
        texttemplate='%{text:,.0f}€',
        textposition='outside',
    )
    
    apply_plotly_theme(fig)
    fig.update_layout(showlegend=False, height=max(350, len(ranking_data) * 30))
    
    st.plotly_chart(fig, key=key, use_container_width=True)
```

---

## 8. Checklist de Implementación (v1.1 Ampliado)

### 8.1 Robustez Técnica y Error Handling
- [ ] **Manejo de SQLite Locks**: ¿Se implementó un reintento o manejo de excepciones para `sqlite3.OperationalError: database is locked`?
- [ ] **Validación de Tipos**: ¿Se usan Dataclasses o Pydantic para el paso de parámetros a componentes UI?
- [ ] **Logging Estratégico**: ¿Se registran las consultas de los usuarios (distritos/años) para análisis de uso?

### 8.2 Protocolo de Exportación
- [ ] **Formatos de Datos**: ¿El Tab de Reportes permite exportar en CSV para análisis externo?
- [ ] **Reportes Profesionales**: ¿Se ha definido si las exportaciones PDF usarán `ReportLab` o si se generarán via HTML (`Playwright`)?

### 8.3 UX y Visualización
- [ ] **Accesibilidad**: ¿Los mapas usan escalas seguras para daltonismo (Viridis/Spectral)?
- [ ] **Latencia**: ¿El GeoJSON se carga desde un recurso estático cacheado?

---

## 9. Referencias y Recursos

### 9.1 Documentación del Proyecto

- **Reglas de Visualización**: `.cursor/rules/300-visualization.mdc`
- **Configuración Global**: `src/app/config.py`
- **Design System**: `src/app/styles.py`
- **Componentes Reutilizables**: `src/app/components.py`

### 9.2 Librerías Externas

- **Streamlit**: https://docs.streamlit.io/
- **Plotly**: https://plotly.com/python/
- **Plotly Mapbox**: https://plotly.com/python/mapbox-layers/
- **GeoPandas**: https://geopandas.org/ (para procesamiento de geometrías)

### 9.3 Estándares de Color

- **ColorBrewer**: https://colorbrewer2.org/ (escalas seguras para daltonismo)
- **Viridis**: https://matplotlib.org/stable/tutorials/colors/colormaps.html#viridis

---

## 10. Glosario de Términos

- **barrio_id**: Identificador único numérico (1-73) para cada barrio de Barcelona.
- **Choropleth Map**: Mapa temático donde áreas se colorean según el valor de una variable.
- **Clipping de Outliers**: Técnica estadística para limitar el rango de valores extremos en visualizaciones.
- **Cockpit**: Interfaz de control que muestra información crítica de forma concentrada.
- **Design System**: Conjunto de componentes, estilos y patrones reutilizables.
- **GeoJSON**: Formato estándar para codificar estructuras de datos geográficos.
- **KPI (Key Performance Indicator)**: Métrica clave que mide el rendimiento de un aspecto específico.
- **SSOT (Single Source of Truth)**: Principio de diseño donde una única fuente contiene la información autoritativa.

---

**Fin del Documento**

*Este documento es la única fuente de verdad (SSOT) para el desarrollo del dashboard Streamlit. Cualquier cambio en la arquitectura o estándares debe reflejarse aquí primero.*

