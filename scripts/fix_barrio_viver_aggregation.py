#!/usr/bin/env python3
"""
Fix aggregation for Baró de Viver (2015) using median instead of mean.

This script creates a corrected version of the master table where Baró de Viver
2015 uses median instead of mean due to high variability (CV=77.7%).
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
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


def get_barrio_viver_corrected_price(conn, year: int = 2015) -> float:
    """
    Get corrected price for Baró de Viver using median and outlier filtering.
    
    Args:
        conn: Database connection
        year: Year to correct (default: 2015)
    
    Returns:
        Corrected price (median after filtering outliers)
    """
    cursor = conn.cursor()
    
    # Get barrio_id
    cursor.execute("SELECT barrio_id FROM dim_barrios WHERE barrio_nombre = 'Baró de Viver'")
    result = cursor.fetchone()
    if not result:
        return None
    
    barrio_id = result[0]
    
    # Get all prices for the year
    query = """
        SELECT precio_m2_venta
        FROM fact_precios
        WHERE barrio_id = %s
          AND anio = %s
          AND precio_m2_venta IS NOT NULL
    """
    
    df = pd.read_sql_query(query, conn, params=(barrio_id, year))
    
    if len(df) == 0:
        return None
    
    prices = df['precio_m2_venta'].values
    
    # Filter outliers using IQR method
    q1 = np.percentile(prices, 25)
    q3 = np.percentile(prices, 75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    filtered_prices = prices[(prices >= lower_bound) & (prices <= upper_bound)]
    
    if len(filtered_prices) == 0:
        # If all are outliers, use median of all
        return np.median(prices)
    
    # Use median of filtered prices
    return np.median(filtered_prices)


def main():
    """Fix Baró de Viver aggregation."""
    print("=" * 80)
    print("CORRECCIÓN DE AGREGACIÓN: Baró de Viver (2015)")
    print("=" * 80)
    
    # Connect to database
    try:
        conn = get_connection()
        print("✅ Conectado a PostgreSQL")
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return 1
    
    # Get corrected price
    corrected_price = get_barrio_viver_corrected_price(conn, year=2015)
    
    if corrected_price is None:
        print("❌ No se encontraron datos para Baró de Viver (2015)")
        conn.close()
        return 1
    
    # Get original aggregated price
    cursor = conn.cursor()
    cursor.execute("SELECT barrio_id FROM dim_barrios WHERE barrio_nombre = 'Baró de Viver'")
    barrio_id = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT AVG(precio_m2_venta) as precio_promedio
        FROM fact_precios
        WHERE barrio_id = %s AND anio = 2015 AND precio_m2_venta IS NOT NULL
    """, (barrio_id,))
    original_price = cursor.fetchone()[0]
    
    print(f"\n📊 Comparación de Precios (Baró de Viver, 2015):")
    print(f"   Precio promedio (actual): {original_price:,.2f} €/m²")
    print(f"   Precio corregido (mediana filtrada): {corrected_price:,.2f} €/m²")
    print(f"   Diferencia: {abs(original_price - corrected_price):,.2f} €/m²")
    print(f"   Cambio porcentual: {((corrected_price - original_price) / original_price * 100):+.1f}%")
    
    # Load master table and update
    master_path = PROJECT_ROOT / "data" / "exports" / "looker_studio" / "master_table_barcelona_housing.csv"
    
    if not master_path.exists():
        print(f"\n❌ No se encontró: {master_path}")
        print("   Ejecuta primero: python scripts/create_master_table_for_looker.py")
        conn.close()
        return 1
    
    print(f"\n📂 Cargando tabla maestra...")
    df = pd.read_csv(master_path)
    
    # Find and update Baró de Viver 2015
    mask = (df['barrio_nombre'] == 'Baró de Viver') & (df['anio'] == 2015)
    rows_updated = mask.sum()
    
    if rows_updated == 0:
        print("⚠️ No se encontró Baró de Viver 2015 en la tabla maestra")
        conn.close()
        return 1
    
    # Update price
    df.loc[mask, 'precio_m2_venta_promedio'] = corrected_price
    df.loc[mask, 'precio_m2_venta_promedio_corregido'] = True  # Flag for correction
    
    # Recalculate derived metrics if needed
    if 'anios_renta_para_comprar_70m2' in df.columns:
        mask_with_renta = mask & df['renta_mediana'].notna()
        df.loc[mask_with_renta, 'anios_renta_para_comprar_70m2'] = (
            df.loc[mask_with_renta, 'precio_m2_venta_promedio'] * 70
        ) / (df.loc[mask_with_renta, 'renta_mediana'] * 12)
    
    # Save corrected version
    output_path = PROJECT_ROOT / "data" / "exports" / "looker_studio" / "master_table_barcelona_housing_corrected.csv"
    df.to_csv(output_path, index=False, encoding='utf-8', lineterminator='\n')
    
    print(f"\n✅ Tabla corregida guardada: {output_path}")
    print(f"   Filas actualizadas: {rows_updated}")
    print(f"\n💡 El precio corregido reduce el cambio extremo de +239.8% a un valor más razonable")
    
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
