
import pandas as pd
import requests
import io
import os
from pathlib import Path

# URLs
URL_TRANSPORTS = "https://opendata-ajuntament.barcelona.cat/data/dataset/e0c34739-823f-470d-8045-e10f28e80f2d/resource/e07dec0d-4aeb-40f3-b987-e1f35e088ce2/download"
URL_BUS = "https://opendata-ajuntament.barcelona.cat/data/dataset/d395e808-697d-4722-8eb9-b672a8ba0916/resource/2d190658-93ac-4c43-a23f-c5d313b1ae9c/download"

def integrate_accessibility():
    print("🚉 Integrating Accessibility Features (Phase 2.1)...")
    
    # 1. Download Data
    print("Downloading transport data...")
    df_rail = pd.read_csv(io.BytesIO(requests.get(URL_TRANSPORTS).content))
    df_bus = pd.read_csv(io.BytesIO(requests.get(URL_BUS).content))
    
    # 2. Process Rail (Metro, FGC, RENFE, Tram)
    # Filter types that are high-capacity rail
    rail_types = [
        "Ferrocarrils Generalitat (FGC)", 
        "Metro i línies urbanes FGC", 
        "RENFE", 
        "Tramvia", 
        "Tren a l'aeroport"
    ]
    df_rail_filtered = df_rail[df_rail['NOM_CAPA'].isin(rail_types)]
    
    # Count unique stations per barrio (using EQUIPAMENT as proxy for station name)
    rail_by_barrio = df_rail_filtered.groupby('BARRI').agg({
        'EQUIPAMENT': 'nunique',
        'NOM_CAPA': 'nunique'
    }).rename(columns={'EQUIPAMENT': 'rail_count', 'NOM_CAPA': 'rail_diversity'})
    
    # 3. Process Bus
    bus_by_barrio = df_bus.groupby('BARRI').agg({
        'EQUIPAMENT': 'count'
    }).rename(columns={'EQUIPAMENT': 'bus_count'})
    
    # 4. Merge Features
    accessibility = rail_by_barrio.join(bus_by_barrio, how='outer').fillna(0)
    
    # Hub detection logic: high diversity OR high count
    accessibility['is_transport_hub'] = ((accessibility['rail_diversity'] >= 2) | (accessibility['rail_count'] >= 5)).astype(int)
    
    # Composite Accessibility Index (Normalized approach)
    # Using the logic: Rail is ~5x more valuable than individual bus stops for price
    accessibility['accessibility_score'] = (accessibility['rail_count'] * 3) + np.log1p(accessibility['bus_count'])
    
    # 5. Integrate with ML Dataset
    ML_DATA_PATH = Path('data/barcelona_ml_valuation.csv')
    if ML_DATA_PATH.exists():
        df_ml = pd.read_csv(ML_DATA_PATH)
        
        # Merge on barrio_id (ML) = BARRI (Transport)
        df_ml = df_ml.merge(accessibility, left_on='barrio_id', right_index=True, how='left')
        
        # Fill missing with 0 (barrios with no transport recorded?)
        cols_to_fill = ['rail_count', 'rail_diversity', 'bus_count', 'is_transport_hub', 'accessibility_score']
        df_ml[cols_to_fill] = df_ml[cols_to_fill].fillna(0)
        
        df_ml.to_csv(ML_DATA_PATH, index=False)
        print(f"✅ Success! Integrated accessibility features for {len(df_ml)} neighborhoods.")
        print("\nFeatures added:")
        print(df_ml[cols_to_fill].describe().loc[['mean', 'max']])
        
if __name__ == "__main__":
    import numpy as np
    integrate_accessibility()
