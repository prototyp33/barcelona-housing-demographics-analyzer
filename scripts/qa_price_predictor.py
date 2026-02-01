import sqlite3
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path
import joblib

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.price_predictor import PricePredictor, MODELS_DIR
from src.app.data_loader import get_connection

def run_qa():
    print("="*60)
    print("🧪 PRICE PREDICTOR QA & INTEGRITY CHECK")
    print("="*60)
    
    # 1. Database Integrity
    print("\n1. Database View: vw_model_prices_demografia")
    conn = get_connection()
    df_model = pd.read_sql_query("SELECT * FROM vw_model_prices_demografia", conn)
    
    num_barrios = df_model['barrio_id'].nunique()
    print(f"    neighborhoods present: {num_barrios}/73")
    
    null_counts = df_model.isnull().sum()
    critical_cols = ["renta_media", "poblacion_total", "num_airbnb", "target_precio_m2"]
    for col in critical_cols:
        if col in null_counts:
            print(f"    NULLs in {col}: {null_counts[col]} ({null_counts[col]/len(df_model)*100:.1f}%)")

    # 2. Artifact Health
    print("\n2. Model Artifacts")
    for model in ["linear", "ridge", "lasso"]:
        path = os.path.join(MODELS_DIR, f"{model}_price_model.joblib")
        exists = os.path.exists(path)
        print(f"    {model}_price_model.joblib: {'✅ OK' if exists else '❌ MISSING'}")
    
    metrics_path = os.path.join(MODELS_DIR, "model_metrics.joblib")
    if os.path.exists(metrics_path):
        metrics = joblib.load(metrics_path)
        print(f"    Metrics file: ✅ OK (R2 Ridge: {metrics.get('ridge', {}).get('r2', 0):.3f})")
    else:
        print(f"    Metrics file: ❌ MISSING")

    # 3. Model Logic & Guardrails Info
    print("\n3. Training Distribution (for UI Guardrails)")
    stats = {}
    for col in ["renta_media", "num_airbnb", "tasa_paro"]:
        valid_data = df_model[col].dropna()
        p1, p99 = np.percentile(valid_data, [1, 99])
        stats[col] = {"p1": p1, "p99": p99, "mean": valid_data.mean()}
        print(f"    {col}: Range [{p1:.0f}, {p99:.0f}], Mean: {valid_data.mean():.0f}")

    # 4. Stress Test (Empty Scenario)
    print("\n4. Robustness Check")
    predictor = PricePredictor()
    empty_df = pd.DataFrame([{"renta_media": 0, "poblacion_total": 0, "porc_jovenes": 0, "porc_mayores": 0, "tasa_paro": 0, "porc_extranjeros": 0, "tam_medio_hogar": 0, "num_airbnb": 0}])
    try:
        pred = predictor.predict(empty_df, model_name="ridge")
        print(f"    Prediction with zero-inputs: ✅ OK ({pred[0]:.0f} €/m²)")
    except Exception as e:
        print(f"    Prediction with zero-inputs: ❌ FAILED ({e})")

    conn.close()
    print("\n" + "="*60)

if __name__ == "__main__":
    run_qa()
