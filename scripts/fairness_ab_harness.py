"""
Fairness A/B Harness (V1 vs V2)
Compares model performance and fairness metrics before and after integrating TMB/OSM features.
"""

import sqlite3
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import KFold
from sklearn.metrics import mean_absolute_error, r2_score
from pathlib import Path
from datetime import datetime

# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "processed" / "database.db"
REPORT_PATH = PROJECT_ROOT / "docs" / "FAIRNESS_AB_TEST_REPORT.md"

# Feature Sets
# V1: Baseline with only economic data (what's actually available)
BASE_FEATURES = [
    'renta_mediana'
]

# V2: Add accessibility features
ACCESSIBILITY_FEATURES = [
    'dist_metro_m',
    'dist_bus_m',
    'access_score',
    'estaciones_metro',
    'estaciones_bus'
]

def get_data():
    conn = sqlite3.connect(DB_PATH)
    
    # Use only available data: prices (2023), renta (2023), mobility (2026)
    # Note: fact_demografia is empty in current DB, so we skip it
    query = """
    SELECT 
        db.barrio_id, db.barrio_nombre, db.distrito_nombre,
        AVG(fp.precio_m2_venta) AS target,
        fr.renta_mediana, 
        fm.estaciones_metro, fm.estaciones_bus, 
        fm.dist_metro_m, fm.dist_bus_m, fm.access_score
    FROM dim_barrios db
    JOIN fact_precios fp ON db.barrio_id = fp.barrio_id AND fp.anio = 2023
    JOIN fact_renta fr ON db.barrio_id = fr.barrio_id AND fr.anio = 2023
    LEFT JOIN fact_movilidad fm ON db.barrio_id = fm.barrio_id
    WHERE fp.precio_m2_venta IS NOT NULL
    GROUP BY db.barrio_id, db.barrio_nombre, db.distrito_nombre, 
             fr.renta_mediana, fm.estaciones_metro, fm.estaciones_bus,
             fm.dist_metro_m, fm.dist_bus_m, fm.access_score
    """
    df = pd.read_sql(query, conn)
    conn.close()
    
    print(f"Data loaded: {len(df)} barrios with complete data")
    print(f"Columns: {df.columns.tolist()}")
    
    return df.dropna(subset=['target'] + BASE_FEATURES)

def calculate_fairness_metrics(df, y_true, y_pred):
    temp_df = df.copy()
    temp_df['abs_error'] = np.abs(y_true - y_pred)
    
    # 1. GES
    district_maes = temp_df.groupby('distrito_nombre')['abs_error'].mean()
    mean_mae = district_maes.mean()
    std_mae = district_maes.std()
    ges = 1 - (std_mae / mean_mae)
    
    # 2. IPR
    median_income = temp_df['renta_mediana'].median()
    mae_low = temp_df[temp_df['renta_mediana'] <= median_income]['abs_error'].mean()
    mae_high = temp_df[temp_df['renta_mediana'] > median_income]['abs_error'].mean()
    ipr = mae_low / mae_high
    
    # 3. PDI
    errors = temp_df['abs_error'].dropna()
    p95 = np.percentile(errors, 95)
    p5 = np.percentile(errors, 5)
    p50 = np.median(errors)
    pdi = (p95 - p5) / p50
    
    return {
        "MAE": mean_absolute_error(y_true, y_pred),
        "R2": r2_score(y_true, y_pred),
        "GES": ges,
        "IPR": ipr,
        "PDI": pdi,
        "district_errors": district_maes.to_dict()
    }

def train_eval(X, y, df_meta):
    # Use cross-validation for stability
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    predictions = np.zeros(len(y))
    
    for train_idx, val_idx in kf.split(X):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
        
        model = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=3,
            learning_rate=0.05,
            random_state=42,
            reg_lambda=1.0
        )
        model.fit(X_train, y_train)
        predictions[val_idx] = model.predict(X_val)
        
    return calculate_fairness_metrics(df_meta, y, predictions)

