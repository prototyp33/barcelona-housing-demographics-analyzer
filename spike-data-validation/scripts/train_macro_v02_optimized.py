#!/usr/bin/env python3
"""
Entrena MACRO v0.2 optimizado eliminando features con alta colinealidad.

Mejoras sobre v0.2 simplificado:
- Elimina renta_mediana_barrio (VIF = 1245, r = 0.9995 con renta_promedio_barrio)
- Mantiene renta_promedio_barrio (más interpretable)

Uso:
    python3 spike-data-validation/scripts/train_macro_v02_optimized.py \
        --input spike-data-validation/data/processed/gracia_merged_agg_barrio_anio_dataset_v02.csv \
        --output spike-data-validation/data/logs/macro_model_v02_optimized.json
"""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

logger = logging.getLogger(__name__)

# Rutas por defecto
DEFAULT_INPUT = Path("spike-data-validation/data/processed/gracia_merged_agg_barrio_anio_dataset_v02.csv")
DEFAULT_REPORT = Path("spike-data-validation/data/logs/macro_model_v02_optimized.json")
DEFAULT_PRED = Path("spike-data-validation/data/processed/macro_predictions_v02_optimized.csv")

LOG_DIR = Path("spike-data-validation/data/logs")
PROCESSED_DIR = Path("spike-data-validation/data/processed")


@dataclass(frozen=True)
class TrainConfig:
    """Configuración del modelo MACRO v0.2 optimizado."""
    seed: int = 42
    temporal_test_year: int = 2025


def setup_logging() -> None:
    """Configura logging."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def prepare_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Prepara features para el modelo MACRO v0.2 optimizado.
    
    Elimina renta_mediana_barrio por alta colinealidad con renta_promedio_barrio.
    
    Args:
        df: DataFrame enriquecido
        
    Returns:
        Tupla (df_clean, feature_names)
    """
    logger.info("Preparando features (optimizado)...")
    
    # Features estructurales (base)
    structural_features = [
        'superficie_m2_barrio_mean',
        'ano_construccion_barrio_mean',
        'plantas_barrio_mean'
    ]
    
    # Features de renta (SOLO promedio, sin mediana por colinealidad)
    renta_features = [
        'renta_promedio_barrio',
        # 'renta_mediana_barrio',  # ELIMINADO: VIF = 1245, r = 0.9995 con renta_promedio
    ]
    
    # Features temporales
    other_features = ['anio']
    
    # Seleccionar features
    all_features = structural_features + other_features + renta_features
    
    # Filtrar features disponibles
    available_features = [f for f in all_features if f in df.columns]
    missing_features = set(all_features) - set(available_features)
    
    if missing_features:
        logger.warning(f"  ⚠️  Features faltantes: {missing_features}")
    
    # Seleccionar columnas necesarias
    required_cols = ['precio_m2_mean'] + available_features
    if 'dataset_id' in df.columns:
        required_cols.append('dataset_id')
    
    # Filtrar filas con todas las features necesarias
    df_clean = df[required_cols].copy()
    
    # Para features numéricas, imputar con mediana si hay nulos
    numeric_features = [f for f in available_features if f != 'anio']
    for col in numeric_features:
        if df_clean[col].isna().any():
            median_val = df_clean[col].median()
            n_missing = df_clean[col].isna().sum()
            df_clean[col] = df_clean[col].fillna(median_val)
            logger.info(f"    Imputado {col}: {n_missing} valores con mediana ({median_val:.2f})")
    
    logger.info(f"  ✅ Features preparadas: {len(available_features)} features")
    logger.info(f"     Observaciones: {len(df_clean)}")
    logger.info(f"     ⚠️  renta_mediana_barrio eliminada (alta colinealidad)")
    
    return df_clean, available_features


