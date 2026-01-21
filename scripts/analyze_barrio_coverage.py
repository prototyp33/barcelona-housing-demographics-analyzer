#!/usr/bin/env python3
"""
Análisis de Cobertura de Barrios

Identifica qué tablas tienen baja cobertura y qué barrios faltan en cada una.
"""

import sys
from pathlib import Path
import sqlite3
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.database import DatabaseManager


def analyze_coverage():
    """Analiza la cobertura de barrios en todas las tablas fact."""
    db_manager = DatabaseManager()
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    # Get all fact tables
    cursor.execute("""
        SELECT name 
        FROM sqlite_master 
        WHERE type='table' 
        AND name LIKE 'fact_%'
        ORDER BY name
    """)
    fact_tables = [row[0] for row in cursor.fetchall()]
    
    # Get all 73 barrios
    cursor.execute("SELECT barrio_id, barrio_nombre FROM dim_barrios ORDER BY barrio_id")
    all_barrios = {row[0]: row[1] for row in cursor.fetchall()}
    
    print("=" * 100)
    print("ANÁLISIS DE COBERTURA DE BARRIOS")
    print("=" * 100)
    print()
    
    coverage_report = []
    
    for table in fact_tables:
        try:
            # Check if table has barrio_id column
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'barrio_id' not in columns:
                continue
            
            # Get unique barrios in this table
            cursor.execute(f"SELECT DISTINCT barrio_id FROM {table} WHERE barrio_id IS NOT NULL")
            barrios_in_table = set(row[0] for row in cursor.fetchall())
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            row_count = cursor.fetchone()[0]
            
            coverage_pct = (len(barrios_in_table) / 73) * 100
            missing_barrios = set(all_barrios.keys()) - barrios_in_table
            
            coverage_report.append({
                'table': table,
                'barrios_covered': len(barrios_in_table),
                'coverage_pct': coverage_pct,
                'missing_count': len(missing_barrios),
                'missing_barrios': missing_barrios,
                'row_count': row_count
            })
            
        except Exception as e:
            print(f"⚠️  Error analyzing {table}: {e}")
    
    # Sort by coverage percentage
    coverage_report.sort(key=lambda x: x['coverage_pct'])
    
    # Print summary
    print("📊 RESUMEN DE COBERTURA")
    print("-" * 100)
    print(f"{'Tabla':<35} {'Barrios':<12} {'Cobertura':<12} {'Registros':<12} {'Faltantes'}")
    print("-" * 100)
    
    low_coverage_tables = []
    
    for item in coverage_report:
        status = "✅" if item['coverage_pct'] == 100 else "⚠️" if item['coverage_pct'] >= 95 else "❌"
        
        print(f"{status} {item['table']:<32} {item['barrios_covered']}/73 ({item['coverage_pct']:>5.1f}%) "
              f"{item['row_count']:>10,}    {item['missing_count']} barrios")
        
        if item['coverage_pct'] < 100 and item['row_count'] > 0:
            low_coverage_tables.append(item)
    
    print()
    
    # Detailed analysis of low coverage tables
    if low_coverage_tables:
        print("=" * 100)
        print("📉 TABLAS CON COBERTURA INCOMPLETA (DETALLE)")
        print("=" * 100)
        print()
        
        for item in low_coverage_tables:
            print(f"🔍 {item['table']}")
            print(f"   Cobertura: {item['barrios_covered']}/73 ({item['coverage_pct']:.1f}%)")
            print(f"   Registros: {item['row_count']:,}")
            print(f"   Barrios faltantes ({item['missing_count']}):")
            
            # Show missing barrios
            missing_names = [all_barrios[bid] for bid in sorted(item['missing_barrios'])]
            for i, name in enumerate(missing_names, 1):
                print(f"      {i:2d}. {name}")
            print()
    
    # Calculate overall statistics
    total_coverage = sum(item['coverage_pct'] for item in coverage_report)
    avg_coverage = total_coverage / len(coverage_report) if coverage_report else 0
    
    tables_100 = sum(1 for item in coverage_report if item['coverage_pct'] == 100)
    tables_95_99 = sum(1 for item in coverage_report if 95 <= item['coverage_pct'] < 100)
    tables_below_95 = sum(1 for item in coverage_report if item['coverage_pct'] < 95)
    
    print("=" * 100)
    print("📈 ESTADÍSTICAS GENERALES")
    print("=" * 100)
    print(f"Cobertura Promedio: {avg_coverage:.1f}%")
    print(f"Tablas con 100% cobertura: {tables_100}")
    print(f"Tablas con 95-99% cobertura: {tables_95_99}")
    print(f"Tablas con <95% cobertura: {tables_below_95}")
    print()
    
    # Find barrios that are commonly missing
    barrio_missing_count = defaultdict(int)
    for item in low_coverage_tables:
        for barrio_id in item['missing_barrios']:
            barrio_missing_count[barrio_id] += 1
    
    if barrio_missing_count:
        print("=" * 100)
        print("🎯 BARRIOS MÁS FRECUENTEMENTE FALTANTES")
        print("=" * 100)
        print()
        
        sorted_missing = sorted(barrio_missing_count.items(), key=lambda x: x[1], reverse=True)
        
        print(f"{'Barrio':<40} {'Falta en N tablas':<20} {'% de tablas'}")
        print("-" * 100)
        
        for barrio_id, count in sorted_missing[:10]:  # Top 10
            barrio_name = all_barrios[barrio_id]
            pct = (count / len(low_coverage_tables)) * 100
            print(f"{barrio_name:<40} {count:<20} {pct:.1f}%")
        print()
    
    conn.close()
    
    return coverage_report


if __name__ == "__main__":
    analyze_coverage()
