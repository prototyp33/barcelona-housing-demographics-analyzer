#!/usr/bin/env python3
"""
Extract advanced hedonic attributes: superficie media and elevator proxy.

Combines superficie data from Portal de Dades with existing structural
attributes to create comprehensive hedonic variables dataset.
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


def load_dim_barrios(db_path: Path) -> pd.DataFrame:
    """Load barrio mapping from database."""
    import sqlite3
    
    if not db_path.exists():
        print(f"Warning: Database not found at {db_path}")
        return pd.DataFrame()
    
    conn = sqlite3.connect(db_path)
    query = "SELECT barrio_id, barrio_nombre FROM dim_barrios;"
    dim_barrios = pd.read_sql_query(query, conn)
    conn.close()
    
    print(f"✓ Loaded {len(dim_barrios)} neighborhoods from database")
    return dim_barrios


def normalize_barrio_name(name: str) -> str:
    """Normalize barrio names for matching."""
    import re
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


def load_superficie_data(csv_path: Path, dim_barrios: pd.DataFrame) -> pd.DataFrame:
    """
    Load superficie media from Portal de Dades.
    
    Uses sales transaction data to get average dwelling surface area.
    """
    print("\nLoading superficie media data...")
    
    df = pd.read_csv(csv_path)
    print(f"  Loaded {len(df):,} records")
    
    # Rename columns
    df = df.rename(columns={
        'Dim-00:TEMPS': 'timestamp',
        'Dim-01:TERRITORI': 'territorio',
        'Dim-01:TERRITORI (type)': 'tipo',
        'VALUE': 'superficie_m2'
    })
    
    # Filter to only Barri level
    df = df[df['tipo'] == 'Barri'].copy()
    print(f"  Filtered to {len(df):,} barrio-level records")
    
    # Get most recent year's data (aggregate by barrio)
    df['year'] = pd.to_datetime(df['timestamp']).dt.year
    latest_year = df['year'].max()
    print(f"  Using data from year: {latest_year}")
    
    df_recent = df[df['year'] >= latest_year - 2]  # Last 2-3 years for stability
    
    # Normalize names for matching
    df_recent['territorio_norm'] = df_recent['territorio'].apply(normalize_barrio_name)
    dim_barrios_norm = dim_barrios.copy()
    dim_barrios_norm['barrio_nombre_norm'] = dim_barrios_norm['barrio_nombre'].apply(normalize_barrio_name)
    
    # Map to barrio_id
    mapping = dim_barrios_norm.set_index('barrio_nombre_norm')['barrio_id'].to_dict()
    df_recent['barrio_id'] = df_recent['territorio_norm'].map(mapping)
    
    # Remove unmapped
    df_recent = df_recent[df_recent['barrio_id'].notna()].copy()
    df_recent['barrio_id'] = df_recent['barrio_id'].astype(int)
    
    # Aggregate by barrio (mean over recent years)
    superficie_agg = df_recent.groupby('barrio_id').agg({
        'superficie_m2': 'mean',
        'territorio': 'first'
    }).reset_index()
    
    superficie_agg['superficie_m2'] = superficie_agg['superficie_m2'].round(2)
    
    print(f"  ✓ Mapped {len(superficie_agg)} neighborhoods")
    print(f"    Range: {superficie_agg['superficie_m2'].min():.1f} - {superficie_agg['superficie_m2'].max():.1f} m²")
    print(f"    Mean: {superficie_agg['superficie_m2'].mean():.1f} m²")
    
    return superficie_agg[['barrio_id', 'superficie_m2']]


def load_structural_attributes(csv_path: Path) -> pd.DataFrame:
    """Load existing structural attributes (building age data)."""
    if not csv_path.exists():
        print(f"Warning: Structural attributes file not found: {csv_path}")
        return pd.DataFrame()
    
    print("\nLoading existing structural attributes...")
    df = pd.read_csv(csv_path)
    
    print(f"✓ Loaded {len(df)} neighborhoods")
    print(f"  Columns: {', '.join(df.columns[:6])}...")
    
    return df


def calculate_elevator_proxy(structural_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate elevator proxy from building age distribution.
    
    Strategy: Newer buildings (post-1960) are more likely to have elevators
    due to building codes. Use % of buildings built after 1960 as proxy.
    """
    print("\nCalculating elevator proxy...")
    
    if structural_df.empty or 'pct_edificios_pre1950' not in structural_df.columns:
        print("  ⚠ Warning: Cannot calculate elevator proxy - missing building age data")
        return pd.DataFrame(columns=['barrio_id', 'pct_edificios_con_ascensor_proxy'])
    
    # Strategy: Buildings post-1960 are highly likely to have elevators
    # We have pct_edificios_pre1950, so we can estimate:
    # - Pre-1950: ~10% have elevator (old buildings, retrofitted)
    # - Post-1950: ~70% have elevator (newer codes)
    # This is a conservative proxy
    
    proxy_df = structural_df[['barrio_id', 'pct_edificios_pre1950']].copy()
    
    # Simple proxy: Inverse of pre-1950 buildings weighted
    # Higher % of old buildings = lower % with elevators
    proxy_df['pct_edificios_con_ascensor_proxy'] = (
        (100 - proxy_df['pct_edificios_pre1950']) * 0.7 + 
        proxy_df['pct_edificios_pre1950'] * 0.1
    ).round(2)
    
    print(f"  ✓ Calculated elevator proxy for {len(proxy_df)} neighborhoods")
    print(f"    Range: {proxy_df['pct_edificios_con_ascensor_proxy'].min():.1f}% - {proxy_df['pct_edificios_con_ascensor_proxy'].max():.1f}%")
    print(f"    Mean: {proxy_df['pct_edificios_con_ascensor_proxy'].mean():.1f}%")
    
    return proxy_df[['barrio_id', 'pct_edificios_con_ascensor_proxy']]


