"""
Modelos predictivos para precios de vivienda.

Incluye:
- Modelo MACRO mejorado (v0.3) con features de regulación, turismo, seguridad y ruido
- Funciones para entrenar, guardar y cargar modelos
- Funciones para hacer predicciones
"""

from __future__ import annotations

import json
import logging
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import sqlite3
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

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


def prepare_macro_features_v03(
    db_path: Optional[Path] = None,
    include_new_features: bool = True
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Prepara features para el modelo MACRO v0.3 mejorado.
    
    Incluye features de:
    - Estructura (superficie, año construcción, plantas)
    - Renta (promedio, mediana)
    - Regulación (nivel_tension, indice_referencia_alquiler, num_licencias_vut)
    - Presión turística (num_listings_airbnb, pct_entire_home, tasa_ocupacion)
    - Seguridad (tasa_criminalidad_1000hab, delitos_patrimonio)
    - Ruido (nivel_lden_medio, pct_poblacion_expuesta_65db)
    
    Args:
        db_path: Ruta opcional a la base de datos.
        include_new_features: Si True, incluye features de módulos nuevos.
    
    Returns:
        Tupla con (DataFrame con features, lista de nombres de features).
    """
    conn = _get_db_connection(db_path)
    
    try:
        logger.info("Preparando features para MACRO v0.3...")
        
        # Cargar datos consolidados desde vistas analíticas
        query = """
            SELECT 
                p.barrio_id,
                p.anio,
                AVG(p.precio_m2_venta) as precio_m2_venta,
                -- Features estructurales (desde fact_oferta_idealista si disponible)
                AVG(oi.superficie_media) as superficie_m2_barrio_mean,
                AVG(oi.precio_m2_medio) as precio_m2_medio_barrio,
                -- Features de renta
                AVG(r.renta_mediana) as renta_mediana_barrio,
                AVG(r.renta_promedio) as renta_promedio_barrio
        """
        
        if include_new_features:
            query += """
                -- Features de regulación
                MAX(reg.nivel_tension) as nivel_tension,
                AVG(reg.indice_referencia_alquiler) as indice_referencia_alquiler,
                AVG(reg.num_licencias_vut) as num_licencias_vut,
                -- Features de presión turística (agregado anual)
                AVG(pt.num_listings_airbnb) as num_listings_airbnb,
                AVG(pt.pct_entire_home) as pct_entire_home,
                AVG(pt.tasa_ocupacion) as tasa_ocupacion,
                -- Features de seguridad (agregado anual)
                AVG(s.tasa_criminalidad_1000hab) as tasa_criminalidad_1000hab,
                AVG(s.delitos_patrimonio) as delitos_patrimonio,
                -- Features de ruido
                AVG(ru.nivel_lden_medio) as nivel_lden_medio,
                AVG(ru.pct_poblacion_expuesta_65db) as pct_poblacion_expuesta_65db
            """
        
        query += """
            FROM fact_precios p
            LEFT JOIN fact_renta r ON p.barrio_id = r.barrio_id AND p.anio = r.anio
            LEFT JOIN fact_oferta_idealista oi ON p.barrio_id = oi.barrio_id AND p.anio = oi.anio
        """
        
        if include_new_features:
            query += """
                LEFT JOIN fact_regulacion reg ON p.barrio_id = reg.barrio_id AND p.anio = reg.anio
                LEFT JOIN fact_presion_turistica pt ON p.barrio_id = pt.barrio_id AND p.anio = pt.anio
                LEFT JOIN fact_seguridad s ON p.barrio_id = s.barrio_id AND p.anio = s.anio
                LEFT JOIN fact_ruido ru ON p.barrio_id = ru.barrio_id AND p.anio = ru.anio
            """
        
        query += """
            WHERE p.precio_m2_venta IS NOT NULL
            GROUP BY p.barrio_id, p.anio
            ORDER BY p.barrio_id, p.anio
        """
        
        df = pd.read_sql_query(query, conn)
        
        if df.empty:
            logger.warning("No se encontraron datos para preparar features")
            return pd.DataFrame(), []
        
        # Features base (siempre incluidas)
        base_features = [
            "superficie_m2_barrio_mean",
            "renta_mediana_barrio",
            "renta_promedio_barrio",
            "anio",
        ]
        
        # Features nuevas (opcionales)
        new_features = []
        if include_new_features:
            new_features = [
                "indice_referencia_alquiler",
                "num_licencias_vut",
                "num_listings_airbnb",
                "pct_entire_home",
                "tasa_ocupacion",
                "tasa_criminalidad_1000hab",
                "delitos_patrimonio",
                "nivel_lden_medio",
                "pct_poblacion_expuesta_65db",
            ]
        
        all_features = base_features + new_features
        
        # Filtrar features disponibles
        available_features = [f for f in all_features if f in df.columns]
        missing_features = set(all_features) - set(available_features)
        
        if missing_features:
            logger.warning("Features faltantes: %s", missing_features)
        
        # Imputar valores faltantes con mediana
        for col in available_features:
            if col != "anio" and df[col].isna().any():
                median_val = df[col].median()
                n_missing = df[col].isna().sum()
                df[col] = df[col].fillna(median_val)
                logger.info("Imputado %s: %s valores con mediana (%.2f)", col, n_missing, median_val)
        
        # Codificar nivel_tension si está disponible
        if include_new_features and "nivel_tension" in df.columns:
            df["nivel_tension_encoded"] = df["nivel_tension"].map({
                "baja": 1,
                "media": 2,
                "alta": 3,
            }).fillna(2)  # Default: media
            if "nivel_tension_encoded" not in available_features:
                available_features.append("nivel_tension_encoded")
        
        logger.info("Features preparadas: %s features, %s observaciones", len(available_features), len(df))
        
        return df, available_features
    
    finally:
        conn.close()


def train_macro_v03(
    db_path: Optional[Path] = None,
    test_year: int = 2024,
    include_new_features: bool = True,
    model_save_path: Optional[Path] = None
) -> Dict:
    """
    Entrena el modelo MACRO v0.3 mejorado.
    
    Args:
        db_path: Ruta opcional a la base de datos.
        test_year: Año a usar como conjunto de test (temporal split).
        include_new_features: Si True, incluye features de módulos nuevos.
        model_save_path: Ruta opcional donde guardar el modelo serializado.
    
    Returns:
        Diccionario con métricas del modelo y el modelo entrenado.
    """
    logger.info("=== Entrenando MACRO v0.3 ===")
    
    # Preparar features
    df, feature_names = prepare_macro_features_v03(db_path, include_new_features)
    
    if df.empty:
        raise ValueError("No hay datos suficientes para entrenar el modelo")
    
    # Separar train/test por año
    df_train = df[df["anio"] < test_year].copy()
    df_test = df[df["anio"] == test_year].copy()
    
    if df_train.empty or df_test.empty:
        logger.warning("No hay suficientes datos para train/test split temporal")
        # Usar split aleatorio como fallback
        from sklearn.model_selection import train_test_split
        df_train, df_test = train_test_split(df, test_size=0.2, random_state=42)
    
    # Preparar X e y
    X_train = df_train[feature_names].values
    y_train = df_train["precio_m2_venta"].values
    
    X_test = df_test[feature_names].values
    y_test = df_test["precio_m2_venta"].values
    
    # Entrenar modelo
    logger.info("Entrenando modelo con %s observaciones de train...", len(X_train))
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    # Evaluar
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)
    
    metrics = {
        "train": {
            "r2": float(r2_score(y_train, y_train_pred)),
            "rmse": float(np.sqrt(mean_squared_error(y_train, y_train_pred))),
            "mae": float(mean_absolute_error(y_train, y_train_pred)),
        },
        "test": {
            "r2": float(r2_score(y_test, y_test_pred)),
            "rmse": float(np.sqrt(mean_squared_error(y_test, y_test_pred))),
            "mae": float(mean_absolute_error(y_test, y_test_pred)),
        },
        "features": feature_names,
        "n_train": len(X_train),
        "n_test": len(X_test),
        "test_year": test_year,
        "include_new_features": include_new_features,
    }
    
    logger.info("Métricas de entrenamiento:")
    logger.info("  Train R²: %.4f, RMSE: %.2f €/m²", metrics["train"]["r2"], metrics["train"]["rmse"])
    logger.info("  Test R²: %.4f, RMSE: %.2f €/m²", metrics["test"]["r2"], metrics["test"]["rmse"])
    
    # Guardar modelo si se especifica ruta
    if model_save_path:
        model_save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(model_save_path, "wb") as f:
            pickle.dump(model, f)
        logger.info("Modelo guardado en: %s", model_save_path)
        
        # Guardar métricas también
        metrics_path = model_save_path.with_suffix(".json")
        with open(metrics_path, "w") as f:
            json.dump(metrics, f, indent=2)
        logger.info("Métricas guardadas en: %s", metrics_path)
    
    return {
        "model": model,
        "metrics": metrics,
        "feature_names": feature_names,
    }


def load_macro_model(model_path: Path) -> Tuple[object, Dict]:
    """
    Carga un modelo MACRO serializado.
    
    Args:
        model_path: Ruta al archivo .pkl del modelo.
    
    Returns:
        Tupla con (modelo, métricas).
    """
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    
    # Cargar métricas si existen
    metrics_path = model_path.with_suffix(".json")
    metrics = {}
    if metrics_path.exists():
        with open(metrics_path, "r") as f:
            metrics = json.load(f)
    
    return model, metrics


def predict_price(
    barrio_id: int,
    year: int,
    model_path: Optional[Path] = None,
    model: Optional[object] = None,
    feature_names: Optional[List[str]] = None,
    db_path: Optional[Path] = None
) -> Dict:
    """
    Predice el precio por m² para un barrio y año específicos.
    
    Args:
        barrio_id: ID del barrio.
        year: Año de la predicción.
        model_path: Ruta opcional al modelo serializado.
        model: Modelo opcional (si ya está cargado).
        feature_names: Lista opcional de nombres de features.
        db_path: Ruta opcional a la base de datos.
    
    Returns:
        Diccionario con predicción y detalles.
    """
    # Cargar modelo si es necesario
    if model is None:
        if model_path is None:
            # Buscar modelo por defecto
            project_root = Path(__file__).parent.parent.parent
            model_path = project_root / "models" / "macro_v0.3.pkl"
        
        if not model_path.exists():
            raise FileNotFoundError(f"Modelo no encontrado: {model_path}")
        
        model, metrics = load_macro_model(model_path)
        if feature_names is None:
            feature_names = metrics.get("features", [])
    
    # Preparar features para el barrio y año
    df, available_features = prepare_macro_features_v03(db_path, include_new_features=True)
    
    # Filtrar por barrio y año
    df_filtered = df[(df["barrio_id"] == barrio_id) & (df["anio"] == year)]
    
    if df_filtered.empty:
        # Si no hay datos exactos, usar el año más cercano
        df_filtered = df[df["barrio_id"] == barrio_id].copy()
        if not df_filtered.empty:
            df_filtered["year_diff"] = abs(df_filtered["anio"] - year)
            df_filtered = df_filtered.nsmallest(1, "year_diff")
            logger.warning(
                "No hay datos para barrio_id=%s, año=%s. Usando año más cercano: %s",
                barrio_id, year, df_filtered["anio"].iloc[0]
            )
    
    if df_filtered.empty:
        raise ValueError(f"No hay datos disponibles para barrio_id={barrio_id}")
    
    # Preparar features para predicción
    X = df_filtered[feature_names].values
    
    # Hacer predicción
    prediction = model.predict(X)[0]
    
    # Obtener precio real si está disponible
    actual_price = df_filtered["precio_m2_venta"].iloc[0] if "precio_m2_venta" in df_filtered.columns else None
    
    return {
        "barrio_id": barrio_id,
        "year": year,
        "predicted_price_m2": float(prediction),
        "actual_price_m2": float(actual_price) if actual_price is not None else None,
        "error": float(prediction - actual_price) if actual_price is not None else None,
        "features_used": feature_names,
    }

