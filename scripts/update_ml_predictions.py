
import pandas as pd
import numpy as np
import xgboost as xgb
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "barcelona_ml_valuation.csv"

def retrain_and_update():
    print("🔄 Retraining model with Phase 2 features and updating predictions...")
    
    if not DATA_PATH.exists():
        print(f"❌ Data not found")
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
        'rail_count',
        'tree_density',
        'vibrancy_biz_density',
        'safety_vibrancy_score',
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
    
    # Model (using the regularized parameters from ModelService/Diagnostic)
    model = xgb.XGBRegressor(
        objective='reg:squarederror',
        n_estimators=100,
        learning_rate=0.04,
        max_depth=3,
        gamma=5.0,
        reg_alpha=1.0,
        reg_lambda=2.0,
        min_child_weight=3,
        subsample=0.7,
        colsample_bytree=0.7,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X, y)
    
    # Predict
    df_clean['precio_estimado'] = model.predict(X)
    df_clean['desviacion_valor'] = df_clean['precio_estimado'] - df_clean['avg_venta_23']
    
    # Update main dataframe
    df.loc[df_clean.index, 'precio_estimado'] = df_clean['precio_estimado']
    df.loc[df_clean.index, 'desviacion_valor'] = df_clean['desviacion_valor']
    
    df.to_csv(DATA_PATH, index=False)
    print("✅ CSV updated with fresh predictions.")

if __name__ == "__main__":
    retrain_and_update()