def combine_advanced_attributes(
    dim_barrios: pd.DataFrame,
    superficie_df: pd.DataFrame,
    elevator_proxy_df: pd.DataFrame,
    structural_df: pd.DataFrame
) -> pd.DataFrame:
    """Combine all advanced attributes into single dataset."""
    print("\nCombining advanced attributes...")
    
    # Start with all barrios
    combined = dim_barrios[['barrio_id', 'barrio_nombre']].copy()
    
    # Add superficie
    if not superficie_df.empty:
        combined = combined.merge(superficie_df, on='barrio_id', how='left')
    
    # Add elevator proxy
    if not elevator_proxy_df.empty:
        combined = combined.merge(elevator_proxy_df, on='barrio_id', how='left')
    
    # Add key structural metrics
    if not structural_df.empty:
        structural_subset = structural_df[[
            'barrio_id', 'anyo_construccion_promedio', 'antiguedad_anos', 
            'num_edificios', 'pct_edificios_pre1950'
        ]].copy()
        combined = combined.merge(structural_subset, on='barrio_id', how='left')
    
    # Add metadata
    combined['source'] = 'portaldades_combined'
    combined['etl_loaded_at'] = datetime.now().isoformat()
    
    print(f"✓ Combined dataset: {len(combined)} neighborhoods")
    print(f"  Columns: {len(combined.columns)}")
    
    return combined


def save_advanced_attributes(df: pd.DataFrame, output_path: Path) -> None:
    """Save advanced attributes to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    
    print(f"\n✓ Saved to: {output_path}")
    print(f"  Records: {len(df)}")


def validate_common_sense(df: pd.DataFrame) -> None:
    """Validate common sense expectations."""
    print("\nVALIDATING COMMON SENSE...")
    print("-" * 80)
    
    # Check 1: Pedralbes should have larger superficie than el Raval
    pedralbes = df[df['barrio_nombre'].str.contains('Pedralbes', case=False, na=False)]
    raval = df[df['barrio_nombre'].str.contains('Raval', case=False, na=False)]
    
    if not pedralbes.empty and not raval.empty:
        pedralbes_sup = pedralbes['superficie_m2'].values[0] if 'superficie_m2' in pedralbes.columns else None
        raval_sup = raval['superficie_m2'].values[0] if 'superficie_m2' in raval.columns else None
        
        if pedralbes_sup and raval_sup:
            if pedralbes_sup > raval_sup:
                print(f"✓ PASS: Pedralbes ({pedralbes_sup:.1f} m²) > el Raval ({raval_sup:.1f} m²)")
            else:
                print(f"✗ FAIL: Pedralbes ({pedralbes_sup:.1f} m²) <= el Raval ({raval_sup:.1f} m²)")
    
    # Check 2: Newer neighborhoods should have higher elevator proxy
    if 'pct_edificios_con_ascensor_proxy' in df.columns and 'antiguedad_anos' in df.columns:
        correlation = df[['antiguedad_anos', 'pct_edificios_con_ascensor_proxy']].corr().iloc[0, 1]
        if correlation < -0.3:  # Negative correlation expected (newer = more elevators)
            print(f"✓ PASS: Elevator proxy negatively correlated with age (r={correlation:.3f})")
        else:
            print(f"⚠ WARNING: Elevator proxy correlation with age unexpected (r={correlation:.3f})")
    
    # Summary stats
    print(f"\nSummary Statistics:")
    if 'superficie_m2' in df.columns:
        print(f"  Superficie: {df['superficie_m2'].mean():.1f} m² (avg), range {df['superficie_m2'].min():.1f}-{df['superficie_m2'].max():.1f}")
    if 'pct_edificios_con_ascensor_proxy' in df.columns:
        print(f"  Elevator proxy: {df['pct_edificios_con_ascensor_proxy'].mean():.1f}% (avg)")


def main() -> int:
    """Main execution."""
    portaldades_dir = PROJECT_ROOT / "data" / "raw" / "portaldades"
    db_path = PROJECT_ROOT / "data" / "processed" / "database.db"
    structural_path = PROJECT_ROOT / "data" / "raw" / "barrio_structural_attributes.csv"
    output_path = PROJECT_ROOT / "data" / "raw" / "advanced_attributes.csv"
    
    superficie_path = portaldades_dir / "portaldades_Superficie_mitjana_m²_dels_habitatges_transmesos_per_compravenda_stnw2pjimy.csv"
    
    print("=" * 80)
    print("ADVANCED HEDONIC ATTRIBUTES EXTRACTION")
    print("=" * 80)
    print()
    
    try:
        # Load barrio mapping
        dim_barrios = load_dim_barrios(db_path)
        if dim_barrios.empty:
            print("ERROR: Could not load neighborhood mapping")
            return 1
        
        # Load superficie data
        superficie_df = load_superficie_data(superficie_path, dim_barrios)
        
        # Load existing structural attributes
        structural_df = load_structural_attributes(structural_path)
        
        # Calculate elevator proxy
        elevator_proxy_df = calculate_elevator_proxy(structural_df)
        
        # Combine all
        combined = combine_advanced_attributes(
            dim_barrios, superficie_df, elevator_proxy_df, structural_df
        )
        
        # Save
        save_advanced_attributes(combined, output_path)
        
        # Validate
        validate_common_sense(combined)
        
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
