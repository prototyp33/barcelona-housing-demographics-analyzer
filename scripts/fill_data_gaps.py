#!/usr/bin/env python3
"""
Fill data gaps using interpolation for small gaps (1-2 years).

This script identifies missing years and fills them using linear interpolation
when gaps are small and reasonable. Larger gaps are documented but not filled.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import os
from dotenv import load_dotenv
import psycopg2

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "database": os.getenv("POSTGRES_DATABASE", "barcelona_housing"),
    "user": os.getenv("POSTGRES_USER", os.getenv("USER", "postgres")),
    "password": os.getenv("POSTGRES_PASSWORD", ""),
    "port": int(os.getenv("POSTGRES_PORT", "5432"))
}


def get_connection():
    """Get PostgreSQL connection."""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Error connecting to PostgreSQL: {e}")
        raise


def identify_gaps(conn) -> pd.DataFrame:
    """
    Identify gaps in price data for all barrios.
    
    Returns:
        DataFrame with gap information
    """
    query = """
        WITH años_totales AS (
            SELECT DISTINCT anio 
            FROM fact_precios 
            WHERE precio_m2_venta IS NOT NULL
            ORDER BY anio
        ),
        barrios_con_años AS (
            SELECT 
                b.barrio_id,
                b.barrio_nombre,
                p.anio,
                AVG(p.precio_m2_venta) as precio_promedio
            FROM dim_barrios b
            INNER JOIN fact_precios p ON b.barrio_id = p.barrio_id
            WHERE p.precio_m2_venta IS NOT NULL
            GROUP BY b.barrio_id, b.barrio_nombre, p.anio
        ),
        barrios_list AS (
            SELECT DISTINCT barrio_id, barrio_nombre FROM barrios_con_años
        ),
        gaps AS (
            SELECT 
                bl.barrio_id,
                bl.barrio_nombre,
                at.anio as año_faltante
            FROM años_totales at
            CROSS JOIN barrios_list bl
            LEFT JOIN barrios_con_años bca ON at.anio = bca.anio AND bl.barrio_id = bca.barrio_id
            WHERE bca.anio IS NULL
        )
        SELECT 
            g.barrio_id,
            g.barrio_nombre,
            g.año_faltante,
            MAX(bca.anio) FILTER (WHERE bca.anio < g.año_faltante) as año_anterior,
            MIN(bca.anio) FILTER (WHERE bca.anio > g.año_faltante) as año_siguiente,
            MAX(bca.precio_promedio) FILTER (WHERE bca.anio < g.año_faltante) as precio_anterior,
            MIN(bca.precio_promedio) FILTER (WHERE bca.anio > g.año_faltante) as precio_siguiente
        FROM gaps g
        LEFT JOIN barrios_con_años bca ON g.barrio_id = bca.barrio_id
        GROUP BY g.barrio_id, g.barrio_nombre, g.año_faltante
        ORDER BY g.barrio_nombre, g.año_faltante
    """
    
    df = pd.read_sql_query(query, conn)
    
    # Calculate gap size
    df['tamaño_gap'] = df.apply(
        lambda row: (
            row['año_siguiente'] - row['año_anterior'] - 1
            if pd.notna(row['año_anterior']) and pd.notna(row['año_siguiente'])
            else 999
        ),
        axis=1
    )
    
    return df


def interpolate_price(year: int, year_before: int, year_after: int,
                      price_before: float, price_after: float) -> float:
    """
    Linear interpolation for price between two years.
    
    Args:
        year: Year to interpolate
        year_before: Previous year with data
        year_after: Next year with data
        price_before: Price in previous year
        price_after: Price in next year
    
    Returns:
        Interpolated price
    """
    if year_before is None or year_after is None:
        return None
    
    if price_before is None or price_after is None:
        return None
    
    # Linear interpolation
    total_years = year_after - year_before
    years_to_interpolate = year - year_before
    
    if total_years == 0:
        return price_before
    
    weight = years_to_interpolate / total_years
    interpolated = price_before + (price_after - price_before) * weight
    
    return interpolated


def fill_gaps_with_interpolation(conn, max_gap_size: int = 2) -> pd.DataFrame:
    """
    Fill gaps using interpolation for gaps <= max_gap_size.
    
    Args:
        conn: Database connection
        max_gap_size: Maximum gap size to fill (default: 2 years)
    
    Returns:
        DataFrame with interpolated values
    """
    gaps_df = identify_gaps(conn)
    
    if len(gaps_df) == 0:
        print("✅ No se encontraron gaps")
        return pd.DataFrame()
    
    # Filter gaps that can be interpolated
    interpolatable = gaps_df[
        (gaps_df['año_anterior'].notna()) & 
        (gaps_df['año_siguiente'].notna()) &
        (gaps_df['tamaño_gap'] <= max_gap_size)
    ].copy()
    
    if len(interpolatable) == 0:
        print("⚠️ No hay gaps interpolables")
        return pd.DataFrame()
    
    # Calculate interpolated prices
    interpolated_values = []
    
    for idx, row in interpolatable.iterrows():
        price = interpolate_price(
            row['año_faltante'],
            int(row['año_anterior']),
            int(row['año_siguiente']),
            row['precio_anterior'],
            row['precio_siguiente']
        )
        
        if price is not None and price > 0:
            interpolated_values.append({
                'barrio_id': row['barrio_id'],
                'barrio_nombre': row['barrio_nombre'],
                'anio': row['año_faltante'],
                'precio_m2_venta_interpolado': price,
                'año_anterior': int(row['año_anterior']),
                'año_siguiente': int(row['año_siguiente']),
                'precio_anterior': row['precio_anterior'],
                'precio_siguiente': row['precio_siguiente'],
                'es_interpolado': True
            })
    
    return pd.DataFrame(interpolated_values)


def generate_gap_report(conn) -> Dict:
    """
    Generate comprehensive gap report.
    
    Returns:
        Dictionary with gap statistics
    """
    gaps_df = identify_gaps(conn)
    
    if len(gaps_df) == 0:
        return {
            'total_gaps': 0,
            'interpolatable': 0,
            'too_large': 0,
            'barrios_affected': 0
        }
    
    # Categorize gaps
    interpolatable = gaps_df[
        (gaps_df['año_anterior'].notna()) & 
        (gaps_df['año_siguiente'].notna()) &
        (gaps_df['tamaño_gap'] <= 2)
    ]
    
    too_large = gaps_df[
        (gaps_df['año_anterior'].notna()) & 
        (gaps_df['año_siguiente'].notna()) &
        (gaps_df['tamaño_gap'] > 2)
    ]
    
    edge_gaps = gaps_df[
        (gaps_df['año_anterior'].isna()) | (gaps_df['año_siguiente'].isna())
    ]
    
    return {
        'total_gaps': len(gaps_df),
        'interpolatable': len(interpolatable),
        'too_large': len(too_large),
        'edge_gaps': len(edge_gaps),
        'barrios_affected': gaps_df['barrio_id'].nunique(),
        'gaps_by_barrio': gaps_df.groupby('barrio_nombre').size().to_dict(),
        'interpolatable_details': interpolatable.to_dict('records') if len(interpolatable) > 0 else [],
        'too_large_details': too_large.to_dict('records') if len(too_large) > 0 else []
    }


def main():
    """Main function."""
    print("=" * 80)
    print("COMPLETAR LAGUNAS DE DATOS CON INTERPOLACIÓN")
    print("=" * 80)
    
    # Connect to database
    try:
        conn = get_connection()
        print("✅ Conectado a PostgreSQL\n")
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return 1
    
    # Generate gap report
    print("📊 Analizando lagunas de datos...")
    report = generate_gap_report(conn)
    
    print(f"\n📈 Resumen de lagunas:")
    print(f"   Total de gaps: {report['total_gaps']}")
    print(f"   Gaps interpolables (≤2 años): {report['interpolatable']}")
    print(f"   Gaps muy grandes (>2 años): {report['too_large']}")
    print(f"   Gaps en bordes (inicio/fin): {report['edge_gaps']}")
    print(f"   Barrios afectados: {report['barrios_affected']}")
    
    if report['barrios_affected'] > 0:
        print(f"\n📋 Barrios con más gaps:")
        sorted_gaps = sorted(
            report['gaps_by_barrio'].items(),
            key=lambda x: x[1],
            reverse=True
        )
        for barrio, count in sorted_gaps[:10]:
            print(f"   • {barrio}: {count} años faltantes")
    
    # Fill interpolatable gaps
    if report['interpolatable'] > 0:
        print(f"\n🔧 Interpolando {report['interpolatable']} gaps...")
        interpolated = fill_gaps_with_interpolation(conn, max_gap_size=2)
        
        if len(interpolated) > 0:
            print(f"\n✅ Valores interpolados generados: {len(interpolated)}")
            
            # Show sample
            print(f"\n📊 Muestra de valores interpolados:")
            for idx, row in interpolated.head(5).iterrows():
                print(f"   • {row['barrio_nombre']} ({row['anio']}): "
                      f"{row['precio_m2_venta_interpolado']:,.0f} €/m² "
                      f"(entre {row['año_anterior']} y {row['año_siguiente']})")
            
            # Export interpolated values
            output_path = PROJECT_ROOT / "data" / "exports" / "anomalies" / "interpolated_prices.csv"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            interpolated.to_csv(output_path, index=False, encoding='utf-8', lineterminator='\n')
            print(f"\n✅ Valores interpolados exportados: {output_path}")
            
            # Update interpolatable_details with interpolated prices
            interpolated_dict = interpolated.set_index(['barrio_nombre', 'anio'])['precio_m2_venta_interpolado'].to_dict()
            for detail in report['interpolatable_details']:
                key = (detail['barrio_nombre'], detail['año_faltante'])
                if key in interpolated_dict:
                    detail['precio_m2_venta_interpolado'] = interpolated_dict[key]
            
            # Generate report
            report_path = PROJECT_ROOT / "data" / "exports" / "anomalies" / "gap_filling_report.md"
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("# Reporte de Completado de Lagunas\n\n")
                f.write(f"**Fecha**: {pd.Timestamp.now().strftime('%Y-%m-%d')}\n\n")
                f.write(f"## Resumen\n\n")
                f.write(f"- **Total de gaps**: {report['total_gaps']}\n")
                f.write(f"- **Gaps interpolados**: {report['interpolatable']}\n")
                f.write(f"- **Gaps muy grandes**: {report['too_large']}\n")
                f.write(f"- **Gaps en bordes**: {report['edge_gaps']}\n\n")
                
                if report['interpolatable_details']:
                    f.write("## Valores Interpolados\n\n")
                    f.write("| Barrio | Año | Precio Interpolado | Año Anterior | Año Siguiente |\n")
                    f.write("|--------|-----|-------------------|--------------|---------------|\n")
                    for detail in report['interpolatable_details']:
                        precio = detail.get('precio_m2_venta_interpolado', 'N/A')
                        if isinstance(precio, (int, float)):
                            precio_str = f"{precio:,.0f} €/m²"
                        else:
                            precio_str = str(precio)
                        f.write(f"| {detail['barrio_nombre']} | {detail['año_faltante']} | "
                               f"{precio_str} | "
                               f"{detail['año_anterior']} | {detail['año_siguiente']} |\n")
                    f.write("\n")
                
                if report['too_large_details']:
                    f.write("## Gaps Muy Grandes (No Interpolados)\n\n")
                    f.write("Estos gaps son demasiado grandes para interpolación segura:\n\n")
                    for detail in report['too_large_details'][:10]:
                        f.write(f"- **{detail['barrio_nombre']}**: Falta año {detail['año_faltante']} "
                               f"(gap de {detail['tamaño_gap']} años)\n")
            
            print(f"✅ Reporte generado: {report_path}")
        else:
            print("⚠️ No se generaron valores interpolados")
    else:
        print("\n✅ No hay gaps interpolables")
    
    # Document gaps that cannot be filled
    if report['too_large'] > 0 or report['edge_gaps'] > 0:
        print(f"\n⚠️ Gaps que no pueden completarse:")
        print(f"   • Gaps muy grandes: {report['too_large']}")
        print(f"   • Gaps en bordes: {report['edge_gaps']}")
        print(f"   Estos requieren datos fuente adicionales")
    
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
