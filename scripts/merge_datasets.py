#!/usr/bin/env python3
"""
Merge all data sources into Analytical Base Table (ABT).

Combines temporal price/income data with static structural/hedonic attributes
to create model-ready master dataset.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def load_datasets() -> dict[str, pd.DataFrame]:
    """Load all input datasets."""
    print("LOADING INPUT DATASETS")
    print("=" * 80)
    
    data_dir = PROJECT_ROOT / "data" / "raw"
    
    datasets = {}
    
    # 1. Official prices (temporal base)
    prices_path = data_dir / "official_prices_2015_2024.csv"
    if prices_path.exists():
        datasets['prices'] = pd.read_csv(prices_path)
        print(f"✓ Prices: {len(datasets['prices']):,} records")
    else:
        raise FileNotFoundError(f"Prices dataset not found: {prices_path}")
    
    # 2. Socioeconomic data (temporal)
    renta_path = data_dir / "socioeconomics_renta_2015_2023.csv"
    if renta_path.exists():
        datasets['renta'] = pd.read_csv(renta_path)
        print(f"✓ Renta: {len(datasets['renta']):,} records")
    else:
        raise FileNotFoundError(f"Renta dataset not found: {renta_path}")
    
    # 3. Structural attributes (static)
    structural_path = data_dir / "barrio_structural_attributes.csv"
    if structural_path.exists():
        datasets['structural'] = pd.read_csv(structural_path)
        print(f"✓ Structural: {len(datasets['structural']):,} records")
    else:
        raise FileNotFoundError(f"Structural dataset not found: {structural_path}")
    
    # 4. Advanced hedonic attributes (static)
    advanced_path = data_dir / "advanced_attributes.csv"
    if advanced_path.exists():
        datasets['advanced'] = pd.read_csv(advanced_path)
        print(f"✓ Advanced: {len(datasets['advanced']):,} records")
    else:
        raise FileNotFoundError(f"Advanced dataset not found: {advanced_path}")
    
    print()
    return datasets


def merge_temporal_data(prices_df: pd.DataFrame, renta_df: pd.DataFrame) -> pd.DataFrame:
    """Merge temporal datasets (prices + renta)."""
    print("MERGING TEMPORAL DATA (Prices + Renta)")
    print("-" * 80)
    
    # Left join: prices is base (has most recent quarters)
    merged = prices_df.merge(
        renta_df,
        on=['barrio_id', 'year', 'quarter'],
        how='left',
        suffixes=('', '_renta')
    )
    
    # Handle duplicate barrio_nombre columns
    if 'barrio_nombre_renta' in merged.columns:
        # Use the one from prices (should be same)
        merged = merged.drop(columns=['barrio_nombre_renta'])
    
    # Drop duplicate metadata columns from renta
    cols_to_drop = [col for col in merged.columns if col.endswith('_renta') and col != 'renta_annual']
    if cols_to_drop:
        merged = merged.drop(columns=cols_to_drop)
    
    print(f"✓ Merged: {len(merged):,} records")
    print(f"  Columns: {len(merged.columns)}")
    print()
    
    return merged


def broadcast_static_attributes(
    temporal_df: pd.DataFrame,
    structural_df: pd.DataFrame,
    advanced_df: pd.DataFrame
) -> pd.DataFrame:
    """Broadcast static attributes to all temporal records."""
    print("BROADCASTING STATIC ATTRIBUTES")
    print("-" * 80)
    
    # Select columns to broadcast (avoid duplicates)
    structural_cols = [
        'barrio_id', 'anyo_construccion_promedio', 'antiguedad_anos',
        'num_edificios', 'pct_edificios_pre1950'
    ]
    structural_subset = structural_df[structural_cols].copy()
    
    advanced_cols = [
        'barrio_id', 'superficie_m2', 'pct_edificios_con_ascensor_proxy'
    ]
    advanced_subset = advanced_df[advanced_cols].copy()
    
    # Merge static data (broadcast to all quarters)
    merged = temporal_df.merge(structural_subset, on='barrio_id', how='left')
    merged = merged.merge(advanced_subset, on='barrio_id', how='left')
    
    print(f"✓ Broadcasted static attributes to {len(merged):,} records")
    print(f"  Columns: {len(merged.columns)}")
    print()
    
    return merged


def feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    """Create derived features for modeling."""
    print("FEATURE ENGINEERING")
    print("-" * 80)
    
    # 1. Log-transformed prices (for normality)
    if 'preu_venda_total' in df.columns:
        df['log_price_sales'] = np.log1p(df['preu_venda_total'] * 1000)  # Convert to €
    
    if 'preu_lloguer_mensual' in df.columns:
        df['log_price_rental'] = np.log1p(df['preu_lloguer_mensual'])
    
    # 2. Dynamic building age (based on current year in data)
    if 'anyo_construccion_promedio' in df.columns and 'year' in df.columns:
        df['building_age_dynamic'] = df['year'] - df['anyo_construccion_promedio']
    
    # 3. Price per income (affordability index - already in renta but recalculate for consistency)
    if 'preu_venda_m2' in df.columns and 'renta_annual' in df.columns:
        df['affordability_ratio'] = (df['preu_venda_m2'] / df['renta_annual'] * 1000).round(4)
    
    # 4. Time features
    if 'year' in df.columns and 'quarter' in df.columns:
        df['year_quarter'] = df['year'].astype(str) + '-' + df['quarter']
        df['time_index'] = (df['year'] - df['year'].min()) * 4 + df['quarter'].str.replace('Q', '').astype(int)
    
    print(f"✓ Created features: log prices, dynamic age, affordability, time index")
    print()
    
    return df


def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Handle missing values with appropriate strategy."""
    print("HANDLING MISSING VALUES")
    print("-" * 80)
    
    # Report missing values
    missing = df.isnull().sum()
    missing_pct = (missing / len(df) * 100).round(2)
    missing_report = pd.DataFrame({
        'missing_count': missing,
        'missing_pct': missing_pct
    })
    missing_report = missing_report[missing_report['missing_count'] > 0].sort_values('missing_count', ascending=False)
    
    if not missing_report.empty:
        print("Missing values detected:")
        print(missing_report.head(10).to_string())
        print()
    
    # Strategy:
    # - Critical price columns: Keep NULLs (indicates no data for that quarter)
    # - Structural attributes: Impute with median (static features shouldn't vary)
    # - Renta: Keep NULLs (indicates year mismatch)
    
    # We'll keep NULLs as-is for now (better for time series analysis)
    # Modeling phase will handle with appropriate imputation/exclusion
    
    print("✓ NULL handling: Preserved for downstream processing")
    print()
    
    return df


