#!/usr/bin/env python3
"""
Add smoothed data columns to master table for better visualization.

Uses moving averages to reduce noise and make trends more visible.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def add_smoothed_columns(df: pd.DataFrame, window: int = 3) -> pd.DataFrame:
    """
    Add smoothed columns using moving average.
    
    Args:
        df: Master table DataFrame
        window: Window size for moving average (default: 3 years)
    
    Returns:
        DataFrame with smoothed columns added
    """
    df = df.copy()
    df = df.sort_values(['barrio_id', 'anio']).reset_index(drop=True)
    
    # Smooth price columns
    price_cols = ['precio_m2_venta_promedio', 'precio_mes_alquiler_promedio']
    
    for col in price_cols:
        if col in df.columns:
            smoothed_col = f"{col}_suavizado"
            df[smoothed_col] = df.groupby('barrio_id')[col].transform(
                lambda x: x.rolling(window=window, min_periods=1, center=True).mean()
            )
    
    # Smooth other numeric columns that vary over time
    time_varying_cols = [
        'poblacion_total', 'total_establecimientos_turisticos',
        'tasa_criminalidad_promedio', 'total_delitos'
    ]
    
    for col in time_varying_cols:
        if col in df.columns:
            smoothed_col = f"{col}_suavizado"
            df[smoothed_col] = df.groupby('barrio_id')[col].transform(
                lambda x: x.rolling(window=window, min_periods=1, center=True).mean()
            )
    
    return df


def main():
    """Add smoothed data to master table CSV."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Add smoothed data columns to master table')
    parser.add_argument('--input', type=str, 
                       default='data/exports/looker_studio/master_table_barcelona_housing.csv',
                       help='Input CSV file')
    parser.add_argument('--output', type=str,
                       default='data/exports/looker_studio/master_table_barcelona_housing_smoothed.csv',
                       help='Output CSV file')
    parser.add_argument('--window', type=int, default=3,
                       help='Moving average window size (default: 3)')
    
    args = parser.parse_args()
    
    input_path = PROJECT_ROOT / args.input
    output_path = PROJECT_ROOT / args.output
    
    if not input_path.exists():
        print(f"❌ Input file not found: {input_path}")
        return 1
    
    print(f"📂 Loading master table from: {input_path}")
    df = pd.read_csv(input_path)
    
    print(f"✅ Loaded {len(df):,} rows")
    print(f"🔧 Adding smoothed columns (window={args.window})...")
    
    df_smoothed = add_smoothed_columns(df, window=args.window)
    
    print(f"💾 Saving to: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_smoothed.to_csv(output_path, index=False, encoding='utf-8', lineterminator='\n')
    
    print(f"✅ Smoothed table saved: {len(df_smoothed):,} rows, {len(df_smoothed.columns)} columns")
    print(f"   New columns: {[c for c in df_smoothed.columns if c not in df.columns]}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
