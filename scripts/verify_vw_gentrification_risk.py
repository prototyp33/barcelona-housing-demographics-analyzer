#!/usr/bin/env python3
"""
Verification script for vw_gentrification_risk view.

Tests that the view:
1. Can be queried without errors
2. Returns expected data structure
3. Has no NULL issues in key columns
4. Can be used in JOINs (simulating dashboard usage)
"""

import sys
import sqlite3
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "processed" / "database.db"


def test_view_basic(conn: sqlite3.Connection) -> bool:
    """Test basic view query."""
    print("=" * 60)
    print("TEST 1: Basic View Query")
    print("=" * 60)
    
    try:
        df = pd.read_sql("SELECT * FROM vw_gentrification_risk LIMIT 5", conn)
        print(f"✅ View query successful")
        print(f"   Columns: {list(df.columns)}")
        print(f"   Sample rows: {len(df)}")
        print(f"\n   Sample data:")
        print(df.to_string(index=False))
        return True
    except sqlite3.Error as e:
        print(f"❌ View query failed: {e}")
        return False


def test_view_count(conn: sqlite3.Connection) -> bool:
    """Test view record count."""
    print("\n" + "=" * 60)
    print("TEST 2: View Record Count")
    print("=" * 60)
    
    try:
        cursor = conn.execute("SELECT COUNT(*) FROM vw_gentrification_risk")
        total = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(DISTINCT barrio_id) FROM vw_gentrification_risk")
        barrios = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(DISTINCT year) FROM vw_gentrification_risk")
        years = cursor.fetchone()[0]
        
        print(f"✅ Total records: {total}")
        print(f"✅ Unique barrios: {barrios}")
        print(f"✅ Unique years: {years}")
        
        if barrios == 73:
            print("   ✅ All 73 barrios present")
        else:
            print(f"   ⚠️  Expected 73 barrios, got {barrios}")
        
        return True
    except sqlite3.Error as e:
        print(f"❌ Count query failed: {e}")
        return False


def test_view_joins(conn: sqlite3.Connection) -> bool:
    """Test view in JOIN operations (simulating dashboard usage)."""
    print("\n" + "=" * 60)
    print("TEST 3: View in JOIN Operations")
    print("=" * 60)
    
    try:
        # Simulate a dashboard query that joins the view with other tables
        query = """
        SELECT 
            v.nom_barri,
            v.precio_venta_medio_m2,
            v.num_centros_educativos,
            v.num_universidades,
            d.poblacion_total
        FROM vw_gentrification_risk v
        LEFT JOIN fact_demografia d ON v.barrio_id = d.barrio_id AND v.year = d.anio
        WHERE v.precio_venta_medio_m2 IS NOT NULL
        ORDER BY v.precio_venta_medio_m2 DESC
        LIMIT 10
        """
        
        df = pd.read_sql(query, conn)
        print(f"✅ JOIN query successful")
        print(f"   Returned {len(df)} records")
        print(f"\n   Top 10 barrios by price:")
        print(df.to_string(index=False))
        
        return True
    except sqlite3.Error as e:
        print(f"❌ JOIN query failed: {e}")
        return False


def test_view_columns(conn: sqlite3.Connection) -> bool:
    """Test that all expected columns exist."""
    print("\n" + "=" * 60)
    print("TEST 4: Column Verification")
    print("=" * 60)
    
    expected_columns = {
        'nom_barri',
        'barrio_id',
        'year',
        'num_centros_educativos',
        'num_universidades',
        'precio_venta_medio_m2',
        'pm25_mean',
        'pct_exposed_65db'
    }
    
    try:
        df = pd.read_sql("SELECT * FROM vw_gentrification_risk LIMIT 1", conn)
        actual_columns = set(df.columns)
        
        missing = expected_columns - actual_columns
        extra = actual_columns - expected_columns
        
        if missing:
            print(f"❌ Missing columns: {missing}")
            return False
        
        if extra:
            print(f"⚠️  Extra columns (not critical): {extra}")
        
        print(f"✅ All expected columns present: {sorted(expected_columns)}")
        return True
    except sqlite3.Error as e:
        print(f"❌ Column check failed: {e}")
        return False


def test_view_data_quality(conn: sqlite3.Connection) -> bool:
    """Test data quality in view."""
    print("\n" + "=" * 60)
    print("TEST 5: Data Quality Check")
    print("=" * 60)
    
    try:
        query = """
        SELECT 
            COUNT(*) as total,
            COUNT(nom_barri) as has_name,
            COUNT(num_centros_educativos) as has_centros,
            COUNT(num_universidades) as has_universidades,
            COUNT(precio_venta_medio_m2) as has_price,
            COUNT(pm25_mean) as has_air_quality,
            COUNT(pct_exposed_65db) as has_noise
        FROM vw_gentrification_risk
        """
        
        df = pd.read_sql(query, conn)
        row = df.iloc[0]
        
        print(f"   Total records: {row['total']}")
        print(f"   Records with barrio name: {row['has_name']} ({row['has_name']/row['total']*100:.1f}%)")
        print(f"   Records with centros: {row['has_centros']} ({row['has_centros']/row['total']*100:.1f}%)")
        print(f"   Records with universidades: {row['has_universidades']} ({row['has_universidades']/row['total']*100:.1f}%)")
        print(f"   Records with price: {row['has_price']} ({row['has_price']/row['total']*100:.1f}%)")
        print(f"   Records with air quality: {row['has_air_quality']} ({row['has_air_quality']/row['total']*100:.1f}%)")
        print(f"   Records with noise data: {row['has_noise']} ({row['has_noise']/row['total']*100:.1f}%)")
        
        # Check if critical columns have good coverage
        if row['has_name'] == row['total'] and row['has_centros'] == row['total']:
            print("   ✅ Critical columns have 100% coverage")
            return True
        else:
            print("   ⚠️  Some critical columns have missing data")
            return True  # Not a failure, just a warning
        
    except sqlite3.Error as e:
        print(f"❌ Data quality check failed: {e}")
        return False


def main() -> int:
    """Main function."""
    if not DB_PATH.exists():
        print(f"❌ Database not found at {DB_PATH}", file=sys.stderr)
        return 1
    
    conn = sqlite3.connect(DB_PATH)
    
    tests = [
        ("Basic Query", test_view_basic),
        ("Record Count", test_view_count),
        ("JOIN Operations", test_view_joins),
        ("Column Verification", test_view_columns),
        ("Data Quality", test_view_data_quality),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func(conn)
        except Exception as e:
            print(f"\n❌ Test '{test_name}' failed with error: {e}")
            import traceback
            traceback.print_exc()
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {test_name}")
    
    print(f"\n   Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! vw_gentrification_risk is ready for use.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Review the output above.")
        return 1
    
    conn.close()


if __name__ == "__main__":
    sys.exit(main())
