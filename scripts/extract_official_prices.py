#!/usr/bin/env python3
"""
Extract official rental and sales prices from Portal de Dades (Generalitat/INCASÒL).

This script processes official price data to create a unified dataset
combining rental bonds (INCASÒL) and sales tax records (Generalitat).
"""

from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def find_latest_file(directory: Path, pattern: str) -> Optional[Path]:
    """Find the most recent file matching pattern."""
    if not directory.exists():
        return None
    
    files = list(directory.glob(pattern))
    if not files:
        return None
    
    # Sort by modification time, newest first
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0]


def extract_year_quarter_from_timestamp(timestamp_str: str) -> tuple[int, str]:
    """
    Extract year and quarter from ISO timestamp.
    
    Args:
        timestamp_str: ISO format like "2014-01-01T00:00:00Z"
        
    Returns:
        Tuple of (year, quarter) like (2014, 'Q1')
    """
    # Parse the date
    date_str = timestamp_str.split('T')[0]
    year, month, _ = date_str.split('-')
    year = int(year)
    month = int(month)
    
    # Determine quarter
    if month <= 3:
        quarter = 'Q1'
    elif month <= 6:
        quarter = 'Q2'
    elif month <= 9:
        quarter = 'Q3'
    else:
        quarter = 'Q4'
    
    return year, quarter


def load_dim_barrios(db_path: Path) -> pd.DataFrame:
    """Load barrio mapping from database."""
    import sqlite3
    
    if not db_path.exists():
        print(f"Warning: Database not found at {db_path}")
        return pd.DataFrame(columns=["barrio_id", "barrio_nombre"])
    
    conn = sqlite3.connect(db_path)
    query = "SELECT barrio_id, barrio_nombre, barrio_nombre_normalizado FROM dim_barrios;"
    dim_barrios = pd.read_sql_query(query, conn)
    conn.close()
    
    print(f"✓ Loaded {len(dim_barrios)} neighborhoods from database")
    return dim_barrios


def normalize_barrio_name(name: str) -> str:
    """Normalize barrio names for matching."""
    # Remove accents, lowercase, remove punctuation
    import unicodedata
    
    name = name.lower().strip()
    # Remove articles
    name = re.sub(r'^(el |la |els |les |l\')', '', name)
    # Normalize unicode
    name = unicodedata.normalize('NFKD', name)
    name = ''.join([c for c in name if not unicodedata.combining(c)])
    # Remove special chars
    name = re.sub(r'[^\w\s]', '', name)
    name = re.sub(r'\s+', '', name)
    
    return name


def load_rental_prices(csv_path: Path, dim_barrios: pd.DataFrame) -> pd.DataFrame:
    """
    Load rental prices from Portal de Dades.
    
    File: Preu_mitjà_del_lloguer_dhabitatges
    Source: INCASÒL (rental bonds)
    """
    print(f"Loading rental prices from: {csv_path.name}")
    
    df = pd.read_csv(csv_path)
    print(f"  Loaded {len(df):,} records")
    
    # Rename columns
    df = df.rename(columns={
        'Dim-00:TEMPS': 'timestamp',
        'Dim-01:TERRITORI': 'territorio',
        'Dim-01:TERRITORI (type)': 'tipo',
        'VALUE': 'preu_lloguer_mensual'
    })
    
    # Filter to only Barri level (not Districte or Barcelona)
    df = df[df['tipo'] == 'Barri'].copy()
    print(f"  Filtered to {len(df):,} barrio-level records")
    
    # Extract year and quarter
    df[['year', 'quarter']] = df['timestamp'].apply(
        lambda x: pd.Series(extract_year_quarter_from_timestamp(x))
    )
    
    # Normalize names for matching
    df['territorio_norm'] = df['territorio'].apply(normalize_barrio_name)
    dim_barrios_norm = dim_barrios.copy()
    dim_barrios_norm['barrio_nombre_norm'] = dim_barrios_norm['barrio_nombre'].apply(normalize_barrio_name)
    
    # Map to barrio_id
    mapping = dim_barrios_norm.set_index('barrio_nombre_norm')['barrio_id'].to_dict()
    df['barrio_id'] = df['territorio_norm'].map(mapping)
    
    # Check for unmapped
    unmapped = df[df['barrio_id'].isna()]['territorio'].unique()
    if len(unmapped) > 0:
        print(f"  ⚠ Warning: {len(unmapped)} neighborhoods couldn't be mapped:")
        for name in sorted(unmapped)[:10]:
            print(f"    - {name}")
    
    # Remove unmapped
    df = df[df['barrio_id'].notna()].copy()
    df['barrio_id'] = df['barrio_id'].astype(int)
    
    # Select final columns
    df = df[['barrio_id', 'territorio', 'year', 'quarter', 'preu_lloguer_mensual']]
    
    print(f"  ✓ Mapped {len(df):,} records to {df['barrio_id'].nunique()} neighborhoods")
    return df


