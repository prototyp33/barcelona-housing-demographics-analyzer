
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import KFold, cross_validate
from sklearn.metrics import mean_absolute_error, r2_score
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "barcelona_ml_valuation.csv"

def run_diagnostic():
    print("🧪 ML MODEL OVERFITTING DIAGNOSTIC\n")
    
    if not DATA_PATH.exists():
        print(f"❌ Data not found at {DATA_PATH}")
        return

    df = pd.read_csv(DATA_PATH)
    
    features = [
        'renta_bruta_llar',
        'indice_penalizacion_topografica',
        'num_plantas_avg',
        'access_penalty',
        'dist_to_center',
        'dist_to_tech_hub',
        'antiguedad_media_bloque',
        'pct_propietarios_extranjeros',
        'indice_gini',
        'pct_juridica',
        'gross_yield',
        'effort_rate',
        'price_growth_1y',
        # Phase 2: Fairness & Feature Expansion
        'rail_count',
        'tree_density',
        'vibrancy_biz_density',
        'safety_vibrancy_score',
        # Phase 2.4: Geospatial Transit Proximity
        'dist_metro_m',
        'dist_train_m',
        'dist_airport_m',
        'transport_log_score'
    ]
    
    target = 'avg_venta_23'
    
    # Preprocessing
    df_clean = df.dropna(subset=features + [target]).copy()
    X = df_clean[features]
    y = df_clean[target]
    
    print(f"Dataset Size: {len(df_clean)} barrios")
    
    # Updated Regularized Model Parameters
    # Aggressive Regularization parameters
    model = xgb.XGBRegressor(
        objective='reg:squarederror',
        n_estimators=80,
        learning_rate=0.03,
        max_depth=3,
        gamma=10.0,
        reg_alpha=2.0,
        reg_lambda=5.0,
        min_child_weight=3,
        subsample=0.7,
        colsample_bytree=0.7,
        random_state=42,
        n_jobs=-1
    )
    
    # 1. K-Fold Cross Validation
    print(f"--- 🔄 Running 5-Fold Cross Validation ---")
    cv_results = cross_validate(
        model, X, y, 
        cv=KFold(n_splits=5, shuffle=True, random_state=42),
        scoring=['neg_mean_absolute_error', 'r2'],
        return_train_score=True
    )
    
    train_mae = -cv_results['train_neg_mean_absolute_error'].mean()
    test_mae = -cv_results['test_neg_mean_absolute_error'].mean()
    train_r2 = cv_results['train_r2'].mean()
    test_r2 = cv_results['test_r2'].mean()
    
    print(f"Train MAE: {train_mae:.2f} €/m²")
    print(f"Test/Val MAE: {test_mae:.2f} €/m²")
    print(f"Train R²: {train_r2:.4f}")
    print(f"Test/Val R²: {test_r2:.4f}")
    
    ratio = test_mae / train_mae if train_mae > 0 else float('inf')
    print(f"\nGap Ratio (Val/Train): {ratio:.2f}x")
    
    if ratio > 1.5:
        print("⚠️ WARNING: Significant overfitting detected (>1.5x gap).")
    else:
        print("✅ Model generalization seems acceptable.")

    # 2. Learning Curves logic (Brief suggestion)
    print("\n--- 📈 Recommendation ---")
    if train_mae < 1.0:
        print("The training error is extremely low (near zero), which indicates the model is essentially a lookup table for the training data.")
        print("Suggest: Reduce 'n_estimators', decrease 'max_depth', and increase 'gamma' or 'lambda' for regularization.")

if __name__ == "__main__":
    run_diagnostic()
