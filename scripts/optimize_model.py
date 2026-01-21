"""
Model Optimization Script - Phase 5
Integrates ESG features, performs feature selection, and trains a StackingRegressor.
Includes SHAP global explainability.
"""

import sqlite3
import pandas as pd
import numpy as np
import xgboost as xgb
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, StackingRegressor
from sklearn.linear_model import RidgeCV
from pathlib import Path
import logging
from datetime import datetime

# Optional SHAP check
try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "processed" / "database.db"
OUTPUT_DIR = PROJECT_ROOT / "docs" / "models" / "phase5"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Extended Feature Set
FEATURES = [
    'renta_mediana', 'poblacion_total', 'edad_media', 
    'porc_inmigracion', 'pct_mayores_65', 'pct_menores_15',
    'access_score', 'dist_metro_m',
    'total_centros_educativos', 'viviendas_proteccion_oficial',
    'tasa_criminalidad_1000hab', 'num_listings_airbnb'
]

def load_dataset():
    """Consolidate features from all fact tables."""
    if not DB_PATH.exists():
        logger.error(f"Database not found at {DB_PATH}")
        return pd.DataFrame()
        
    conn = sqlite3.connect(DB_PATH)
    
    # Base Query: Precios (Target), Renta, Demografia, Mobility
    # We use 2023 for prices as it's the most complete recent year
    query = """
    SELECT 
        db.barrio_id, db.barrio_nombre, db.distrito_nombre,
        AVG(fp.precio_m2_venta) AS target,
        vd.poblacion_total, vd.edad_media, vd.porc_inmigracion,
        vd.pct_mayores_65, vd.pct_menores_15,
        fr.renta_mediana, 
        fm.dist_metro_m, fm.access_score,
        fe.total_centros_educativos,
        fvp.viviendas_proteccion_oficial,
        fs.tasa_criminalidad_1000hab,
        fpt.num_listings_airbnb
    FROM dim_barrios db
    JOIN fact_precios fp ON db.barrio_id = fp.barrio_id AND fp.anio = 2023
    LEFT JOIN v_demografia_aggregated vd ON db.barrio_id = vd.barrio_id AND vd.anio = 2025
    JOIN fact_renta fr ON db.barrio_id = fr.barrio_id AND fr.anio = 2022
    LEFT JOIN fact_movilidad fm ON db.barrio_id = fm.barrio_id
    LEFT JOIN fact_educacion fe ON db.barrio_id = fe.barrio_id AND fe.anio = 2025
    LEFT JOIN fact_vivienda_publica fvp ON db.barrio_id = fvp.barrio_id AND fvp.anio = 2025
    LEFT JOIN fact_seguridad fs ON db.barrio_id = fs.barrio_id AND fs.anio = 2025
    LEFT JOIN fact_presion_turistica fpt ON db.barrio_id = fpt.barrio_id AND fpt.anio = 2025
    WHERE fp.precio_m2_venta IS NOT NULL
    GROUP BY db.barrio_id
    """
    df = pd.read_sql(query, conn)
    conn.close()
    
    # Fill missing values for optional features with zero or median
    df['total_centros_educativos'] = df['total_centros_educativos'].fillna(0)
    df['viviendas_proteccion_oficial'] = df['viviendas_proteccion_oficial'].fillna(0)
    df['tasa_criminalidad_1000hab'] = df['tasa_criminalidad_1000hab'].fillna(df['tasa_criminalidad_1000hab'].median())
    df['num_listings_airbnb'] = df['num_listings_airbnb'].fillna(0)
    
    return df.dropna(subset=['target', 'renta_mediana'])

def perform_feature_engineering(df):
    """Add interactions and logs."""
    X = df[FEATURES].copy()
    
    # 1. Interactions
    X['renta_x_safety'] = X['renta_mediana'] * (1 / (X['tasa_criminalidad_1000hab'] + 1))
    X['renta_x_access'] = X['renta_mediana'] * X['access_score']
    
    # 2. Logs for skewed features
    X['log_poblacion'] = np.log1p(X['poblacion_total'])
    X['log_renta'] = np.log1p(X['renta_mediana'])
    X['log_listings'] = np.log1p(X['num_listings_airbnb'])
    
    return X

