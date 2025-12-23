"""
Clasificación y clustering de barrios por perfil.

Incluye:
- Clustering de barrios por perfil (gentrificado, estable, en declive)
- Clasificación de riesgo/oportunidad
- Detección de barrios en transición
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import sqlite3
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

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


def _load_barrio_features(
    year: Optional[int] = None,
    db_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Carga features de todos los barrios para clustering.
    
    Args:
        year: Año opcional. Si None, usa el más reciente.
        db_path: Ruta opcional a la base de datos.
    
    Returns:
        DataFrame con features por barrio.
    """
    conn = _get_db_connection(db_path)
    
    try:
        query = """
            SELECT 
                barrio_id,
                barrio_nombre,
                distrito_nombre,
                precio_m2_venta_promedio,
                precio_mes_alquiler_promedio,
                poblacion_total_promedio,
                renta_mediana_promedio,
                tasa_criminalidad_1000hab_promedio,
                nivel_lden_medio_promedio,
                num_listings_airbnb_promedio,
                indice_referencia_alquiler_promedio,
                num_licencias_vut_promedio
            FROM v_barrio_scorecard
        """
        
        df = pd.read_sql_query(query, conn)
        
        if df.empty:
            logger.warning("No se encontraron datos en v_barrio_scorecard")
            return pd.DataFrame()
        
        # Si hay año específico, filtrar desde v_tendencias_consolidadas
        if year:
            query_trends = """
                SELECT 
                    barrio_id,
                    precio_m2_venta,
                    poblacion_total,
                    renta_mediana,
                    tasa_criminalidad_1000hab_anual,
                    nivel_lden_medio,
                    num_listings_airbnb_anual
                FROM v_tendencias_consolidadas
                WHERE anio = ?
            """
            df_year = pd.read_sql_query(query_trends, conn, params=[year])
            
            if not df_year.empty:
                # Merge con scorecard, priorizando datos del año específico
                for col in ["precio_m2_venta", "poblacion_total", "renta_mediana",
                           "tasa_criminalidad_1000hab_anual", "nivel_lden_medio",
                           "num_listings_airbnb_anual"]:
                    if col in df_year.columns:
                        df = df.merge(
                            df_year[["barrio_id", col]],
                            on="barrio_id",
                            how="left",
                            suffixes=("", "_year")
                        )
                        # Usar valor del año si está disponible
                        year_col = col + "_year"
                        if year_col in df.columns:
                            df[col.replace("_anual", "")] = df[year_col].fillna(df[col.replace("_anual", "")])
                            df = df.drop(columns=[year_col])
        
        return df
    
    finally:
        conn.close()


def classify_barrio(
    barrio_id: int,
    year: Optional[int] = None,
    db_path: Optional[Path] = None
) -> Dict:
    """
    Clasifica un barrio por perfil (gentrificado, estable, en declive).
    
    Args:
        barrio_id: ID del barrio.
        year: Año opcional para la clasificación.
        db_path: Ruta opcional a la base de datos.
    
    Returns:
        Diccionario con clasificación y scores.
    """
    conn = _get_db_connection(db_path)
    
    try:
        # Obtener datos del barrio desde vista de riesgo de gentrificación
        query = """
            SELECT *
            FROM v_riesgo_gentrificacion
            WHERE barrio_id = ?
        """
        
        df = pd.read_sql_query(query, conn, params=[barrio_id])
        
        if df.empty:
            logger.warning("No se encontraron datos de riesgo para barrio_id=%s", barrio_id)
            return {
                "barrio_id": barrio_id,
                "classification": "unknown",
                "risk_score": None,
                "risk_category": None,
            }
        
        row = df.iloc[0]
        
        # Obtener score de riesgo
        risk_score = row.get("score_riesgo_gentrificacion")
        risk_category = row.get("categoria_riesgo", "Desconocido")
        
        # Clasificar perfil basado en score y cambios
        pct_cambio_precio = row.get("pct_cambio_precio_5_anios", 0)
        pct_cambio_renta = row.get("pct_cambio_renta_5_anios", 0)
        pct_cambio_poblacion = row.get("pct_cambio_poblacion_5_anios", 0)
        
        if risk_score is None:
            classification = "unknown"
        elif risk_score >= 70:
            classification = "gentrificado"
        elif risk_score >= 40:
            classification = "en_transicion"
        elif pct_cambio_precio < -10:
            classification = "en_declive"
        else:
            classification = "estable"
        
        return {
            "barrio_id": barrio_id,
            "barrio_nombre": row.get("barrio_nombre"),
            "classification": classification,
            "risk_score": float(risk_score) if risk_score is not None else None,
            "risk_category": risk_category,
            "pct_cambio_precio_5_anios": float(pct_cambio_precio) if pd.notna(pct_cambio_precio) else None,
            "pct_cambio_renta_5_anios": float(pct_cambio_renta) if pd.notna(pct_cambio_renta) else None,
            "pct_cambio_poblacion_5_anios": float(pct_cambio_poblacion) if pd.notna(pct_cambio_poblacion) else None,
        }
    
    finally:
        conn.close()


def cluster_barrios(
    n_clusters: int = 4,
    year: Optional[int] = None,
    db_path: Optional[Path] = None
) -> Tuple[pd.DataFrame, object]:
    """
    Agrupa barrios en clusters por perfil similar.
    
    Args:
        n_clusters: Número de clusters a crear.
        year: Año opcional para el análisis.
        db_path: Ruta opcional a la base de datos.
    
    Returns:
        Tupla con (DataFrame con clusters asignados, modelo KMeans entrenado).
    """
    # Cargar features
    df = _load_barrio_features(year, db_path)
    
    if df.empty:
        raise ValueError("No hay datos suficientes para clustering")
    
    # Seleccionar features numéricas para clustering
    feature_cols = [
        "precio_m2_venta_promedio",
        "renta_mediana_promedio",
        "tasa_criminalidad_1000hab_promedio",
        "nivel_lden_medio_promedio",
        "num_listings_airbnb_promedio",
        "poblacion_total_promedio",
    ]
    
    # Filtrar columnas disponibles
    available_features = [col for col in feature_cols if col in df.columns]
    
    if len(available_features) < 2:
        raise ValueError("No hay suficientes features disponibles para clustering")
    
    # Preparar datos
    X = df[available_features].fillna(df[available_features].median())
    
    # Normalizar
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Aplicar KMeans
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(X_scaled)
    
    # Añadir clusters al DataFrame
    df_result = df.copy()
    df_result["cluster"] = clusters
    
    # Interpretar clusters (simplificado)
    cluster_labels = []
    for i in range(n_clusters):
        cluster_data = df_result[df_result["cluster"] == i]
        avg_precio = cluster_data["precio_m2_venta_promedio"].mean() if "precio_m2_venta_promedio" in cluster_data.columns else 0
        avg_renta = cluster_data["renta_mediana_promedio"].mean() if "renta_mediana_promedio" in cluster_data.columns else 0
        
        if avg_precio > df_result["precio_m2_venta_promedio"].quantile(0.75):
            label = "Alto Precio"
        elif avg_precio < df_result["precio_m2_venta_promedio"].quantile(0.25):
            label = "Bajo Precio"
        else:
            label = "Precio Medio"
        
        cluster_labels.append(label)
    
    df_result["cluster_label"] = df_result["cluster"].map({i: cluster_labels[i] for i in range(n_clusters)})
    
    logger.info("Clustering completado: %s clusters, %s barrios", n_clusters, len(df_result))
    
    return df_result, kmeans

