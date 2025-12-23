"""
Módulo de análisis avanzado para insights accionables.

Incluye:
- Análisis descriptivos (tendencias, correlaciones, comparaciones)
- Modelos predictivos
- Forecasting de tendencias
- Clasificación de barrios
"""

from .descriptive import (
    calculate_trends,
    compare_barrios,
    identify_outliers,
    calculate_correlations,
    generate_scorecard,
)

__all__ = [
    "calculate_trends",
    "compare_barrios",
    "identify_outliers",
    "calculate_correlations",
    "generate_scorecard",
]
