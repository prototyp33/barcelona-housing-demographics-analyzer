"""
Motor de recomendaciones para barrios.

Incluye:
- Motor de recomendaciones multi-criterio
- Escenarios específicos de uso
"""

from .engine import recommend_barrios, calculate_barrio_score
from .scenarios import get_recommendations, SCENARIO_TYPES

__all__ = [
    "recommend_barrios",
    "calculate_barrio_score",
    "get_recommendations",
    "SCENARIO_TYPES",
]

