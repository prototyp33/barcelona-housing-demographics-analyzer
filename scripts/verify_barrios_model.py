import sys
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.price_predictor import PricePredictor

def verify_barrios():
    predictor = PricePredictor()
    
    # Target barrios
    barrio_names = ["L'Antiga Esquerra de l'Eixample", "el Raval"]
    
    # Load data
    df_all = predictor.load_data()
    
    print("="*60)
    print("🔍 VERIFICACIÓN DE MODELO PARA BARRIOS ESPECÍFICOS")
    print("="*60)
    
    for name in barrio_names:
        # Get latest data for this barrio
        df_barrio = df_all[df_all['barrio_nombre'].str.lower() == name.lower()].sort_values('anio', ascending=False).head(1)
        
        if df_barrio.empty:
            print(f"\n❌ No se encontraron datos para: {name}")
            continue
            
        print(f"\n📍 Barrio: {name} (Año {df_barrio['anio'].iloc[0]})")
        print(f"   Renta Media: {df_barrio['renta_media'].iloc[0]:,.0f}€")
        print(f"   Airbnb Listings: {df_barrio['num_airbnb'].iloc[0]:.0f}")
        print(f"   Precio Real m2: {df_barrio['target_precio_m2'].iloc[0]:,.0f}€")
        
        # Predictions
        features = df_barrio[predictor.feature_cols]
        pred_ridge = predictor.predict(features, model_name="ridge")[0]
        pred_lasso = predictor.predict(features, model_name="lasso")[0]
        
        print(f"   Predicción Ridge: {pred_ridge:,.0f}€/m² (Diferencia: {pred_ridge - df_barrio['target_precio_m2'].iloc[0]:+.0f}€)")
        print(f"   Predicción Lasso: {pred_lasso:,.0f}€/m² (Diferencia: {pred_lasso - df_barrio['target_precio_m2'].iloc[0]:+.0f}€)")
        
        # Marginal impact of Airbnb for this barrio
        insights = predictor.get_model_insights("ridge")
        real_impact_airbnb = insights['real_world_impacts'].get('num_airbnb', 0)
        
        assigned_to_airbnb = df_barrio['num_airbnb'].iloc[0] * real_impact_airbnb
        print(f"   Impacto atribuible a Airbnb: {assigned_to_airbnb:,.0f}€/m²")

if __name__ == "__main__":
    verify_barrios()
