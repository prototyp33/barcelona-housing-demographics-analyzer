import sqlite3
import pandas as pd
from pathlib import Path
from sklearn.cluster import KMeans
from sklearn.preprocessing import RobustScaler

db_path = Path("data/master.db")
if not db_path.exists():
    db_path = Path("data/processed/database.db")
conn = sqlite3.connect(db_path)

query = """
SELECT 
    b.barrio_id, b.barrio_nombre, b.distrito_nombre,
    p23.avg_venta_23, p23.avg_alquiler_23,
    p22.avg_venta_22,
    r.renta_bruta_llar, r.indice_gini,
    c.superficie_media_m2, c.antiguedad_media_bloque, 
    c.num_propietarios_juridica, c.num_propietarios_fisica,
    c.pct_propietarios_extranjeros, c.indice_penalizacion_topografica, c.num_plantas_avg
FROM dim_barrios b
LEFT JOIN (
    SELECT barrio_id, AVG(precio_m2_venta) as avg_venta_23, AVG(precio_mes_alquiler) as avg_alquiler_23
    FROM fact_precios WHERE anio = 2023 GROUP BY barrio_id
) p23 ON b.barrio_id = p23.barrio_id
LEFT JOIN (
    SELECT barrio_id, AVG(precio_m2_venta) as avg_venta_22
    FROM fact_precios WHERE anio = 2022 GROUP BY barrio_id
) p22 ON b.barrio_id = p22.barrio_id
LEFT JOIN fact_renta_avanzada r ON b.barrio_id = r.barrio_id AND r.anio = 2023
LEFT JOIN fact_catastro_avanzado c ON b.barrio_id = c.barrio_id AND c.anio = 2023
"""

df = pd.read_sql(query, conn)

# Feature engineering
df['gross_yield'] = (df['avg_alquiler_23'] * 12) / (df['avg_venta_23'] * df['superficie_media_m2'].fillna(80)) * 100
df['effort_rate'] = (df['avg_alquiler_23'] / ((df['renta_bruta_llar'] * 0.78) / 12)) * 100
df['price_growth_1y'] = (df['avg_venta_23'] - df['avg_venta_22']) / df['avg_venta_22'] * 100
df['pct_juridica'] = (df['num_propietarios_juridica'] / (df['num_propietarios_fisica'] + df['num_propietarios_juridica'] + 1e-6)) * 100

# NEW: Elevator/Access Factor (Old + Tall = High Risk of no elevator)
df['access_penalty'] = (
    (df['antiguedad_media_bloque'] - 40).clip(lower=0) * 
    (df['num_plantas_avg'] - 3).clip(lower=0)
) / 10.0 # Normalized proxy

# NEW: Merge POI Distances
centroids_path = Path("data/processed/barrio_centroids.csv")
if centroids_path.exists():
    df_centroids = pd.read_csv(centroids_path)
    df = df.merge(df_centroids[['barrio_id', 'dist_to_center', 'dist_to_tech_hub']], on='barrio_id', how='left')

# Fill NaNs for the model
df['indice_penalizacion_topografica'] = df['indice_penalizacion_topografica'].fillna(0)
df['access_penalty'] = df['access_penalty'].fillna(0)
df['dist_to_center'] = df['dist_to_center'].fillna(df['dist_to_center'].mean())
df['dist_to_tech_hub'] = df['dist_to_tech_hub'].fillna(df['dist_to_tech_hub'].mean())
df['pct_propietarios_extranjeros'] = df['pct_propietarios_extranjeros'].fillna(df['pct_propietarios_extranjeros'].mean())

# NEIGHBORHOOD SEGMENTATION (Clustering)
cluster_vars = [
    'avg_venta_23', 'gross_yield', 'effort_rate', 
    'price_growth_1y', 'renta_bruta_llar', 'indice_gini', 
    'pct_juridica', 'pct_propietarios_extranjeros', 'antiguedad_media_bloque'
]

# Fill NaNs for clustering variables specifically
for var in cluster_vars:
    df[var] = df[var].fillna(df[var].mean())

# Scaling for clustering
scaler = RobustScaler()
X_scaled = scaler.fit_transform(df[cluster_vars])

# K-Means Clustering
kmeans = KMeans(n_clusters=4, random_state=42)
df['segmento'] = kmeans.fit_predict(X_scaled)

# Export
df.to_csv("data/barcelona_ml_valuation.csv", index=False)
print("✅ barcelona_ml_valuation.csv updated with Topographical, Access penalties, POI distances, and Neighborhood Segments.")
