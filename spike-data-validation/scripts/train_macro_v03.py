#!/usr/bin/env python3
"""
Entrena y evalúa MACRO v0.3 con features optimizadas de renta y demografía.

Mejoras sobre v0.2 optimizado:
- Features de renta: renta_euros_mean, renta_promedio_mean, renta_mediana_mean, renta_min_mean
  (basadas en Fase 1: |corr| > 0.3)
- Features demográficas: poblacion_total, prop_hombres, prop_mujeres, prop_18_34, prop_50_64
  (basadas en Fase 1: |corr| > 0.3)
- Validación de VIF para detectar colinealidad
- Comparación con v0.2 optimizado

Uso:
    python3 spike-data-validation/scripts/train_macro_v03.py \
        --input spike-data-validation/data/processed/gracia_merged_agg_barrio_anio_dataset_v03.csv \
        --output spike-data-validation/data/logs/macro_model_v03.json
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
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tools.tools import add_constant

logger = logging.getLogger(__name__)

# Rutas por defecto
DEFAULT_INPUT = Path("spike-data-validation/data/processed/gracia_merged_agg_barrio_anio_dataset_v03.csv")
DEFAULT_REPORT = Path("spike-data-validation/data/logs/macro_model_v03.json")
DEFAULT_PRED = Path("spike-data-validation/data/processed/macro_predictions_v03.csv")
DEFAULT_COMPARISON = Path("spike-data-validation/data/logs/macro_v02_vs_v03_comparison.json")

LOG_DIR = Path("spike-data-validation/data/logs")
PROCESSED_DIR = Path("spike-data-validation/data/processed")


@dataclass(frozen=True)
class TrainConfig:
    """Configuración del modelo MACRO v0.3."""
    seed: int = 42
    temporal_test_year: int = 2025
    vif_threshold: float = 5.0  # Umbral para detectar colinealidad


def setup_logging() -> None:
    """Configura logging."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def calculate_vif(df: pd.DataFrame, feature_names: List[str]) -> Dict[str, float]:
    """
    Calcula VIF (Variance Inflation Factor) para detectar colinealidad.
    
    Args:
        df: DataFrame con features
        feature_names: Lista de nombres de features numéricas
        
    Returns:
        Diccionario con VIF por feature
    """
    logger.info("Calculando VIF para detectar colinealidad...")
    
    # Filtrar features disponibles y numéricas
    available_features = [f for f in feature_names if f in df.columns]
    numeric_features = [f for f in available_features if f != 'anio']
    
    if len(numeric_features) == 0:
        logger.warning("  ⚠️  No hay features numéricas para calcular VIF")
        return {}
    
    # Preparar datos para VIF (sin nulos)
    df_vif = df[numeric_features].dropna()
    
    if len(df_vif) < len(numeric_features) + 1:
        logger.warning(f"  ⚠️  Insuficientes datos para VIF: {len(df_vif)} < {len(numeric_features) + 1}")
        return {}
    
    # Calcular VIF
    X_with_const = add_constant(df_vif)
    vif_data = {}
    
    try:
        for i, feature in enumerate(numeric_features, start=1):  # +1 porque add_constant añade intercept
            vif_value = variance_inflation_factor(X_with_const.values, i)
            vif_data[feature] = float(vif_value)
            
            if vif_value > TrainConfig().vif_threshold:
                logger.warning(f"    ⚠️  {feature}: VIF = {vif_value:.2f} (alta colinealidad)")
            else:
                logger.info(f"    ✅ {feature}: VIF = {vif_value:.2f}")
    except Exception as e:
        logger.error(f"  ❌ Error calculando VIF: {e}")
        return {}
    
    return vif_data


