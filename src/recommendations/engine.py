"""
Motor de recomendaciones multi-criterio para barrios.

Calcula scores basados en:
- Affordability (precio vs. renta)
- Calidad de vida (seguridad, ruido)
- Oportunidad de inversión (tendencias)
- Estabilidad (volatilidad de precios)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import sqlite3

from ..database_setup import DEFAULT_DB_NAME

logger = logging.getLogger(__name__)


def _get_db_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """
    Obtiene conexión a la base de datos.
    
    Args:
        db_path: Ruta opcional a la base de datos.
    
    Returns:
        Conexión SQLite.
    """
    if db_path is None:
        project_root = Path(__file__).parent.parent.parent
        db_path = project_root / "data" / "processed" / DEFAULT_DB_NAME
    
    return sqlite3.connect(str(db_path))


def calculate_barrio_score(
    barrio_id: int,
    weights: Optional[Dict[str, float]] = None,
    db_path: Optional[Path] = None
) -> Dict:
    """
    Calcula score multi-criterio para un barrio.
    
    Args:
        barrio_id: ID del barrio.
        weights: Pesos opcionales para cada criterio (default: iguales).
        db_path: Ruta opcional a la base de datos.
    
    Returns:
        Diccionario con scores por criterio y score total.
    """
    conn = _get_db_connection(db_path)
    
    try:
        # Obtener datos del barrio desde scorecard
        query = """
            SELECT *
            FROM v_barrio_scorecard
            WHERE barrio_id = ?
        """
        
        df = pd.read_sql_query(query, conn, params=[barrio_id])
        
        if df.empty:
            logger.warning("No se encontró scorecard para barrio_id=%s", barrio_id)
            return {"barrio_id": barrio_id, "total_score": 0.0}
        
        row = df.iloc[0]
        
        # Obtener promedios de Barcelona para normalización
        query_avg = """
            SELECT 
                AVG(precio_m2_venta_promedio) AS precio_avg,
                AVG(renta_mediana_promedio) AS renta_avg,
                AVG(tasa_criminalidad_1000hab_promedio) AS criminalidad_avg,
                AVG(nivel_lden_medio_promedio) AS ruido_avg
            FROM v_barrio_scorecard
        """
        
        df_avg = pd.read_sql_query(query_avg, conn)
        avg_data = df_avg.iloc[0].to_dict() if not df_avg.empty else {}
        
        # Calcular scores normalizados (0-100)
        scores = {}
        
        # 1. Affordability (inverso: menor precio/renta = mejor)
        precio = row.get("precio_m2_venta_promedio", 0)
        renta = row.get("renta_mediana_promedio", 0)
        if precio > 0 and renta > 0 and avg_data.get("precio_avg", 0) > 0:
            ratio = precio / avg_data["precio_avg"]
            scores["affordability"] = max(0, min(100, 100 - (ratio - 1) * 50))
        else:
            scores["affordability"] = 50  # Neutral si no hay datos
        
        # 2. Calidad de vida (seguridad + ruido)
        criminalidad = row.get("tasa_criminalidad_1000hab_promedio", 0)
        ruido = row.get("nivel_lden_medio_promedio", 0)
        
        score_seguridad = 50
        if criminalidad > 0 and avg_data.get("criminalidad_avg", 0) > 0:
            ratio = criminalidad / max(avg_data["criminalidad_avg"], 1)
            score_seguridad = max(0, min(100, 100 - (ratio - 1) * 50))
        
        score_ruido = 50
        if ruido > 0 and avg_data.get("ruido_avg", 0) > 0:
            ratio = ruido / max(avg_data["ruido_avg"], 1)
            score_ruido = max(0, min(100, 100 - (ratio - 1) * 50))
        
        scores["calidad_vida"] = (score_seguridad + score_ruido) / 2
        
        # 3. Oportunidad de inversión (tendencias positivas)
        # Usar datos de riesgo de gentrificación si disponible
        query_risk = """
            SELECT score_riesgo_gentrificacion, pct_cambio_precio_5_anios
            FROM v_riesgo_gentrificacion
            WHERE barrio_id = ?
        """
        df_risk = pd.read_sql_query(query_risk, conn, params=[barrio_id])
        
        score_oportunidad = 50
        if not df_risk.empty:
            risk_score = df_risk.iloc[0].get("score_riesgo_gentrificacion", 50)
            cambio_precio = df_risk.iloc[0].get("pct_cambio_precio_5_anios", 0)
            # Mayor riesgo = mayor oportunidad (pero con límite)
            score_oportunidad = min(100, 50 + (risk_score / 2) + (cambio_precio / 10))
        
        scores["oportunidad"] = score_oportunidad
        
        # 4. Estabilidad (baja volatilidad = mejor)
        # Simplificado: asumir estabilidad media si no hay datos de volatilidad
        scores["estabilidad"] = 75  # Default: alta estabilidad
        
        # Pesos por defecto (iguales)
        if weights is None:
            weights = {
                "affordability": 0.25,
                "calidad_vida": 0.25,
                "oportunidad": 0.25,
                "estabilidad": 0.25,
            }
        
        # Calcular score total ponderado
        total_score = sum(scores[key] * weights.get(key, 0.25) for key in scores)
        
        return {
            "barrio_id": barrio_id,
            "barrio_nombre": row.get("barrio_nombre"),
            "scores": scores,
            "total_score": float(total_score),
            "weights": weights,
        }
    
    finally:
        conn.close()


def recommend_barrios(
    criteria: Optional[Dict[str, float]] = None,
    top_n: int = 10,
    min_score: float = 50.0,
    db_path: Optional[Path] = None
) -> List[Dict]:
    """
    Recomienda barrios basado en criterios multi-dimensionales.
    
    Args:
        criteria: Pesos opcionales para cada criterio.
        top_n: Número de barrios a recomendar.
        min_score: Score mínimo para incluir en recomendaciones.
        db_path: Ruta opcional a la base de datos.
    
    Returns:
        Lista de diccionarios con barrios recomendados y sus scores.
    """
    conn = _get_db_connection(db_path)
    
    try:
        # Obtener todos los barrios
        query = """
            SELECT barrio_id
            FROM dim_barrios
            ORDER BY barrio_id
        """
        
        df_barrios = pd.read_sql_query(query, conn)
        
        if df_barrios.empty:
            return []
        
        # Calcular scores para todos los barrios
        recommendations = []
        
        for _, row in df_barrios.iterrows():
            barrio_id = row["barrio_id"]
            
            try:
                score_data = calculate_barrio_score(barrio_id, criteria, db_path)
                
                if score_data["total_score"] >= min_score:
                    recommendations.append(score_data)
            
            except Exception as e:
                logger.warning("Error calculando score para barrio_id=%s: %s", barrio_id, e)
                continue
        
        # Ordenar por score total (descendente)
        recommendations.sort(key=lambda x: x["total_score"], reverse=True)
        
        # Retornar top N
        return recommendations[:top_n]
    
    finally:
        conn.close()

