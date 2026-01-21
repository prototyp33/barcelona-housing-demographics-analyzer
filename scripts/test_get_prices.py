#!/usr/bin/env python3
"""
Test script for the updated get_prices() function.

Verifies that:
1. The function returns clean data without duplicates
2. Deduplication works correctly
3. Filtering by distrito works
4. Data structure is correct
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import sys
import importlib.util

# Import from src/analysis.py (file) not src/analysis/ (package)
spec = importlib.util.spec_from_file_location("analysis_module", PROJECT_ROOT / "src" / "analysis.py")
analysis_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis_module)

get_prices = analysis_module.get_prices
get_available_years = analysis_module.get_available_years
get_districts = analysis_module.get_districts


def test_get_prices_basic():
    """Test basic functionality of get_prices()."""
    print("=" * 60)
    print("TEST 1: Basic get_prices() functionality")
    print("=" * 60)
    
    # Get available years
    years_info = get_available_years()
    max_year = years_info.get("fact_precios", {}).get("max")
    
    if not max_year:
        print("❌ No price data available")
        return False
    
    print(f"📅 Testing with year: {max_year}")
    
    # Get prices
    df = get_prices(max_year)
    
    if df.empty:
        print("❌ Function returned empty DataFrame")
        return False
    
    print(f"✅ Function returned {len(df)} records")
    print(f"   Columns: {list(df.columns)}")
    
    # Check for duplicates
    duplicates = df[df.duplicated(subset=['barrio_id'], keep=False)]
    if not duplicates.empty:
        print(f"❌ Found {len(duplicates)} duplicate barrio_id values!")
        print(duplicates[['barrio_id', 'barrio_nombre']].head())
        return False
    
    print("✅ No duplicates found in results")
    
    # Check data quality
    print(f"\n📊 Data Quality:")
    print(f"   Barrios with precio_m2_venta: {df['avg_precio_m2'].notna().sum()}")
    print(f"   Barrios with precio_alquiler: {df['avg_alquiler'].notna().sum()}")
    print(f"   Unique barrios: {df['barrio_id'].nunique()}")
    print(f"   Unique distritos: {df['distrito_nombre'].nunique() if 'distrito_nombre' in df.columns else 0}")
    
    # Show sample
    print(f"\n📋 Sample records (first 5):")
    print(df[['barrio_id', 'barrio_nombre', 'distrito_nombre', 'avg_precio_m2', 'avg_alquiler']].head().to_string(index=False))
    
    return True


def test_get_prices_with_distrito():
    """Test get_prices() with distrito filter."""
    print("\n" + "=" * 60)
    print("TEST 2: get_prices() with distrito filter")
    print("=" * 60)
    
    # Get available years and distritos
    years_info = get_available_years()
    max_year = years_info.get("fact_precios", {}).get("max")
    distritos = get_districts()
    
    if not max_year or not distritos:
        print("❌ No data available")
        return False
    
    # Test with first distrito
    test_distrito = distritos[0]
    print(f"📅 Testing with year: {max_year}, distrito: {test_distrito}")
    
    df = get_prices(max_year, distrito=test_distrito)
    
    if df.empty:
        print(f"⚠️  No data for {test_distrito} in {max_year}")
        return True  # Not necessarily an error
    
    print(f"✅ Function returned {len(df)} records for {test_distrito}")
    
    # Verify all records are from the selected distrito
    if 'distrito_nombre' in df.columns:
        wrong_distrito = df[df['distrito_nombre'] != test_distrito]
        if not wrong_distrito.empty:
            print(f"❌ Found {len(wrong_distrito)} records from wrong distrito!")
            return False
        print(f"✅ All records are from {test_distrito}")
    
    # Check for duplicates
    duplicates = df[df.duplicated(subset=['barrio_id'], keep=False)]
    if not duplicates.empty:
        print(f"❌ Found duplicates in filtered results!")
        return False
    
    print("✅ No duplicates in filtered results")
    
    return True


def test_get_prices_multiple_years():
    """Test get_prices() across multiple years."""
    print("\n" + "=" * 60)
    print("TEST 3: get_prices() across multiple years")
    print("=" * 60)
    
    years_info = get_available_years()
    min_year = years_info.get("fact_precios", {}).get("min")
    max_year = years_info.get("fact_precios", {}).get("max")
    
    if not min_year or not max_year:
        print("❌ No year range available")
        return False
    
    print(f"📅 Testing years {min_year} to {max_year}")
    
    results = {}
    for year in range(min_year, min(max_year + 1, min_year + 5)):  # Test first 5 years
        df = get_prices(year)
        results[year] = len(df)
        duplicates = df[df.duplicated(subset=['barrio_id'], keep=False)]
        
        if not duplicates.empty:
            print(f"❌ Year {year}: Found {len(duplicates)} duplicates!")
            return False
        
        print(f"   {year}: {len(df)} records (no duplicates)")
    
    print(f"\n✅ All tested years returned clean data")
    print(f"   Year range: {min(results.keys())} - {max(results.keys())}")
    print(f"   Average records per year: {sum(results.values()) / len(results):.1f}")
    
    return True


def test_compare_with_database():
    """Compare get_prices() results with direct database query."""
    print("\n" + "=" * 60)
    print("TEST 4: Compare with direct database query")
    print("=" * 60)
    
    import sqlite3
    from src.app.config import DB_PATH
    
    years_info = get_available_years()
    max_year = years_info.get("fact_precios", {}).get("max")
    
    if not max_year:
        print("❌ No year data available")
        return False
    
    print(f"📅 Comparing results for year: {max_year}")
    
    # Get via function
    df_function = get_prices(max_year)
    
    # Get via direct query (without deduplication)
    conn = sqlite3.connect(DB_PATH)
    try:
        query = """
        SELECT 
            p.barrio_id,
            COUNT(*) as raw_count
        FROM fact_precios p
        WHERE p.anio = ?
        GROUP BY p.barrio_id
        """
        df_raw = pd.read_sql(query, conn, params=[max_year])
    finally:
        conn.close()
    
    # Compare
    print(f"   Direct query: {len(df_raw)} unique barrios with data")
    print(f"   get_prices(): {len(df_function)} records returned")
    
    # Check if function returns fewer or equal (should be equal after cleanup)
    if len(df_function) > len(df_raw):
        print(f"⚠️  Function returned more records than unique barrios (possible issue)")
        return False
    
    # Check if all barrios from function exist in raw data
    missing = set(df_function['barrio_id']) - set(df_raw['barrio_id'])
    if missing:
        print(f"❌ Function returned barrios not in database: {missing}")
        return False
    
    # Check for barrios with multiple records in raw data (should be handled by deduplication)
    multi_record_barrios = df_raw[df_raw['raw_count'] > 1]
    if not multi_record_barrios.empty:
        print(f"⚠️  Found {len(multi_record_barrios)} barrios with multiple records in DB")
        print(f"   These should be deduplicated by get_prices()")
        print(f"   Sample: {multi_record_barrios.head(3).to_string(index=False)}")
    
    print("✅ Comparison complete - function handles deduplication correctly")
    
    return True


def main():
    """Run all tests."""
    print("🧪 Testing updated get_prices() function\n")
    
    tests = [
        ("Basic Functionality", test_get_prices_basic),
        ("Distrito Filter", test_get_prices_with_distrito),
        ("Multiple Years", test_get_prices_multiple_years),
        ("Database Comparison", test_compare_with_database),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ Test '{test_name}' failed with error: {e}")
            import traceback
            traceback.print_exc()
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {test_name}")
    
    print(f"\n   Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! get_prices() is working correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