def prepare_features(df: pd.DataFrame, remove_high_vif: bool = True) -> Tuple[pd.DataFrame, List[str]]:
    """
    Prepara features para el modelo MACRO v0.3.
    
    Features basadas en Fase 1 (|corr| > 0.3):
    - Renta: renta_euros_mean, renta_promedio_mean, renta_mediana_mean, renta_min_mean
    - Demografía: poblacion_total, prop_hombres, prop_mujeres, prop_18_34, prop_50_64
    
    Args:
        df: DataFrame enriquecido v0.3
        remove_high_vif: Si True, elimina features con VIF alto después de calcular
        
    Returns:
        Tupla (df_clean, feature_names)
    """
    logger.info("Preparando features (v0.3 - optimizado con Fase 1)...")
    
    # Features estructurales (base)
    structural_features = [
        'superficie_m2_barrio_mean',
        'ano_construccion_barrio_mean',
        'plantas_barrio_mean'
    ]
    
    # Features de renta (v0.3 - basadas en Fase 1)
    # NOTA: Solo incluir renta_min_mean (mayor correlación) para evitar colinealidad
    renta_features = [
        'renta_min_mean',        # r=0.342, p=0.022 (mayor correlación, menor VIF)
        # 'renta_euros_mean',      # ELIMINADO: VIF infinito (colinealidad perfecta)
        # 'renta_promedio_mean',   # ELIMINADO: VIF = 1282.59 (alta colinealidad)
        # 'renta_mediana_mean',    # ELIMINADO: VIF = 122.23 (alta colinealidad)
    ]
    
    # Features demográficas (v0.3 - basadas en Fase 1)
    # NOTA: Solo incluir las más relevantes para evitar colinealidad
    # prop_hombres y prop_mujeres son complementarios (suman 1), solo incluir una
    demografia_features = [
        'prop_50_64',        # r=-0.941, p=0.017 (muy alta correlación negativa)
        'prop_18_34',        # r=0.763, p=0.134
        # 'poblacion_total',   # ELIMINADO: VIF = 0 (pero puede tener colinealidad con otras)
        # 'prop_hombres',      # ELIMINADO: complementario con prop_mujeres
        # 'prop_mujeres',      # ELIMINADO: complementario con prop_hombres
    ]
    
    # Features temporales
    other_features = ['anio']
    
    # Seleccionar features
    all_features = structural_features + other_features + renta_features + demografia_features
    
    # Filtrar features disponibles
    available_features = [f for f in all_features if f in df.columns]
    missing_features = set(all_features) - set(available_features)
    
    if missing_features:
        logger.warning(f"  ⚠️  Features faltantes: {missing_features}")
    
    logger.info(f"  ✅ Features disponibles: {len(available_features)}/{len(all_features)}")
    logger.info(f"     - Estructurales: {len([f for f in structural_features if f in available_features])}")
    logger.info(f"     - Renta: {len([f for f in renta_features if f in available_features])}")
    logger.info(f"     - Demografía: {len([f for f in demografia_features if f in available_features])}")
    
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


def load_v02_metrics() -> Dict[str, Any]:
    """
    Carga métricas del modelo v0.2 optimizado para comparación.
    
    Returns:
        Diccionario con métricas de v0.2 o vacío si no existe
    """
    v02_report = Path("spike-data-validation/data/logs/macro_model_v02_optimized.json")
    
    if not v02_report.exists():
        logger.warning(f"  ⚠️  Reporte v0.2 no encontrado: {v02_report}")
        return {}
    
    try:
        with open(v02_report, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"  ⚠️  Error cargando métricas v0.2: {e}")
        return {}


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
    logger.info("ENTRENAMIENTO Y EVALUACIÓN - MACRO v0.3")
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
    
    # Calcular VIF en train set
    vif_results = calculate_vif(df_train, feature_names)
    
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
        'model_version': 'MACRO v0.3',
        'timestamp': datetime.now().isoformat(),
        'train': train_metrics,
        'test': test_metrics,
        'test_bias': test_bias,
        'n_train': len(df_train),
        'n_test': len(df_test),
        'features': feature_names_full,
        'coefficients': {k: float(v) for k, v in coefficients.items()},
        'intercept': intercept,
        'vif': vif_results,
        'vif_threshold': config.vif_threshold,
        'high_vif_features': [f for f, vif in vif_results.items() if vif > config.vif_threshold]
    }
    
    return metrics, pred_df


