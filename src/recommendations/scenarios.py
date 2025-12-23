"""
Escenarios específicos de recomendación de barrios.

Casos de uso:
- Mejor relación calidad-precio
- Barrios en crecimiento
- Barrios estables para familias
- Oportunidades de inversión
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from .engine import recommend_barrios, calculate_barrio_score

# Tipos de escenarios disponibles
SCENARIO_TYPES = [
    "mejor_calidad_precio",
    "barrios_crecimiento",
    "estables_familias",
    "oportunidades_inversion",
]


def get_recommendations(
    scenario: str,
    filters: Optional[Dict] = None,
    top_n: int = 10,
    db_path: Optional[Path] = None
) -> List[Dict]:
    """
    Obtiene recomendaciones para un escenario específico.
    
    Args:
        scenario: Tipo de escenario (ver SCENARIO_TYPES).
        filters: Filtros opcionales adicionales.
        top_n: Número de barrios a recomendar.
        db_path: Ruta opcional a la base de datos.
    
    Returns:
        Lista de barrios recomendados con explicaciones.
    """
    # Definir pesos por escenario
    scenario_weights = {
        "mejor_calidad_precio": {
            "affordability": 0.40,  # Prioridad alta en precio
            "calidad_vida": 0.40,   # Prioridad alta en calidad
            "oportunidad": 0.10,
            "estabilidad": 0.10,
        },
        "barrios_crecimiento": {
            "affordability": 0.20,
            "calidad_vida": 0.20,
            "oportunidad": 0.50,    # Prioridad alta en oportunidad
            "estabilidad": 0.10,
        },
        "estables_familias": {
            "affordability": 0.30,
            "calidad_vida": 0.40,   # Prioridad alta en calidad de vida
            "oportunidad": 0.10,
            "estabilidad": 0.20,    # Prioridad en estabilidad
        },
        "oportunidades_inversion": {
            "affordability": 0.20,
            "calidad_vida": 0.20,
            "oportunidad": 0.50,    # Prioridad muy alta en oportunidad
            "estabilidad": 0.10,
        },
    }
    
    if scenario not in scenario_weights:
        raise ValueError(f"Escenario '{scenario}' no válido. Disponibles: {SCENARIO_TYPES}")
    
    weights = scenario_weights[scenario]
    
    # Obtener recomendaciones
    recommendations = recommend_barrios(
        criteria=weights,
        top_n=top_n,
        min_score=50.0,
        db_path=db_path
    )
    
    # Añadir explicaciones para cada recomendación
    scenario_explanations = {
        "mejor_calidad_precio": "Mejor relación entre calidad de vida y precio",
        "barrios_crecimiento": "Barrios con alto potencial de crecimiento",
        "estables_familias": "Barrios estables ideales para familias",
        "oportunidades_inversion": "Barrios con oportunidades de inversión",
    }
    
    for rec in recommendations:
        rec["scenario"] = scenario
        rec["explanation"] = scenario_explanations.get(scenario, "")
        rec["reason"] = _generate_reason(rec, scenario)
    
    return recommendations


def _generate_reason(recommendation: Dict, scenario: str) -> str:
    """
    Genera una explicación de por qué se recomienda un barrio.
    
    Args:
        recommendation: Datos de la recomendación.
        scenario: Escenario de recomendación.
    
    Returns:
        String con la explicación.
    """
    scores = recommendation.get("scores", {})
    barrio_nombre = recommendation.get("barrio_nombre", "Barrio")
    
    reasons = []
    
    if scenario == "mejor_calidad_precio":
        if scores.get("affordability", 0) > 70:
            reasons.append("excelente relación precio-calidad")
        if scores.get("calidad_vida", 0) > 70:
            reasons.append("alta calidad de vida")
    
    elif scenario == "barrios_crecimiento":
        if scores.get("oportunidad", 0) > 70:
            reasons.append("alto potencial de crecimiento")
        if scores.get("affordability", 0) > 60:
            reasons.append("precios aún asequibles")
    
    elif scenario == "estables_familias":
        if scores.get("calidad_vida", 0) > 70:
            reasons.append("excelente calidad de vida")
        if scores.get("estabilidad", 0) > 70:
            reasons.append("alta estabilidad")
        if scores.get("affordability", 0) > 60:
            reasons.append("precios razonables")
    
    elif scenario == "oportunidades_inversion":
        if scores.get("oportunidad", 0) > 70:
            reasons.append("alto potencial de inversión")
        if scores.get("affordability", 0) > 50:
            reasons.append("precios accesibles")
    
    if not reasons:
        reasons.append("buen balance general de métricas")
    
    return f"{barrio_nombre} es recomendado porque tiene {', '.join(reasons)}."

