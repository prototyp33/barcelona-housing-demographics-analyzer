import pandas as pd

df = pd.read_csv('data/barcelona_ml_valuation.csv')
coll = df[df['barrio_nombre'] == 'el Coll'].iloc[0]

print(f"--- 🔍 DIAGNÓSTICO ESTRATÉGICO: {coll['barrio_nombre']} ---")
print(f"Precio Real: {coll['avg_venta_23']:.2f}€/m2")
print(f"Fair Value ML: {coll['precio_estimado']:.2f}€/m2")
print(f"Desviación (Opportunity Gap): {((coll['avg_venta_23'] - coll['precio_estimado'])/coll['precio_estimado']*100):.2f}%")

print("\n⚠️ ANÁLISIS DE RESIDUO (Trampa vs Oportunidad):")
print("1. El 'Error' del ML (-15.8%) se explica por factores no tabulados:")
print("   - Factor Topográfico: 'Impuesto de la Pendiente'.")
print("   - Accesibilidad: Penalización por Metro Profundo (74m).")
print("   - Parque s/Ascensor: Sesgo que deprime la media del barrio.")

print("\n💡 VERDICTO DE INVERSIÓN (Asset Management):")
print("Para que el 'Fair Value' de 3.300€+ sea real, el activo DEBE cumplir:")
print("- Estar en edificios post-1980 (con ascensor).")
print("- Estar cerca del Pg. Mare de Déu del Coll (cuerda de nivel baja).")
print("- Si el activo es un 4º sin ascensor -> NO es una ganga, es una TRAMPA DE VALOR.")
