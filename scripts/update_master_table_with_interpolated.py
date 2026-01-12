#!/usr/bin/env python3
"""
Update master table with interpolated values.

This script loads interpolated prices and updates the master table,
adding a flag to indicate interpolated data.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def main():
    """Update master table with interpolated values."""
    print("=" * 80)
    print("ACTUALIZAR TABLA MAESTRA CON VALORES INTERPOLADOS")
    print("=" * 80)
    
    # Load interpolated prices
    interpolated_path = PROJECT_ROOT / "data" / "exports" / "anomalies" / "interpolated_prices.csv"
    
    if not interpolated_path.exists():
        print(f"❌ No se encontró: {interpolated_path}")
        print("   Ejecuta primero: python scripts/fill_data_gaps.py")
        return 1
    
    interpolated = pd.read_csv(interpolated_path)
    print(f"\n✅ Valores interpolados cargados: {len(interpolated)}")
    
    # Load master table
    master_path = PROJECT_ROOT / "data" / "exports" / "looker_studio" / "master_table_barcelona_housing.csv"
    
    if not master_path.exists():
        print(f"❌ No se encontró: {master_path}")
        print("   Ejecuta primero: python scripts/create_master_table_for_looker.py")
        return 1
    
    print(f"\n📂 Cargando tabla maestra...")
    df = pd.read_csv(master_path)
    print(f"   Filas originales: {len(df)}")
    
    # Add interpolated flag column if it doesn't exist
    if 'dato_interpolado' not in df.columns:
        df['dato_interpolado'] = 0
    
    # Update prices with interpolated values
    updates_count = 0
    
    for idx, row in interpolated.iterrows():
        mask = (
            (df['barrio_id'] == row['barrio_id']) & 
            (df['anio'] == row['anio'])
        )
        
        if mask.sum() > 0:
            # Update price
            df.loc[mask, 'precio_m2_venta_promedio'] = row['precio_m2_venta_interpolado']
            df.loc[mask, 'dato_interpolado'] = 1
            df.loc[mask, 'precio_venta_faltante'] = 0  # No longer missing
            
            updates_count += mask.sum()
            
            print(f"   ✅ {row['barrio_nombre']} ({row['anio']}): "
                  f"{row['precio_m2_venta_interpolado']:,.0f} €/m²")
        else:
            print(f"   ⚠️ No se encontró fila para {row['barrio_nombre']} ({row['anio']})")
    
    if updates_count == 0:
        print("\n⚠️ No se actualizaron filas")
        return 1
    
    # Recalculate derived metrics if needed
    if 'anios_renta_para_comprar_70m2' in df.columns:
        mask_with_renta = (df['dato_interpolado'] == 1) & df['renta_mediana'].notna()
        df.loc[mask_with_renta, 'anios_renta_para_comprar_70m2'] = (
            df.loc[mask_with_renta, 'precio_m2_venta_promedio'] * 70
        ) / (df.loc[mask_with_renta, 'renta_mediana'] * 12)
    
    # Update completitud_datos for interpolated rows
    if 'completitud_datos' in df.columns:
        quality_cols = ['precio_m2_venta_promedio', 'precio_mes_alquiler_promedio',
                        'poblacion_total', 'total_establecimientos_turisticos',
                        'tasa_criminalidad_promedio', 'renta_mediana']
        available_cols = [col for col in quality_cols if col in df.columns]
        
        mask_interpolated = df['dato_interpolado'] == 1
        df.loc[mask_interpolated, 'completitud_datos'] = (
            df.loc[mask_interpolated, available_cols].notna().sum(axis=1) / len(available_cols) * 100
        ).round(1)
    
    # Save updated master table
    output_path = PROJECT_ROOT / "data" / "exports" / "looker_studio" / "master_table_barcelona_housing_filled.csv"
    df.to_csv(output_path, index=False, encoding='utf-8', lineterminator='\n')
    
    print(f"\n✅ Tabla maestra actualizada guardada: {output_path}")
    print(f"   Filas actualizadas: {updates_count}")
    print(f"   Total de filas con datos interpolados: {df['dato_interpolado'].sum()}")
    
    # Summary
    print(f"\n📊 Resumen:")
    print(f"   Filas con datos interpolados: {df['dato_interpolado'].sum()}")
    print(f"   Filas con datos faltantes (precio_venta): {df['precio_venta_faltante'].sum()}")
    print(f"   Completitud promedio: {df['completitud_datos'].mean():.1f}%")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
