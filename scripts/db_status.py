#!/usr/bin/env python3
"""
Quick Database Status - Barcelona Housing Demographics Analyzer

Muestra un resumen rápido del estado de todas las tablas.
"""

import sys
from pathlib import Path
import sqlite3

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.database import DatabaseManager

def main():
    """Función principal."""
    print("=" * 90)
    print("DATABASE STATUS - Barcelona Housing Demographics")
    print("=" * 90)
    print()
    
    db = DatabaseManager()
    conn = db.get_connection()
    
    try:
        cursor = conn.cursor()
        
        # Obtener todas las tablas fact_
        cursor.execute("""
            SELECT name 
            FROM sqlite_master 
            WHERE type='table' 
            AND name LIKE 'fact_%'
            ORDER BY name
        """)
        fact_tables = [row[0] for row in cursor.fetchall()]
        
        # Obtener dim_barrios
        cursor.execute("""
            SELECT name 
            FROM sqlite_master 
            WHERE type='table' 
            AND name LIKE 'dim_%'
            ORDER BY name
        """)
        dim_tables = [row[0] for row in cursor.fetchall()]
        
        # Obtener vistas
        cursor.execute("""
            SELECT name 
            FROM sqlite_master 
            WHERE type='view'
            ORDER BY name
        """)
        views = [row[0] for row in cursor.fetchall()]
        
        print(f"📊 RESUMEN GENERAL")
        print("-" * 90)
        print(f"  Tablas dimensión: {len(dim_tables)}")
        print(f"  Tablas de hechos: {len(fact_tables)}")
        print(f"  Vistas: {len(views)}")
        print()
        
        # Dimensiones
        print("=" * 90)
        print("📍 TABLAS DIMENSIÓN")
        print("=" * 90)
        print()
        print(f"{'Tabla':<40} {'Registros':>15} {'Geometrías':>15}")
        print("-" * 90)
        
        for table in dim_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            
            # Verificar geometrías
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE geometry_json IS NOT NULL")
                geom_count = cursor.fetchone()[0]
                geom_str = f"{geom_count}/{count}"
            except:
                geom_str = "N/A"
            
            print(f"{table:<40} {count:>15,} {geom_str:>15}")
        
        print()
        
        # Fact tables
        print("=" * 90)
        print("📈 TABLAS DE HECHOS")
        print("=" * 90)
        print()
        print(f"{'Tabla':<40} {'Registros':>12} {'Años':>15} {'Cobertura':>15}")
        print("-" * 90)
        
        for table in fact_tables:
            # Contar registros
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            
            # Rango de años
            try:
                cursor.execute(f"SELECT MIN(anio), MAX(anio) FROM {table} WHERE anio IS NOT NULL")
                min_year, max_year = cursor.fetchone()
                year_str = f"{min_year}-{max_year}" if min_year else "N/A"
            except:
                year_str = "N/A"
            
            # Cobertura de barrios
            try:
                cursor.execute(f"SELECT COUNT(DISTINCT barrio_id) FROM {table} WHERE barrio_id IS NOT NULL")
                unique_barrios = cursor.fetchone()[0]
                coverage = f"{unique_barrios}/73 ({unique_barrios/73*100:.0f}%)"
            except:
                coverage = "N/A"
            
            # Estado
            status = "✅" if count > 0 else "⚠️ "
            
            print(f"{status} {table:<37} {count:>12,} {year_str:>15} {coverage:>15}")
        
        print()
        
        # Vistas principales
        print("=" * 90)
        print("👁️  VISTAS PRINCIPALES")
        print("=" * 90)
        print()
        print(f"{'Vista':<50} {'Registros':>15}")
        print("-" * 90)
        
        key_views = [v for v in views if v.startswith('v_') and not v.startswith('vw_')]
        
        for view in key_views[:10]:  # Mostrar solo las primeras 10
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {view}")
                count = cursor.fetchone()[0]
                status = "✅" if count > 0 else "⚠️ "
                print(f"{status} {view:<47} {count:>15,}")
            except Exception as e:
                print(f"❌ {view:<47} {'ERROR':>15}")
        
        if len(key_views) > 10:
            print(f"... y {len(key_views) - 10} vistas más")
        
        print()
        print("=" * 90)
        print("✅ Estado de base de datos verificado")
        print("=" * 90)
        print()
        print("💡 Para ver detalles completos ejecuta: python3 scripts/inspect_database_schema.py")
        print()
        
    finally:
        conn.close()


if __name__ == "__main__":
    main()
