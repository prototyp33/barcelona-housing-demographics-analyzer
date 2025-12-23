"""
Análisis descriptivos avanzados para insights accionables.

Funciones para calcular tendencias, comparar barrios, identificar outliers,
calcular correlaciones y generar scorecards completos.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
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


def calculate_trends(
    barrio_id: int,
    metric: str,
    years: Optional[List[int]] = None,
    db_path: Optional[Path] = None
) -> Dict:
    """
    Calcula tendencias temporales de una métrica para un barrio.
    
    Detecta cambios significativos, calcula tasas de crecimiento y
    identifica puntos de inflexión.
    
    Args:
        barrio_id: ID del barrio.
        metric: Nombre de la métrica (ej: 'precio_m2_venta', 'poblacion_total').
        years: Lista opcional de años a analizar. Si None, usa todos disponibles.
        db_path: Ruta opcional a la base de datos.
    
    Returns:
        Diccionario con:
        - values: Lista de valores por año
        - years: Lista de años
        - trend_direction: 'increasing', 'decreasing', 'stable'
        - growth_rate: Tasa de crecimiento anual promedio (%)
        - significant_changes: Lista de cambios significativos detectados
        - inflection_points: Años donde hay cambios de tendencia
    """
    conn = _get_db_connection(db_path)
    
    try:
        # Mapear métricas a tablas y columnas
        metric_mapping = {
            "precio_m2_venta": ("fact_precios", "precio_m2_venta"),
            "precio_mes_alquiler": ("fact_precios", "precio_mes_alquiler"),
            "poblacion_total": ("fact_demografia", "poblacion_total"),
            "renta_mediana": ("fact_renta", "renta_mediana"),
            "tasa_criminalidad_1000hab": ("fact_seguridad", "tasa_criminalidad_1000hab"),
            "nivel_lden_medio": ("fact_ruido", "nivel_lden_medio"),
            "num_listings_airbnb": ("fact_presion_turistica", "num_listings_airbnb"),
        }
        
        if metric not in metric_mapping:
            raise ValueError(f"Métrica '{metric}' no soportada. Disponibles: {list(metric_mapping.keys())}")
        
        table, column = metric_mapping[metric]
        
        # Construir query
        query = f"""
            SELECT anio, AVG({column}) as value
            FROM {table}
            WHERE barrio_id = ?
        """
        
        if years:
            placeholders = ",".join("?" * len(years))
            query += f" AND anio IN ({placeholders})"
            params = [barrio_id] + years
        else:
            params = [barrio_id]
        
        query += " GROUP BY anio ORDER BY anio"
        
        df = pd.read_sql_query(query, conn, params=params)
        
        if df.empty:
            logger.warning("No se encontraron datos para barrio_id=%s, metric=%s", barrio_id, metric)
            return {
                "values": [],
                "years": [],
                "trend_direction": "unknown",
                "growth_rate": 0.0,
                "significant_changes": [],
                "inflection_points": [],
            }
        
        values = df["value"].tolist()
        years_list = df["anio"].tolist()
        
        # Calcular tendencia
        if len(values) < 2:
            trend_direction = "stable"
            growth_rate = 0.0
        else:
            # Calcular tasa de crecimiento promedio
            growth_rates = []
            for i in range(1, len(values)):
                if values[i - 1] > 0:
                    growth = ((values[i] - values[i - 1]) / values[i - 1]) * 100
                    growth_rates.append(growth)
            
            growth_rate = np.mean(growth_rates) if growth_rates else 0.0
            
            # Determinar dirección de tendencia
            if growth_rate > 2.0:
                trend_direction = "increasing"
            elif growth_rate < -2.0:
                trend_direction = "decreasing"
            else:
                trend_direction = "stable"
        
        # Detectar cambios significativos (>10% trimestre a trimestre o año a año)
        significant_changes = []
        for i in range(1, len(values)):
            if values[i - 1] > 0:
                change_pct = abs((values[i] - values[i - 1]) / values[i - 1] * 100)
                if change_pct > 10:
                    significant_changes.append({
                        "year": years_list[i],
                        "previous_year": years_list[i - 1],
                        "change_pct": change_pct,
                        "previous_value": values[i - 1],
                        "new_value": values[i],
                    })
        
        # Detectar puntos de inflexión (cambios de dirección)
        inflection_points = []
        if len(values) >= 3:
            for i in range(1, len(values) - 1):
                prev_change = values[i] - values[i - 1]
                next_change = values[i + 1] - values[i]
                # Cambio de dirección
                if (prev_change > 0 and next_change < 0) or (prev_change < 0 and next_change > 0):
                    inflection_points.append(years_list[i])
        
        return {
            "values": values,
            "years": years_list,
            "trend_direction": trend_direction,
            "growth_rate": float(growth_rate),
            "significant_changes": significant_changes,
            "inflection_points": inflection_points,
        }
    
    finally:
        conn.close()


def compare_barrios(
    barrio_ids: List[int],
    metrics: List[str],
    year: Optional[int] = None,
    db_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Compara múltiples barrios en múltiples métricas.
    
    Args:
        barrio_ids: Lista de IDs de barrios a comparar.
        metrics: Lista de métricas a comparar.
        year: Año opcional para la comparación. Si None, usa el más reciente.
        db_path: Ruta opcional a la base de datos.
    
    Returns:
        DataFrame con comparación de barrios y métricas.
    """
    conn = _get_db_connection(db_path)
    
    try:
        # Usar vista de scorecard si está disponible
        query = """
            SELECT barrio_id, barrio_nombre
            FROM v_barrio_scorecard
            WHERE barrio_id IN ({})
        """.format(",".join("?" * len(barrio_ids)))
        
        df_scorecard = pd.read_sql_query(query, conn, params=barrio_ids)
        
        if df_scorecard.empty:
            # Fallback: obtener desde dim_barrios
            query = """
                SELECT barrio_id, barrio_nombre
                FROM dim_barrios
                WHERE barrio_id IN ({})
            """.format(",".join("?" * len(barrio_ids)))
            df_scorecard = pd.read_sql_query(query, conn, params=barrio_ids)
        
        # Mapear métricas a columnas de la vista
        metric_columns = {
            "precio_m2_venta": "precio_m2_venta_promedio",
            "precio_mes_alquiler": "precio_mes_alquiler_promedio",
            "poblacion_total": "poblacion_total_promedio",
            "renta_mediana": "renta_mediana_promedio",
            "tasa_criminalidad_1000hab": "tasa_criminalidad_1000hab_promedio",
            "nivel_lden_medio": "nivel_lden_medio_promedio",
            "num_listings_airbnb": "num_listings_airbnb_promedio",
        }
        
        # Construir query con métricas seleccionadas
        selected_columns = ["barrio_id", "barrio_nombre"]
        for metric in metrics:
            if metric in metric_columns:
                selected_columns.append(metric_columns[metric] + f" AS {metric}")
        
        query = f"""
            SELECT {", ".join(selected_columns)}
            FROM v_barrio_scorecard
            WHERE barrio_id IN ({",".join("?" * len(barrio_ids))})
        """
        
        df = pd.read_sql_query(query, conn, params=barrio_ids)
        
        return df
    
    finally:
        conn.close()


