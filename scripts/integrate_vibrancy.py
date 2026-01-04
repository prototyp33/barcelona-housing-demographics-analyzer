
import pandas as pd
import glob
from pathlib import Path

def integrate_vibrancy():
    print("✨ Integrating Vibrancy/Safety Features (Phase 2.3)...")
    
    # 1. Load Business Census Data
    biz_files = glob.glob('data/raw/opendatabcn/opendatabcn_cens-locals-planta-baixa-act-economica_*.csv')
    if not biz_files:
        print("❌ Business census data not found.")
        return
    
    biz_file = biz_files[0]
    print(f"Reading business data from {biz_file}...")
    df_biz = pd.read_csv(biz_file, low_memory=False)
    
    # 2. Filter for "Vibrant" businesses
    vibrant_groups = [
        'Restaurants, bars i hotels (Inclòs hostals, pensions i fondes)',
        'Oci i cultura',
        'Equipament personal',
        'Quotidià alimentari',
        'Equipaments culturals i recreatius'
    ]
    
    df_vibrant = df_biz[df_biz['Nom_Grup_Activitat'].isin(vibrant_groups)]
    
    # 3. Aggregate by Neighborhood
    vibrant_counts = df_vibrant.groupby('Codi_Barri').size().rename('vibrant_biz_count')
    total_biz = df_biz.groupby('Codi_Barri').size().rename('total_biz_count')
    
    # 4. Load Area Data (already downloaded in previous step)
    area_files = glob.glob('data/raw/opendatabcn/opendatabcn_est-superficie_*.csv')
    area_file = area_files[0]
    df_area = pd.read_csv(area_file)
    latest_year = df_area['Any'].max()
    df_area = df_area[df_area['Any'] == latest_year]
    area_map = df_area.set_index('Codi_Barri')['Superfície (ha)'].to_dict()
    
    # 5. Calculate Metrics
    biz_metrics = pd.DataFrame(vibrant_counts)
    biz_metrics['total_biz_count'] = total_biz
    biz_metrics['area_ha'] = biz_metrics.index.map(area_map)
    
    biz_metrics['vibrancy_biz_density'] = biz_metrics['vibrant_biz_count'] / biz_metrics['area_ha']
    biz_metrics['biz_occupancy_index'] = biz_metrics['vibrant_biz_count'] / biz_metrics['total_biz_count']
    
    # 6. Integrate with ML Dataset
    ML_DATA_PATH = Path('data/barcelona_ml_valuation.csv')
    if ML_DATA_PATH.exists():
        df_ml = pd.read_csv(ML_DATA_PATH)
        
        df_ml = df_ml.merge(biz_metrics[['vibrancy_biz_density', 'biz_occupancy_index']], 
                          left_on='barrio_id', right_index=True, how='left')
        
        # Fill missing
        df_ml['vibrancy_biz_density'] = df_ml['vibrancy_biz_density'].fillna(0)
        df_ml['biz_occupancy_index'] = df_ml['biz_occupancy_index'].fillna(0)
        
        # Qualitative Safety Perspective Score
        # Combination of high occupancy (fewer shuttered shops) and high density
        max_density = df_ml['vibrancy_biz_density'].max()
        if max_density > 0:
            df_ml['safety_vibrancy_score'] = (
                (df_ml['vibrancy_biz_density'] / max_density * 0.7) + 
                (df_ml['biz_occupancy_index'] * 0.3)
            )
        else:
            df_ml['safety_vibrancy_score'] = 0
            
        df_ml.to_csv(ML_DATA_PATH, index=False)
        print(f"✅ Success! Integrated vibrancy features for {len(df_ml)} neighborhoods.")
        print("\nFeatures added:")
        print(df_ml[['vibrancy_biz_density', 'biz_occupancy_index', 'safety_vibrancy_score']].describe().loc[['mean', 'max']])

if __name__ == "__main__":
    integrate_vibrancy()
