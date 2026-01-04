
import pandas as pd
import requests
import io
import json
import numpy as np
from pathlib import Path
from math import radians, cos, sin, asin, sqrt

# URLs
URL_RAIL = "https://opendata-ajuntament.barcelona.cat/data/dataset/e0c34739-823f-470d-8045-e10f28e80f2d/resource/e07dec0d-4aeb-40f3-b987-e1f35e088ce2/download"
URL_BICING = "https://opendata-ajuntament.barcelona.cat/data/dataset/informacio-estacions-bicing/resource/f3689404-fd33-4613-88ee-180a424263f3/download"

def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371 # Radius of earth in kilometers
    return c * r * 1000 # Return in meters

def refine_accessibility_v2():
    print("🛰️ Refining Accessibility with Geospatial Precision (Phase 2.4)...")
    
    # 1. Get stations and coordinates
    print("Downloading high-precision station data...")
    df_rail = pd.read_csv(io.BytesIO(requests.get(URL_RAIL).content))
    df_bicing = pd.read_csv(io.BytesIO(requests.get(URL_BICING).content))
    
    # Filter only heavy/fast rail lines
    rail_types = ["Ferrocarrils Generalitat (FGC)", "Metro i línies urbanes FGC", "RENFE"]
    rail_pts = df_rail[df_rail['NOM_CAPA'].isin(rail_types)][['LONGITUD', 'LATITUD']].values
    bicing_pts = df_bicing[['longitude', 'latitude']].values
    
    # 2. Get Neighborhood Centroids
    # If no GeoJSON logic, use average of existing transport points as a proxy for the 'center' of business in the barrio
    centroid_map = df_rail.groupby('BARRI').agg({'LONGITUD': 'mean', 'LATITUD': 'mean'})
    
    # 3. Calculate Distances
    results = []
    print("Calculating distances to nearest network nodes...")
    for barrio_id, row in centroid_map.iterrows():
        b_lon, b_lat = row['LONGITUD'], row['LATITUD']
        
        # Min distance to Rail
        dist_rail = min([haversine(b_lon, b_lat, p[0], p[1]) for p in rail_pts])
        
        # Min distance to Bicing
        dist_bicing = min([haversine(b_lon, b_lat, p[0], p[1]) for p in bicing_pts])
        
        # Bicing density in "neighborhood vicinity" (count within 500m)
        bicing_nearby = sum([1 for p in bicing_pts if haversine(b_lon, b_lat, p[0], p[1]) <= 500])
        
        # Interchange Hub Bonus
        # Count rail stations within 300m of the neighborhood center
        rail_hub_score = sum([1 for p in rail_pts if haversine(b_lon, b_lat, p[0], p[1]) <= 300])
        
        results.append({
            'barrio_id': int(barrio_id),
            'dist_to_nearest_rail': dist_rail,
            'dist_to_nearest_bicing': dist_bicing,
            'bicing_proximity_count': bicing_nearby,
            'rail_hub_proximity_score': rail_hub_score
        })
        
    df_geo = pd.DataFrame(results).set_index('barrio_id')
    
    # 4. Integrate with ML Dataset
    ML_DATA_PATH = Path('data/barcelona_ml_valuation.csv')
    if ML_DATA_PATH.exists():
        df_ml = pd.read_csv(ML_DATA_PATH)
        df_ml = df_ml.merge(df_geo, left_on='barrio_id', right_index=True, how='left')
        
        # Normalize and fill
        df_ml = df_ml.fillna(df_ml.mean(numeric_only=True))
        
        # Create a "Public Transport Premium" score (Inverse distance)
        # Closer is better (higher score)
        df_ml['transport_premium_index'] = (1000 / (df_ml['dist_to_nearest_rail'] + 100)) + (df_ml['bicing_proximity_count'] * 0.5)
        
        df_ml.to_csv(ML_DATA_PATH, index=False)
        print("✅ Refined accessibility integrated.bordere problem addressed with continuous proximity.")
        print(df_ml[['dist_to_nearest_rail', 'dist_to_nearest_bicing', 'transport_premium_index']].describe().loc[['mean', 'min', 'max']])

if __name__ == "__main__":
    refine_accessibility_v2()
