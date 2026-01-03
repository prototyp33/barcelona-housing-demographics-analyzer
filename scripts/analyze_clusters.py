import pandas as pd
import sqlite3
from pathlib import Path

# Configuración
db_path = Path("data/master.db")
clusters_path = Path("data/neighborhood_clusters.csv")

# 1. Cargar datos
df_clusters = pd.read_csv(clusters_path)
conn = sqlite3.connect(db_path)

# Obtener datos de 2023 para caracterizar los grupos
query = """
SELECT 
    b.barrio_id, b.barrio_nombre, b.distrito_nombre,
    AVG(p.precio_m2_venta) as precio_m2,
    AVG(p.precio_mes_alquiler) as renta_alquiler,
    r.renta_bruta_llar,
    r.indice_gini,
    c.superficie_media_m2,
    c.antiguedad_media_bloque
FROM dim_barrios b
JOIN fact_precios p ON b.barrio_id = p.barrio_id AND p.anio = 2023
JOIN fact_renta_avanzada r ON b.barrio_id = r.barrio_id AND r.anio = 2023
LEFT JOIN fact_catastro_avanzado c ON b.barrio_id = c.barrio_id AND c.anio = 2023
GROUP BY b.barrio_id
"""
df_data = pd.read_sql(query, conn)
conn.close()

# 2. Integrar Clústeres
df_full = df_data.merge(df_clusters[['barrio_id', 'cluster']], on='barrio_id')

# 3. Calcular Yield
df_full['yield'] = (df_full['renta_alquiler'] * 12) / (df_full['precio_m2'] * 80) * 100

# 4. Análisis por Clúster
profile = df_full.groupby('cluster').agg({
    'barrio_nombre': 'count',
    'precio_m2': 'mean',
    'renta_bruta_llar': 'mean',
    'yield': 'mean',
    'indice_gini': 'mean',
    'antiguedad_media_bloque': 'mean'
}).sort_values('precio_m2', ascending=False)

print("\n--- PERFIL ESTRATÉGICO DE CLÚSTERES ---")
print(profile)

print("\n--- EJEMPLOS POR CLÚSTER ---")
for cluster in sorted(df_full['cluster'].unique()):
    examples = df_full[df_full['cluster'] == cluster]['barrio_nombre'].head(5).tolist()
    print(f"Clúster {cluster}: {', '.join(examples)}")
