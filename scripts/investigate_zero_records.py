#!/usr/bin/env python3
"""
Investigation Script: Zero Records in fact_calidad_aire and fact_turismo_intensidad

Diagnoses why these tables have 0 records and identifies the root cause.
"""

import sys
import sqlite3
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data/processed/database.db"
RAW_DIR = PROJECT_ROOT / "data/raw"


def check_table_records(conn: sqlite3.Connection, table: str) -> Dict:
    """Check record count and structure of a table."""
    try:
        count = pd.read_sql(f"SELECT COUNT(*) as n FROM {table}", conn)["n"].iloc[0]
        if count > 0:
            sample = pd.read_sql(f"SELECT * FROM {table} LIMIT 5", conn)
            columns = list(sample.columns)
        else:
            # Get structure even if empty
            cursor = conn.execute(f"PRAGMA table_info({table})")
            columns = [row[1] for row in cursor.fetchall()]
            sample = pd.DataFrame()
        
        return {
            "exists": True,
            "count": int(count),
            "columns": columns,
            "sample": sample
        }
    except sqlite3.Error as e:
        return {
            "exists": False,
            "error": str(e),
            "count": 0,
            "columns": []
        }


def check_raw_files(pattern: str, dataset_id: Optional[str] = None) -> List[Path]:
    """Find raw data files matching pattern or dataset ID."""
    files = []
    
    # Search in opendatabcn directory
    opendata_dir = RAW_DIR / "opendatabcn"
    if opendata_dir.exists():
        if dataset_id:
            files.extend(opendata_dir.glob(f"*{dataset_id}*"))
        if pattern:
            files.extend(opendata_dir.glob(f"*{pattern}*"))
    
    # Search in portaldades directory
    portaldades_dir = RAW_DIR / "portaldades"
    if portaldades_dir.exists():
        if dataset_id:
            files.extend(portaldades_dir.glob(f"*{dataset_id}*"))
        if pattern:
            files.extend(portaldades_dir.glob(f"*{pattern}*"))
    
    # Search in calidad_aire directory
    calidad_dir = RAW_DIR / "calidad_aire"
    if calidad_dir.exists():
        files.extend(calidad_dir.glob("*"))
    
    return sorted(set(files), key=lambda p: p.stat().st_mtime, reverse=True)


def check_manifest(raw_dir: Path) -> Dict:
    """Check manifest.json for registered datasets."""
    manifest_path = raw_dir / "manifest.json"
    if not manifest_path.exists():
        return {"exists": False, "entries": []}
    
    import json
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        return {"exists": True, "entries": manifest}
    except Exception as e:
        return {"exists": True, "error": str(e), "entries": []}


def investigate_air_quality(conn: sqlite3.Connection) -> Dict:
    """Investigate why fact_calidad_aire has 0 records."""
    print("=" * 60)
    print("🔍 INVESTIGATING: fact_calidad_aire (0 records)")
    print("=" * 60)
    
    result = {
        "table_status": check_table_records(conn, "fact_calidad_aire"),
        "raw_files": [],
        "processing_script": None,
        "etl_integration": False,
    }
    
    # Check table
    print(f"\n📊 Table Status:")
    print(f"   Records: {result['table_status']['count']}")
    print(f"   Columns: {result['table_status']['columns']}")
    
    # Check raw files
    print(f"\n📁 Raw Files Search:")
    air_files = check_raw_files("calidad", "aire") + check_raw_files("air", "quality")
    result["raw_files"] = [str(f) for f in air_files]
    
    if air_files:
        print(f"   ✅ Found {len(air_files)} file(s):")
        for f in air_files[:5]:
            size = f.stat().st_size / 1024  # KB
            print(f"      - {f.name} ({size:.1f} KB)")
            
            # Check file content
            try:
                df_sample = pd.read_csv(f, nrows=3)
                print(f"         Columns: {list(df_sample.columns)[:5]}")
                print(f"         Rows (sample): {len(df_sample)}")
            except Exception as e:
                print(f"         ⚠️  Error reading: {e}")
    else:
        print(f"   ❌ No raw files found")
    
    # Check for processing script
    processing_script = PROJECT_ROOT / "src" / "processing" / "prepare_calidad_aire.py"
    if processing_script.exists():
        result["processing_script"] = str(processing_script)
        print(f"\n✅ Processing script exists: {processing_script.name}")
    else:
        print(f"\n❌ No processing script found: prepare_calidad_aire.py")
        print(f"   Expected location: src/processing/prepare_calidad_aire.py")
    
    # Check ETL integration
    pipeline_file = PROJECT_ROOT / "src" / "etl" / "pipeline.py"
    if pipeline_file.exists():
        content = pipeline_file.read_text()
        if "calidad_aire" in content.lower() or "air_quality" in content.lower():
            result["etl_integration"] = True
            print(f"\n✅ ETL pipeline references air quality")
        else:
            print(f"\n❌ ETL pipeline does NOT process air quality")
            print(f"   Air quality processing is missing from pipeline.py")
    
    return result


