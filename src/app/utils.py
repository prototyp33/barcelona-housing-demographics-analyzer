"""
Utilidades de formateo y constantes compartidas para el dashboard.
"""

def format_smart_currency(value: float) -> str:
    """
    Formatea valores monetarios de forma profesional.
    Ej: 1500000 -> "1,5M €"
    Ej: 1250 -> "1.250 €"
    """
    if not value or value == 0:
        return "—"
    
    if abs(value) >= 1_000_000:
        return f"{value/1_000_000:.1f}M €".replace('.', ',')
    
    # Formato con separador de miles . y moneda €
    return f"{value:,.0f} €".replace(',', 'X').replace('.', ',').replace('X', '.')

def get_noise_level_color(db_value: float) -> str:
    """
    Retorna el color semántico basado en el nivel de ruido (dB).
    Umbrales: <55 (verde), 55-65 (amarillo), >65 (rojo).
    """
    if db_value < 55:
        return "green"
    if db_value <= 65:
        return "orange"
    return "red"

# Paleta de colores profesional del reporte
PROFESSIONAL_COLORS = {
    'primary': '#005EB8',  # Azul Barcelona
    'success': '#10B981',  # Verde
    'warning': '#F59E0B',  # Amarillo
    'danger': '#EF4444',   # Rojo
}

