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
# V1: Baseline with economic + demographic data
BASE_FEATURES = [
    'renta_mediana',
    'poblacion_total',
    'edad_media',
    'porc_inmigracion',
    'pct_mayores_65',
    'pct_menores_15'
]

# V2: Add accessibility features (Refined to reduce multicollinearity)
ACCESSIBILITY_FEATURES = [
    'access_score',
    'dist_metro_m'
]

def get_data():
    conn = sqlite3.connect(DB_PATH)
    
    # Use v_demografia_aggregated view which aggregates fact_demografia_ampliada
    query = """
    SELECT 
        db.barrio_id, db.barrio_nombre, db.distrito_nombre,
        AVG(fp.precio_m2_venta) AS target,
        vd.poblacion_total, vd.edad_media, vd.porc_inmigracion,
        vd.pct_mayores_65, vd.pct_menores_15,
        fr.renta_mediana, 
        fm.dist_metro_m, fm.access_score
    FROM dim_barrios db
    JOIN fact_precios fp ON db.barrio_id = fp.barrio_id AND fp.anio = 2023
    LEFT JOIN v_demografia_aggregated vd ON db.barrio_id = vd.barrio_id AND vd.anio = 2025
    JOIN fact_renta fr ON db.barrio_id = fr.barrio_id AND fr.anio = 2022
    LEFT JOIN fact_movilidad fm ON db.barrio_id = fm.barrio_id
    WHERE fp.precio_m2_venta IS NOT NULL
    GROUP BY db.barrio_id, db.barrio_nombre, db.distrito_nombre, 
             vd.poblacion_total, vd.edad_media, vd.porc_inmigracion,
             vd.pct_mayores_65, vd.pct_menores_15,
             fr.renta_mediana, fm.dist_metro_m, fm.access_score
    """
    df = pd.read_sql(query, conn)
    conn.close()
    
    print(f"Data loaded: {len(df)} barrios with complete data")
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

from sklearn.preprocessing import RobustScaler, PolynomialFeatures
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, VotingRegressor
from sklearn.model_selection import GridSearchCV

from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, VotingRegressor
from sklearn.model_selection import GridSearchCV
from sklearn.feature_selection import SelectKBest, f_regression

def train_eval(X_raw, y, df_meta):
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    predictions = np.zeros(len(y))
    feature_importances = []
    
    # Pre-calculate sample weights based on district representation
    # Higher weights for districts with fewer barrios to improve GES (equity)
    district_counts = df_meta['distrito_nombre'].value_counts()
    sample_weights = df_meta['distrito_nombre'].map(lambda x: 1.0 / np.sqrt(district_counts[x]))
    
    for train_idx, val_idx in kf.split(X_raw):
        X_train_raw, X_val_raw = X_raw.iloc[train_idx].copy(), X_raw.iloc[val_idx].copy()
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
        sw_train = sample_weights.iloc[train_idx].values
        
        # 1. Feature Engineering
        for df_t in [X_train_raw, X_val_raw]:
            # Interaction
            if 'renta_mediana' in df_t.columns and 'access_score' in df_t.columns:
                df_t['renta_x_access'] = df_t['renta_mediana'] * df_t['access_score']
            
            # Distance Transformations (Log + Poly as requested)
            if 'dist_metro_m' in df_t.columns:
                df_t['log_dist_metro'] = np.log1p(df_t['dist_metro_m'])
                df_t['dist_metro_sq'] = (df_t['dist_metro_m'] / 500) ** 2
            
            if 'poblacion_total' in df_t.columns:
                df_t['log_poblacion'] = np.log1p(df_t['poblacion_total'])
            
            # Polynomial for access score
            if 'access_score' in df_t.columns:
                df_t['access_score_sq'] = df_t['access_score'] ** 2

        # 2. Scaling (StandardScaler as requested by user)
        scaler = StandardScaler()
        X_train_scaled = pd.DataFrame(scaler.fit_transform(X_train_raw), columns=X_train_raw.columns)
        X_val_scaled = pd.DataFrame(scaler.transform(X_val_raw), columns=X_val_raw.columns)
        
        # 3. Feature Selection (Eliminate multicollinearity)
        # We select top K features to avoid noise on this very small dataset (73 rows)
        selector = SelectKBest(f_regression, k=min(12, X_train_scaled.shape[1]))
        X_train = pd.DataFrame(selector.fit_transform(X_train_scaled, y_train), 
                               columns=X_train_scaled.columns[selector.get_support()])
        X_val = pd.DataFrame(selector.transform(X_val_scaled), 
                             columns=X_val_scaled.columns[selector.get_support()])
        
        # 4. Model Tuning & Ensemble
        xgb_model = xgb.XGBRegressor(random_state=42)
        param_grid = {
            'n_estimators': [100, 200],
            'max_depth': [3, 4],
            'learning_rate': [0.05, 0.1],
            'reg_lambda': [1.0, 10.0]
        }
        
        grid = GridSearchCV(xgb_model, param_grid, cv=3, scoring='neg_mean_absolute_error')
        grid.fit(X_train, y_train, sample_weight=sw_train)
        best_xgb = grid.best_estimator_
        
        rf_model = RandomForestRegressor(n_estimators=200, max_depth=5, random_state=42)
        gb_model = GradientBoostingRegressor(n_estimators=200, learning_rate=0.05, max_depth=3, random_state=42)
        
        # Weighted Ensemble: XGB usually performs better
        ensemble = VotingRegressor([
            ('xgb', best_xgb),
            ('rf', rf_model),
            ('gb', gb_model)
        ], weights=[2, 1, 1])
        
        ensemble.fit(X_train, y_train, sample_weight=sw_train)
        predictions[val_idx] = ensemble.predict(X_val)
        
        # Record importance
        feature_importances.append(best_xgb.feature_importances_)
        
    metrics = calculate_fairness_metrics(df_meta, y, predictions)
    avg_importance = np.mean(feature_importances, axis=0)
    metrics['feature_importances'] = dict(zip(X_train.columns, avg_importance))
    
    return metrics

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
    print("\nV1 Feature Importances:")
    for feat, imp in sorted(v1_metrics['feature_importances'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {feat}: {imp:.4f}")
    
    # Version 2: With Accessibility
    print("\nEvaluating Model V2 (Accessibility Extension)...")
    # Clean for V2 (need transit cols)
    v2_df = df.dropna(subset=ACCESSIBILITY_FEATURES)
    print(f"Records for V2: {len(v2_df)}")
    v2_metrics = train_eval(v2_df[BASE_FEATURES + ACCESSIBILITY_FEATURES], v2_df['target'], v2_df)
    print("\nV2 Feature Importances:")
    for feat, imp in sorted(v2_metrics['feature_importances'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {feat}: {imp:.4f}")
    
    generate_report(v1_metrics, v2_metrics)

if __name__ == "__main__":
    run_harness()
