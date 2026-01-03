import pandas as pd
import numpy as np

df_ml = pd.read_csv('data/barcelona_ml_valuation.csv')
df_ml['desviacion_valor'] = ((df_ml['avg_venta_23'] - df_ml['precio_estimado']) / df_ml['precio_estimado']) * 100

def simulator(budget_euros, strategy='yield', min_size_m2=65):
    reco = df_ml.copy()
    # Solo consideras barrios con precio > 0 para evitar errores de carga
    reco = reco[reco['avg_venta_23'] > 0]
    reco['entry_cost'] = reco['avg_venta_23'] * min_size_m2
    reco = reco[reco['entry_cost'] <= budget_euros]
    
    if reco.empty: return None
    
    if strategy == 'yield':
        final = reco.sort_values('gross_yield', ascending=False)
    elif strategy == 'upside':
        # Buscamos alto crecimiento histórico + estar infravalorado (desviacion negativa)
        reco['score'] = reco['price_growth_1y'] - (reco['desviacion_valor'] * 0.5)
        final = reco.sort_values('score', ascending=False)
    else: # strategy 'safe' / value
        final = reco.sort_values('desviacion_valor', ascending=True)
    
    return final.head(3)

print("\n🚀 SIMULACIÓN DE INVERSIÓN INTELIGENTE - BARCELONA 2024\n")

print("--- 💸 E1: MAXIMIZACIÓN DE CASH-FLOW (Presupuesto: 180,000€) ---")
res1 = simulator(180000, strategy='yield')
if res1 is not None:
    print(res1[['barrio_nombre', 'avg_venta_23', 'gross_yield', 'segmento']].to_string(index=False))

print("\n--- 💎 E2: BUSCADOR DE VALOR/GANGAS (Presupuesto: 350,000€) ---")
res2 = simulator(350000, strategy='safe')
if res2 is not None:
    print(res2[['barrio_nombre', 'avg_venta_23', 'desviacion_valor', 'segmento']].to_string(index=False))

print("\n--- 📈 E3: CRECIMIENTO Y PLUSVALÍA (Presupuesto: 600,000€) ---")
res3 = simulator(600000, strategy='upside')
if res3 is not None:
    print(res3[['barrio_nombre', 'avg_venta_23', 'price_growth_1y', 'desviacion_valor']].to_string(index=False))

print("\n--- 🛡️ E4: PRESERVACIÓN PATRIMONIAL (Presupuesto: 1,000,000€) ---")
# Filtramos directamente el segmento Prime
prime_reco = df_ml[df_ml['segmento'].str.contains('Prime', na=False)].sort_values('avg_venta_23', ascending=False).head(3)
print(prime_reco[['barrio_nombre', 'avg_venta_23', 'renta_bruta_llar', 'segmento']].to_string(index=False))