def remove_duplicate_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate columns."""
    print("REMOVING DUPLICATE COLUMNS")
    print("-" * 80)
    
    # Check for _x, _y suffixes
    x_cols = [col for col in df.columns if col.endswith('_x')]
    y_cols = [col for col in df.columns if col.endswith('_y')]
    
    if x_cols or y_cols:
        print(f"⚠ Warning: Found duplicate columns: {len(x_cols)} with _x, {len(y_cols)} with _y")
        print(f"  Columns: {x_cols + y_cols}")
    else:
        print("✓ No duplicate columns found")
    
    print()
    return df


def validate_output(df: pd.DataFrame) -> dict:
    """Validate the master dataset quality."""
    print("DATA QUALITY VALIDATION")
    print("=" * 80)
    
    validation = {}
    
    # 1. Row count
    validation['num_rows'] = len(df)
    validation['expected_rows'] = 2742  # From prices dataset
    validation['rows_check'] = abs(validation['num_rows'] - validation['expected_rows']) < 100
    
    print(f"Row Count: {validation['num_rows']:,} (expected ~{validation['expected_rows']:,}) "
          f"{'✓' if validation['rows_check'] else '✗'}")
    
    # 2. Column count
    validation['num_columns'] = len(df.columns)
    validation['expected_columns'] = 25
    validation['cols_check'] = validation['num_columns'] >= validation['expected_columns']
    
    print(f"Column Count: {validation['num_columns']} (expected ≥{validation['expected_columns']}) "
          f"{'✓' if validation['cols_check'] else '✗'}")
    
    # 3. Duplicate columns
    duplicate_cols = [col for col in df.columns if '_x' in col or '_y' in col]
    validation['has_duplicates'] = len(duplicate_cols) > 0
    validation['duplicate_check'] = not validation['has_duplicates']
    
    print(f"Duplicate Columns: {len(duplicate_cols)} {'✗' if validation['has_duplicates'] else '✓'}")
    
    # 4. Key columns present
    key_columns = ['barrio_id', 'year', 'quarter', 'preu_venda_total', 'renta_annual', 
                   'superficie_m2', 'antiguedad_anos']
    missing_key_cols = [col for col in key_columns if col not in df.columns]
    validation['key_cols_check'] = len(missing_key_cols) == 0
    
    print(f"Key Columns: {'✓ All present' if validation['key_cols_check'] else f'✗ Missing: {missing_key_cols}'}")
    
    # 5. Coverage
    validation['num_barrios'] = df['barrio_id'].nunique()
    validation['num_years'] = df['year'].nunique() if 'year' in df.columns else 0
    validation['num_quarters'] = df['quarter'].nunique() if 'quarter' in df.columns else 0
    
    print(f"\nCoverage:")
    print(f"  Neighborhoods: {validation['num_barrios']}")
    print(f"  Years: {validation['num_years']}")
    print(f"  Quarters per year: {validation['num_quarters']}")
    
    # Overall pass/fail
    validation['passed'] = all([
        validation['rows_check'],
        validation['cols_check'],
        validation['duplicate_check'],
        validation['key_cols_check']
    ])
    
    print(f"\n{'✅ ALL CHECKS PASSED' if validation['passed'] else '⚠️ SOME CHECKS FAILED'}")
    print()
    
    return validation


def save_master_table(df: pd.DataFrame, output_path: Path) -> None:
    """Save the analytical base table."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    
    print(f"✓ Saved master table: {output_path}")
    print(f"  Size: {output_path.stat().st_size / 1024:.1f} KB")


