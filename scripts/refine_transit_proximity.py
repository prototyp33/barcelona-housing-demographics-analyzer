
import pandas as pd
import requests
import io
import numpy as np
from pathlib import Path
from math import radians, cos, sin, asin, sqrt

# URLs
URL_TRANSPORTS = "https://opendata-ajuntament.barcelona.cat/data/dataset/e0c34739-823f-470d-8045-e10f28e80f2d/resource/e07dec0d-4aeb-40f3-b987-e1f35e088ce2/download"
URL_BUS = "https://opendata-ajuntament.barcelona.cat/data/dataset/d395e808-697d-4722-8eb9-b672a8ba0916/resource/2d190658-93ac-4c43-a23f-c5d313b1ae9c/download"

def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371 # km
    return c * r * 1000 # meters

def refine_transit_v3():
    print("🚉 Refining Transport Proximity: Metro, FGC, and Bus (Phase 2.5)...")
    
    # 1. Load Data
    print("Downloading station coordinates...")
    df_all = pd.read_csv(io.BytesIO(requests.get(URL_TRANSPORTS).content))
    df_bus = pd.read_csv(io.BytesIO(requests.get(URL_BUS).content))
    
    # 2. Extract specific points
    # Split Metro and FGC based on the category names
    # Ferrocarrils Generalitat (FGC)
    fgc_pts = df_all[df_all['NOM_CAPA'] == 'Ferrocarrils Generalitat (FGC)'][['LONGITUD', 'LATITUD']].values
    # Metro (and FGC urban lines)
    metro_pts = df_all[df_all['NOM_CAPA'] == 'Metro i línies urbanes FGC'][['LONGITUD', 'LATITUD']].values
    # Bus
    bus_pts = df_bus[['LONGITUD', 'LATITUD']].values
    
    # 3. Get Neighborhood Centroids
    barrio_centroids = df_all.groupby('BARRI').agg({'LONGITUD': 'mean', 'LATITUD': 'mean'})
    
    results = []
    print("Calculating geodesic distances for all barrios...")
    for barrio_id, row in barrio_centroids.iterrows():
        b_lon, b_lat = row['LONGITUD'], row['LATITUD']
        
        # Absolute proximity (nearest node)
        d_metro = min([haversine(b_lon, b_lat, p[0], p[1]) for p in metro_pts]) if len(metro_pts) > 0 else 5000
        d_fgc = min([haversine(b_lon, b_lat, p[0], p[1]) for p in fgc_pts]) if len(fgc_pts) > 0 else 5000
        d_bus = min([haversine(b_lon, b_lat, p[0], p[1]) for p in bus_pts]) if len(bus_pts) > 0 else 5000
        
        # Micro-density (Bus stops in 300m walking radius)
        bus_nearby = sum([1 for p in bus_pts if haversine(b_lon, b_lat, p[0], p[1]) <= 300])
        
        results.append({
            'barrio_id': int(barrio_id),
            'dist_metro_m': d_metro,
            'dist_fgc_m': d_fgc,
            'dist_bus_m': d_bus,
            'bus_density_300m': bus_nearby
        })
        
    df_refined = pd.DataFrame(results).set_index('barrio_id')
    
    # 4. Integrate with ML Dataset
    ML_DATA_PATH = Path('data/barcelona_ml_valuation.csv')
    if ML_DATA_PATH.exists():
        df_ml = pd.read_csv(ML_DATA_PATH)
        
        # Drop previous iterations to avoid column bloat
        cols_to_drop = ['dist_metro_m', 'dist_fgc_m', 'dist_bus_m', 'bus_density_300m', 
                       'dist_train_m', 'dist_center_m', 'dist_airport_m', 'transport_log_score']
        df_ml = df_ml.drop(columns=[c for c in cols_to_drop if c in df_ml.columns])
        
        # Merge new metrics
        df_ml = df_ml.merge(df_refined, left_on='barrio_id', right_index=True, how='left')
        
        # Fill missing values with mean
        df_ml = df_ml.fillna(df_ml.mean(numeric_only=True))
        
        # Modern Accessibility Score (weighted by comfort/speed: Metro/FGC > Bus)
        # Higher score is better
        df_ml['access_score_v3'] = (
            (1000 / (df_ml['dist_metro_m'] + 100) * 0.5) +
            (1000 / (df_ml['dist_fgc_m'] + 100) * 0.3) +
            (df_ml['bus_density_300m'] * 0.2)
        )
        
        df_ml.to_csv(ML_DATA_PATH, index=False)
        print("✅ Refined transit metrics integrated (separated Bus, Metro, and FGC).")
        print(df_ml[['dist_metro_m', 'dist_fgc_m', 'dist_bus_m', 'access_score_v3']].describe().loc[['mean', 'max']])

if __name__ == "__main__":
    refine_transit_v3()
