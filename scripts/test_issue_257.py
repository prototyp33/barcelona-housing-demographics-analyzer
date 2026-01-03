
from src.extraction.tmb import TMBExtractor
from src.extraction.osm import OSMExtractor
import pandas as pd

def test_ingestion():
    print("🧪 Testing Issue #257: TMB/OSM Ingestion...")
    
    # 1. TMB GTFS
    tmb = TMBExtractor()
    results, meta_tmb = tmb.extract_all()
    if results:
        print(f"✅ TMB/BCN Transit: Successfully loaded data.")
        for key, df in results.items():
            print(f"   - {key}: {len(df)} records.")
            print(f"     Columns: {df.columns.tolist()[:5]}...")
    else:
        print(f"❌ TMB Transit Failed")

    # 2. OSM Overpass
    osm = OSMExtractor()
    # Query for pharmacies as a small sample
    df_osm, meta_osm = osm.query_amenities(["pharmacy"])
    if df_osm is not None:
        print(f"✅ OSM Overpass: Successfully loaded {len(df_osm)} pharmacies.")
        print(df_osm[['name', 'lat', 'lon']].head())
    else:
        print(f"❌ OSM Overpass Failed: {meta_osm.get('error')}")

if __name__ == "__main__":
    test_ingestion()
