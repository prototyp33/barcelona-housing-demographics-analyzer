#!/usr/bin/env python3
"""
Script de verificación del estado del Sprint de Integridad de Datos.

Verifica los tres criterios críticos del sprint:
1. fact_precios: Multi-source records preserved (>1014 rows)
2. dim_barrios: 73/73 barrios have valid geometry_json
3. fact_demografia: <10% null values in key fields

También verifica métricas adicionales de calidad.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Colores para output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"


def get_db_path() -> Path:
    """Obtiene la ruta a la base de datos."""
    db_path = Path("data/processed/database.db")
    if not db_path.exists():
        print(f"{RED}❌ Base de datos no encontrada: {db_path}{RESET}")
        sys.exit(1)
    return db_path


def check_fact_precios(conn: sqlite3.Connection) -> Tuple[bool, Dict[str, int]]:
    """
    Verifica que fact_precios tenga suficientes registros multi-fuente.
    
    Criterio: >1014 registros preservando datos de múltiples fuentes.
    """
    cursor = conn.cursor()
    
    # Total de registros
    cursor.execute("SELECT COUNT(*) FROM fact_precios")
    total = cursor.fetchone()[0]
    
    # Registros por fuente
    cursor.execute("""
        SELECT source, COUNT(*) as count
        FROM fact_precios
        GROUP BY source
    """)
    sources = dict(cursor.fetchall())
    
    # Registros con múltiples datasets (concatenados con |)
    cursor.execute("""
        SELECT COUNT(*) FROM fact_precios
        WHERE dataset_id LIKE '%|%' OR source LIKE '%|%'
    """)
    multi_source = cursor.fetchone()[0]
    
    # Verificar que no hay duplicados reales
    cursor.execute("""
        SELECT barrio_id, anio, COALESCE(trimestre, -1), 
               COALESCE(dataset_id, ''), COALESCE(source, ''), COUNT(*) as cnt
        FROM fact_precios
        GROUP BY barrio_id, anio, COALESCE(trimestre, -1), 
                 COALESCE(dataset_id, ''), COALESCE(source, '')
        HAVING COUNT(*) > 1
    """)
    duplicates = cursor.fetchall()
    
    passed = total > 1014 and len(duplicates) == 0
    
    return passed, {
        "total": total,
        "sources": sources,
        "multi_source_records": multi_source,
        "duplicates": len(duplicates),
    }


def check_dim_barrios_geometries(conn: sqlite3.Connection) -> Tuple[bool, Dict[str, int]]:
    """
    Verifica que todos los barrios tengan geometrías válidas.
    
    Criterio: 73/73 barrios con geometry_json válido.
    """
    cursor = conn.cursor()
    
    # Total de barrios
    cursor.execute("SELECT COUNT(*) FROM dim_barrios")
    total = cursor.fetchone()[0]
    
    # Barrios con geometría no nula y no vacía
    cursor.execute("""
        SELECT COUNT(*) FROM dim_barrios
        WHERE geometry_json IS NOT NULL 
        AND geometry_json != ''
        AND geometry_json != 'null'
    """)
    with_geometry = cursor.fetchone()[0]
    
    # Barrios sin geometría
    cursor.execute("""
        SELECT barrio_id, barrio_nombre 
        FROM dim_barrios
        WHERE geometry_json IS NULL 
           OR geometry_json = ''
           OR geometry_json = 'null'
    """)
    missing = cursor.fetchall()
    
    passed = total == 73 and with_geometry == 73
    
    return passed, {
        "total": total,
        "with_geometry": with_geometry,
        "missing": len(missing),
        "missing_details": missing[:5],  # Primeros 5 para reporte
    }


def check_fact_demografia_nulls(conn: sqlite3.Connection) -> Tuple[bool, Dict[str, float]]:
    """
    Verifica que fact_demografia tenga <10% nulls en campos clave.
    
    Campos clave: poblacion_total, hogares_totales, edad_media
    """
    cursor = conn.cursor()
    
    # Total de registros
    cursor.execute("SELECT COUNT(*) FROM fact_demografia")
    total = cursor.fetchone()[0]
    
    if total == 0:
        return False, {"total": 0, "null_percentages": {}}
    
    # Contar nulls por campo clave
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN poblacion_total IS NULL THEN 1 ELSE 0 END) as null_poblacion,
            SUM(CASE WHEN hogares_totales IS NULL THEN 1 ELSE 0 END) as null_hogares,
            SUM(CASE WHEN edad_media IS NULL THEN 1 ELSE 0 END) as null_edad,
            SUM(CASE WHEN porc_inmigracion IS NULL THEN 1 ELSE 0 END) as null_inmigracion,
            SUM(CASE WHEN densidad_hab_km2 IS NULL THEN 1 ELSE 0 END) as null_densidad
        FROM fact_demografia
    """)
    row = cursor.fetchone()
    total_rows, null_poblacion, null_hogares, null_edad, null_inmigracion, null_densidad = row
    
    # Calcular porcentajes
    pct_poblacion = (null_poblacion / total_rows) * 100 if total_rows > 0 else 0
    pct_hogares = (null_hogares / total_rows) * 100 if total_rows > 0 else 0
    pct_edad = (null_edad / total_rows) * 100 if total_rows > 0 else 0
    pct_inmigracion = (null_inmigracion / total_rows) * 100 if total_rows > 0 else 0
    pct_densidad = (null_densidad / total_rows) * 100 if total_rows > 0 else 0
    
    # Campos críticos deben tener <10% nulls
    critical_fields_ok = (
        pct_poblacion < 10 and
        pct_hogares < 10 and
        pct_edad < 10
    )
    
    return critical_fields_ok, {
        "total": total_rows,
        "null_percentages": {
            "poblacion_total": pct_poblacion,
            "hogares_totales": pct_hogares,
            "edad_media": pct_edad,
            "porc_inmigracion": pct_inmigracion,
            "densidad_hab_km2": pct_densidad,
        },
        "null_counts": {
            "poblacion_total": null_poblacion,
            "hogares_totales": null_hogares,
            "edad_media": null_edad,
            "porc_inmigracion": null_inmigracion,
            "densidad_hab_km2": null_densidad,
        },
    }