def investigate_tourism(conn: sqlite3.Connection) -> Dict:
    """Investigate why fact_turismo_intensidad has 0 records."""
    print("\n" + "=" * 60)
    print("🔍 INVESTIGATING: fact_turismo_intensidad (0 records)")
    print("=" * 60)
    
    result = {
        "table_status": check_table_records(conn, "fact_turismo_intensidad"),
        "raw_files": [],
        "manifest_entries": [],
        "dataset_ids": {},
    }
    
    # Check table
    print(f"\n📊 Table Status:")
    print(f"   Records: {result['table_status']['count']}")
    print(f"   Columns: {result['table_status']['columns']}")
    
    # Check expected dataset IDs from opendata.py (read file directly)
    opendata_path = PROJECT_ROOT / "src" / "extraction" / "opendata.py"
    expected_datasets = {
        "tourism_intensity": "intensitat-activitat-turistica",  # Default from code
        "tourism_hut": "habitatges-us-turistic",  # Default from code
    }
    
    # Try to extract actual values from file
    if opendata_path.exists():
        content = opendata_path.read_text()
        import re
        # Look for DATASETS dictionary
        match = re.search(r'"tourism_intensity":\s*"([^"]+)"', content)
        if match:
            expected_datasets["tourism_intensity"] = match.group(1)
        match = re.search(r'"tourism_hut":\s*"([^"]+)"', content)
        if match:
            expected_datasets["tourism_hut"] = match.group(1)
    
    result["dataset_ids"] = expected_datasets
    print(f"\n📋 Expected Dataset IDs:")
    for key, dataset_id in expected_datasets.items():
        status = "✅" if dataset_id else "❌"
        print(f"   {status} {key}: {dataset_id}")
    
    # Check raw files
    print(f"\n📁 Raw Files Search:")
    tourism_files = []
    for key, dataset_id in expected_datasets.items():
        if dataset_id:
            files = check_raw_files(None, dataset_id)
            tourism_files.extend(files)
            if files:
                print(f"   ✅ Found files for {key} ({dataset_id}):")
                for f in files[:3]:
                    size = f.stat().st_size / 1024
                    print(f"      - {f.name} ({size:.1f} KB)")
            else:
                print(f"   ❌ No files found for {key} (dataset_id: {dataset_id})")
    
    # Also search by name patterns
    name_patterns = ["turismo", "tourism", "hut", "intensitat"]
    for pattern in name_patterns:
        files = check_raw_files(pattern)
        if files:
            print(f"   📁 Files matching '{pattern}':")
            for f in files[:3]:
                print(f"      - {f.name}")
    
    result["raw_files"] = [str(f) for f in tourism_files]
    
    # Check manifest
    print(f"\n📋 Manifest Check:")
    manifest = check_manifest(RAW_DIR)
    if manifest["exists"]:
        entries = manifest.get("entries", [])
        tourism_entries = [
            e for e in entries 
            if any(kw in e.get("type", "").lower() for kw in ["tourism", "turismo", "hut"])
        ]
        result["manifest_entries"] = tourism_entries
        
        if tourism_entries:
            print(f"   ✅ Found {len(tourism_entries)} tourism-related entries in manifest")
            for e in tourism_entries[:3]:
                print(f"      - {e.get('type')}: {e.get('file_path', 'N/A')}")
        else:
            print(f"   ⚠️  No tourism entries in manifest")
    else:
        print(f"   ⚠️  Manifest.json not found")
    
    # Check processing function exists
    processing_file = PROJECT_ROOT / "src" / "etl" / "transformations" / "advanced_analysis.py"
    if processing_file.exists():
        content = processing_file.read_text()
        if "prepare_fact_turismo_intensidad" in content:
            print(f"\n✅ Processing function exists: prepare_fact_turismo_intensidad")
        else:
            print(f"\n❌ Processing function NOT found")
    else:
        print(f"\n❌ Processing file NOT found")
    
    return result


