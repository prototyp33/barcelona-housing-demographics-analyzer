#!/usr/bin/env python3
"""
Script de validación para fact_ruido.

Verifica que los datos cumplen los criterios de calidad esperados:
- Cobertura de barrios: 73 barrios
- Cobertura temporal: mínimo 2022 (último Mapa Estratégico de Ruido)
- Completitud: ≥80% de registros con nivel_lden_medio > 0
- Rangos válidos: niveles entre 40-80 dB(A)
"""

import sqlite3
import sys
from pathlib import Path

# Añadir el directorio raíz al path para importar módulos
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database_setup import DEFAULT_DB_NAME, create_database_schema


def main() -> int:
    """Ejecuta validaciones sobre fact_ruido."""
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
            "SELECT name FROM sqlite_master WHERE type='table' AND name='fact_ruido';"
        )
        if not cursor.fetchone():
            print("❌ La tabla fact_ruido no existe")
            return 1
        
        print("\n=== Validación fact_ruido ===")
        
        # 1. Cobertura de barrios
        cursor.execute("SELECT COUNT(DISTINCT barrio_id) FROM fact_ruido;")
        barrios_count = cursor.fetchone()[0]
        print(f"- Barrios distintos: {barrios_count}/73")
        
        # 2. Cobertura temporal
        cursor.execute(
            "SELECT MIN(anio), MAX(anio) FROM fact_ruido;"
        )
        min_year, max_year = cursor.fetchone()
        print(f"- Rango de años: {min_year} - {max_year}")
        
        cursor.execute(
            "SELECT DISTINCT anio FROM fact_ruido ORDER BY anio;"
        )
        years = [row[0] for row in cursor.fetchall()]
        print(f"- Años presentes: {years}")
        
        # 3. Completitud de métricas clave
        cursor.execute(
            """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN nivel_lden_medio IS NOT NULL AND nivel_lden_medio > 0 THEN 1 ELSE 0 END) as con_lden,
                SUM(CASE WHEN nivel_ld_dia IS NOT NULL AND nivel_ld_dia > 0 THEN 1 ELSE 0 END) as con_ld,
                SUM(CASE WHEN nivel_ln_noche IS NOT NULL AND nivel_ln_noche > 0 THEN 1 ELSE 0 END) as con_ln,
                SUM(CASE WHEN pct_poblacion_expuesta_65db IS NOT NULL THEN 1 ELSE 0 END) as con_exposicion
            FROM fact_ruido;
            """
        )
        total, con_lden, con_ld, con_ln, con_exposicion = cursor.fetchone()
        
        pct_lden = (con_lden / total * 100) if total > 0 else 0
        pct_ld = (con_ld / total * 100) if total > 0 else 0
        pct_ln = (con_ln / total * 100) if total > 0 else 0
        pct_exposicion = (con_exposicion / total * 100) if total > 0 else 0
        
        print(f"- Registros con nivel_lden_medio > 0: {con_lden}/{total} ({pct_lden:.2f}%)")
        print(f"- Registros con nivel_ld_dia > 0: {con_ld}/{total} ({pct_ld:.2f}%)")
        print(f"- Registros con nivel_ln_noche > 0: {con_ln}/{total} ({pct_ln:.2f}%)")
        print(f"- Registros con pct_poblacion_expuesta_65db: {con_exposicion}/{total} ({pct_exposicion:.2f}%)")
        
        # 4. Validar rangos de valores
        cursor.execute(
            """
            SELECT 
                MIN(nivel_lden_medio) as min_lden,
                MAX(nivel_lden_medio) as max_lden,
                AVG(nivel_lden_medio) as avg_lden
            FROM fact_ruido
            WHERE nivel_lden_medio IS NOT NULL AND nivel_lden_medio > 0;
            """
        )
        min_lden, max_lden, avg_lden = cursor.fetchone()
        if min_lden:
            print(f"\nRangos de nivel_lden_medio:")
            print(f"  - Mínimo: {min_lden:.2f} dB(A)")
            print(f"  - Máximo: {max_lden:.2f} dB(A)")
            print(f"  - Promedio: {avg_lden:.2f} dB(A)")
        
        # 5. Validar criterios
        print("\nCriterios:")
        criterios_ok = True
        
        # Criterio 1: 73 barrios
        if barrios_count >= 73:
            print(f"* 73 barrios con datos: OK ({barrios_count} >= 73)")
        else:
            print(f"* 73 barrios con datos: FALLO ({barrios_count} < 73)")
            criterios_ok = False
        
        # Criterio 2: Cobertura temporal mínima 2022
        years_set = set(years)
        has_2022 = 2022 in years_set
        
        if has_2022:
            print("* Cobertura 2022: OK (2022=True)")
        else:
            print(f"* Cobertura 2022: FALLO (2022={has_2022})")
            criterios_ok = False
        
        # Criterio 3: ≥80% completitud en nivel_lden_medio
        if pct_lden >= 80:
            print(f"* ≥80% completitud en nivel_lden_medio: OK ({pct_lden:.2f}%)")
        else:
            print(f"* ≥80% completitud en nivel_lden_medio: FALLO ({pct_lden:.2f}% < 80%)")
            criterios_ok = False
        
        # Criterio 4: Rangos válidos (40-80 dB(A))
        if min_lden and max_lden:
            if 40 <= min_lden <= 80 and 40 <= max_lden <= 80:
                print(f"* Rangos válidos (40-80 dB(A)): OK ({min_lden:.2f}-{max_lden:.2f})")
            else:
                print(f"* Rangos válidos (40-80 dB(A)): FALLO ({min_lden:.2f}-{max_lden:.2f})")
                criterios_ok = False
        
        # 6. Mostrar barrios faltantes si hay menos de 73
        if barrios_count < 73:
            cursor.execute(
                """
                SELECT b.barrio_id, b.barrio_nombre
                FROM dim_barrios b
                LEFT JOIN fact_ruido f ON b.barrio_id = f.barrio_id
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

