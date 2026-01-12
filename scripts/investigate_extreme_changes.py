#!/usr/bin/env python3
"""
Investigate extreme changes (>100%) in price data.

This script analyzes the source data for barrios with extreme year-over-year
changes to determine if they are data errors or real market changes.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
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


def investigate_barrio_extreme_change(conn, barrio_nombre: str, year: int, 
                                     change_pct: float) -> Dict:
    """
    Investigate extreme change for a specific barrio and year.
    
    Args:
        conn: Database connection
        barrio_nombre: Name of the barrio
        year: Year of the extreme change
        change_pct: Percentage change detected
    
    Returns:
        Dictionary with investigation results
    """
    # Get barrio_id
    cursor = conn.cursor()
    cursor.execute("""
        SELECT barrio_id FROM dim_barrios 
        WHERE barrio_nombre LIKE %s
    """, (f"%{barrio_nombre}%",))
    result = cursor.fetchone()
    if not result:
        return {"error": f"Barrio not found: {barrio_nombre}"}
    
    barrio_id = result[0]
    
    # Get detailed data for the year and surrounding years
    query = """
        SELECT 
            p.anio,
            p.trimestre,
            p.precio_m2_venta,
            p.precio_mes_alquiler,
            p.source,
            p.dataset_id,
            COUNT(*) OVER (PARTITION BY p.anio) as registros_por_anio
        FROM fact_precios p
        WHERE p.barrio_id = %s
          AND p.anio BETWEEN %s AND %s
          AND (p.precio_m2_venta IS NOT NULL OR p.precio_mes_alquiler IS NOT NULL)
        ORDER BY p.anio, p.trimestre
    """
    
    df = pd.read_sql_query(query, conn, params=(barrio_id, year - 1, year + 1))
    
    if len(df) == 0:
        return {"error": "No data found"}
    
    # Aggregate by year
    agg_dict = {
        'precio_m2_venta': ['count', 'min', 'max', 'mean', 'std'],
        'precio_mes_alquiler': ['count', 'min', 'max', 'mean', 'std']
    }
    
    # Add source and dataset_id if they exist
    if 'source' in df.columns:
        agg_dict['source'] = lambda x: ', '.join(x.dropna().unique())
    if 'dataset_id' in df.columns:
        agg_dict['dataset_id'] = lambda x: ', '.join(map(str, x.dropna().unique()))
    
    yearly_stats = df.groupby('anio').agg(agg_dict).reset_index()
    
    # Flatten column names
    new_columns = []
    for col in yearly_stats.columns:
        if col == 'anio':
            new_columns.append('anio')
        elif isinstance(col, tuple):
            new_columns.append('_'.join(str(c) for c in col if c).strip('_'))
        else:
            new_columns.append(str(col))
    yearly_stats.columns = new_columns
    
    # Calculate year-over-year changes
    yearly_stats = yearly_stats.sort_values('anio')
    yearly_stats['precio_change_pct'] = yearly_stats['precio_m2_venta_mean'].pct_change() * 100
    yearly_stats['alquiler_change_pct'] = yearly_stats['precio_mes_alquiler_mean'].pct_change() * 100
    
    # Identify the extreme change
    extreme_year = yearly_stats[yearly_stats['anio'] == year]
    
    result = {
        'barrio_nombre': barrio_nombre,
        'barrio_id': barrio_id,
        'extreme_year': year,
        'detected_change_pct': change_pct,
        'yearly_stats': yearly_stats.to_dict('records'),
        'raw_data_count': len(df),
        'sources': df['source'].unique().tolist(),
        'datasets': df['dataset_id'].dropna().unique().tolist()
    }
    
    # Analysis flags
    if len(yearly_stats) >= 2:
        prev_year = yearly_stats[yearly_stats['anio'] == year - 1]
        if len(prev_year) > 0:
            result['previous_year_mean'] = prev_year['precio_m2_venta_mean'].iloc[0]
            result['extreme_year_mean'] = extreme_year['precio_m2_venta_mean'].iloc[0] if len(extreme_year) > 0 else None
            result['calculated_change_pct'] = (
                (result['extreme_year_mean'] - result['previous_year_mean']) / 
                result['previous_year_mean'] * 100
            ) if result['extreme_year_mean'] and result['previous_year_mean'] else None
    
    # Check for data quality issues
    result['quality_flags'] = []
    
    # Multiple sources in same year?
    sources_by_year = df.groupby('anio')['source'].nunique()
    if year in sources_by_year.index and sources_by_year[year] > 1:
        result['quality_flags'].append(f"Múltiples fuentes en {year}: {sources_by_year[year]}")
    
    # High variance?
    if len(extreme_year) > 0:
        stddev = extreme_year['precio_m2_venta_std'].iloc[0]
        mean = extreme_year['precio_m2_venta_mean'].iloc[0]
        if pd.notna(stddev) and pd.notna(mean) and mean > 0:
            cv = (stddev / mean) * 100
            if cv > 50:
                result['quality_flags'].append(f"Alta variabilidad en {year}: CV={cv:.1f}%")
    
    # Few records?
    if len(extreme_year) > 0:
        count = extreme_year['precio_m2_venta_count'].iloc[0]
        if count < 3:
            result['quality_flags'].append(f"Pocos registros en {year}: {count}")
    
    return result


def main():
    """Main investigation function."""
    print("=" * 80)
    print("INVESTIGACIÓN DE CAMBIOS EXTREMOS EN DATOS FUENTE")
    print("=" * 80)
    
    # Load extreme changes from CSV
    abrupt_changes_path = PROJECT_ROOT / "data" / "exports" / "anomalies" / "abrupt_changes_venta.csv"
    
    if not abrupt_changes_path.exists():
        print(f"❌ No se encontró: {abrupt_changes_path}")
        print("   Ejecuta primero: python scripts/investigate_data_anomalies.py")
        return 1
    
    abrupt_changes = pd.read_csv(abrupt_changes_path)
    
    # Find the column name for percentage change (could be cambio_porcentual or cambio_porcentual)
    change_col = None
    for col in abrupt_changes.columns:
        if 'cambio' in col.lower() and 'pct' in col.lower():
            change_col = col
            break
        elif 'change' in col.lower() and 'pct' in col.lower():
            change_col = col
            break
    
    if change_col is None:
        # Try to find any numeric column that might represent change
        numeric_cols = abrupt_changes.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            # Look for column with 'change' or 'cambio' in name
            for col in numeric_cols:
                if 'change' in col.lower() or 'cambio' in col.lower():
                    change_col = col
                    break
    
    if change_col is None:
        print("❌ No se encontró columna de cambio porcentual")
        print(f"   Columnas disponibles: {abrupt_changes.columns.tolist()}")
        return 1
    
    extreme_changes = abrupt_changes[abrupt_changes[change_col].abs() > 100].copy()
    
    print(f"\n📊 Cambios extremos detectados: {len(extreme_changes)}")
    
    if len(extreme_changes) == 0:
        print("✅ No hay cambios extremos para investigar")
        return 0
    
    # Connect to database
    try:
        conn = get_connection()
        print("✅ Conectado a PostgreSQL")
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return 1
    
    # Investigate each extreme change
    investigations = []
    
    for idx, row in extreme_changes.iterrows():
        barrio = row['barrio_nombre']
        
        # Find year column (could be anio_final, anio, etc.)
        year_col = None
        for col in row.index:
            if 'anio' in col.lower() or 'year' in col.lower():
                if 'final' in col.lower() or col == 'anio':
                    year_col = col
                    break
        
        if year_col is None:
            print(f"⚠️ No se encontró columna de año para {barrio}")
            continue
        
        year = int(row[year_col])
        change = row[change_col]
        
        print(f"\n{'=' * 80}")
        print(f"Investigando: {barrio} ({year}) - Cambio: {change:+.1f}%")
        print(f"{'=' * 80}")
        
        investigation = investigate_barrio_extreme_change(conn, barrio, year, change)
        
        if 'error' in investigation:
            print(f"⚠️ {investigation['error']}")
            continue
        
        investigations.append(investigation)
        
        # Print findings
        print(f"\n📊 Estadísticas por año:")
        for year_stat in investigation['yearly_stats']:
            print(f"   Año {year_stat.get('anio', 'N/A'):.0f}:")
            print(f"      Registros: {year_stat.get('precio_m2_venta_count', 0):.0f}")
            if pd.notna(year_stat.get('precio_m2_venta_mean')):
                print(f"      Precio promedio: {year_stat['precio_m2_venta_mean']:,.0f} €/m²")
            if pd.notna(year_stat.get('precio_m2_venta_std')):
                print(f"      Desviación estándar: {year_stat['precio_m2_venta_std']:,.0f} €/m²")
            if 'source' in year_stat:
                print(f"      Fuentes: {year_stat['source']}")
            if pd.notna(year_stat.get('precio_change_pct')):
                print(f"      Cambio vs año anterior: {year_stat['precio_change_pct']:+.1f}%")
        
        if investigation['quality_flags']:
            print(f"\n⚠️ Flags de calidad:")
            for flag in investigation['quality_flags']:
                print(f"   • {flag}")
        
        # Assessment
        print(f"\n💡 Evaluación:")
        if len(investigation['quality_flags']) > 0:
            print(f"   🔴 POSIBLE ERROR DE DATOS")
            print(f"   Razones: {', '.join(investigation['quality_flags'])}")
        elif investigation.get('calculated_change_pct') and abs(investigation['calculated_change_pct']) > 150:
            print(f"   🟠 CAMBIO MUY EXTREMO - Requiere validación externa")
        else:
            print(f"   🟡 CAMBIO REAL POSIBLE - Verificar con datos externos")
    
    conn.close()
    
    # Export detailed investigations
    if investigations:
        import json
        output_path = PROJECT_ROOT / "data" / "exports" / "anomalies" / "extreme_changes_investigation.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(investigations, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n✅ Investigaciones detalladas exportadas: {output_path}")
        
        # Create summary report
        summary_path = PROJECT_ROOT / "data" / "exports" / "anomalies" / "extreme_changes_summary.md"
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("# Resumen de Investigación de Cambios Extremos\n\n")
            f.write(f"**Fecha**: {pd.Timestamp.now().strftime('%Y-%m-%d')}\n\n")
            f.write(f"**Total investigados**: {len(investigations)}\n\n")
            
            for inv in investigations:
                f.write(f"## {inv['barrio_nombre']} ({inv['extreme_year']})\n\n")
                f.write(f"- **Cambio detectado**: {inv['detected_change_pct']:+.1f}%\n")
                f.write(f"- **Registros analizados**: {inv['raw_data_count']}\n")
                f.write(f"- **Fuentes**: {', '.join(inv['sources'])}\n")
                
                if inv['quality_flags']:
                    f.write(f"- **⚠️ Flags de calidad**:\n")
                    for flag in inv['quality_flags']:
                        f.write(f"  - {flag}\n")
                
                f.write("\n")
        
        print(f"✅ Resumen exportado: {summary_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
