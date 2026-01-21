"""
Configuración global del dashboard.

Define constantes, configuración de página y temas de visualización.
"""

from __future__ import annotations

from pathlib import Path

# Rutas
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "processed" / "database.db"
# Export consolidado para BI (Looker/Streamlit)
MASTER_TABLE_CSV_PATH = PROJECT_ROOT / "data" / "exports" / "looker_studio" / "master_table_barcelona_housing.csv"

# Configuración de página Streamlit
PAGE_CONFIG = {
    "page_title": "Barcelona Housing Analytics",
    "page_icon": "🏠",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

# Paleta de colores (Design System "Kristin" adaptado)
COLORS = {
    # Tokens del Design System
    "bg_canvas": "#F4F5F7",      # Fondo general (Light Grey)
    "bg_card": "#FFFFFF",        # Fondo de tarjetas
    "text_primary": "#1A1A1A",   # Títulos y cifras principales
    "text_secondary": "#8E92BC", # Subtítulos y metadatos
    "accent_blue": "#2F80ED",    # Botones y estados activos
    "accent_red": "#EB5757",     # Alertas y tendencias negativas
    "accent_green": "#27AE60",   # Éxito y tendencias positivas
    # Legacy (mantener para compatibilidad)
    "primary": "#E63946",        # Rojo Barcelona (deprecated, usar accent_red)
    "secondary": "#1D3557",      # Azul oscuro (deprecated)
    "background": "#F1FAEE",     # Blanco hueso (deprecated, usar bg_canvas)
}

# Escalas de color para mapas (colorblind-friendly)
# Ref: https://colorbrewer2.org/ - escalas seguras para daltonismo
COLOR_SCALES = {
    "prices": "Viridis",       # Seguro para deuteranopia/protanopia
    "effort": "RdYlBu_r",      # Divergente seguro (v1.1 SSOT)
    "change": "RdYlBu_r",      # Divergente seguro
    "correlation": "PuOr",     # Divergente púrpura-naranja (seguro)
    "yield": "Spectral",       # Accesible para rentabilidad (v1.1 SSOT)
}

# Metadatos por métrica (v1.1 SSOT)
METRIC_METADATA = {
    "Precio Venta": {
        "max_year": 2023, 
        "min_year": 2015, 
        "scale": COLOR_SCALES["prices"],
        "unit": "€/m²"
    },
    "Renta Mensual": {
        "max_year": 2022, 
        "min_year": 2022, 
        "scale": COLOR_SCALES["yield"],
        "unit": "€",
        "info": "Datos de renta disponibles únicamente para 2022"
    },
    "Esfuerzo Compra": {
        "max_year": 2022, 
        "min_year": 2022, 
        "scale": COLOR_SCALES["effort"],
        "unit": "Ratio",
        "info": "Basado en Renta 2022"
    },
    "Demografía": {
        "max_year": 2025, 
        "min_year": 2015, 
        "scale": "Viridis",
        "unit": "Personas"
    }
}

# Años disponibles (se actualizará dinámicamente desde la BD)
DEFAULT_YEAR = 2023
MIN_YEAR = 2015
MAX_YEAR = 2025

# Tamaño de vivienda tipo para cálculos de esfuerzo
VIVIENDA_TIPO_M2 = 70

# Estándares de Mapas (v1.1 SSOT) - Migrado a MapLibre
# Nota: Usar 'map' en lugar de 'mapbox' para evitar deprecation warnings
# Compatible con la nueva API de Plotly que usa MapLibre en lugar de Mapbox
MAP_CONFIG = {
    "map_style": "carto-positron",  # Estilo compatible con MapLibre
    "zoom": 10.5,
    "center": {"lat": 41.39, "lon": 2.17},
    "opacity": 0.7
}

# Mantener MAPBOX_CONFIG para compatibilidad durante la migración
MAPBOX_CONFIG = MAP_CONFIG