def compare_with_v02(metrics_v03: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compara métricas de v0.3 con v0.2 optimizado.
    
    Args:
        metrics_v03: Métricas del modelo v0.3
        
    Returns:
        Diccionario con comparación
    """
    logger.info("\n" + "=" * 70)
    logger.info("COMPARACIÓN v0.2 Optimizado vs v0.3")
    logger.info("=" * 70)
    
    metrics_v02 = load_v02_metrics()
    
    if not metrics_v02:
        logger.warning("  ⚠️  No se pudo cargar métricas v0.2 para comparación")
        return {}
    
    comparison = {
        'v02_metrics': {
            'test_r2': metrics_v02.get('test', {}).get('r2', 0),
            'test_rmse': metrics_v02.get('test', {}).get('rmse', 0),
            'test_mae': metrics_v02.get('test', {}).get('mae', 0),
            'test_bias': metrics_v02.get('test_bias', 0),
            'n_features': len(metrics_v02.get('features', []))
        },
        'v03_metrics': {
            'test_r2': metrics_v03.get('test', {}).get('r2', 0),
            'test_rmse': metrics_v03.get('test', {}).get('rmse', 0),
            'test_mae': metrics_v03.get('test', {}).get('mae', 0),
            'test_bias': metrics_v03.get('test_bias', 0),
            'n_features': len(metrics_v03.get('features', []))
        },
        'improvement': {
            'r2_delta': metrics_v03.get('test', {}).get('r2', 0) - metrics_v02.get('test', {}).get('r2', 0),
            'rmse_delta': metrics_v02.get('test', {}).get('rmse', 0) - metrics_v03.get('test', {}).get('rmse', 0),  # Positivo = mejora
            'mae_delta': metrics_v02.get('test', {}).get('mae', 0) - metrics_v03.get('test', {}).get('mae', 0),  # Positivo = mejora
            'bias_delta': abs(metrics_v03.get('test_bias', 0)) - abs(metrics_v02.get('test_bias', 0))  # Negativo = mejora
        }
    }
    
    # Log comparación
    logger.info("\n📊 Métricas Test (2025):")
    logger.info(f"   R²:  {comparison['v02_metrics']['test_r2']:.4f} → {comparison['v03_metrics']['test_r2']:.4f} (Δ {comparison['improvement']['r2_delta']:+.4f})")
    logger.info(f"   RMSE: {comparison['v02_metrics']['test_rmse']:.2f} → {comparison['v03_metrics']['test_rmse']:.2f} €/m² (Δ {comparison['improvement']['rmse_delta']:+.2f})")
    logger.info(f"   MAE:  {comparison['v02_metrics']['test_mae']:.2f} → {comparison['v03_metrics']['test_mae']:.2f} €/m² (Δ {comparison['improvement']['mae_delta']:+.2f})")
    logger.info(f"   Bias: {comparison['v02_metrics']['test_bias']:+.2f} → {comparison['v03_metrics']['test_bias']:+.2f} €/m² (Δ {comparison['improvement']['bias_delta']:+.2f})")
    logger.info(f"   Features: {comparison['v02_metrics']['n_features']} → {comparison['v03_metrics']['n_features']}")
    
    # Evaluar si se cumplen objetivos
    r2_improved = comparison['improvement']['r2_delta'] > 0
    rmse_improved = comparison['improvement']['rmse_delta'] > 0
    r2_target = comparison['v03_metrics']['test_r2'] >= 0.85
    rmse_target = comparison['v03_metrics']['test_rmse'] <= 250
    
    comparison['objectives_met'] = {
        'r2_improved': r2_improved,
        'rmse_improved': rmse_improved,
        'r2_target_met': r2_target,
        'rmse_target_met': rmse_target,
        'overall_success': r2_target and rmse_target
    }
    
    if r2_target and rmse_target:
        logger.info("\n✅ OBJETIVOS CUMPLIDOS:")
        logger.info(f"   R² ≥ 0.85: ✅ ({comparison['v03_metrics']['test_r2']:.4f})")
        logger.info(f"   RMSE ≤ 250: ✅ ({comparison['v03_metrics']['test_rmse']:.2f})")
    else:
        logger.warning("\n⚠️  OBJETIVOS NO CUMPLIDOS:")
        if not r2_target:
            logger.warning(f"   R² ≥ 0.85: ❌ ({comparison['v03_metrics']['test_r2']:.4f})")
        if not rmse_target:
            logger.warning(f"   RMSE ≤ 250: ❌ ({comparison['v03_metrics']['test_rmse']:.2f})")
    
    return comparison


def main() -> int:
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Entrena modelo MACRO v0.3 con features optimizadas"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="Archivo CSV del dataset MACRO v0.3 enriquecido"
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
    parser.add_argument(
        "--comparison",
        type=Path,
        default=DEFAULT_COMPARISON,
        help="Archivo JSON de comparación v0.2 vs v0.3"
    )
    
    args = parser.parse_args()
    setup_logging()
    
    logger.info("=" * 70)
    logger.info("ENTRENAMIENTO MACRO v0.3")
    logger.info("Features basadas en Fase 1 (|corr| > 0.3)")
    logger.info("=" * 70)
    
    # Cargar datos
    logger.info(f"Cargando dataset: {args.input}")
    if not args.input.exists():
        logger.error(f"Archivo no encontrado: {args.input}")
        logger.info("💡 Sugerencia: Ejecutar primero enrich_macro_dataset_v03.py")
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
    
    # Comparar con v0.2
    comparison = compare_with_v02(metrics)
    
    # Guardar métricas
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with open(args.report, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    logger.info(f"\n✅ Métricas guardadas: {args.report}")
    
    # Guardar predicciones
    args.pred.parent.mkdir(parents=True, exist_ok=True)
    pred_df.to_csv(args.pred, index=False)
    logger.info(f"✅ Predicciones guardadas: {args.pred}")
    
    # Guardar comparación
    if comparison:
        args.comparison.parent.mkdir(parents=True, exist_ok=True)
        with open(args.comparison, 'w', encoding='utf-8') as f:
            json.dump(comparison, f, indent=2, ensure_ascii=False)
        logger.info(f"✅ Comparación guardada: {args.comparison}")
    
    logger.info("=" * 70)
    logger.info("✅ Proceso completado")
    logger.info("=" * 70)
    
    return 0


if __name__ == "__main__":
    exit(main())

