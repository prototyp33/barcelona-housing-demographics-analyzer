
import pandas as pd
import numpy as np

df_ml = pd.read_csv('data/barcelona_ml_valuation.csv')

# Mapeo de segmentos (basado en el análisis de clusters)
segment_map = {
    0: "💎 Prime / Safe Haven",
    1: "🏠 Stable Residential (Periphery)",
    2: "🏛️ Historic Center / Eixample",
    3: "📈 High Yield / Investment"
}

def simulator(budget_euros, strategy='yield', min_size_m2=65):
    reco = df_ml.copy()
    reco = reco[reco['avg_venta_23'] > 0]
    reco['entry_cost'] = reco['avg_venta_23'] * min_size_m2
    reco = reco[reco['entry_cost'] <= budget_euros]
    
    if reco.empty: return None
    
    if strategy == 'yield':
        final = reco.sort_values('gross_yield', ascending=False)
    elif strategy == 'upside':
        reco['score'] = reco['price_growth_1y'] - (reco['desviacion_valor'] * 0.5)
        final = reco.sort_values('score', ascending=False)
    else: # strategy 'safe' / value
        final = reco.sort_values('desviacion_valor', ascending=True)
    
    final['segmento_nombre'] = final['segmento'].map(segment_map)
    return final.head(3)

print("\n🔍 CUSTOM INVESTMENT SIMULATION REPORT\n")

scenarios = [
    {"name": "Budget Investor (Low Entry)", "budget": 150000, "strategy": "yield"},
    {"name": "Balanced Portfolio (Mid Range)", "budget": 450000, "strategy": "safe"},
    {"name": "High Capital Growth (Aggressive)", "budget": 750000, "strategy": "upside"}
]

for s in scenarios:
    print(f"--- 🔹 Scenario: {s['name']} (Budget: {s['budget']:,}€, Strategy: {s['strategy']}) ---")
    res = simulator(s['budget'], strategy=s['strategy'])
    if res is not None:
        cols = ['barrio_nombre', 'avg_venta_23', 'gross_yield', 'desviacion_valor', 'segmento_nombre']
        print(res[cols].to_string(index=False))
    else:
        print("No options found for this budget.")
    print("\n")
