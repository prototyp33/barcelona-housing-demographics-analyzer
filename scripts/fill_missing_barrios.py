#!/usr/bin/env python3
"""
Relleno de Barrios Faltantes

Completa la cobertura de barrios usando estimaciones basadas en:
1. Promedios del distrito
2. Promedios de barrios similares (por población/área)
3. Valores por defecto conservadores

IMPORTANTE: Los valores rellenados se marcan con un flag para distinguirlos
de los datos reales.
"""

import sys
from pathlib import Path
import sqlite3
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.database import DatabaseManager


def fill_fact_servicios_salud(conn):
    """
    Rellena fact_servicios_salud para los 4 barrios faltantes.
    
    Barrios faltantes:
    - la Clota
    - Torre Baró
    - Ciutat Meridiana
    - Vallbona
    """
    cursor = conn.cursor()
    
    print("\n🏥 Rellenando fact_servicios_salud...")
    
    # Get missing barrios
    cursor.execute("""
        SELECT b.barrio_id, b.barrio_nombre, b.distrito_nombre, b.area_km2
        FROM dim_barrios b
        WHERE b.barrio_id NOT IN (
            SELECT DISTINCT barrio_id FROM fact_servicios_salud
        )
        ORDER BY b.barrio_nombre
    """)
    
    missing_barrios = cursor.fetchall()
    
    if not missing_barrios:
        print("   ✅ No hay barrios faltantes")
        return 0
    
    print(f"   Barrios faltantes: {len(missing_barrios)}")
    
    # Calculate district averages
    cursor.execute("""
        SELECT 
            b.distrito_nombre,
            AVG(s.num_centros_salud) as avg_centros,
            AVG(s.num_hospitales) as avg_hospitales,
            AVG(s.num_farmacias) as avg_farmacias,
            AVG(s.densidad_servicios_por_km2) as avg_densidad_km2,
            AVG(s.densidad_servicios_por_1000hab) as avg_densidad_hab
        FROM fact_servicios_salud s
        JOIN dim_barrios b ON s.barrio_id = b.barrio_id
        GROUP BY b.distrito_nombre
    """)
    
    district_avgs = {row[0]: row[1:] for row in cursor.fetchall()}
    
    inserted = 0
    for barrio_id, barrio_nombre, distrito_nombre, area_km2 in missing_barrios:
        # Get district averages or use defaults
        if distrito_nombre in district_avgs:
            avg_centros, avg_hospitales, avg_farmacias, avg_dens_km2, avg_dens_hab = district_avgs[distrito_nombre]
        else:
            # Conservative defaults for peripheral neighborhoods
            avg_centros, avg_hospitales, avg_farmacias = 0, 0, 1
            avg_dens_km2, avg_dens_hab = 0.5, 0.5
        
        # Round to integers for counts
        num_centros = max(0, round(avg_centros))
        num_hospitales = max(0, round(avg_hospitales))
        num_farmacias = max(1, round(avg_farmacias))  # At least 1 pharmacy
        total_servicios = num_centros + num_hospitales + num_farmacias
        
        # Calculate densities
        densidad_km2 = total_servicios / area_km2 if area_km2 else 0
        
        cursor.execute("""
            INSERT INTO fact_servicios_salud (
                barrio_id, anio, num_centros_salud, num_hospitales, num_farmacias,
                total_servicios_sanitarios, densidad_servicios_por_km2,
                densidad_servicios_por_1000hab, dataset_id, source, etl_loaded_at
            ) VALUES (?, 2025, ?, ?, ?, ?, ?, ?, 'estimated', 'coverage_fill_script', ?)
        """, (
            barrio_id, num_centros, num_hospitales, num_farmacias,
            total_servicios, densidad_km2, avg_dens_hab,
            datetime.now().isoformat()
        ))
        
        print(f"   ✅ {barrio_nombre}: {num_centros} centros, {num_hospitales} hospitales, {num_farmacias} farmacias")
        inserted += 1
    
    conn.commit()
    return inserted


def fill_fact_comercio(conn):
    """Rellena fact_comercio para los 3 barrios faltantes."""
    cursor = conn.cursor()
    
    print("\n🏪 Rellenando fact_comercio...")
    
    cursor.execute("""
        SELECT b.barrio_id, b.barrio_nombre, b.distrito_nombre, b.area_km2
        FROM dim_barrios b
        WHERE b.barrio_id NOT IN (
            SELECT DISTINCT barrio_id FROM fact_comercio
        )
        ORDER BY b.barrio_nombre
    """)
    
    missing_barrios = cursor.fetchall()
    
    if not missing_barrios:
        print("   ✅ No hay barrios faltantes")
        return 0
    
    print(f"   Barrios faltantes: {len(missing_barrios)}")
    
    # Use conservative estimates for peripheral neighborhoods
    inserted = 0
    for barrio_id, barrio_nombre, distrito_nombre, area_km2 in missing_barrios:
        # Small peripheral neighborhoods typically have minimal commercial activity
        num_locales = 5
        num_terrazas = 1
        num_licencias = 3
        total_establecimientos = num_locales + num_terrazas + num_licencias
        
        densidad_km2 = total_establecimientos / area_km2 if area_km2 else 0
        
        cursor.execute("""
            INSERT INTO fact_comercio (
                barrio_id, anio, num_locales_comerciales, num_terrazas, num_licencias,
                total_establecimientos, densidad_comercial_por_km2,
                densidad_comercial_por_1000hab, dataset_id, source, etl_loaded_at
            ) VALUES (?, 2025, ?, ?, ?, ?, ?, ?, 'estimated', 'coverage_fill_script', ?)
        """, (
            barrio_id, num_locales, num_terrazas, num_licencias,
            total_establecimientos, densidad_km2, 5.0,  # Conservative density per 1000 hab
            datetime.now().isoformat()
        ))
        
        print(f"   ✅ {barrio_nombre}: {total_establecimientos} establecimientos")
        inserted += 1
    
    conn.commit()
    return inserted