def load_sales_prices(csv_path: Path, dim_barrios: pd.DataFrame) -> pd.DataFrame:
    """
    Load sales prices from Portal de Dades.
    
    File: Preu_mitjà_de_les_compravendes_dhabitatge_registrades
    Source: Generalitat (property tax records)
    """
    print(f"Loading sales prices from: {csv_path.name}")
    
    df = pd.read_csv(csv_path)
    print(f"  Loaded {len(df):,} records")
    
    # Rename columns
    df = df.rename(columns={
        'Dim-00:TEMPS': 'timestamp',
        'Dim-01:TERRITORI': 'territorio',
        'Dim-01:TERRITORI (type)': 'tipo',
        'VALUE': 'preu_venda_total'
    })
    
    # Filter to only Barri level
    df = df[df['tipo'] == 'Barri'].copy()
    print(f"  Filtered to {len(df):,} barrio-level records")
    
    # Extract year and quarter
    df[['year', 'quarter']] = df['timestamp'].apply(
        lambda x: pd.Series(extract_year_quarter_from_timestamp(x))
    )
    
    # Normalize names for matching
    df['territorio_norm'] = df['territorio'].apply(normalize_barrio_name)
    dim_barrios_norm = dim_barrios.copy()
    dim_barrios_norm['barrio_nombre_norm'] = dim_barrios_norm['barrio_nombre'].apply(normalize_barrio_name)
    
    # Map to barrio_id
    mapping = dim_barrios_norm.set_index('barrio_nombre_norm')['barrio_id'].to_dict()
    df['barrio_id'] = df['territorio_norm'].map(mapping)
    
    # Check for unmapped
    unmapped = df[df['barrio_id'].isna()]['territorio'].unique()
    if len(unmapped) > 0:
        print(f"  ⚠ Warning: {len(unmapped)} neighborhoods couldn't be mapped")
    
    # Remove unmapped
    df = df[df['barrio_id'].notna()].copy()
    df['barrio_id'] = df['barrio_id'].astype(int)
    
    # Select final columns
    df = df[['barrio_id', 'territorio', 'year', 'quarter', 'preu_venda_total']]
    
    print(f"  ✓ Mapped {len(df):,} records to {df['barrio_id'].nunique()} neighborhoods")
    return df


def load_rental_per_m2(csv_path: Path, dim_barrios: pd.DataFrame) -> pd.DataFrame:
    """Load rental price per m²."""
    print(f"Loading rental ​price/m² from: {csv_path.name}")
    
    df = pd.read_csv(csv_path)
    df = df.rename(columns={
        'Dim-00:TEMPS': 'timestamp',
        'Dim-01:TERRITORI': 'territorio',
        'Dim-01:TERRITORI (type)': 'tipo',
        'VALUE': 'preu_lloguer_m2'
    })
    
    df = df[df['tipo'] == 'Barri'].copy()
    df[['year', 'quarter']] = df['timestamp'].apply(
        lambda x: pd.Series(extract_year_quarter_from_timestamp(x))
    )
    
    df['territorio_norm'] = df['territorio'].apply(normalize_barrio_name)
    dim_barrios_norm = dim_barrios.copy()
    dim_barrios_norm['barrio_nombre_norm'] = dim_barrios_norm['barrio_nombre'].apply(normalize_barrio_name)
    mapping = dim_barrios_norm.set_index('barrio_nombre_norm')['barrio_id'].to_dict()
    df['barrio_id'] = df['territorio_norm'].map(mapping)
    
    df = df[df['barrio_id'].notna()].copy()
    df['barrio_id'] = df['barrio_id'].astype(int)
    
    df = df[['barrio_id', 'year', 'quarter', 'preu_lloguer_m2']]
    print(f"  ✓ Loaded {len(df):,} records")
    return df


