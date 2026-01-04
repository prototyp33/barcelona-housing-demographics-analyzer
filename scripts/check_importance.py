
import pandas as pd
import xgboost as xgb
from pathlib import Path
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "barcelona_ml_valuation.csv"

def check_importance():
    df = pd.read_csv(DATA_PATH)
    features = [
        'renta_bruta_llar', 'indice_penalizacion_topografica', 'num_plantas_avg',
        'access_penalty', 'dist_to_center', 'dist_to_tech_hub',
        'antiguedad_media_bloque', 'pct_propietarios_extranjeros',
        'indice_gini', 'pct_juridica', 'gross_yield', 'effort_rate',
        'price_growth_1y', 'accessibility_score', 'rail_count',
        'tree_density', 'green_score', 'vibrancy_biz_density', 'safety_vibrancy_score'
    ]
    target = 'avg_venta_23'
    df_clean = df.dropna(subset=features + [target])
    X = df_clean[features]
    y = df_clean[target]
    
    model = xgb.XGBRegressor(n_estimators=100, max_depth=3, random_state=42)
    model.fit(X, y)
    
    importances = pd.Series(model.feature_importances_, index=features).sort_values(ascending=False)
    print("\n--- Feature Importance ---")
    print(importances)

if __name__ == "__main__":
    check_importance()
