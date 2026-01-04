
import pandas as pd
import numpy as np
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "barcelona_ml_valuation.csv"

def calculate_fairness():
    print("⚖️ FAIRNESS METRICS AUDIT\n")
    
    if not DATA_PATH.exists():
        print("❌ Data not found.")
        return

    df = pd.read_csv(DATA_PATH)
    
    # Ensure error metrics exist
    df['abs_error'] = np.abs(df['avg_venta_23'] - df['precio_estimado'])
    df['abs_error_pct'] = (df['abs_error'] / df['avg_venta_23']) * 100

    # 1. Geographic Equity Score (GES)
    # GES = 1 - (std_dev_of_district_MAEs / mean_district_MAE)
    district_maes = df.groupby('distrito_nombre')['abs_error'].mean()
    mean_mae = district_maes.mean()
    std_mae = district_maes.std()
    ges = 1 - (std_mae / mean_mae)
    
    print(f"1. Geographic Equity Score (GES): {ges:.4f}")
    print(f"   Target: > 0.85 {'✅' if ges > 0.85 else '⚠️'}")
    print(f"   (Measures if the model is equally accurate across all districts)\n")

    # 2. Income Parity Ratio (IPR)
    # IPR = MAE_low_income / MAE_high_income
    median_income = df['renta_bruta_llar'].median()
    mae_low = df[df['renta_bruta_llar'] <= median_income]['abs_error'].mean()
    mae_high = df[df['renta_bruta_llar'] > median_income]['abs_error'].mean()
    ipr = mae_low / mae_high
    
    print(f"2. Income Parity Ratio (IPR): {ipr:.4f}")
    print(f"   Target: 0.8-1.2 {'✅' if 0.8 <= ipr <= 1.2 else '⚠️'}")
    print(f"   (Ratio of accuracy between low and high income areas)\n")

    # 3. Prediction Dispersion Index (PDI)
    # PDI = (95th - 5th percentile error) / median error
    errors = df['abs_error'].dropna()
    p95 = np.percentile(errors, 95)
    p5 = np.percentile(errors, 5)
    p50 = np.median(errors)
    pdi = (p95 - p5) / p50
    
    print(f"3. Prediction Dispersion Index (PDI): {pdi:.4f}")
    print(f"   Target: < 3.0 {'✅' if pdi < 3.0 else '⚠️'}")
    print(f"   (Measures the consistency of error magnitude)\n")

    # Summary of District performance for identifying outliers
    print("--- 📍 District MAE Breakdown ---")
    print(district_maes.sort_values(ascending=False))

if __name__ == "__main__":
    calculate_fairness()