def load_sales_per_m2(csv_path: Path, dim_barrios: pd.DataFrame) -> pd.DataFrame:
    """Load sales price per m²."""
    print(f"Loading sales price/m² from: {csv_path.name}")
    
    df = pd.read_csv(csv_path)
    df = df.rename(columns={
        'Dim-00:TEMPS': 'timestamp',
        'Dim-01:TERRITORI': 'territorio',
        'Dim-01:TERRITORI (type)': 'tipo',
        'VALUE': 'preu_venda_m2'
    })
    
    df = df[df['tipo'] == 'Barri'].copy()
    df[['year', 'quarter']] = df['timestamp'].apply(
        lambda x: pd.Series(extract_year_quarter_from_timestamp(x))
    )
    
    df['territorio_norm'] = df['territorio'].apply(normalize_barrio_name)
    dim_barrios_norm = dim_barrios.copy()
    dim_barrios_norm['barrio_nombre_norm'] = dim_barrios_norm['barrio_nombre'].apply(normalize_barrio_name)
    mapping = dim_barrios_norm.set_index('barrio_nombre_norm')['barrio_id'].to_dict()
    df['barrio_id'] = df['territorio_norm'].map(mapping)
    
    df = df[df['barrio_id'].notna()].copy()
    df['barrio_id'] = df['barrio_id'].astype(int)
    
    df = df[['barrio_id', 'year', 'quarter', 'preu_venda_m2']]
    print(f"  ✓ Loaded {len(df):,} records")
    return df


def combine_datasets(
    rental: pd.DataFrame,
    sales: pd.DataFrame,
    rental_m2: pd.DataFrame,
    sales_m2: pd.DataFrame,
    dim_barrios: pd.DataFrame
) -> pd.DataFrame:
    """Combine all price datasets into unified format."""
    print("\nCombining datasets...")
    
    # Aggregate each dataset by barrio_id, year, quarter (using mean for duplicates)
    rental_agg = rental.groupby(['barrio_id', 'year', 'quarter'], as_index=False).agg({
        'preu_lloguer_mensual': 'mean',
        'territorio': 'first'
    })
    
    rental_m2_agg = rental_m2.groupby(['barrio_id', 'year', 'quarter'], as_index=False).agg({
        'preu_lloguer_m2': 'mean'
    })
    
    sales_agg = sales.groupby(['barrio_id', 'year', 'quarter'], as_index=False).agg({
        'preu_venda_total': 'mean',
        'territorio': 'first'
    })
    
    sales_m2_agg = sales_m2.groupby(['barrio_id', 'year', 'quarter'], as_index=False).agg({
        'preu_venda_m2': 'mean'
    })
    
    # Full outer join on barrio_id, year, quarter
    combined = rental_agg.merge(
        rental_m2_agg,
        on=['barrio_id', 'year', 'quarter'],
        how='outer'
    )
    
    combined = combined.merge(
        sales_agg,
        on=['barrio_id', 'year', 'quarter'],
        how='outer',
        suffixes=('', '_sales')
    )
    
    combined = combined.merge(
        sales_m2_agg,
        on=['barrio_id', 'year', 'quarter'],
        how='outer'
    )
    
    # Add barrio names
    combined = combined.merge(
        dim_barrios[['barrio_id', 'barrio_nombre']],
        on='barrio_id',
        how='left'
    )
    
    # Use barrio_nombre from dim_barrios (canonical)
    if 'territorio' in combined.columns:
        combined = combined.drop(columns=['territorio'])
    if 'territorio_sales' in combined.columns:
        combined = combined.drop(columns=['territorio_sales'])
    
    # Create period column
    combined['period'] = combined['year'].astype(str) + combined['quarter']
    
    # Add metadata
    combined['source_rental'] = 'incasol_portaldades'
    combined['source_sales'] = 'generalitat_portaldades'
    combined['etl_loaded_at'] = datetime.now().isoformat()
    
    # Filter to 2015-2024 as per task requirement
    combined = combined[(combined['year'] >= 2015) & (combined['year'] <= 2024)]
    
    # Sort
    combined = combined.sort_values(['barrio_id', 'year', 'quarter']).reset_index(drop=True)
    
    print(f"✓ Combined dataset: {len(combined):,} records")
    print(f"  Neighborhoods: {combined['barrio_id'].nunique()}")
    print(f"  Year range: {combined['year'].min()}-{combined['year'].max()}")
    print(f"  Quarters: {combined.groupby('year')['quarter'].nunique().mean():.1f} avg per year")
    
    return combined


