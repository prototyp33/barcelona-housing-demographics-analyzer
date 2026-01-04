
import pandas as pd
import numpy as np

# Load the un-collapsed master data if possible, or use the ML result
df_ml = pd.read_csv('data/barcelona_ml_valuation.csv')

def analyze_bias():
    print("🔬 DATA BIAS ANALYSIS REPORT\n")
    
    # 1. Geographic Bias: Error distribution by District
    print("--- 📍 Geographic Bias (MAE by District) ---")
    df_ml['abs_error'] = np.abs(df_ml['avg_venta_23'] - df_ml['precio_estimado'])
    district_error = df_ml.groupby('distrito_nombre')['abs_error'].agg(['mean', 'count']).sort_values('mean', ascending=False)
    print(district_error)
    print("\n*Interpretation: If certain districts have much higher mean error, the model might be missing local fundamental factors (e.g., crime, tourism, or specific local amenities).\n")
    
    # 2. Socioeconomic Bias: Residuals vs Income
    print("--- 💰 Socioeconomic Bias (Residuals vs Income) ---")
    # Low income vs High income split
    median_income = df_ml['renta_bruta_llar'].median()
    low_income = df_ml[df_ml['renta_bruta_llar'] <= median_income]
    high_income = df_ml[df_ml['renta_bruta_llar'] > median_income]
    
    print(f"Median Household Income: {median_income:,.0f}€")
    print(f"MAE Low Income Barrio: {low_income['abs_error'].mean():.2f} €/m²")
    print(f"MAE High Income Barrio: {high_income['abs_error'].mean():.2f} €/m²")
    
    # Check for systematic over/under estimation
    print(f"Avg Deviation Low Income: {low_income['desviacion_valor'].mean():.2f}%")
    print(f"Avg Deviation High Income: {high_income['desviacion_valor'].mean():.2f}%")
    print("\n*Interpretation: If 'Avg Deviation' is significantly positive or negative for a group, the model systematically overvalues or undervalues those areas.\n")
    
    # 3. Source Bias (Density of specific attributes)
    print("--- 📊 Variable Coverage Bias ---")
    critical_vars = ['superficie_media_m2', 'antiguedad_media_bloque', 'indice_gini', 'gross_yield']
    missing_data = df_ml[critical_vars].isna().sum()
    print("Missing Values in Critical Market Indicators:")
    print(missing_data)
    
    # 4. Outlier Analysis
    print("\n--- 🔍 Top Model Disagreements (Potential Bias or Opportunity?) ---")
    outliers = df_ml.sort_values('abs_error', ascending=False).head(5)
    print(outliers[['barrio_nombre', 'avg_venta_23', 'precio_estimado', 'abs_error', 'desviacion_valor']])

if __name__ == "__main__":
    analyze_bias()
