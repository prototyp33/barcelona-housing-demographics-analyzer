import pandas as pd
import numpy as np

# Load the final CSV
file_path = 'data/exports/looker_studio/master_table_barcelona_housing.csv'
df = pd.read_csv(file_path)

print("--- 1. DISTRIBUTION OF CONFIDENCE ---")
print(df['confidence_score'].value_counts(normalize=True))

print("\n--- 2. DISTRIBUTION OF CONTEXT ---")
print(df['market_context'].value_counts())

print("\n--- 3. MOST COMMON FLAGS ---")
print(df['quality_flags'].value_counts().head(10))

print("\n--- 4. NULL CHECK ---")
cols_to_check = ['precio_m2_venta_promedio', 'confidence_score', 'quality_flags']
print(df[cols_to_check].isnull().sum())

# Torre Baro 2019 Check (Current state on disk)
torre_baro_2019 = df[(df['codi_barri'] == 54) & (df['anio'] == 2019)]
if not torre_baro_2019.empty:
    print("\n--- 5. TORRE BARÓ 2019 (CURRENT STATE ON DISK) ---")
    print(torre_baro_2019[['precio_m2_venta_promedio', 'num_registros_precios', 'confidence_score', 'quality_flags']])