def identify_outliers(
    metric: str,
    threshold: float = 2.0,
    year: Optional[int] = None,
    db_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Identifica barrios con valores atípicos en una métrica.
    
    Usa el método de desviación estándar (Z-score) para detectar outliers.
    
    Args:
        metric: Nombre de la métrica a analizar.
        threshold: Umbral de desviación estándar (default: 2.0).
        year: Año opcional. Si None, usa el más reciente disponible.
        db_path: Ruta opcional a la base de datos.
    
    Returns:
        DataFrame con barrios outliers y sus valores.
    """
    conn = _get_db_connection(db_path)
    
    try:
        # Obtener datos de la métrica
        metric_mapping = {
            "precio_m2_venta": ("fact_precios", "precio_m2_venta"),
            "precio_mes_alquiler": ("fact_precios", "precio_mes_alquiler"),
            "poblacion_total": ("fact_demografia", "poblacion_total"),
            "renta_mediana": ("fact_renta", "renta_mediana"),
            "tasa_criminalidad_1000hab": ("fact_seguridad", "tasa_criminalidad_1000hab"),
            "nivel_lden_medio": ("fact_ruido", "nivel_lden_medio"),
        }
        
        if metric not in metric_mapping:
            raise ValueError(f"Métrica '{metric}' no soportada")
        
        table, column = metric_mapping[metric]
        
        query = f"""
            SELECT b.barrio_id, b.barrio_nombre, AVG(t.{column}) as value
            FROM {table} t
            JOIN dim_barrios b ON t.barrio_id = b.barrio_id
            WHERE t.{column} IS NOT NULL
        """
        
        params = []
        if year:
            query += " AND t.anio = ?"
            params.append(year)
        else:
            # Usar año más reciente
            query += """
                AND t.anio = (SELECT MAX(anio) FROM {table} WHERE barrio_id = t.barrio_id)
            """.format(table=table)
        
        query += " GROUP BY b.barrio_id, b.barrio_nombre"
        
        df = pd.read_sql_query(query, conn, params=params)
        
        if df.empty:
            return pd.DataFrame()
        
        # Calcular Z-scores
        mean = df["value"].mean()
        std = df["value"].std()
        
        if std == 0:
            return pd.DataFrame()  # No hay variación
        
        df["z_score"] = (df["value"] - mean) / std
        df["is_outlier"] = abs(df["z_score"]) > threshold
        
        # Filtrar solo outliers
        outliers = df[df["is_outlier"]].copy()
        outliers = outliers.sort_values("z_score", ascending=False)
        
        return outliers[["barrio_id", "barrio_nombre", "value", "z_score"]]
    
    finally:
        conn.close()


def calculate_correlations(
    metrics: List[str],
    year: Optional[int] = None,
    db_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Calcula correlaciones cruzadas entre múltiples métricas.
    
    Args:
        metrics: Lista de métricas a correlacionar.
        year: Año opcional. Si None, usa el más reciente disponible.
        db_path: Ruta opcional a la base de datos.
    
    Returns:
        DataFrame con matriz de correlaciones.
    """
    conn = _get_db_connection(db_path)
    
    try:
        # Usar vista de correlaciones si está disponible
        query = "SELECT * FROM v_correlaciones_cruzadas"
        params = []
        
        if year:
            query += " WHERE anio = ?"
            params.append(year)
        else:
            query += " WHERE anio = (SELECT MAX(anio) FROM v_correlaciones_cruzadas)"
        
        df = pd.read_sql_query(query, conn, params=params)
        
        if df.empty:
            logger.warning("No se encontraron datos para calcular correlaciones")
            return pd.DataFrame()
        
        # Mapear métricas a columnas
        metric_columns = {
            "precio_m2_venta": "precio_m2_venta",
            "precio_mes_alquiler": "precio_mes_alquiler",
            "poblacion_total": "poblacion_total",
            "renta_mediana": "renta_mediana",
            "tasa_criminalidad_1000hab": "tasa_criminalidad_1000hab",
            "nivel_lden_medio": "nivel_lden_medio",
            "num_listings_airbnb": "num_listings_airbnb",
            "densidad_hab_km2": "densidad_hab_km2",
        }
        
        # Seleccionar columnas disponibles
        available_metrics = [m for m in metrics if m in metric_columns and metric_columns[m] in df.columns]
        
        if not available_metrics:
            logger.warning("Ninguna métrica disponible para correlación")
            return pd.DataFrame()
        
        # Calcular matriz de correlaciones
        corr_data = df[[metric_columns[m] for m in available_metrics]].corr()
        
        # Renombrar índices y columnas
        corr_data.index = available_metrics
        corr_data.columns = available_metrics
        
        return corr_data
    
    finally:
        conn.close()


def generate_scorecard(
    barrio_id: int,
    year: Optional[int] = None,
    db_path: Optional[Path] = None
) -> Dict:
    """
    Genera un scorecard completo de un barrio con todas las dimensiones.
    
    Args:
        barrio_id: ID del barrio.
        year: Año opcional. Si None, usa el más reciente disponible.
        db_path: Ruta opcional a la base de datos.
    
    Returns:
        Diccionario con scorecard completo incluyendo:
        - Información básica del barrio
        - Métricas por dimensión (precios, demografía, seguridad, etc.)
        - Scores normalizados (0-100)
        - Comparación con promedio de Barcelona
    """
    conn = _get_db_connection(db_path)
    
    try:
        # Obtener datos del barrio desde vista scorecard
        query = """
            SELECT *
            FROM v_barrio_scorecard
            WHERE barrio_id = ?
        """
        
        df_barrio = pd.read_sql_query(query, conn, params=[barrio_id])
        
        if df_barrio.empty:
            logger.warning("No se encontró scorecard para barrio_id=%s", barrio_id)
            return {}
        
        barrio_data = df_barrio.iloc[0].to_dict()
        
        # Obtener promedios de Barcelona para comparación
        query_avg = """
            SELECT 
                AVG(precio_m2_venta_promedio) AS precio_m2_venta_avg_bcn,
                AVG(precio_mes_alquiler_promedio) AS precio_mes_alquiler_avg_bcn,
                AVG(poblacion_total_promedio) AS poblacion_total_avg_bcn,
                AVG(renta_mediana_promedio) AS renta_mediana_avg_bcn,
                AVG(tasa_criminalidad_1000hab_promedio) AS tasa_criminalidad_avg_bcn,
                AVG(nivel_lden_medio_promedio) AS nivel_lden_avg_bcn
            FROM v_barrio_scorecard
        """
        
        df_avg = pd.read_sql_query(query_avg, conn)
        avg_data = df_avg.iloc[0].to_dict() if not df_avg.empty else {}
        
        # Calcular scores normalizados (0-100)
        scores = {}
        
        # Score de affordability (inverso: menor precio/renta = mejor score)
        if barrio_data.get("precio_m2_venta_promedio") and avg_data.get("precio_m2_venta_avg_bcn"):
            ratio = barrio_data["precio_m2_venta_promedio"] / avg_data["precio_m2_venta_avg_bcn"]
            scores["affordability"] = max(0, min(100, 100 - (ratio - 1) * 50))
        
        # Score de seguridad (inverso: menor criminalidad = mejor score)
        if barrio_data.get("tasa_criminalidad_1000hab_promedio") and avg_data.get("tasa_criminalidad_avg_bcn"):
            ratio = barrio_data["tasa_criminalidad_1000hab_promedio"] / max(avg_data["tasa_criminalidad_avg_bcn"], 1)
            scores["seguridad"] = max(0, min(100, 100 - (ratio - 1) * 50))
        
        # Score de calidad ambiental (inverso: menor ruido = mejor score)
        if barrio_data.get("nivel_lden_medio_promedio") and avg_data.get("nivel_lden_avg_bcn"):
            ratio = barrio_data["nivel_lden_medio_promedio"] / max(avg_data["nivel_lden_avg_bcn"], 1)
            scores["calidad_ambiental"] = max(0, min(100, 100 - (ratio - 1) * 50))
        
        # Score de presión turística (inverso: menor presión = mejor score)
        if barrio_data.get("num_listings_airbnb_promedio"):
            # Normalizar respecto a máximo esperado (1000 listings)
            scores["presion_turistica"] = max(0, min(100, 100 - (barrio_data["num_listings_airbnb_promedio"] / 10)))
        
        # Score general (promedio de todos los scores)
        if scores:
            scores["general"] = np.mean(list(scores.values()))
        
        return {
            "barrio_id": barrio_id,
            "barrio_nombre": barrio_data.get("barrio_nombre"),
            "distrito_nombre": barrio_data.get("distrito_nombre"),
            "ultimo_anio_datos": barrio_data.get("ultimo_anio_datos"),
            "metricas": barrio_data,
            "promedios_barcelona": avg_data,
            "scores": scores,
        }
    
    finally:
        conn.close()

