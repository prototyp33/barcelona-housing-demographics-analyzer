
import pandas as pd
import glob
import os
from pathlib import Path

def integrate_environmental():
    print("🌳 Integrating Environmental Features (Phase 2.2)...")
    
    # 1. Load Tree Data
    tree_files = glob.glob('data/raw/opendatabcn/opendatabcn_arbrat-zona_*.csv')
    if not tree_files:
        print("❌ Tree data not found in data/raw/opendatabcn/")
        return
    
    tree_file = tree_files[0]
    print(f"Reading tree data from {tree_file}...")
    df_trees = pd.read_csv(tree_file)
    
    # Count trees per neighborhood
    # Note: codi_barri in tree data is float, 48.0 etc.
    tree_counts = df_trees.groupby('codi_barri').size().rename('tree_count')
    
    # 2. Load Neighborhood Area Data
    area_files = glob.glob('data/raw/opendatabcn/opendatabcn_est-superficie_*.csv')
    if not area_files:
        print("❌ Area data (est-superficie) not found.")
        return
        
    area_file = area_files[0]
    print(f"Reading area data from {area_file}...")
    df_area = pd.read_csv(area_file)
    
    # Use most recent year if multiple
    latest_year = df_area['Any'].max()
    df_area = df_area[df_area['Any'] == latest_year]
    
    # Map area to codi_barri
    area_map = df_area.set_index('Codi_Barri')['Superfície (ha)'].to_dict()
    
    # 3. Calculate Density
    env_metrics = pd.DataFrame(tree_counts)
    env_metrics['area_ha'] = env_metrics.index.map(area_map)
    env_metrics['tree_density'] = env_metrics['tree_count'] / env_metrics['area_ha']
    
    # Handle missing area or infinity
    env_metrics['tree_density'] = env_metrics['tree_density'].replace([float('inf'), -float('inf')], 0).fillna(0)
    
    # 4. Integrate with ML Dataset
    ML_DATA_PATH = Path('data/barcelona_ml_valuation.csv')
    if ML_DATA_PATH.exists():
        df_ml = pd.read_csv(ML_DATA_PATH)
        
        # Merge on barrio_id (ML) = index (env_metrics which is codi_barri)
        df_ml = df_ml.merge(env_metrics[['tree_count', 'tree_density']], left_on='barrio_id', right_index=True, how='left')
        
        # Fill missing with 0
        df_ml['tree_count'] = df_ml['tree_count'].fillna(0)
        df_ml['tree_density'] = df_ml['tree_density'].fillna(0)
        
        # Add a qualitative "Green Score" (normalized density 0-1)
        max_density = df_ml['tree_density'].max()
        if max_density > 0:
            df_ml['green_score'] = df_ml['tree_density'] / max_density
        else:
            df_ml['green_score'] = 0
            
        df_ml.to_csv(ML_DATA_PATH, index=False)
        print(f"✅ Success! Integrated environmental features for {len(df_ml)} neighborhoods.")
        print("\nFeatures added:")
        print(df_ml[['tree_count', 'tree_density', 'green_score']].describe().loc[['mean', 'max']])

if __name__ == "__main__":
    integrate_environmental()