def build_design_matrix(
    df: pd.DataFrame,
    feature_names: List[str],
    use_dummies_dataset: bool = True,
    dataset_dummy_columns: List[str] = None
) -> Tuple[np.ndarray, List[str], pd.DataFrame, List[str]]:
    """
    Construye matriz de diseño X con features numéricas y dummies.
    
    Args:
        df: DataFrame con features
        feature_names: Lista de nombres de features numéricas
        use_dummies_dataset: Si True, añade dummies de dataset_id
        dataset_dummy_columns: Columnas de dummies a usar (para consistencia train/test)
        
    Returns:
        Tupla (X, feature_names_full, df_base, dataset_dummy_cols_used)
    """
    df_base = df.copy()
    
    # Features numéricas
    X_parts: List[np.ndarray] = [np.ones(len(df_base))]  # Intercept
    names: List[str] = ["intercept"]
    
    for feat in feature_names:
        if feat in df_base.columns:
            X_parts.append(pd.to_numeric(df_base[feat], errors="coerce").to_numpy(dtype=float))
            names.append(feat)
    
    # Dummies de dataset_id (usar columnas predefinidas para consistencia)
    dataset_dummy_cols_used = []
    if use_dummies_dataset and 'dataset_id' in df_base.columns:
        if dataset_dummy_columns is None:
            # Primera vez: crear dummies
            dataset_dummies = pd.get_dummies(df_base['dataset_id'], prefix='dataset', drop_first=True)
            dataset_dummy_cols_used = dataset_dummies.columns.tolist()
        else:
            # Usar columnas predefinidas (para test)
            dataset_dummies = pd.get_dummies(df_base['dataset_id'], prefix='dataset', drop_first=True)
            # Asegurar que todas las columnas esperadas estén presentes
            for col in dataset_dummy_columns:
                if col in dataset_dummies.columns:
                    dataset_dummy_cols_used.append(col)
                else:
                    # Añadir columna de ceros si no existe
                    dataset_dummies[col] = 0
                    dataset_dummy_cols_used.append(col)
            # Mantener solo las columnas esperadas
            dataset_dummies = dataset_dummies[dataset_dummy_columns]
        
        for col in dataset_dummy_cols_used:
            X_parts.append(dataset_dummies[col].to_numpy(dtype=float))
            names.append(col)
    
    X = np.column_stack(X_parts)
    
    return X, names, df_base, dataset_dummy_cols_used


