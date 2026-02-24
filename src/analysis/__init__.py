"""
Módulo de análisis avanzado para insights accionables.

Incluye:
- Análisis descriptivos (tendencias, correlaciones, comparaciones)
- Modelos predictivos
- Forecasting de tendencias
- Clasificación de barrios
"""

from .data_access import (
    get_connection,
    get_neighborhood_data,
    get_available_years,
    get_districts,
    get_prices,
    get_yield_analysis,
    get_renta,
    get_demografia,
    get_affordability_data,
    get_temporal_comparison,
    get_correlation_data,
    get_kpis,
    get_price_trends,
    get_geojson,
    get_accessibility_metrics,
    get_safety_and_tourism,
)
from .descriptive import (
    calculate_trends,
    compare_barrios,
    identify_outliers,
    calculate_correlations,
    generate_scorecard,
)

__all__ = [
    "get_connection",
    "get_neighborhood_data",
    "get_available_years",
    "get_districts",
    "get_prices",
    "get_yield_analysis",
    "get_renta",
    "get_demografia",
    "get_affordability_data",
    "get_temporal_comparison",
    "get_correlation_data",
    "get_kpis",
    "get_price_trends",
    "get_geojson",
    "get_accessibility_metrics",
    "get_safety_and_tourism",
    "calculate_trends",
    "compare_barrios",
    "identify_outliers",
    "calculate_correlations",
    "generate_scorecard",
]