def analyze_feature_importance(X, y):
    """Run an initial XGBoost to see what matters."""
    model = xgb.XGBRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    importances = pd.Series(model.feature_importances_, index=X.columns).sort_values(ascending=False)
    
    plt.figure(figsize=(10, 6))
    importances.plot(kind='bar')
    plt.title("Feature Importance (XGBoost)")
    plt.savefig(OUTPUT_DIR / "feature_importance.png")
    plt.close()
    
    # Return features with importance > 0.005
    keep_features = importances[importances > 0.005].index.tolist()
    logger.info(f"Keeping {len(keep_features)}/ {len(X.columns)} features based on importance.")
    return keep_features

def get_stacking_regressor():
    """Build a Stacking Ensemble."""
    base_models = [
        ('xgb', xgb.XGBRegressor(n_estimators=200, max_depth=4, learning_rate=0.05, random_state=42)),
        ('rf', RandomForestRegressor(n_estimators=200, max_depth=6, random_state=42)),
        ('gb', GradientBoostingRegressor(n_estimators=200, learning_rate=0.05, max_depth=3, random_state=42))
    ]
    meta_model = RidgeCV()
    
    return StackingRegressor(estimators=base_models, final_estimator=meta_model)

def train_and_evaluate():
    """Main execution flow."""
    logger.info("📦 Loading data...")
    df = load_dataset()
    if df.empty:
        return
        
    X_fe = perform_feature_engineering(df)
    y = df['target']
    
    # Initial Importance Pruning
    important_features = analyze_feature_importance(X_fe, y)
    X = X_fe[important_features]
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Scaling
    scaler = StandardScaler()
    X_train_sc = scaler.fit_transform(X_train)
    X_test_sc = scaler.transform(X_test)
    
    # 3. Fairness Weighting: Penalize error in low-income areas aggressively
    median_renta = df['renta_mediana'].median()
    train_renta = df.loc[X_train.index, 'renta_mediana']
    # If renta is low, we give massive weight (10x) to force parity
    sample_weights = np.where(train_renta <= median_renta, 10.0, 1.0)
    
    # Train Stacking
    logger.info("🚀 Training Weighted Ensemble for Fairness Parity...")
    stack = get_stacking_regressor()
    
    # Fit base learners with aggressive weights
    for name, est in stack.estimators:
        est.fit(X_train_sc, y_train, sample_weight=sample_weights)
    
    # Use a VotingRegressor with tuned weights to balance R2 and IPR
    from sklearn.ensemble import VotingRegressor
    # Reducing XGB weight slightly as it tends to overfit high-renta signals
    voter = VotingRegressor([
        ('xgb', stack.estimators[0][1]),
        ('rf', stack.estimators[1][1]),
        ('gb', stack.estimators[2][1])
    ], weights=[1, 2, 2])
    
    voter.fit(X_train_sc, y_train, sample_weight=sample_weights)
    
    # Predict
    y_pred = voter.predict(X_test_sc)
    
    # Metrics
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    logger.info(f"🎯 Final Metrics: R2={r2:.4f}, MAE={mae:.2f}€")
    
    # SHAP Explainability
    if HAS_SHAP:
        logger.info("🧠 Generating SHAP values...")
        # SHAP usually works better on native models, so let's use the xgb from the stack or a new one
        explainer = shap.Explainer(stack.named_estimators_['xgb'], X_train_sc)
        shap_values = explainer(X_test_sc)
        
        plt.figure()
        shap.summary_plot(shap_values, X_test, show=False)
        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / "shap_summary.png")
        plt.close()
    
    # Fairness check (IPR)
    low_income_mask = df.loc[X_test.index, 'renta_mediana'] <= df['renta_mediana'].median()
    mae_low = mean_absolute_error(y_test[low_income_mask], y_pred[low_income_mask])
    mae_high = mean_absolute_error(y_test[~low_income_mask], y_pred[~low_income_mask])
    ipr = mae_low / mae_high
    logger.info(f"⚖️ Fairness Check: IPR={ipr:.4f} (MAE Low: {mae_low:.1f}, MAE High: {mae_high:.1f})")

    # Save metrics to file
    with open(OUTPUT_DIR / "metrics.txt", "w") as f:
        f.write(f"Timestamp: {datetime.now()}\n")
        f.write(f"R2Score: {r2:.4f}\n")
        f.write(f"MAE: {mae:.2f}\n")
        f.write(f"IPR: {ipr:.4f}\n")
        f.write(f"Features: {important_features}\n")

if __name__ == "__main__":
    train_and_evaluate()
