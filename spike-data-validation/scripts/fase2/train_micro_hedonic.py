#!/usr/bin/env python3
"""
Modelo Hedonic Pricing MICRO v1.0 (Fase 2 - Issue #202).

Entrena modelo hedonic pricing a nivel edificio usando:
- Variables Catastro: superficie_m2, ano_construccion, plantas
- Variables Idealista: habitaciones, banos, exterior, ascensor
- Variable dependiente: precio_m2

Compara con baseline MACRO (Issue #203) para validar mejora.

Uso:
    python3 spike-data-validation/scripts/fase2/train_micro_hedonic.py
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

INPUT_MATCHED = Path("spike-data-validation/data/processed/fase2/catastro_idealista_matched.csv")
OUTPUT_DIR = Path("spike-data-validation/data/processed/fase2")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def setup_logging() -> None:
    """Configura logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def prepare_features(
    df: pd.DataFrame, 
    clean_outliers: bool = True,
    use_log_transform: bool = True,
    use_interactions: bool = True
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Prepara features y target para el modelo.
    
    Args:
        df: DataFrame con datos combinados
        clean_outliers: Si True, filtra outliers en superficie
        
    Returns:
        Tupla con (X, y) donde X son features y y es target
    """
    df_clean = df.copy()
    
    # Limpiar outliers en superficie (valores fuera de rango razonable)
    if clean_outliers and "superficie_m2" in df_clean.columns:
        initial_count = len(df_clean)
        # Filtrar superficie razonable (30-200 m² para pisos)
        df_clean = df_clean[
            (df_clean["superficie_m2"] >= 30) & (df_clean["superficie_m2"] <= 200)
        ].copy()
        removed = initial_count - len(df_clean)
        if removed > 0:
            logger.info("   Outliers superficie eliminados: %s observaciones", removed)
    
    # Variable dependiente: precio_m2
    if "precio_m2" not in df_clean.columns and "precio" in df_clean.columns and "superficie_m2" in df_clean.columns:
        df_clean["precio_m2"] = df_clean["precio"] / df_clean["superficie_m2"]
    
    # Aplicar transformación logarítmica si se solicita
    if use_log_transform:
        if "superficie_m2" in df_clean.columns:
            df_clean["log_superficie"] = np.log(df_clean["superficie_m2"] + 1)
        if "precio_m2" in df_clean.columns:
            df_clean["log_precio_m2"] = np.log(df_clean["precio_m2"])
        y = df_clean["log_precio_m2"].copy() if "log_precio_m2" in df_clean.columns else df_clean["precio_m2"].copy()
    else:
        y = df_clean["precio_m2"].copy()
    
    # Features numéricas de Catastro
    features_catastro = []
    if use_log_transform and "log_superficie" in df_clean.columns:
        features_catastro.append("log_superficie")
    elif "superficie_m2" in df_clean.columns:
        features_catastro.append("superficie_m2")
    if "ano_construccion" in df_clean.columns:
        features_catastro.append("ano_construccion")
    if "plantas" in df_clean.columns:
        features_catastro.append("plantas")
    
    # Features numéricas de Idealista
    features_idealista = []
    if "habitaciones" in df_clean.columns:
        features_idealista.append("habitaciones")
    if "banos" in df_clean.columns:
        features_idealista.append("banos")
    
    # Features categóricas (one-hot encoding)
    features_categorical = []
    if "barrio_id" in df_clean.columns:
        # Crear dummies para barrio_id
        barrio_dummies = pd.get_dummies(df_clean["barrio_id"], prefix="barrio", drop_first=True)
        features_categorical.append(barrio_dummies)
    
    if "exterior" in df_clean.columns:
        df_clean["exterior_bool"] = df_clean["exterior"].astype(int)
        features_idealista.append("exterior_bool")
    
    if "ascensor" in df_clean.columns:
        df_clean["ascensor_bool"] = df_clean["ascensor"].astype(int)
        features_idealista.append("ascensor_bool")
    
    # Combinar todas las features
    X_numeric = df_clean[features_catastro + features_idealista].copy()
    
    if features_categorical:
        X_categorical = pd.concat(features_categorical, axis=1)
        X = pd.concat([X_numeric, X_categorical], axis=1)
    else:
        X = X_numeric
    
    # Añadir interacciones si se solicita
    if use_interactions and "barrio_id" in df_clean.columns:
        barrio_dummies = pd.get_dummies(df_clean["barrio_id"], prefix="barrio", drop_first=True)
        
        # Interacción: superficie × barrio
        if use_log_transform and "log_superficie" in X.columns:
            for barrio_col in barrio_dummies.columns:
                X[f"log_superficie_x_{barrio_col}"] = X["log_superficie"] * barrio_dummies[barrio_col]
        elif "superficie_m2" in X.columns:
            for barrio_col in barrio_dummies.columns:
                X[f"superficie_x_{barrio_col}"] = X["superficie_m2"] * barrio_dummies[barrio_col]
        
        # Interacción: año × barrio
        if "ano_construccion" in X.columns:
            for barrio_col in barrio_dummies.columns:
                X[f"ano_x_{barrio_col}"] = X["ano_construccion"] * barrio_dummies[barrio_col]
        
        logger.info("   Interacciones añadidas: superficie×barrio, año×barrio")
    
    # Filtrar filas con datos completos
    mask = X.notna().all(axis=1) & y.notna()
    X = X[mask].copy()
    y = y[mask].copy()
    
    logger.info("Features preparadas:")
    logger.info("   Numéricas: %s", features_catastro + features_idealista)
    logger.info("   Categóricas: %s", len(features_categorical) if features_categorical else 0)
    logger.info("   Total features: %s", X.shape[1])
    logger.info("   Observaciones válidas: %s", len(X))
    
    return X, y


def train_model(
    X: pd.DataFrame,
    y: pd.Series,
    model_type: str = "linear",
    test_size: float = 0.2,
    random_state: int = 42,
    use_cv: bool = True,
    cv_folds: int = 5,
) -> Tuple[Any, Dict[str, Any]]:
    """
    Entrena modelo hedonic pricing.
    
    Args:
        X: Features
        y: Target (precio_m2)
        model_type: Tipo de modelo ("linear", "rf", "gbm")
        test_size: Proporción de test set
        random_state: Semilla aleatoria
        
    Returns:
        Tupla con (modelo entrenado, métricas)
    """
    # Usar cross-validation o train/test split
    if use_cv and len(X) >= cv_folds * 2:
        logger.info("")
        logger.info("Usando %s-fold cross-validation", cv_folds)
        kf = KFold(n_splits=cv_folds, shuffle=True, random_state=random_state)
        
        # Para compatibilidad, también hacer un split para evaluación final
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
    else:
        logger.info("")
        logger.info("Usando train/test split (muestra pequeña para CV)")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        use_cv = False
    
    logger.info("")
    logger.info("Split train/test:")
    logger.info("   Train: %s observaciones", len(X_train))
    logger.info("   Test: %s observaciones", len(X_test))
    
    # Escalar features (solo para modelos que lo necesiten)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Seleccionar modelo
    if model_type == "linear":
        model = LinearRegression()
        use_scaled = True
    elif model_type == "rf":
        model = RandomForestRegressor(n_estimators=100, random_state=random_state, max_depth=10)
        use_scaled = False
    elif model_type == "gbm":
        model = GradientBoostingRegressor(n_estimators=100, random_state=random_state, max_depth=5)
        use_scaled = False
    else:
        raise ValueError(f"Modelo desconocido: {model_type}")
    
    # Entrenar
    logger.info("")
    logger.info("Entrenando modelo: %s", model_type)
    if use_scaled:
        model.fit(X_train_scaled, y_train)
        y_pred_train = model.predict(X_train_scaled)
        y_pred_test = model.predict(X_test_scaled)
    else:
        model.fit(X_train, y_train)
        y_pred_train = model.predict(X_train)
        y_pred_test = model.predict(X_test)
    
    # Calcular métricas (si y está en escala log, convertir predicciones a escala original)
    use_log_target = y_train.min() < 0 or y_train.max() < 10  # Heurística: si valores < 10, probablemente es log
    
    if use_log_target:
        # Convertir de vuelta a escala original para métricas
        y_train_orig = np.exp(y_train)
        y_test_orig = np.exp(y_test)
        y_pred_train_orig = np.exp(y_pred_train)
        y_pred_test_orig = np.exp(y_pred_test)
        
        # Métricas en escala original
        metrics = {
            "model_type": model_type,
            "use_log_transform": True,
            "train_r2": float(r2_score(y_train_orig, y_pred_train_orig)),
            "test_r2": float(r2_score(y_test_orig, y_pred_test_orig)),
            "train_rmse": float(np.sqrt(mean_squared_error(y_train_orig, y_pred_train_orig))),
            "test_rmse": float(np.sqrt(mean_squared_error(y_test_orig, y_pred_test_orig))),
            "train_bias": float(np.mean(y_train_orig - y_pred_train_orig)),
            "test_bias": float(np.mean(y_test_orig - y_pred_test_orig)),
            "n_features": X.shape[1],
            "n_train": len(X_train),
            "n_test": len(X_test),
            # Métricas en escala log (para referencia)
            "train_r2_log": float(r2_score(y_train, y_pred_train)),
            "test_r2_log": float(r2_score(y_test, y_pred_test)),
        }
    else:
        # Métricas en escala original
        metrics = {
            "model_type": model_type,
            "use_log_transform": False,
            "train_r2": float(r2_score(y_train, y_pred_train)),
            "test_r2": float(r2_score(y_test, y_pred_test)),
            "train_rmse": float(np.sqrt(mean_squared_error(y_train, y_pred_train))),
            "test_rmse": float(np.sqrt(mean_squared_error(y_test, y_pred_test))),
            "train_bias": float(np.mean(y_train - y_pred_train)),
            "test_bias": float(np.mean(y_test - y_pred_test)),
            "n_features": X.shape[1],
            "n_train": len(X_train),
            "n_test": len(X_test),
        }
    
    # Añadir métricas de cross-validation si se usó
    if use_cv:
        # CV en escala log
        cv_scores_r2_log = cross_val_score(model, X_train_scaled if use_scaled else X_train, y_train, 
                                           cv=kf, scoring='r2')
        cv_scores_rmse_log = -cross_val_score(model, X_train_scaled if use_scaled else X_train, y_train,
                                              cv=kf, scoring='neg_root_mean_squared_error')
        
        metrics["cv_r2_log_mean"] = float(cv_scores_r2_log.mean())
        metrics["cv_r2_log_std"] = float(cv_scores_r2_log.std())
        metrics["cv_rmse_log_mean"] = float(cv_scores_rmse_log.mean())
        metrics["cv_rmse_log_std"] = float(cv_scores_rmse_log.std())
        
        # Convertir CV a escala original si se usó log
        if use_log_target:
            # Para CV, necesitamos hacer predicciones y convertir
            cv_r2_orig = []
            cv_rmse_orig = []
            for train_idx, val_idx in kf.split(X_train):
                X_cv_train = X_train_scaled[train_idx] if use_scaled else X_train.iloc[train_idx]
                X_cv_val = X_train_scaled[val_idx] if use_scaled else X_train.iloc[val_idx]
                y_cv_train = y_train.iloc[train_idx] if isinstance(y_train, pd.Series) else y_train[train_idx]
                y_cv_val = y_train.iloc[val_idx] if isinstance(y_train, pd.Series) else y_train[val_idx]
                
                model_cv = type(model)(**model.get_params() if hasattr(model, 'get_params') else {})
                model_cv.fit(X_cv_train, y_cv_train)
                y_pred_cv = model_cv.predict(X_cv_val)
                
                y_cv_val_orig = np.exp(y_cv_val)
                y_pred_cv_orig = np.exp(y_pred_cv)
                
                cv_r2_orig.append(r2_score(y_cv_val_orig, y_pred_cv_orig))
                cv_rmse_orig.append(np.sqrt(mean_squared_error(y_cv_val_orig, y_pred_cv_orig)))
            
            metrics["cv_r2_mean"] = float(np.mean(cv_r2_orig))
            metrics["cv_r2_std"] = float(np.std(cv_r2_orig))
            metrics["cv_rmse_mean"] = float(np.mean(cv_rmse_orig))
            metrics["cv_rmse_std"] = float(np.std(cv_rmse_orig))
        else:
            metrics["cv_r2_mean"] = float(cv_scores_r2_log.mean())
            metrics["cv_r2_std"] = float(cv_scores_r2_log.std())
            metrics["cv_rmse_mean"] = float(cv_scores_rmse_log.mean())
            metrics["cv_rmse_std"] = float(cv_scores_rmse_log.std())
        
        logger.info("")
        logger.info("Cross-validation (%s-fold):", cv_folds)
        if use_log_target:
            logger.info("   R² (log): %.4f ± %.4f", metrics["cv_r2_log_mean"], metrics["cv_r2_log_std"])
            logger.info("   RMSE (log): %.4f ± %.4f", metrics["cv_rmse_log_mean"], metrics["cv_rmse_log_std"])
        logger.info("   R² (original): %.4f ± %.4f", metrics["cv_r2_mean"], metrics["cv_r2_std"])
        logger.info("   RMSE (original): %.2f ± %.2f €/m²", metrics["cv_rmse_mean"], metrics["cv_rmse_std"])
    
    logger.info("")
    logger.info("Métricas:")
    logger.info("   R² train: %.4f", metrics["train_r2"])
    logger.info("   R² test:  %.4f", metrics["test_r2"])
    logger.info("   RMSE train: %.2f €/m²", metrics["train_rmse"])
    logger.info("   RMSE test:  %.2f €/m²", metrics["test_rmse"])
    logger.info("   Bias train: %.2f €/m²", metrics["train_bias"])
    logger.info("   Bias test:  %.2f €/m²", metrics["test_bias"])
    
    return model, metrics


def compare_with_macro_baseline(micro_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compara métricas MICRO con baseline MACRO (Issue #203).
    
    Args:
        micro_metrics: Métricas del modelo MICRO
        
    Returns:
        Diccionario con comparación
    """
    # Métricas MACRO baseline (Issue #203)
    macro_baseline = {
        "r2_test": 0.710,
        "rmse_test": 323.47,  # €/m²
        "bias_test": 203.0,  # €/m² (sesgo positivo)
    }
    
    comparison = {
        "macro_baseline": macro_baseline,
        "micro_current": {
            "r2_test": micro_metrics.get("test_r2", 0),
            "rmse_test": micro_metrics.get("test_rmse", 0),
            "bias_test": micro_metrics.get("test_bias", 0),
        },
        "improvement": {
            "r2_delta": micro_metrics.get("test_r2", 0) - macro_baseline["r2_test"],
            "rmse_delta": macro_baseline["rmse_test"] - micro_metrics.get("test_rmse", 0),  # Positivo = mejora
            "bias_delta": abs(micro_metrics.get("test_bias", 0)) - abs(macro_baseline["bias_test"]),  # Negativo = mejora
        },
    }
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("COMPARACIÓN MICRO vs MACRO BASELINE")
    logger.info("=" * 70)
    logger.info("")
    logger.info("R² Test:")
    logger.info("   MACRO:  %.4f", macro_baseline["r2_test"])
    logger.info("   MICRO:  %.4f", comparison["micro_current"]["r2_test"])
    logger.info("   Delta:  %+.4f", comparison["improvement"]["r2_delta"])
    logger.info("")
    logger.info("RMSE Test:")
    logger.info("   MACRO:  %.2f €/m²", macro_baseline["rmse_test"])
    logger.info("   MICRO:  %.2f €/m²", comparison["micro_current"]["rmse_test"])
    logger.info("   Delta:  %+.2f €/m² (positivo = mejora)", comparison["improvement"]["rmse_delta"])
    logger.info("")
    logger.info("Bias Test:")
    logger.info("   MACRO:  %.2f €/m²", macro_baseline["bias_test"])
    logger.info("   MICRO:  %.2f €/m²", comparison["micro_current"]["bias_test"])
    logger.info("   Delta:  %+.2f €/m² (negativo = mejora)", comparison["improvement"]["bias_delta"])
    
    return comparison


def main() -> int:
    """Punto de entrada principal."""
    setup_logging()
    
    parser = argparse.ArgumentParser(description="Entrenar modelo hedonic MICRO")
    parser.add_argument("--input", type=str, default=None, help="CSV con datos matched")
    parser.add_argument("--model", type=str, default="linear", choices=["linear", "rf", "gbm"], help="Tipo de modelo")
    parser.add_argument("--test-size", type=float, default=0.2, help="Proporción test set")
    parser.add_argument("--seed", type=int, default=42, help="Semilla aleatoria")
    parser.add_argument("--clean-outliers", action="store_true", default=True, help="Limpiar outliers en superficie")
    parser.add_argument("--log-transform", action="store_true", default=True, help="Usar transformación logarítmica")
    parser.add_argument("--interactions", action="store_true", default=True, help="Incluir interacciones")
    parser.add_argument("--use-cv", action="store_true", default=True, help="Usar cross-validation")
    parser.add_argument("--cv-folds", type=int, default=5, help="Número de folds para CV")
    args = parser.parse_args()
    
    # Cargar datos
    input_path = Path(args.input) if args.input else INPUT_MATCHED
    
    if not input_path.exists():
        logger.error("No se encuentra: %s", input_path)
        logger.error("Ejecuta primero el matching: match_catastro_idealista.py")
        return 1
    
    logger.info("=" * 70)
    logger.info("MODELO HEDONIC PRICING MICRO v1.0")
    logger.info("=" * 70)
    logger.info("Input: %s", input_path)
    logger.info("Modelo: %s", args.model)
    logger.info("Transformación log: %s", args.log_transform)
    logger.info("Interacciones: %s", args.interactions)
    logger.info("Cross-validation: %s", args.use_cv)
    logger.info("")
    
    df = pd.read_csv(input_path)
    logger.info("Cargadas %s observaciones", len(df))
    
    # Preparar features
    X, y = prepare_features(
        df, 
        clean_outliers=args.clean_outliers,
        use_log_transform=args.log_transform,
        use_interactions=args.interactions
    )
    
    if len(X) < 20:
        logger.error("❌ Muy pocas observaciones válidas: %s (mínimo 20)", len(X))
        return 1
    
    # Entrenar modelo
    model, metrics = train_model(
        X, y, 
        model_type=args.model, 
        test_size=args.test_size, 
        random_state=args.seed,
        use_cv=args.use_cv,
        cv_folds=args.cv_folds
    )
    
    # Comparar con baseline MACRO
    comparison = compare_with_macro_baseline(metrics)
    
    # Evaluar criterios GO/NO-GO
    logger.info("")
    logger.info("=" * 70)
    logger.info("EVALUACIÓN CRITERIOS GO/NO-GO")
    logger.info("=" * 70)
    
    criteria = {
        "r2_test_ge_075": metrics["test_r2"] >= 0.75,
        "rmse_test_le_250": metrics["test_rmse"] <= 250.0,
        "bias_test_le_100": abs(metrics["test_bias"]) <= 100.0,
        "improves_macro_r2": comparison["improvement"]["r2_delta"] > 0,
        "improves_macro_rmse": comparison["improvement"]["rmse_delta"] > 0,
    }
    
    criteria_passed = sum(criteria.values())
    criteria_total = len(criteria)
    
    logger.info("")
    logger.info("Criterios:")
    logger.info("   R² test ≥ 0.75:        %s (%.4f)", "✅" if criteria["r2_test_ge_075"] else "❌", metrics["test_r2"])
    logger.info("   RMSE test ≤ 250 €/m²:  %s (%.2f)", "✅" if criteria["rmse_test_le_250"] else "❌", metrics["test_rmse"])
    logger.info("   Bias test ≤ ±100 €/m²: %s (%.2f)", "✅" if criteria["bias_test_le_100"] else "❌", metrics["test_bias"])
    logger.info("   Mejora R² vs MACRO:    %s (%.4f)", "✅" if criteria["improves_macro_r2"] else "❌", comparison["improvement"]["r2_delta"])
    logger.info("   Mejora RMSE vs MACRO:  %s (%.2f)", "✅" if criteria["improves_macro_rmse"] else "❌", comparison["improvement"]["rmse_delta"])
    logger.info("")
    logger.info("Criterios cumplidos: %s/%s", criteria_passed, criteria_total)
    
    if criteria_passed >= 4:
        logger.info("")
        logger.info("✅ GO CON PRODUCCIÓN")
        logger.info("   Modelo MICRO cumple criterios principales")
        decision = "GO"
    elif criteria_passed >= 3:
        logger.info("")
        logger.warning("⚠️  REVISAR")
        logger.warning("   Modelo MICRO cumple algunos criterios, pero necesita ajustes")
        decision = "REVISAR"
    else:
        logger.info("")
        logger.error("❌ NO-GO")
        logger.error("   Modelo MICRO no cumple criterios suficientes")
        decision = "NO_GO"
    
    # Guardar resultados
    results = {
        "timestamp": datetime.now().isoformat(),
        "model_type": args.model,
        "metrics": metrics,
        "comparison": comparison,
        "criteria": criteria,
        "criteria_passed": criteria_passed,
        "criteria_total": criteria_total,
        "decision": decision,
        "input_file": str(input_path),
    }
    
    results_path = OUTPUT_DIR / f"micro_hedonic_{args.model}_results.json"
    results_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    logger.info("")
    logger.info("📄 Resultados guardados: %s", results_path)
    
    return 0 if decision == "GO" else 1


if __name__ == "__main__":
    raise SystemExit(main())