def train_eval_temporal_split(
    df: pd.DataFrame,
    feature_names: List[str],
    config: TrainConfig
) -> Tuple[Dict[str, Any], pd.DataFrame]:
    """
    Entrena y evalúa modelo con split temporal.
    
    Args:
        df: DataFrame con features
        feature_names: Lista de nombres de features
        config: Configuración de entrenamiento
        
    Returns:
        Tupla (métricas, predicciones)
    """
    logger.info("=" * 70)
    logger.info("ENTRENAMIENTO Y EVALUACIÓN - MACRO v0.2 (Optimizado)")
    logger.info("=" * 70)
    
    # Split temporal
    train_mask = df['anio'] < config.temporal_test_year
    test_mask = df['anio'] == config.temporal_test_year
    
    df_train = df[train_mask].copy()
    df_test = df[test_mask].copy()
    
    logger.info(f"Train: {len(df_train)} observaciones ({df_train['anio'].min()}-{df_train['anio'].max()})")
    logger.info(f"Test: {len(df_test)} observaciones ({df_test['anio'].min()}-{df_test['anio'].max()})")
    
    if len(df_train) == 0 or len(df_test) == 0:
        logger.error("No hay suficientes datos para split temporal")
        return {}, pd.DataFrame()
    
    # Construir matrices de diseño (train primero para obtener columnas de dummies)
    X_train, feature_names_full, _, dataset_dummy_cols = build_design_matrix(df_train, feature_names)
    X_test, _, _, _ = build_design_matrix(df_test, feature_names, dataset_dummy_columns=dataset_dummy_cols)
    
    y_train = df_train['precio_m2_mean'].to_numpy()
    y_test = df_test['precio_m2_mean'].to_numpy()
    
    # Entrenar modelo
    logger.info("Entrenando modelo...")
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    # Predicciones
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)
    
    # Métricas
    train_metrics = {
        'r2': float(r2_score(y_train, y_train_pred)),
        'rmse': float(np.sqrt(mean_squared_error(y_train, y_train_pred))),
        'mae': float(mean_absolute_error(y_train, y_train_pred))
    }
    
    test_metrics = {
        'r2': float(r2_score(y_test, y_test_pred)),
        'rmse': float(np.sqrt(mean_squared_error(y_test, y_test_pred))),
        'mae': float(mean_absolute_error(y_test, y_test_pred))
    }
    
    # Bias (sesgo)
    test_bias = float(np.mean(y_test_pred - y_test))
    
    logger.info("\n📊 Métricas de Entrenamiento:")
    logger.info(f"   R²: {train_metrics['r2']:.4f}")
    logger.info(f"   RMSE: {train_metrics['rmse']:.2f} €/m²")
    logger.info(f"   MAE: {train_metrics['mae']:.2f} €/m²")
    
    logger.info("\n📊 Métricas de Test (2025):")
    logger.info(f"   R²: {test_metrics['r2']:.4f}")
    logger.info(f"   RMSE: {test_metrics['rmse']:.2f} €/m²")
    logger.info(f"   MAE: {test_metrics['mae']:.2f} €/m²")
    logger.info(f"   Bias: {test_bias:+.2f} €/m²")
    
    # Coeficientes
    coefficients = dict(zip(feature_names_full, model.coef_))
    intercept = float(model.intercept_)
    
    logger.info("\n📊 Coeficientes del Modelo:")
    logger.info(f"   Intercept: {intercept:.2f}")
    for feat, coef in sorted(coefficients.items()):
        if feat != 'intercept':
            logger.info(f"   {feat}: {coef:.4f}")
    
    # DataFrame de predicciones
    pred_data = {
        'anio': df_test['anio'].values,
        'precio_m2_mean_true': y_test,
        'precio_m2_mean_pred': y_test_pred,
        'residual': y_test - y_test_pred
    }
    
    # Añadir barrio_id si está disponible
    if 'barrio_id' in df_test.columns:
        pred_data['barrio_id'] = df_test['barrio_id'].values
    
    # Añadir dataset_id si está disponible
    if 'dataset_id' in df_test.columns:
        pred_data['dataset_id'] = df_test['dataset_id'].values
    
    pred_df = pd.DataFrame(pred_data)
    
    # Métricas completas
    metrics = {
        'model_version': 'MACRO v0.2 (optimizado)',
        'timestamp': datetime.now().isoformat(),
        'train': train_metrics,
        'test': test_metrics,
        'test_bias': test_bias,
        'n_train': len(df_train),
        'n_test': len(df_test),
        'features': feature_names_full,
        'coefficients': {k: float(v) for k, v in coefficients.items()},
        'intercept': intercept,
        'optimizaciones': {
            'renta_mediana_barrio_eliminada': True,
            'razon': 'Alta colinealidad (VIF = 1245, r = 0.9995 con renta_promedio_barrio)'
        }
    }
    
    return metrics, pred_df


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Entrena modelo MACRO v0.2 optimizado (sin renta_mediana_barrio)"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="Archivo CSV del dataset MACRO v0.2 enriquecido"
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=DEFAULT_REPORT,
        help="Archivo JSON de métricas"
    )
    parser.add_argument(
        "--pred",
        type=Path,
        default=DEFAULT_PRED,
        help="Archivo CSV de predicciones"
    )
    
    args = parser.parse_args()
    setup_logging()
    
    # Cargar datos
    logger.info(f"Cargando dataset: {args.input}")
    if not args.input.exists():
        logger.error(f"Archivo no encontrado: {args.input}")
        return 1
    
    df = pd.read_csv(args.input)
    logger.info(f"  ✅ {len(df)} observaciones cargadas")
    
    # Preparar features
    df_clean, feature_names = prepare_features(df)
    
    # Entrenar y evaluar
    config = TrainConfig()
    metrics, pred_df = train_eval_temporal_split(df_clean, feature_names, config)
    
    if not metrics:
        return 1
    
    # Guardar métricas
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with open(args.report, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    logger.info(f"✅ Métricas guardadas: {args.report}")
    
    # Guardar predicciones
    args.pred.parent.mkdir(parents=True, exist_ok=True)
    pred_df.to_csv(args.pred, index=False)
    logger.info(f"✅ Predicciones guardadas: {args.pred}")
    
    logger.info("=" * 70)
    logger.info("✅ Proceso completado")
    
    return 0


if __name__ == "__main__":
    exit(main())

