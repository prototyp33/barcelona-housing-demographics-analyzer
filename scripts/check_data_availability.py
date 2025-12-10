#!/usr/bin/env python3
"""
Script de verificación de disponibilidad de datos.

Verifica la disponibilidad y completitud de datos en todas las tablas principales:
- dim_barrios: Barrios y geometrías
- fact_precios: Datos de precios
- fact_renta: Datos de renta (crítico para 2022)
- fact_demografia: Datos demográficos

Uso:
    python scripts/check_data_availability.py [--json] [--year YEAR]

Ejemplo:
    python scripts/check_data_availability.py --year 2022
    python scripts/check_data_availability.py --json > report.json
"""

import argparse
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

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


def check_data_availability(
    conn: sqlite3.Connection,
    critical_year: Optional[int] = None
) -> Dict[str, Any]:
    """
    Verifica la disponibilidad de datos en todas las tablas principales.
    
    Args:
        conn: Conexión a la base de datos.
        critical_year: Año crítico para verificar (default: 2022).
    
    Returns:
        Dict con resultados de la verificación.
    """
    cursor = conn.cursor()
    results = {
        "timestamp": datetime.now().isoformat(),
        "tables": {},
        "summary": {
            "total_barrios_expected": 73,
            "status": "unknown"
        },
        "warnings": [],
        "errors": []
    }
    
    # ============================================================================
    # CONSULTA PRINCIPAL: Verificación de disponibilidad
    # ============================================================================
    query = """
    SELECT 
        'dim_barrios' as tabla,
        COUNT(*) as registros,
        COUNT(DISTINCT barrio_id) as barrios_unicos,
        SUM(CASE WHEN geometry_json IS NOT NULL THEN 1 ELSE 0 END) as con_geometria
    FROM dim_barrios

    UNION ALL

    SELECT 
        'fact_precios',
        COUNT(*),
        COUNT(DISTINCT barrio_id),
        COUNT(DISTINCT anio)
    FROM fact_precios

    UNION ALL

    SELECT 
        'fact_renta',
        COUNT(*),
        COUNT(DISTINCT barrio_id),
        COUNT(DISTINCT anio)
    FROM fact_renta
    WHERE anio = ?

    UNION ALL

    SELECT 
        'fact_demografia',
        COUNT(*),
        COUNT(DISTINCT barrio_id),
        COUNT(DISTINCT anio)
    FROM fact_demografia;
    """
    
    critical_year = critical_year or 2022
    cursor.execute(query, (critical_year,))
    rows = cursor.fetchall()
    
    # Procesar resultados
    for row in rows:
        tabla, registros, barrios_unicos, metrica = row
        results["tables"][tabla] = {
            "registros": registros,
            "barrios_unicos": barrios_unicos,
            "metrica_adicional": metrica
        }
    
    # ============================================================================
    # VERIFICACIONES ADICIONALES
    # ============================================================================
    
    # 1. Verificar dim_barrios
    dim_barrios = results["tables"].get("dim_barrios", {})
    expected_barrios = 73
    
    if dim_barrios.get("barrios_unicos", 0) < expected_barrios:
        results["errors"].append(
            f"dim_barrios: Faltan {expected_barrios - dim_barrios['barrios_unicos']} barrios"
        )
    
    con_geometria = dim_barrios.get("metrica_adicional", 0)  # con_geometria está en metrica_adicional
    barrios_unicos = dim_barrios.get("barrios_unicos", 0)
    if con_geometria < barrios_unicos:
        missing_geo = barrios_unicos - con_geometria
        results["warnings"].append(
            f"dim_barrios: {missing_geo} barrios sin geometría"
        )
    
    # 2. Verificar fact_precios
    fact_precios = results["tables"].get("fact_precios", {})
    if fact_precios.get("registros", 0) < 100:
        results["warnings"].append(
            f"fact_precios: Solo {fact_precios['registros']} registros (esperado >100)"
        )
    
    # 3. Verificar fact_renta (CRÍTICO)
    fact_renta = results["tables"].get("fact_renta", {})
    if fact_renta.get("registros", 0) == 0:
        results["errors"].append(
            f"fact_renta: No hay datos para el año crítico {critical_year}"
        )
    elif fact_renta.get("barrios_unicos", 0) < expected_barrios:
        missing = expected_barrios - fact_renta["barrios_unicos"]
        results["warnings"].append(
            f"fact_renta: Faltan datos de renta para {missing} barrios en {critical_year}"
        )
    
    # 4. Verificar fact_demografia
    fact_demografia = results["tables"].get("fact_demografia", {})
    if fact_demografia.get("barrios_unicos", 0) < expected_barrios:
        missing = expected_barrios - fact_demografia["barrios_unicos"]
        results["warnings"].append(
            f"fact_demografia: Faltan datos para {missing} barrios"
        )
    
    # 5. Verificar cobertura temporal
    cursor.execute("""
        SELECT 
            MIN(anio) as min_year,
            MAX(anio) as max_year,
            COUNT(DISTINCT anio) as years_count
        FROM fact_precios
    """)
    precios_years = cursor.fetchone()
    if precios_years:
        results["tables"]["fact_precios"]["cobertura_temporal"] = {
            "min_year": precios_years[0],
            "max_year": precios_years[1],
            "years_count": precios_years[2]
        }
    
    cursor.execute("""
        SELECT 
            MIN(anio) as min_year,
            MAX(anio) as max_year,
            COUNT(DISTINCT anio) as years_count
        FROM fact_demografia
    """)
    demo_years = cursor.fetchone()
    if demo_years:
        results["tables"]["fact_demografia"]["cobertura_temporal"] = {
            "min_year": demo_years[0],
            "max_year": demo_years[1],
            "years_count": demo_years[2]
        }
    
    # Determinar estado general
    if results["errors"]:
        results["summary"]["status"] = "error"
    elif results["warnings"]:
        results["summary"]["status"] = "warning"
    else:
        results["summary"]["status"] = "ok"
    
    return results