def main() -> int:
    """Main execution."""
    output_path = PROJECT_ROOT / "data" / "processed" / "barcelona_housing_master_table.csv"
    
    print("=" * 80)
    print("ANALYTICAL BASE TABLE (ABT) CREATION")
    print("=" * 80)
    print()
    
    try:
        # 1. Load all datasets
        datasets = load_datasets()
        
        # 2. Merge temporal data (prices + renta)
        temporal_merged = merge_temporal_data(datasets['prices'], datasets['renta'])
        
        # 3. Broadcast static attributes
        full_merged = broadcast_static_attributes(
            temporal_merged,
            datasets['structural'],
            datasets['advanced']
        )
        
        # 4. Feature engineering
        engineered = feature_engineering(full_merged)
        
        # 5. Handle missing values
        cleaned = handle_missing_values(engineered)
        
        # 6. Remove duplicates
        final = remove_duplicate_columns(cleaned)
        
        # 7. Validate
        validation = validate_output(final)
        
        # 8. Save
        save_master_table(final, output_path)
        
        print()
        print("=" * 80)
        print("✅ MASTER TABLE CREATION COMPLETE")
        print("=" * 80)
        print(f"\nOutput: {output_path}")
        print(f"Records: {len(final):,}")
        print(f"Features: {len(final.columns)}")
        print(f"\nStatus: {'READY FOR MODELING' if validation['passed'] else 'REVIEW REQUIRED'}")
        
        return 0 if validation['passed'] else 1
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
