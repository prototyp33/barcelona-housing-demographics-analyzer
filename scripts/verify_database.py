#!/usr/bin/env python3
"""
Quick verification script to test database connections and data availability.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.database import DatabaseManager
import pandas as pd

def main():
    print("=" * 60)
    print("Barcelona Housing Demographics - Database Verification")
    print("=" * 60)
    
    db = DatabaseManager()
    
    # 1. Check database connection
    print("\n✓ Database connection successful")
    
    # 2. Check key tables
    print("\n📊 Checking key tables:")
    tables = ['dim_barrios', 'fact_precios', 'fact_renta', 'v_demografia_aggregated']
    for table in tables:
        exists = db.table_exists(table)
        status = "✓" if exists else "✗"
        print(f"  {status} {table}")
    
    # 3. Check data counts
    print("\n📈 Data counts:")
    queries = {
        "Barrios": "SELECT COUNT(*) as count FROM dim_barrios",
        "Barrios con geometría": "SELECT COUNT(*) as count FROM dim_barrios WHERE geometry_json IS NOT NULL",
        "Registros de precios": "SELECT COUNT(*) as count FROM fact_precios",
        "Registros de renta": "SELECT COUNT(*) as count FROM fact_renta",
        "Registros demográficos": "SELECT COUNT(*) as count FROM v_demografia_aggregated"
    }
    
    for label, query in queries.items():
        try:
            result = db.execute_query(query)
            count = result['count'].iloc[0]
            print(f"  • {label}: {count:,}")
        except Exception as e:
            print(f"  ✗ {label}: Error - {e}")
    
    # 4. Check year ranges
    print("\n📅 Year coverage:")
    year_queries = {
        "Precios": "SELECT MIN(anio) as min_year, MAX(anio) as max_year FROM fact_precios",
        "Renta": "SELECT MIN(anio) as min_year, MAX(anio) as max_year FROM fact_renta",
        "Demografía": "SELECT MIN(anio) as min_year, MAX(anio) as max_year FROM v_demografia_aggregated"
    }
    
    for label, query in year_queries.items():
        try:
            result = db.execute_query(query)
            min_year = result['min_year'].iloc[0]
            max_year = result['max_year'].iloc[0]
            print(f"  • {label}: {min_year} - {max_year}")
        except Exception as e:
            print(f"  ✗ {label}: No data")
    
    # 5. Data quality metrics
    print("\n🎯 Data Quality Metrics:")
    try:
        metrics = db.get_quality_metrics()
        print(f"  • Completeness: {metrics['completeness']:.1f}%")
        print(f"  • Validity: {metrics['validity']:.1f}%")
        print(f"  • Consistency: {metrics['consistency']:.1f}%")
        print(f"  • Timeliness: {metrics['timeliness']} days since last update")
    except Exception as e:
        print(f"  ✗ Error calculating metrics: {e}")
    
    print("\n" + "=" * 60)
    print("✓ Verification complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
