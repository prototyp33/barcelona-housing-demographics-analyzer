#!/usr/bin/env python3
"""
Data Availability Audit Script
Analyzes the actual data coverage in the Barcelona Housing database
to determine what historical data exists for each source.

Usage:
    python scripts/audit_data_availability.py --db-path data/processed/database.db
"""

import argparse
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import json


def get_db_connection(db_path: Path) -> sqlite3.Connection:
    """Create database connection."""
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        sys.exit(1)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def analyze_dim_barrios(conn: sqlite3.Connection) -> Dict:
    """Analyze dimension table coverage."""
    cursor = conn.cursor()
    
    # Basic stats
    cursor.execute("SELECT COUNT(*) as total FROM dim_barrios")
    total = cursor.fetchone()["total"]
    
    # Geometry coverage
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN geometry_json IS NOT NULL THEN 1 ELSE 0 END) as with_geometry,
            COUNT(DISTINCT distrito_id) as distritos
        FROM dim_barrios
    """)
    row = cursor.fetchone()
    
    # Sources
    cursor.execute("SELECT DISTINCT source_dataset FROM dim_barrios WHERE source_dataset IS NOT NULL")
    sources = [r["source_dataset"] for r in cursor.fetchall()]
    
    return {
        "total_barrios": total,
        "with_geometry": row["with_geometry"],
        "geometry_coverage_pct": round(100 * row["with_geometry"] / total, 1) if total > 0 else 0,
        "total_distritos": row["distritos"],
        "sources": sources
    }


def analyze_fact_precios(conn: sqlite3.Connection) -> Dict:
    """Analyze price data coverage."""
    cursor = conn.cursor()
    
    # Year coverage
    cursor.execute("""
        SELECT 
            MIN(anio) as min_year,
            MAX(anio) as max_year,
            COUNT(DISTINCT anio) as years_count,
            COUNT(*) as total_records,
            COUNT(DISTINCT barrio_id) as barrios_count
        FROM fact_precios
    """)
    row = cursor.fetchone()
    
    # Records per year
    cursor.execute("""
        SELECT 
            anio,
            COUNT(*) as records,
            COUNT(DISTINCT barrio_id) as barrios,
            COUNT(DISTINCT dataset_id) as datasets,
            SUM(CASE WHEN precio_m2_venta IS NOT NULL THEN 1 ELSE 0 END) as with_venta,
            SUM(CASE WHEN precio_mes_alquiler IS NOT NULL THEN 1 ELSE 0 END) as with_alquiler
        FROM fact_precios
        GROUP BY anio
        ORDER BY anio
    """)
    years_data = [dict(r) for r in cursor.fetchall()]
    
    # Sources
    cursor.execute("SELECT DISTINCT source FROM fact_precios WHERE source IS NOT NULL")
    sources = [r["source"] for r in cursor.fetchall()]
    
    # Dataset IDs
    cursor.execute("""
        SELECT dataset_id, COUNT(*) as count 
        FROM fact_precios 
        WHERE dataset_id IS NOT NULL 
        GROUP BY dataset_id 
        ORDER BY count DESC
    """)
    datasets = [{"id": r["dataset_id"], "records": r["count"]} for r in cursor.fetchall()]
    
    return {
        "year_range": f"{row['min_year']}-{row['max_year']}" if row["min_year"] else "No data",
        "years_count": row["years_count"],
        "total_records": row["total_records"],
        "barrios_count": row["barrios_count"],
        "years_detail": years_data,
        "sources": sources,
        "datasets": datasets[:10]  # Top 10
    }


def analyze_fact_demografia(conn: sqlite3.Connection) -> Dict:
    """Analyze standard demographics coverage."""
    cursor = conn.cursor()
    
    # Year coverage
    cursor.execute("""
        SELECT 
            MIN(anio) as min_year,
            MAX(anio) as max_year,
            COUNT(DISTINCT anio) as years_count,
            COUNT(*) as total_records,
            COUNT(DISTINCT barrio_id) as barrios_count
        FROM fact_demografia
    """)
    row = cursor.fetchone()
    
    # Records per year
    cursor.execute("""
        SELECT 
            anio,
            COUNT(*) as records,
            COUNT(DISTINCT barrio_id) as barrios,
            SUM(CASE WHEN poblacion_total IS NOT NULL THEN 1 ELSE 0 END) as with_poblacion,
            SUM(CASE WHEN densidad_hab_km2 IS NOT NULL THEN 1 ELSE 0 END) as with_densidad
        FROM fact_demografia
        GROUP BY anio
        ORDER BY anio
    """)
    years_data = [dict(r) for r in cursor.fetchall()]
    
    return {
        "year_range": f"{row['min_year']}-{row['max_year']}" if row["min_year"] else "No data",
        "years_count": row["years_count"],
        "total_records": row["total_records"],
        "barrios_count": row["barrios_count"],
        "years_detail": years_data
    }


def analyze_fact_demografia_ampliada(conn: sqlite3.Connection) -> Dict:
    """Analyze detailed demographics coverage."""
    cursor = conn.cursor()
    
    # Check if table has data
    cursor.execute("SELECT COUNT(*) as total FROM fact_demografia_ampliada")
    total = cursor.fetchone()["total"]
    
    if total == 0:
        return {"status": "NO DATA", "total_records": 0}
    
    # Year coverage
    cursor.execute("""
        SELECT 
            MIN(anio) as min_year,
            MAX(anio) as max_year,
            COUNT(DISTINCT anio) as years_count,
            COUNT(*) as total_records,
            COUNT(DISTINCT barrio_id) as barrios_count
        FROM fact_demografia_ampliada
    """)
    row = cursor.fetchone()
    
    # Dimensions
    cursor.execute("""
        SELECT 
            COUNT(DISTINCT sexo) as sexos,
            COUNT(DISTINCT grupo_edad) as grupos_edad,
            COUNT(DISTINCT nacionalidad) as nacionalidades
        FROM fact_demografia_ampliada
    """)
    dims = cursor.fetchone()
    
    return {
        "year_range": f"{row['min_year']}-{row['max_year']}",
        "years_count": row["years_count"],
        "total_records": row["total_records"],
        "barrios_count": row["barrios_count"],
        "dimensions": {
            "sexos": dims["sexos"],
            "grupos_edad": dims["grupos_edad"],
            "nacionalidades": dims["nacionalidades"]
        }
    }


def analyze_fact_renta(conn: sqlite3.Connection) -> Dict:
    """Analyze income data coverage."""
    cursor = conn.cursor()
    
    # Check if table has data
    cursor.execute("SELECT COUNT(*) as total FROM fact_renta")
    total = cursor.fetchone()["total"]
    
    if total == 0:
        return {"status": "NO DATA", "total_records": 0}
    
    # Year coverage
    cursor.execute("""
        SELECT 
            MIN(anio) as min_year,
            MAX(anio) as max_year,
            COUNT(DISTINCT anio) as years_count,
            COUNT(*) as total_records,
            COUNT(DISTINCT barrio_id) as barrios_count
        FROM fact_renta
    """)
    row = cursor.fetchone()
    
    # Records per year
    cursor.execute("""
        SELECT 
            anio,
            COUNT(*) as records,
            COUNT(DISTINCT barrio_id) as barrios,
            ROUND(AVG(renta_euros), 0) as avg_renta
        FROM fact_renta
        GROUP BY anio
        ORDER BY anio
    """)
    years_data = [dict(r) for r in cursor.fetchall()]
    
    # Check for critical 2022 data (hardcoded in app)
    cursor.execute("SELECT COUNT(*) as count FROM fact_renta WHERE anio = 2022")
    has_2022 = cursor.fetchone()["count"] > 0
    
    return {
        "year_range": f"{row['min_year']}-{row['max_year']}",
        "years_count": row["years_count"],
        "total_records": row["total_records"],
        "barrios_count": row["barrios_count"],
        "years_detail": years_data,
        "has_2022_data": has_2022,
        "warning": "⚠️  Missing 2022 data (required for affordability calculations)" if not has_2022 else None
    }


def analyze_fact_oferta_idealista(conn: sqlite3.Connection) -> Dict:
    """Analyze Idealista offer data coverage."""
    cursor = conn.cursor()
    
    # Check if table has data
    cursor.execute("SELECT COUNT(*) as total FROM fact_oferta_idealista")
    total = cursor.fetchone()["total"]
    
    if total == 0:
        return {"status": "NO DATA", "total_records": 0}
    
    # Coverage
    cursor.execute("""
        SELECT 
            MIN(anio) as min_year,
            MAX(anio) as max_year,
            MIN(mes) as min_month,
            MAX(mes) as max_month,
            COUNT(DISTINCT operacion) as operaciones,
            COUNT(*) as total_records
        FROM fact_oferta_idealista
    """)
    row = cursor.fetchone()
    
    # Per operation
    cursor.execute("""
        SELECT 
            operacion,
            COUNT(*) as records,
            COUNT(DISTINCT barrio_id) as barrios
        FROM fact_oferta_idealista
        GROUP BY operacion
    """)
    operations = [dict(r) for r in cursor.fetchall()]
    
    return {
        "year_range": f"{row['min_year']}-{row['max_year']}",
        "total_records": row["total_records"],
        "operations": operations
    }


def print_report(data: Dict) -> None:
    """Print formatted report."""
    print("\\n" + "="*80)
    print("📊 BARCELONA HOUSING DATABASE - DATA AVAILABILITY AUDIT")
    print("="*80)
    
    # Dimension
    print("\\n📍 DIM_BARRIOS (Neighborhoods Dimension)")
    print("-" * 80)
    d = data["dim_barrios"]
    print(f"   Total Barrios:        {d['total_barrios']}")
    print(f"   With Geometry:        {d['with_geometry']} ({d['geometry_coverage_pct']}%)")
    print(f"   Total Distritos:      {d['total_distritos']}")
    print(f"   Sources:              {', '.join(d['sources']) if d['sources'] else 'N/A'}")
    
    # Prices
    print("\\n💰 FACT_PRECIOS (Housing Prices)")
    print("-" * 80)
    p = data["fact_precios"]
    if p["total_records"] > 0:
        print(f"   Year Range:           {p['year_range']}")
        print(f"   Years with Data:      {p['years_count']}")
        print(f"   Total Records:        {p['total_records']:,}")
        print(f"   Barrios Covered:      {p['barrios_count']}")
        print(f"   Sources:              {', '.join(p['sources'])}")
        print(f"   Datasets:             {len(p['datasets'])} unique")
        print(f"\\n   📅 Records per Year:")
        for year in p["years_detail"]:
            print(f"      {year['anio']}: {year['records']:>4} records | "
                  f"{year['barrios']:>2} barrios | {year['datasets']:>2} datasets | "
                  f"Venta: {year['with_venta']:>3} | Alquiler: {year['with_alquiler']:>3}")
    else:
        print("   ❌ NO DATA")
    
    # Demographics standard
    print("\\n👥 FACT_DEMOGRAFIA (Standard Demographics)")
    print("-" * 80)
    d = data["fact_demografia"]
    if d["total_records"] > 0:
        print(f"   Year Range:           {d['year_range']}")
        print(f"   Years with Data:      {d['years_count']}")
        print(f"   Total Records:        {d['total_records']:,}")
        print(f"   Barrios Covered:      {d['barrios_count']}")
        print(f"\\n   📅 Records per Year:")
        for year in d["years_detail"]:
            print(f"      {year['anio']}: {year['records']:>2} records | "
                  f"{year['barrios']:>2} barrios | "
                  f"Población: {year['with_poblacion']:>2} | Densidad: {year['with_densidad']:>2}")
    else:
        print("   ❌ NO DATA")
    
    # Demographics detailed
    print("\\n👨‍👩‍👧‍👦 FACT_DEMOGRAFIA_AMPLIADA (Detailed Demographics)")
    print("-" * 80)
    da = data["fact_demografia_ampliada"]
    if da.get("status") == "NO DATA":
        print("   ❌ NO DATA")
    else:
        print(f"   Year Range:           {da['year_range']}")
        print(f"   Years with Data:      {da['years_count']}")
        print(f"   Total Records:        {da['total_records']:,}")
        print(f"   Barrios Covered:      {da['barrios_count']}")
        print(f"   Dimensions:")
        print(f"      Sexos:             {da['dimensions']['sexos']}")
        print(f"      Grupos Edad:       {da['dimensions']['grupos_edad']}")
        print(f"      Nacionalidades:    {da['dimensions']['nacionalidades']}")
    
    # Income
    print("\\n💶 FACT_RENTA (Income Data)")
    print("-" * 80)
    r = data["fact_renta"]
    if r.get("status") == "NO DATA":
        print("   ❌ NO DATA")
    else:
        print(f"   Year Range:           {r['year_range']}")
        print(f"   Years with Data:      {r['years_count']}")
        print(f"   Total Records:        {r['total_records']:,}")
        print(f"   Barrios Covered:      {r['barrios_count']}")
        print(f"   2022 Data (Critical): {'✅ YES' if r['has_2022_data'] else '❌ NO'}")
        if r.get("warning"):
            print(f"   {r['warning']}")
        print(f"\\n   📅 Average Rent per Year:")
        for year in r.get("years_detail", []):
            print(f"      {year['anio']}: {year['barrios']:>2} barrios | "
                  f"Avg Renta: €{year['avg_renta']:,.0f}")
    
    # Idealista
    print("\\n🏠 FACT_OFERTA_IDEALISTA (Idealista Listings)")
    print("-" * 80)
    i = data["fact_oferta_idealista"]
    if i.get("status") == "NO DATA":
        print("   ❌ NO DATA")
    else:
        print(f"   Year Range:           {i['year_range']}")
        print(f"   Total Records:        {i['total_records']:,}")
        print(f"   Operations:")
        for op in i["operations"]:
            print(f"      {op['operacion']:>10}: {op['records']:>4} records | {op['barrios']:>2} barrios")
    
    # Summary
    print("\\n" + "="*80)
    print("📋 SUMMARY & RECOMMENDATIONS")
    print("="*80)
    
    critical_issues = []
    warnings = []
    
    # Check critical data
    if data["dim_barrios"]["total_barrios"] < 73:
        critical_issues.append(f"❌ Missing barrios: {73 - data['dim_barrios']['total_barrios']} (expected 73)")
    
    if data["dim_barrios"]["geometry_coverage_pct"] < 95:
        warnings.append(f"⚠️  Low geometry coverage: {data['dim_barrios']['geometry_coverage_pct']}% (target: ≥95%)")
    
    if data["fact_precios"]["total_records"] == 0:
        critical_issues.append("❌ No price data available")
    
    if data["fact_renta"].get("status") == "NO DATA" or not data["fact_renta"].get("has_2022_data", False):
        critical_issues.append("❌ Missing 2022 income data (CRITICAL for dashboard affordability calculations)")
    else:
        # Sanity check for income values
        avg_renta = data["fact_renta"]["years_detail"][0]["avg_renta"]
        if avg_renta < 5000 or avg_renta > 100000:
            warnings.append(f"⚠️  Suspicious average income: €{avg_renta:,.0f} (Expected range: €5k-€100k)")
    
    if data["fact_demografia"]["total_records"] == 0:
        critical_issues.append("❌ No demographic data available")
    
    if critical_issues:
        print("\\n🚨 CRITICAL ISSUES:")
        for issue in critical_issues:
            print(f"   {issue}")
    
    if warnings:
        print("\\n⚠️  WARNINGS:")
        for warning in warnings:
            print(f"   {warning}")
    
    if not critical_issues and not warnings:
        print("\\n✅ All critical data requirements are met!")
    
    print("\\n" + "="*80 + "\\n")
    
    # Return status code for CI
    return 1 if critical_issues else 0


def export_json(data: Dict, output_path: Path) -> None:
    """Export audit results to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\\n📄 Audit results exported to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Audit data availability in Barcelona Housing database"
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=Path("data/processed/database.db"),
        help="Path to SQLite database (default: data/processed/database.db)"
    )
    parser.add_argument(
        "--export-json",
        type=Path,
        help="Export results to JSON file"
    )
    
    args = parser.parse_args()
    
    # Connect to database
    conn = get_db_connection(args.db_path)
    
    # Analyze all tables
    data = {
        "audit_date": "2025-12-06",
        "database_path": str(args.db_path),
        "dim_barrios": analyze_dim_barrios(conn),
        "fact_precios": analyze_fact_precios(conn),
        "fact_demografia": analyze_fact_demografia(conn),
        "fact_demografia_ampliada": analyze_fact_demografia_ampliada(conn),
        "fact_renta": analyze_fact_renta(conn),
        "fact_oferta_idealista": analyze_fact_oferta_idealista(conn)
    }
    
    conn.close()
    
    # Print report
    exit_code = print_report(data)
    
    # Export if requested
    if args.export_json:
        export_json(data, args.export_json)
        
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
