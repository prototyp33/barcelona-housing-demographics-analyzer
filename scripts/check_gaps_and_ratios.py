import pandas as pd
import numpy as np

# Cargar datos
file_path = 'data/exports/looker_studio/master_table_barcelona_housing.csv'
df = pd.read_csv(file_path)

# Adaptación de nombres de columnas
# Any -> anio
# Codi_Barri -> codi_barri
# Preu_Mitja -> precio_m2_venta_promedio
# Nom_Barri -> barrio_nombre
# Codi_Districte -> distrito_nombre

# 1. IDENTIFICAR GAPS EN 2012-2013
# Filtramos años objetivo
gaps_df = df[df['anio'].isin([2012, 2013])]
# Buscamos dónde el precio es nulo o 0
missing_data = gaps_df[(gaps_df['precio_m2_venta_promedio'].isna()) | (gaps_df['precio_m2_venta_promedio'] == 0)]

print(f"--- GAPS DETECTADOS (2012-2013) ---")
print(f"Total registros faltantes: {len(missing_data)}")
affected_barrios = sorted(missing_data['codi_barri'].unique())
print(f"Barrios afectados ({len(affected_barrios)}): {affected_barrios}")

# 2. CALCULAR FACTOR DE AJUSTE (RATIO)
# Para cada barrio afectado, calculamos su relación con el distrito en años CON datos (2014-2024)
ratio_report = []

for barrio in affected_barrios:
    # Obtener datos del barrio (excluyendo 2012-2013)
    barrio_data = df[(df['codi_barri'] == barrio) & (df['anio'] > 2013)]
    
    if len(barrio_data) > 0:
        # Obtener el distrito de este barrio
        distrito_nombre = barrio_data['distrito_nombre'].iloc[0]
        nom_barri = barrio_data['barrio_nombre'].iloc[0]
        
        # Obtener datos del DISTRITO COMPLETO en esos mismos años (excluyendo nulos)
        distrito_data = df[(df['distrito_nombre'] == distrito_nombre) & (df['anio'] > 2013) & (df['precio_m2_venta_promedio'] > 0)]
        
        # Calcular medias históricas (promedio de promedios anuales del distrito)
        # Agrupamos por año para que el distrito tenga un valor representativo anual
        distrito_yearly = distrito_data.groupby('anio')['precio_m2_venta_promedio'].mean()
        
        # Media del barrio en el periodo
        avg_barrio = barrio_data['precio_m2_venta_promedio'].mean()
        # Media del distrito en el mismo periodo
        avg_distrito = distrito_yearly.mean()
        
        # Calcular Ratio
        ratio = avg_barrio / avg_distrito if avg_distrito > 0 else 1.0
        
        ratio_report.append({
            'codi_barri': barrio,
            'barrio_nombre': nom_barri,
            'distrito_nombre': distrito_nombre,
            'Avg_Price_Barrio': round(avg_barrio, 2),
            'Avg_Price_Distrito': round(avg_distrito, 2),
            'Adjustment_Factor': round(ratio, 4)
        })
    else:
        print(f"⚠️ ALERTA: El barrio {barrio} no tiene datos ni siquiera después de 2013.")

# Mostrar tabla de ratios
df_ratios = pd.DataFrame(ratio_report)
if not df_ratios.empty:
    print("\n--- FACTORES DE AJUSTE CALCULADOS ---")
    print(df_ratios[['barrio_nombre', 'Avg_Price_Barrio', 'Avg_Price_Distrito', 'Adjustment_Factor']])
else:
    print("\nNo se pudieron calcular factores de ajuste.")
