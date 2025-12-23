#!/usr/bin/env python3
"""
Script de validación para fact_seguridad.

Verifica que los datos cumplen los criterios de calidad esperados:
- Cobertura de barrios: al menos 50 de 73 barrios (≥68%)
- Cobertura temporal: al menos 2020-2024
- Completitud: ≥70% de registros con delitos_patrimonio o delitos_seguridad_personal > 0
"""

import sqlite3
import sys
from pathlib import Path

# Añadir el directorio raíz al path para importar módulos
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database_setup import DEFAULT_DB_NAME, create_database_schema


def main() -> int:
    """Ejecuta validaciones sobre fact_seguridad."""
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
            "SELECT name FROM sqlite_master WHERE type='table' AND name='fact_seguridad';"
        )
        if not cursor.fetchone():
            print("❌ La tabla fact_seguridad no existe")
            return 1
        
        print("\n=== Validación fact_seguridad ===")
        
        # 1. Cobertura de barrios
        cursor.execute("SELECT COUNT(DISTINCT barrio_id) FROM fact_seguridad;")
        barrios_count = cursor.fetchone()[0]
        print(f"- Barrios distintos: {barrios_count}/73")
        
        # 2. Cobertura temporal
        cursor.execute(
            "SELECT MIN(anio), MAX(anio) FROM fact_seguridad;"
        )
        min_year, max_year = cursor.fetchone()
        print(f"- Rango de años: {min_year} - {max_year}")
        
        cursor.execute(
            "SELECT DISTINCT anio FROM fact_seguridad ORDER BY anio;"
        )
        years = [row[0] for row in cursor.fetchall()]
        print(f"- Años presentes: {years}")
        
        # 3. Completitud de métricas clave
        cursor.execute(
            """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN delitos_patrimonio > 0 THEN 1 ELSE 0 END) as con_delitos_patrimonio,
                SUM(CASE WHEN delitos_seguridad_personal > 0 THEN 1 ELSE 0 END) as con_delitos_personal,
                SUM(CASE WHEN tasa_criminalidad_1000hab IS NOT NULL AND tasa_criminalidad_1000hab > 0 THEN 1 ELSE 0 END) as con_tasa
            FROM fact_seguridad;
            """
        )
        total, con_patrimonio, con_personal, con_tasa = cursor.fetchone()
        
        pct_patrimonio = (con_patrimonio / total * 100) if total > 0 else 0
        pct_personal = (con_personal / total * 100) if total > 0 else 0
        pct_tasa = (con_tasa / total * 100) if total > 0 else 0
        
        print(f"- Registros con delitos_patrimonio > 0: {con_patrimonio}/{total} ({pct_patrimonio:.2f}%)")
        print(f"- Registros con delitos_seguridad_personal > 0: {con_personal}/{total} ({pct_personal:.2f}%)")
        print(f"- Registros con tasa_criminalidad_1000hab > 0: {con_tasa}/{total} ({pct_tasa:.2f}%)")
        
        # 4. Validar criterios
        print("\nCriterios:")
        criterios_ok = True
        
        # Criterio 1: Al menos 50 barrios (≥68%)
        if barrios_count >= 50:
            print(f"* ≥50 barrios con datos: OK ({barrios_count} >= 50)")
        else:
            print(f"* ≥50 barrios con datos: FALLO ({barrios_count} < 50)")
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
        
        # Criterio 3: ≥70% completitud en delitos
        pct_completitud = max(pct_patrimonio, pct_personal)
        if pct_completitud >= 70:
            print(f"* ≥70% completitud en delitos: OK ({pct_completitud:.2f}%)")
        else:
            print(f"* ≥70% completitud en delitos: FALLO ({pct_completitud:.2f}% < 70%)")
            criterios_ok = False
        
        # 5. Mostrar barrios faltantes si hay menos de 73
        if barrios_count < 73:
            cursor.execute(
                """
                SELECT b.barrio_id, b.barrio_nombre
                FROM dim_barrios b
                LEFT JOIN fact_seguridad f ON b.barrio_id = f.barrio_id
                WHERE f.barrio_id IS NULL
                ORDER BY b.barrio_id;
                """
            )
            missing_barrios = cursor.fetchall()
            if missing_barrios:
                print(f"\n⚠️  Barrios sin datos ({len(missing_barrios)}):")
                for barrio_id, barrio_nombre in missing_barrios[:20]:  # Mostrar solo los primeros 20
                    print(f"   - {barrio_id}: {barrio_nombre}")
                if len(missing_barrios) > 20:
                    print(f"   ... y {len(missing_barrios) - 20} más")
        
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

