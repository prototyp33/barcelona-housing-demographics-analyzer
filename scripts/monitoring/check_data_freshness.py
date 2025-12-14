#!/usr/bin/env python3
"""
Script para verificar frescura de datos en PostgreSQL.

Verifica que los datos más recientes no sean más antiguos que un umbral especificado.
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    import psycopg2
    import pandas as pd
except ImportError:
    print("❌ Error: psycopg2-binary and pandas required")
    print("   Install: pip install psycopg2-binary pandas")
    sys.exit(1)


def check_data_freshness(database_url: str, threshold_days: int = 7):
    """
    Verifica frescura de datos en todas las tablas fact.
    
    Args:
        database_url: URL de conexión a PostgreSQL
        threshold_days: Número de días máximo desde última actualización
    """
    conn = psycopg2.connect(database_url)
    
    # Tablas a verificar
    fact_tables = [
        'fact_precios',
        'fact_demografia',
        'fact_demografia_ampliada',
        'fact_renta'
    ]
    
    results = []
    all_passed = True
    
    for table in fact_tables:
        try:
            # Obtener fecha más reciente
            query = f"""
                SELECT MAX(etl_loaded_at) as last_update
                FROM {table}
            """
            df = pd.read_sql_query(query, conn)
            
            if df['last_update'].iloc[0] is None:
                print(f"⚠️  {table}: No data found")
                results.append({
                    'table': table,
                    'status': 'no_data',
                    'last_update': None
                })
                continue
            
            last_update = pd.to_datetime(df['last_update'].iloc[0])
            days_old = (datetime.now() - last_update).days
            
            if days_old > threshold_days:
                print(f"❌ {table}: Data is {days_old} days old (threshold: {threshold_days})")
                all_passed = False
                results.append({
                    'table': table,
                    'status': 'stale',
                    'last_update': last_update.isoformat(),
                    'days_old': days_old
                })
            else:
                print(f"✅ {table}: Data is {days_old} days old (OK)")
                results.append({
                    'table': table,
                    'status': 'fresh',
                    'last_update': last_update.isoformat(),
                    'days_old': days_old
                })
        
        except Exception as e:
            print(f"❌ {table}: Error checking freshness - {e}")
            all_passed = False
            results.append({
                'table': table,
                'status': 'error',
                'error': str(e)
            })
    
    conn.close()
    
    # Resumen
    print("\n" + "="*50)
    print("Data Freshness Summary")
    print("="*50)
    for result in results:
        if result['status'] == 'fresh':
            print(f"✅ {result['table']}: {result['days_old']} days old")
        elif result['status'] == 'stale':
            print(f"❌ {result['table']}: {result['days_old']} days old (STALE)")
        elif result['status'] == 'no_data':
            print(f"⚠️  {result['table']}: No data")
        else:
            print(f"❌ {result['table']}: Error - {result.get('error', 'Unknown')}")
    
    return 0 if all_passed else 1


def main():
    parser = argparse.ArgumentParser(description='Check data freshness in PostgreSQL')
    parser.add_argument('--database-url', required=True, help='PostgreSQL connection URL')
    parser.add_argument('--threshold-days', type=int, default=7, help='Maximum days since last update')
    
    args = parser.parse_args()
    
    exit_code = check_data_freshness(args.database_url, args.threshold_days)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

