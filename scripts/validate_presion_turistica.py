#!/usr/bin/env python3
"""
Script de validación para fact_presion_turistica.

Verifica que los datos cumplen los criterios de calidad esperados:
- Cobertura de barrios: al menos 70 de 73 barrios (95%+)
- Cobertura temporal: al menos 2020-2024
- Completitud: ≥80% de registros con num_listings_airbnb > 0
"""

import sqlite3
import sys
from pathlib import Path

from src.database_setup import DEFAULT_DB_NAME, create_database_schema


def main() -> int:
    """Ejecuta validaciones sobre fact_presion_turistica."""
    # Determinar ruta de la base de datos
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    db_path = project_root / "data" / "processed" / DEFAULT_DB_NAME
    
    if not db_path.exists():
        print(f"❌ Base de datos no encontrada: {db_path}")
        return 1
    
    print(f"Usando base de datos: {db_path}")
    
    conn = sqlite3.connect(db_path)
    try:
        # Asegurar que el esquema existe
        create_database_schema(conn)
        
        # Verificar que la tabla existe
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='fact_presion_turistica';"
        )
        if not cursor.fetchone():
            print("❌ La tabla fact_presion_turistica no existe")
            return 1
        
        print("\n=== Validación fact_presion_turistica ===")
        
        # 1. Cobertura de barrios
        cursor.execute("SELECT COUNT(DISTINCT barrio_id) FROM fact_presion_turistica;")
        barrios_count = cursor.fetchone()[0]
        print(f"- Barrios distintos: {barrios_count}/73")
        
        # 2. Cobertura temporal
        cursor.execute(
            "SELECT MIN(anio), MAX(anio) FROM fact_presion_turistica;"
        )
        min_year, max_year = cursor.fetchone()
        print(f"- Rango de años: {min_year} - {max_year}")
        
        cursor.execute(
            "SELECT DISTINCT anio FROM fact_presion_turistica ORDER BY anio;"
        )
        years = [row[0] for row in cursor.fetchall()]
        print(f"- Años presentes: {years}")
        
        # 3. Completitud de métricas clave
        cursor.execute(
            """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN num_listings_airbnb > 0 THEN 1 ELSE 0 END) as con_listings,
                SUM(CASE WHEN precio_noche_promedio > 0 THEN 1 ELSE 0 END) as con_precio,
                SUM(CASE WHEN tasa_ocupacion IS NOT NULL THEN 1 ELSE 0 END) as con_ocupacion
            FROM fact_presion_turistica;
            """
        )
        total, con_listings, con_precio, con_ocupacion = cursor.fetchone()
        
        pct_listings = (con_listings / total * 100) if total > 0 else 0
        pct_precio = (con_precio / total * 100) if total > 0 else 0
        pct_ocupacion = (con_ocupacion / total * 100) if total > 0 else 0
        
        print(f"- Registros con num_listings_airbnb > 0: {con_listings}/{total} ({pct_listings:.2f}%)")
        print(f"- Registros con precio_noche_promedio > 0: {con_precio}/{total} ({pct_precio:.2f}%)")
        print(f"- Registros con tasa_ocupacion no nula: {con_ocupacion}/{total} ({pct_ocupacion:.2f}%)")
        
        # 4. Validar criterios
        print("\nCriterios:")
        criterios_ok = True
        
        # Criterio 1: Al menos 70 barrios (95%+)
        if barrios_count >= 70:
            print("* ≥70 barrios con datos: OK")
        else:
            print(f"* ≥70 barrios con datos: FALLO ({barrios_count} < 70)")
            criterios_ok = False
        
        # Criterio 2: Cobertura temporal mínima 2020-2024
        years_set = set(years)
        has_2020 = 2020 in years_set
        has_2024 = 2024 in years_set
        
        if has_2020 and has_2024:
            print("* Cobertura 2020-2024: OK (2020=True, 2024=True)")
        else:
            print(f"* Cobertura 2020-2024: FALLO (2020={has_2020}, 2024={has_2024})")
            criterios_ok = False
        
        # Criterio 3: ≥80% completitud en num_listings_airbnb
        if pct_listings >= 80:
            print(f"* ≥80% completitud en num_listings_airbnb: OK ({pct_listings:.2f}%)")
        else:
            print(f"* ≥80% completitud en num_listings_airbnb: FALLO ({pct_listings:.2f}% < 80%)")
            criterios_ok = False
        
        # 5. Mostrar barrios faltantes si hay menos de 73
        if barrios_count < 73:
            cursor.execute(
                """
                SELECT b.barrio_id, b.barrio_nombre
                FROM dim_barrios b
                LEFT JOIN fact_presion_turistica f ON b.barrio_id = f.barrio_id
                WHERE f.barrio_id IS NULL
                ORDER BY b.barrio_id;
                """
            )
            missing_barrios = cursor.fetchall()
            if missing_barrios:
                print(f"\n⚠️  Barrios sin datos ({len(missing_barrios)}):")
                for barrio_id, barrio_nombre in missing_barrios:
                    print(f"   - {barrio_id}: {barrio_nombre}")
        
        if criterios_ok:
            print("\n✅ Todas las validaciones pasaron")
            return 0
        else:
            print("\n❌ Algunas validaciones fallaron")
            return 1
            
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())