def save_official_prices(df: pd.DataFrame, output_path: Path) -> None:
    """Save combined official prices to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Column order
    columns = [
        'barrio_id', 'barrio_nombre', 'year', 'quarter', 'period',
        'preu_lloguer_mensual', 'preu_lloguer_m2',
        'preu_venda_total', 'preu_venda_m2',
        'source_rental', 'source_sales', 'etl_loaded_at'
    ]
    
    # Only include existing columns
    available = [col for col in columns if col in df.columns]
    df_out = df[available].copy()
    
    # Round prices
    price_cols = [c for c in df_out.columns if c.startswith('preu_')]
    for col in price_cols:
        df_out[col] = df_out[col].round(2)
    
    df_out.to_csv(output_path, index=False)
    print(f"\n✓ Saved to: {output_path}")
    print(f"  Total records: {len(df_out):,}")


def main() -> int:
    """Main execution."""
    portaldades_dir = PROJECT_ROOT / "data" / "raw" / "portaldades"
    db_path = PROJECT_ROOT / "data" / "processed" / "database.db"
    output_path = PROJECT_ROOT / "data" / "raw" / "official_prices_2015_2024.csv"
    
    print("=" * 80)
    print("OFFICIAL PRICES EXTRACTION (INCASÒL + GENERALITAT)")
    print("=" * 80)
    print()
    
    try:
        # Load barrio mapping
        dim_barrios = load_dim_barrios(db_path)
        if dim_barrios.empty:
            print("ERROR: Could not load neighborhood mapping")
            return 1
        
        print()
        
        # Find and load datasets
        rental_path = portaldades_dir / "portaldades_Preu_mitjà_del_lloguer_dhabitatges_b37xv8wcjh.csv"
        rental_m2_path = portaldades_dir / "portaldades_Preu_mitjà_per_superfície_m²_del_lloguer_dhabitatges_5ibudgqbrb.csv"
        sales_path = portaldades_dir / "portaldades_Preu_mitjà_de_les_compravendes_dhabitatge_registrades_la6s9fp57r.csv"
        sales_m2_path = portaldades_dir / "portaldades_Preu_mitjà_per_superfície_m²_de_les_compravendes_dhabitatge_registrades_u25rr7oxh6.csv"
        
        rental_df = load_rental_prices(rental_path, dim_barrios)
        print()
        rental_m2_df = load_rental_per_m2(rental_m2_path, dim_barrios)
        print()
        sales_df = load_sales_prices(sales_path, dim_barrios)
        print()
        sales_m2_df = load_sales_per_m2(sales_m2_path, dim_barrios)
        
        # Combine
        combined = combine_datasets(rental_df, sales_df, rental_m2_df, sales_m2_df, dim_barrios)
        
        # Save
        save_official_prices(combined, output_path)
        
        # Summary statistics
        print("\nSUMMARY STATISTICS")
        print("-" * 80)
        print(f"Rental prices: {combined['preu_lloguer_mensual'].notna().sum():,} records")
        print(f"  Mean: €{combined['preu_lloguer_mensual'].mean():.2f}/month")
        print(f"  Range: €{combined['preu_lloguer_mensual'].min():.2f} - €{combined['preu_lloguer_mensual'].max():.2f}")
        print()
        print(f"Sales prices: {combined['preu_venda_total'].notna().sum():,} records")
        print(f"  Mean: €{combined['preu_venda_total'].mean():,.0f}")
        print(f"  Range: €{combined['preu_venda_total'].min():,.0f} - €{combined['preu_venda_total'].max():,.0f}")
        print()
        print("✅ Extraction complete!")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