def print_table_report(results: Dict[str, Any]) -> None:
    """Imprime reporte en formato tabla."""
    print("=" * 80)
    print(f"{BOLD}📊 VERIFICACIÓN DE DISPONIBILIDAD DE DATOS{RESET}")
    print("=" * 80)
    print(f"Generado: {results['timestamp']}\n")
    
    print(f"{'Tabla':<20} {'Registros':<12} {'Barrios Únicos':<15} {'Métrica Adicional':<20}")
    print("-" * 80)
    
    tables = results["tables"]
    
    # dim_barrios
    dim = tables.get("dim_barrios", {})
    dim_geo = dim.get("metrica_adicional", 0)
    print(f"{'dim_barrios':<20} {dim.get('registros', 0):<12} {dim.get('barrios_unicos', 0):<15} {f'Con geometría: {dim_geo}':<20}")
    
    # fact_precios
    precios = tables.get("fact_precios", {})
    precios_years = precios.get("metrica_adicional", 0)
    print(f"{'fact_precios':<20} {precios.get('registros', 0):<12,} {precios.get('barrios_unicos', 0):<15} {f'Años únicos: {precios_years}':<20}")
    
    # fact_renta
    renta = tables.get("fact_renta", {})
    renta_years = renta.get("metrica_adicional", 0)
    print(f"{'fact_renta':<20} {renta.get('registros', 0):<12} {renta.get('barrios_unicos', 0):<15} {f'Años únicos: {renta_years}':<20}")
    
    # fact_demografia
    demo = tables.get("fact_demografia", {})
    demo_years = demo.get("metrica_adicional", 0)
    print(f"{'fact_demografia':<20} {demo.get('registros', 0):<12} {demo.get('barrios_unicos', 0):<15} {f'Años únicos: {demo_years}':<20}")
    
    print("-" * 80)
    
    # Análisis detallado
    print(f"\n{BOLD}📈 ANÁLISIS DETALLADO:{RESET}\n")
    
    expected = results["summary"]["total_barrios_expected"]
    
    # dim_barrios
    dim_count = dim.get("barrios_unicos", 0)
    dim_geo = dim.get("metrica_adicional", 0)
    print(f"  {BOLD}dim_barrios:{RESET}")
    print(f"    • Barrios esperados: {expected}")
    print(f"    • Barrios presentes: {dim_count}")
    if dim_count >= expected:
        print(f"    {GREEN}✅ Todos los barrios presentes{RESET}")
    else:
        print(f"    {RED}❌ Faltan {expected - dim_count} barrios{RESET}")
    
    if dim_geo >= dim_count:
        print(f"    {GREEN}✅ Todas las geometrías presentes ({dim_geo}/{dim_count}){RESET}")
    else:
        print(f"    {YELLOW}⚠️  {dim_count - dim_geo} barrios sin geometría{RESET}")
    
    # fact_precios
    precios_count = precios.get("registros", 0)
    precios_barrios = precios.get("barrios_unicos", 0)
    precios_years = precios.get("cobertura_temporal", {})
    print(f"\n  {BOLD}fact_precios:{RESET}")
    print(f"    • Total registros: {precios_count:,}")
    print(f"    • Barrios con datos: {precios_barrios}/{expected}")
    if precios_years:
        print(f"    • Cobertura temporal: {precios_years['min_year']}-{precios_years['max_year']} ({precios_years['years_count']} años)")
    
    # fact_renta
    renta_count = renta.get("registros", 0)
    renta_barrios = renta.get("barrios_unicos", 0)
    print(f"\n  {BOLD}fact_renta:{RESET}")
    if renta_count == 0:
        print(f"    {RED}❌ No hay datos de renta para el año crítico{RESET}")
    else:
        print(f"    • Registros: {renta_count:,}")
        print(f"    • Barrios con datos: {renta_barrios}/{expected}")
        if renta_barrios < expected:
            print(f"    {YELLOW}⚠️  Faltan datos para {expected - renta_barrios} barrios{RESET}")
    
    # fact_demografia
    demo_count = demo.get("registros", 0)
    demo_barrios = demo.get("barrios_unicos", 0)
    demo_years = demo.get("cobertura_temporal", {})
    print(f"\n  {BOLD}fact_demografia:{RESET}")
    print(f"    • Total registros: {demo_count:,}")
    print(f"    • Barrios con datos: {demo_barrios}/{expected}")
    if demo_years:
        print(f"    • Cobertura temporal: {demo_years['min_year']}-{demo_years['max_year']} ({demo_years['years_count']} años)")
    
    # Warnings y Errors
    if results["warnings"]:
        print(f"\n{BOLD}{YELLOW}⚠️  ADVERTENCIAS:{RESET}")
        for warning in results["warnings"]:
            print(f"    • {warning}")
    
    if results["errors"]:
        print(f"\n{BOLD}{RED}❌ ERRORES:{RESET}")
        for error in results["errors"]:
            print(f"    • {error}")
    
    # Estado general
    status = results["summary"]["status"]
    print(f"\n{BOLD}Estado General:{RESET} ", end="")
    if status == "ok":
        print(f"{GREEN}✅ OK{RESET}")
    elif status == "warning":
        print(f"{YELLOW}⚠️  ADVERTENCIAS{RESET}")
    else:
        print(f"{RED}❌ ERRORES{RESET}")
    
    print("=" * 80)


def main() -> None:
    """Punto de entrada principal."""
    parser = argparse.ArgumentParser(
        description="Verifica la disponibilidad de datos en la base de datos"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Salida en formato JSON"
    )
    parser.add_argument(
        "--year",
        type=int,
        default=2022,
        help="Año crítico para verificar fact_renta (default: 2022)"
    )
    
    args = parser.parse_args()
    
    # Conectar a la base de datos
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    
    try:
        # Ejecutar verificación
        results = check_data_availability(conn, critical_year=args.year)
        
        # Imprimir resultados
        if args.json:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            print_table_report(results)
        
        # Exit code basado en estado
        if results["summary"]["status"] == "error":
            sys.exit(1)
        elif results["summary"]["status"] == "warning":
            sys.exit(2)
        else:
            sys.exit(0)
    
    finally:
        conn.close()


if __name__ == "__main__":
    main()