def fill_fact_medio_ambiente(conn):
    """Rellena fact_medio_ambiente para los 3 barrios faltantes."""
    cursor = conn.cursor()
    
    print("\n🌳 Rellenando fact_medio_ambiente...")
    
    cursor.execute("""
        SELECT b.barrio_id, b.barrio_nombre, b.area_km2
        FROM dim_barrios b
        WHERE b.barrio_id NOT IN (
            SELECT DISTINCT barrio_id FROM fact_medio_ambiente
        )
        ORDER BY b.barrio_nombre
    """)
    
    missing_barrios = cursor.fetchall()
    
    if not missing_barrios:
        print("   ✅ No hay barrios faltantes")
        return 0
    
    print(f"   Barrios faltantes: {len(missing_barrios)}")
    
    # Get city-wide averages for environmental metrics
    cursor.execute("""
        SELECT 
            AVG(nivel_lden_medio) as avg_ruido,
            AVG(pct_poblacion_expuesta_65db) as avg_exp_ruido,
            AVG(superficie_zonas_verdes_m2) as avg_zonas_verdes,
            AVG(num_parques_jardines) as avg_parques,
            AVG(num_arboles) as avg_arboles
        FROM fact_medio_ambiente
    """)
    
    avg_ruido, avg_exp_ruido, avg_zonas_verdes, avg_parques, avg_arboles = cursor.fetchone()
    
    inserted = 0
    for barrio_id, barrio_nombre, area_km2 in missing_barrios:
        # Peripheral neighborhoods typically have lower noise and more green space
        nivel_ruido = avg_ruido * 0.8 if avg_ruido else 55.0  # 20% less noise
        pct_exp_ruido = avg_exp_ruido * 0.7 if avg_exp_ruido else 30.0
        
        # More green space in peripheral areas
        zonas_verdes = avg_zonas_verdes * 1.5 if avg_zonas_verdes else 50000
        num_parques = max(1, round(avg_parques)) if avg_parques else 1
        num_arboles = round(avg_arboles * 1.2) if avg_arboles else 100
        
        m2_per_hab = zonas_verdes / 5000  # Assume ~5000 inhabitants
        
        cursor.execute("""
            INSERT INTO fact_medio_ambiente (
                barrio_id, anio, nivel_lden_medio, pct_poblacion_expuesta_65db,
                superficie_zonas_verdes_m2, num_parques_jardines, num_arboles,
                m2_zonas_verdes_por_habitante, dataset_id, source, etl_loaded_at
            ) VALUES (?, 2025, ?, ?, ?, ?, ?, ?, 'estimated', 'coverage_fill_script', ?)
        """, (
            barrio_id, nivel_ruido, pct_exp_ruido, zonas_verdes,
            num_parques, num_arboles, m2_per_hab,
            datetime.now().isoformat()
        ))
        
        print(f"   ✅ {barrio_nombre}: {num_parques} parques, {num_arboles} árboles, {m2_per_hab:.1f} m²/hab")
        inserted += 1
    
    conn.commit()
    return inserted


def main():
    """Main execution."""
    print("=" * 100)
    print("RELLENO DE BARRIOS FALTANTES")
    print("=" * 100)
    print()
    print("⚠️  IMPORTANTE: Este script rellena barrios faltantes con ESTIMACIONES")
    print("   Los valores se marcan con source='coverage_fill_script' y dataset_id='estimated'")
    print()
    
    db_manager = DatabaseManager()
    conn = db_manager.get_connection()
    
    try:
        total_inserted = 0
        
        # Fill each table
        total_inserted += fill_fact_servicios_salud(conn)
        total_inserted += fill_fact_comercio(conn)
        total_inserted += fill_fact_medio_ambiente(conn)
        
        print()
        print("=" * 100)
        print(f"✅ COMPLETADO: {total_inserted} registros insertados")
        print("=" * 100)
        print()
        print("📊 Verificar cobertura actualizada:")
        print("   python scripts/analyze_barrio_coverage.py")
        print()
        print("📈 Verificar health score:")
        print("   python scripts/schema_health_cli.py current")
        print()
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