def check_etl_pipeline_integration() -> Dict:
    """Check if air quality and tourism are integrated in ETL pipeline."""
    print("\n" + "=" * 60)
    print("🔍 CHECKING: ETL Pipeline Integration")
    print("=" * 60)
    
    pipeline_file = PROJECT_ROOT / "src" / "etl" / "pipeline.py"
    content = pipeline_file.read_text()
    
    result = {
        "air_quality_processed": False,
        "tourism_processed": False,
        "air_quality_loaded": False,
        "tourism_loaded": False,
    }
    
    # Check for air quality processing
    if "calidad_aire" in content.lower() or "air_quality" in content.lower():
        result["air_quality_processed"] = True
        print("   ✅ Air quality processing found in pipeline")
    else:
        print("   ❌ Air quality processing NOT found in pipeline")
    
    # Check for tourism processing
    if "turismo_intensidad" in content.lower() or "tourism_intensity" in content.lower():
        result["tourism_processed"] = True
        print("   ✅ Tourism processing found in pipeline")
    else:
        print("   ❌ Tourism processing NOT found in pipeline")
    
    # Check for table loading
    if "fact_calidad_aire" in content:
        result["air_quality_loaded"] = True
        print("   ✅ fact_calidad_aire loading found")
    else:
        print("   ❌ fact_calidad_aire loading NOT found")
    
    if "fact_turismo_intensidad" in content:
        result["tourism_loaded"] = True
        print("   ✅ fact_turismo_intensidad loading found")
    else:
        print("   ❌ fact_turismo_intensidad loading NOT found")
    
    return result


def generate_recommendations(results: Dict) -> List[str]:
    """Generate actionable recommendations based on investigation."""
    recommendations = []
    
    # Air quality recommendations
    air_result = results["air_quality"]
    if not air_result["processing_script"]:
        recommendations.append(
            "🔧 Create src/processing/prepare_calidad_aire.py to process air quality raster data"
        )
    if not air_result["etl_integration"]:
        recommendations.append(
            "🔧 Integrate air quality processing into src/etl/pipeline.py"
        )
    if air_result["raw_files"]:
        recommendations.append(
            f"📊 Process existing raw file: {Path(air_result['raw_files'][0]).name}"
        )
    else:
        recommendations.append(
            "📥 Extract air quality data from OpenData BCN API"
        )
    
    # Tourism recommendations
    tourism_result = results["tourism"]
    if not tourism_result["raw_files"]:
        recommendations.append(
            "📥 Extract tourism data using OpenDataBCNExtractor for datasets: "
            f"{tourism_result['dataset_ids']}"
        )
    if not tourism_result["manifest_entries"]:
        recommendations.append(
            "📋 Run extraction script to register tourism datasets in manifest.json"
        )
    
    return recommendations


def main() -> int:
    """Main investigation function."""
    if not DB_PATH.exists():
        print(f"❌ Database not found at {DB_PATH}", file=sys.stderr)
        return 1
    
    conn = sqlite3.connect(DB_PATH)
    
    try:
        results = {
            "air_quality": investigate_air_quality(conn),
            "tourism": investigate_tourism(conn),
            "etl_integration": check_etl_pipeline_integration(),
        }
        
        # Generate recommendations
        print("\n" + "=" * 60)
        print("💡 RECOMMENDATIONS")
        print("=" * 60)
        recommendations = generate_recommendations(results)
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 INVESTIGATION SUMMARY")
        print("=" * 60)
        print(f"Air Quality:")
        print(f"   Table records: {results['air_quality']['table_status']['count']}")
        print(f"   Raw files found: {len(results['air_quality']['raw_files'])}")
        print(f"   Processing script: {'✅' if results['air_quality']['processing_script'] else '❌'}")
        print(f"   ETL integration: {'✅' if results['air_quality']['etl_integration'] else '❌'}")
        
        print(f"\nTourism:")
        print(f"   Table records: {results['tourism']['table_status']['count']}")
        print(f"   Raw files found: {len(results['tourism']['raw_files'])}")
        print(f"   Manifest entries: {len(results['tourism']['manifest_entries'])}")
        
    finally:
        conn.close()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