def check_additional_metrics(conn: sqlite3.Connection) -> Dict[str, any]:
    """Verifica métricas adicionales de calidad."""
    cursor = conn.cursor()
    
    metrics = {}
    
    # Integridad referencial
    cursor.execute("""
        SELECT COUNT(*) FROM fact_precios fp
        LEFT JOIN dim_barrios db ON fp.barrio_id = db.barrio_id
        WHERE db.barrio_id IS NULL
    """)
    orphan_precios = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(*) FROM fact_demografia fd
        LEFT JOIN dim_barrios db ON fd.barrio_id = db.barrio_id
        WHERE db.barrio_id IS NULL
    """)
    orphan_demografia = cursor.fetchone()[0]
    
    metrics["referential_integrity"] = {
        "orphan_precios": orphan_precios,
        "orphan_demografia": orphan_demografia,
        "passed": orphan_precios == 0 and orphan_demografia == 0,
    }
    
    # Cobertura temporal
    cursor.execute("SELECT MIN(anio), MAX(anio) FROM fact_precios")
    precios_years = cursor.fetchone()
    
    cursor.execute("SELECT MIN(anio), MAX(anio) FROM fact_demografia")
    demografia_years = cursor.fetchone()
    
    metrics["temporal_coverage"] = {
        "precios": {"min": precios_years[0], "max": precios_years[1]},
        "demografia": {"min": demografia_years[0], "max": demografia_years[1]},
    }
    
    return metrics


def print_section_header(title: str) -> None:
    """Imprime un encabezado de sección."""
    print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
    print(f"{BOLD}{BLUE}{title:^60}{RESET}")
    print(f"{BOLD}{BLUE}{'='*60}{RESET}\n")


def print_result(passed: bool, message: str, details: Dict = None) -> None:
    """Imprime el resultado de una verificación."""
    status = f"{GREEN}✅ PASSED{RESET}" if passed else f"{RED}❌ FAILED{RESET}"
    print(f"{status} {message}")
    
    if details:
        for key, value in details.items():
            if isinstance(value, dict):
                print(f"   {key}:")
                for k, v in value.items():
                    print(f"     - {k}: {v}")
            elif isinstance(value, list) and len(value) > 0:
                print(f"   {key}:")
                for item in value[:5]:  # Mostrar solo primeros 5
                    print(f"     - {item}")
            else:
                print(f"   {key}: {value}")


def main() -> int:
    """Función principal."""
    print(f"{BOLD}{BLUE}")
    print("=" * 60)
    print("  VERIFICACIÓN DEL SPRINT DE INTEGRIDAD DE DATOS")
    print("=" * 60)
    print(f"{RESET}")
    
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    
    try:
        # Verificar fact_precios
        print_section_header("1. VERIFICACIÓN: fact_precios")
        precios_passed, precios_details = check_fact_precios(conn)
        print_result(
            precios_passed,
            f"fact_precios tiene {precios_details['total']} registros (objetivo: >1014)",
            precios_details,
        )
        
        # Verificar dim_barrios geometrías
        print_section_header("2. VERIFICACIÓN: dim_barrios.geometry_json")
        geom_passed, geom_details = check_dim_barrios_geometries(conn)
        print_result(
            geom_passed,
            f"dim_barrios: {geom_details['with_geometry']}/{geom_details['total']} barrios con geometría",
            geom_details,
        )
        
        # Verificar fact_demografia nulls
        print_section_header("3. VERIFICACIÓN: fact_demografia nulls")
        demografia_passed, demografia_details = check_fact_demografia_nulls(conn)
        null_pcts = demografia_details.get("null_percentages", {})
        print_result(
            demografia_passed,
            f"fact_demografia: <10% nulls en campos críticos",
            {
                "Total registros": demografia_details["total"],
                "Porcentajes de nulls": null_pcts,
            },
        )
        
        # Métricas adicionales
        print_section_header("4. MÉTRICAS ADICIONALES")
        additional = check_additional_metrics(conn)
        print_result(
            additional["referential_integrity"]["passed"],
            "Integridad referencial",
            additional["referential_integrity"],
        )
        print(f"\n   Cobertura temporal:")
        print(f"     - fact_precios: {additional['temporal_coverage']['precios']['min']}-{additional['temporal_coverage']['precios']['max']}")
        print(f"     - fact_demografia: {additional['temporal_coverage']['demografia']['min']}-{additional['temporal_coverage']['demografia']['max']}")
        
        # Resumen final
        print_section_header("RESUMEN DEL SPRINT")
        all_passed = precios_passed and geom_passed and demografia_passed
        
        if all_passed:
            print(f"{GREEN}{BOLD}✅ SPRINT COMPLETADO EXITOSAMENTE{RESET}")
            print(f"\n   Todos los criterios críticos han sido cumplidos:")
            print(f"   ✅ fact_precios: {precios_details['total']} registros preservados")
            print(f"   ✅ dim_barrios: {geom_details['with_geometry']}/73 geometrías cargadas")
            print(f"   ✅ fact_demografia: <10% nulls en campos críticos")
            return 0
        else:
            print(f"{RED}{BOLD}❌ SPRINT INCOMPLETO{RESET}")
            print(f"\n   Criterios fallidos:")
            if not precios_passed:
                print(f"   ❌ fact_precios: {precios_details['total']} registros (objetivo: >1014)")
            if not geom_passed:
                print(f"   ❌ dim_barrios: {geom_details['with_geometry']}/73 geometrías")
            if not demografia_passed:
                print(f"   ❌ fact_demografia: >10% nulls en campos críticos")
            return 1
    
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())

