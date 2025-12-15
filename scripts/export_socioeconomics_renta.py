#!/usr/bin/env python3
"""
Export socioeconomic data (Renta Familiar) with quarterly interpolation.

Extracts income data from fact_renta, interpolates to quarters,
combines with official prices, and calculates affordability ratios.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def load_renta_from_db(db_path: Path) -> pd.DataFrame:
    """Load income data from fact_renta table."""
    import sqlite3
    
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")
    
    print("Loading income data from database...")
    conn = sqlite3.connect(db_path)
    
    query = """
    SELECT 
        fr.barrio_id,
        db.barrio_nombre,
        fr.anio as year,
        fr.renta_euros as renta_annual,
        fr.renta_min,
        fr.renta_max,
        fr.source
    FROM fact_renta fr
    LEFT JOIN dim_barrios db ON fr.barrio_id = db.barrio_id
    WHERE fr.anio BETWEEN 2015 AND 2023
    ORDER BY fr.barrio_id, fr.anio
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    print(f"✓ Loaded {len(df):,} records")
    print(f"  Neighborhoods: {df['barrio_id'].nunique()}")
    print(f"  Years: {df['year'].min()}-{df['year'].max()}")
    
    return df


def interpolate_to_quarters(df: pd.DataFrame) -> pd.DataFrame:
    """
    Interpolate annual income data to quarterly using forward-fill.
    
    Strategy: Each year's income value is repeated for all 4 quarters.
    """
    print("\nInterpolating annual data to quarters...")
    
    # Create quarterly records
    quarters = ['Q1', 'Q2', 'Q3', 'Q4']
    
    quarterly_records = []
    for _, row in df.iterrows():
        for quarter in quarters:
            quarterly_records.append({
                'barrio_id': row['barrio_id'],
                'barrio_nombre': row['barrio_nombre'],
                'year': row['year'],
                'quarter': quarter,
                'period': f"{row['year']}{quarter}",
                'renta_annual': row['renta_annual'],
                'renta_min': row['renta_min'],
                'renta_max': row['renta_max'],
                'source': row['source']
            })
    
    df_quarterly = pd.DataFrame(quarterly_records)
    
    print(f"✓ Created {len(df_quarterly):,} quarterly records")
    print(f"  From {len(df)} annual records")
    
    return df_quarterly


def load_official_prices(csv_path: Path) -> pd.DataFrame:
    """Load official prices data."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Official prices file not found: {csv_path}")
    
    print("\nLoading official prices...")
    df = pd.read_csv(csv_path)
    
    print(f"✓ Loaded {len(df):,} price records")
    
    return df


def combine_and_calculate_affordability(
    renta_df: pd.DataFrame,
    prices_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Combine income and price data, calculate affordability ratio.
    
    Affordability Ratio = Price per m² / Annual Income per capita
    Higher ratio = less affordable
    """
    print("\nCombining income and price data...")
    
    # Merge on barrio_id, year, quarter
    combined = renta_df.merge(
        prices_df[['barrio_id', 'year', 'quarter', 
                   'preu_lloguer_mensual', 'preu_lloguer_m2',
                   'preu_venda_total', 'preu_venda_m2']],
        on=['barrio_id', 'year', 'quarter'],
        how='left'
    )
    
    print(f"✓ Combined dataset: {len(combined):,} records")
    
    # Calculate affordability ratios
    print("\nCalculating affordability metrics...")
    
    # 1. Price/Income ratio (for sales)
    # How many years of income to buy average property
    combined['price_to_income_ratio'] = (
        combined['preu_venda_total'] * 1000 / combined['renta_annual']
    ).round(2)
    
    # 2. Rental burden (annual rent as % of income)
    combined['rent_burden_pct'] = (
        combined['preu_lloguer_mensual'] * 12 / combined['renta_annual'] * 100
    ).round(2)
    
    # 3. Price per m² relative to income
    # How many Euros of income per Euro of price/m²
    combined['affordability_index'] = (
        combined['renta_annual'] / combined['preu_venda_m2']
    ).round(2)
    
    # Add metadata
    combined['etl_loaded_at'] = datetime.now().isoformat()
    
    # Summary
    print(f"\nAffordability Statistics:")
    print(f"  Price/Income Ratio:")
    print(f"    Mean: {combined['price_to_income_ratio'].mean():.1f}x income")
    print(f"    Range: {combined['price_to_income_ratio'].min():.1f}x - {combined['price_to_income_ratio'].max():.1f}x")
    print(f"  Rent Burden:")
    print(f"    Mean: {combined['rent_burden_pct'].mean():.1f}% of income")
    print(f"    Range: {combined['rent_burden_pct'].min():.1f}% - {combined['rent_burden_pct'].max():.1f}%")
    
    return combined


def save_socioeconomics_renta(df: pd.DataFrame, output_path: Path) -> None:
    """Save socioeconomic data to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Column order
    columns = [
        'barrio_id', 'barrio_nombre', 'year', 'quarter', 'period',
        'renta_annual', 'renta_min', 'renta_max',
        'preu_lloguer_mensual', 'preu_lloguer_m2',
        'preu_venda_total', 'preu_venda_m2',
        'price_to_income_ratio', 'rent_burden_pct', 'affordability_index',
        'source', 'etl_loaded_at'
    ]
    
    # Only include existing columns
    available = [col for col in columns if col in df.columns]
    df_out = df[available].copy()
    
    # Round numeric columns
    numeric_cols = df_out.select_dtypes(include=['float64']).columns
    df_out[numeric_cols] = df_out[numeric_cols].round(2)
    
    df_out.to_csv(output_path, index=False)
    
    print(f"\n✓ Saved to: {output_path}")
    print(f"  Records: {len(df_out):,}")
    print(f"  Columns: {len(available)}")


def main() -> int:
    """Main execution."""
    db_path = PROJECT_ROOT / "data" / "processed" / "database.db"
    prices_path = PROJECT_ROOT / "data" / "raw" / "official_prices_2015_2024.csv"
    output_path = PROJECT_ROOT / "data" / "raw" / "socioeconomics_renta_2015_2023.csv"
    
    print("=" * 80)
    print("SOCIOECONOMIC DATA EXPORT (Renta Familiar)")
    print("=" * 80)
    print()
    
    try:
        # 1. Load income data from database
        renta_df = load_renta_from_db(db_path)
        
        # 2. Interpolate to quarters
        renta_quarterly = interpolate_to_quarters(renta_df)
        
        # 3. Load official prices
        prices_df = load_official_prices(prices_path)
        
        # 4. Combine and calculate affordability
        combined = combine_and_calculate_affordability(renta_quarterly, prices_df)
        
        # 5. Save output
        save_socioeconomics_renta(combined, output_path)
        
        print()
        print("✅ Export complete!")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