def generate_report(v1_metrics, v2_metrics):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""# ⚖️ Fairness A/B Test Report
Generated: {now}

## 🚀 Comparison Summary

| Metric | Version 1 (Baseline) | Version 2 (Accessibility+) | Change | Status |
| :--- | :--- | :--- | :--- | :--- |
| **MAE** | {v1_metrics['MAE']:.2f}€ | {v2_metrics['MAE']:.2f}€ | {((v2_metrics['MAE'] - v1_metrics['MAE'])/v1_metrics['MAE']*100):+.1f}% | {'✅' if v2_metrics['MAE'] < v1_metrics['MAE'] else '⚠️'} |
| **R2** | {v1_metrics['R2']:.4f} | {v2_metrics['R2']:.4f} | {v2_metrics['R2'] - v1_metrics['R2']:+.4f} | {'✅' if v2_metrics['R2'] > v1_metrics['R2'] else '⚠️'} |
| **GES** (Equity) | {v1_metrics['GES']:.4f} | {v2_metrics['GES']:.4f} | {v2_metrics['GES'] - v1_metrics['GES']:+.4f} | {'✅' if v2_metrics['GES'] > v1_metrics['GES'] else '📉'} |
| **IPR** (Income) | {v1_metrics['IPR']:.4f} | {v2_metrics['IPR']:.4f} | {abs(1-v2_metrics['IPR']) - abs(1-v1_metrics['IPR']):+.4f} | {'✅' if abs(1-v2_metrics['IPR']) < abs(1-v1_metrics['IPR']) else '⚠️'} |
| **PDI** (Dispersion) | {v1_metrics['PDI']:.4f} | {v2_metrics['PDI']:.4f} | {v2_metrics['PDI'] - v1_metrics['PDI']:.4f} | {'✅' if v2_metrics['PDI'] < v1_metrics['PDI'] else '⚠️'} |

---

## 📍 Geographic Impact (MAE per District)

| District | V1 MAE | V2 MAE | Change |
| :--- | :--- | :--- | :--- |
"""
    # Sort by V1 error to highlight hard cases
    districts = sorted(v1_metrics['district_errors'].keys(), key=lambda x: v1_metrics['district_errors'][x], reverse=True)
    
    for d in districts:
        m1 = v1_metrics['district_errors'][d]
        m2 = v2_metrics['district_errors'].get(d, 0)
        diff = m2 - m1
        pct = (diff / m1 * 100) if m1 > 0 else 0
        report += f"| {d} | {m1:.1f}€ | {m2:.1f}€ | {pct:+.1f}% | {'✅' if diff < 0 else '❌'}\n"

    report += """
---

## 💡 Key Findings

### 1. Accuracy vs Fairness Trade-off
Analysis reveals if the addition of TMB/OSM data helped reduce the gap between central and peripheral districts.

### 2. High-Error District Recovery
Specifically looking at districts like **Nou Barris** and **Ciutat Vella** to see if accessibility features corrected former undervaluations.

### 3. Dispersion & Consistency
The PDI index indicates if the model is producing "wilder" predictions or if it has become more grounded.
"""
    
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"✅ Report generated at: {REPORT_PATH}")

def run_harness():
    print("🚀 Starting Fairness A/B Harness...")
    df = get_data()
    print(f"Loaded {len(df)} records for training.")
    
    y = df['target']
    
    # Version 1: Baseline
    print("Evaluating Model V1 (Baseline)...")
    v1_metrics = train_eval(df[BASE_FEATURES], y, df)
    
    # Version 2: With Accessibility
    print("Evaluating Model V2 (Accessibility Extension)...")
    # Clean for V2 (need transit cols)
    v2_df = df.dropna(subset=ACCESSIBILITY_FEATURES)
    print(f"Records for V2: {len(v2_df)}")
    v2_metrics = train_eval(v2_df[BASE_FEATURES + ACCESSIBILITY_FEATURES], v2_df['target'], v2_df)
    
    generate_report(v1_metrics, v2_metrics)

if __name__ == "__main__":
    run_harness()
