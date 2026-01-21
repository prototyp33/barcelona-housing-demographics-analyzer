#!/usr/bin/env python3
"""
Test script for air quality processing.

Tests that prepare_calidad_aire can process the existing raw file.
"""

import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import sqlite3

# Import with path handling
import importlib.util
processing_path = PROJECT_ROOT / "src" / "processing" / "prepare_calidad_aire.py"
spec = importlib.util.spec_from_file_location("prepare_calidad_aire", processing_path)
prepare_calidad_aire_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare_calidad_aire_module)
prepare_calidad_aire = prepare_calidad_aire_module.prepare_calidad_aire


def test_air_quality_processing():
    """Test air quality processing with existing raw file."""
    print("=" * 60)
    print("🧪 Testing Air Quality Processing")
    print("=" * 60)
    
    # Load barrios from database
    db_path = PROJECT_ROOT / "data" / "processed" / "database.db"
    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    try:
        barrios_df = pd.read_sql(
            "SELECT barrio_id, barrio_nombre_normalizado, geometry_json FROM dim_barrios",
            conn
        )
        print(f"✅ Loaded {len(barrios_df)} barrios from database")
    finally:
        conn.close()
    
    if barrios_df.empty:
        print("❌ No barrios found in database")
        return False
    
    # Check geometry coverage
    barrios_with_geom = barrios_df[barrios_df['geometry_json'].notna()]
    print(f"   Barrios with geometry: {len(barrios_with_geom)}/{len(barrios_df)}")
    
    if len(barrios_with_geom) == 0:
        print("❌ No barrios have geometry_json. Cannot process spatial data.")
        return False
    
    # Test processing
    raw_data_path = PROJECT_ROOT / "data" / "raw"
    print(f"\n📁 Processing from: {raw_data_path}")
    
    try:
        fact_calidad_aire = prepare_calidad_aire(
            raw_data_path=raw_data_path,
            barrios_df=barrios_df,
            reference_time=datetime.utcnow(),
        )
        
        if fact_calidad_aire.empty:
            print("❌ Processing returned empty DataFrame")
            return False
        
        print(f"\n✅ Processing successful!")
        print(f"   Records: {len(fact_calidad_aire)}")
        print(f"   Columns: {list(fact_calidad_aire.columns)}")
        print(f"   Barrios with data: {fact_calidad_aire['barrio_id'].nunique()}")
        
        # Check data quality
        print(f"\n📊 Data Quality:")
        print(f"   Records with no2_mean: {fact_calidad_aire['no2_mean'].notna().sum()}")
        print(f"   Records with pm25_mean: {fact_calidad_aire['pm25_mean'].notna().sum()}")
        
        # Show sample
        print(f"\n📋 Sample records:")
        sample = fact_calidad_aire.head(5)
        print(sample[['barrio_id', 'anio', 'no2_mean', 'pm25_mean']].to_string(index=False))
        
        return True
        
    except Exception as e:
        print(f"\n❌ Processing failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_air_quality_processing()
    sys.exit(0 if success else 1)
