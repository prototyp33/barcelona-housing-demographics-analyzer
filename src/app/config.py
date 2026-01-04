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
    "effort": "Cividis",       # Optimizado para colorblind
    "change": "RdYlBu_r",      # Divergente seguro (evita rojo-verde)
    "correlation": "PuOr",     # Divergente púrpura-naranja (seguro)
}

# Años disponibles (se actualizará dinámicamente desde la BD)
DEFAULT_YEAR = 2023
MIN_YEAR = 2015
MAX_YEAR = 2025

# Tamaño de vivienda tipo para cálculos de esfuerzo
VIVIENDA_TIPO_M2 = 70

