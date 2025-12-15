#!/usr/bin/env python3
"""
Extract structural attributes for Barcelona neighborhoods from Open Data BCN.

Phase 1: Building construction year aggregation to calculate average building age.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def parse_construction_year_range(year_str: str) -> Tuple[float, float]:
    """
    Parse construction year string into (midpoint, uncertainty) tuple.
    
    Args:
        year_str: Year string like "<1901", "1901-1940", "2005", etc.
        
    Returns:
        Tuple of (midpoint_year, range_span) for weighting
        
    Examples:
        >>> parse_construction_year_range("<1901")
        (1850.0, 51.0)
        >>> parse_construction_year_range("1901-1940")
        (1920.5, 39.0)
        >>> parse_construction_year_range("2005")
        (2005.0, 0.0)
    """
    year_str = str(year_str).strip()
    
    # Handle individual years
    if year_str.isdigit():
        year = float(year_str)
        return (year, 0.0)
    
    # Handle "<1901" (before 1901)
    if year_str.startswith("<"):
        cutoff = float(year_str[1:])
        # Assume buildings could be from 1800-cutoff, use midpoint
        midpoint = (1800 + cutoff) / 2.0
        span = cutoff - 1800
        return (midpoint, span)
    
    # Handle ranges like "1901-1940"
    if "-" in year_str:
        parts = year_str.split("-")
        if len(parts) == 2:
            try:
                start = float(parts[0])
                end = float(parts[1])
                midpoint = (start + end) / 2.0
                span = end - start
                return (midpoint, span)
            except ValueError:
                pass
    
    # Handle ">2020" (after 2020) - unlikely but possible
    if year_str.startswith(">"):
        cutoff = float(year_str[1:])
        midpoint = cutoff + 5.0  # Assume avg 5 years after cutoff
        return (midpoint, 10.0)
    
    # Fallback: try to parse as number
    try:
        year = float(year_str)
        return (year, 0.0)
    except ValueError:
        # Unknown format, use modern default
        print(f"Warning: Could not parse year '{year_str}', using 2000")
        return (2000.0, 25.0)


def load_building_age_data(csv_path: Path) -> pd.DataFrame:
    """
    Load building construction year data from Open Data BCN CSV.
    
    Args:
        csv_path: Path to the construction year CSV file
        
    Returns:
        DataFrame with columns: Codi_barri, Any_construccio, Nombre
    """
    print(f"Loading building age data from: {csv_path}")
    df = pd.read_csv(csv_path)
    
    # Verify required columns
    required_cols = ["Codi_barri", "Any_construccio", "Nombre"]
    missing = set(required_cols) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    print(f"Loaded {len(df):,} records from {df['Codi_barri'].nunique()} neighborhoods")
    return df


def aggregate_to_neighborhoods(df: pd.DataFrame, reference_year: int = 2025) -> pd.DataFrame:
    """
    Aggregate building construction data from census sections to neighborhoods.
    
    Args:
        df: DataFrame with Codi_barri, Any_construccio, Nombre
        reference_year: Current year for age calculations (default 2025)
        
    Returns:
        DataFrame with one row per neighborhood containing aggregated metrics
    """
    print("Parsing construction years and calculating midpoints...")
    
    # Parse year ranges to midpoints
    df_parsed = df.copy()
    year_data = df_parsed["Any_construccio"].apply(parse_construction_year_range)
    df_parsed["year_midpoint"] = year_data.apply(lambda x: x[0])
    df_parsed["year_range_span"] = year_data.apply(lambda x: x[1])
    
    # Clean and convert types
    df_parsed["Codi_barri"] = pd.to_numeric(df_parsed["Codi_barri"], errors="coerce")
    df_parsed["Nombre"] = pd.to_numeric(df_parsed["Nombre"], errors="coerce")
    
    # Remove invalid data
    df_parsed = df_parsed.dropna(subset=["Codi_barri", "year_midpoint", "Nombre"])
    df_parsed = df_parsed[df_parsed["Nombre"] > 0]  # Only positive counts
    
    print(f"Aggregating {len(df_parsed):,} valid records to neighborhood level...")
    
    # Calculate weighted average construction year per neighborhood
    def weighted_avg(group):
        return (group["year_midpoint"] * group["Nombre"]).sum() / group["Nombre"].sum()
    
    def calc_percentiles(group):
        """Calculate distribution statistics."""
        # Create weighted list for percentile calculation
        years = []
        for _, row in group.iterrows():
            years.extend([row["year_midpoint"]] * int(row["Nombre"]))
        
        return pd.Series({
            "year_p25": pd.Series(years).quantile(0.25) if years else None,
            "year_median": pd.Series(years).quantile(0.50) if years else None,
            "year_p75": pd.Series(years).quantile(0.75) if years else None,
        })
    
    aggregated = df_parsed.groupby("Codi_barri").apply(
        lambda g: pd.Series({
            "anyo_construccion_promedio": weighted_avg(g),
            "num_edificios": int(g["Nombre"].sum()),
            "anyo_min": g["year_midpoint"].min(),
            "anyo_max": g["year_midpoint"].max(),
            **calc_percentiles(g),
        })
    ).reset_index()
    
    # Rename Codi_barri to barrio_id for consistency
    aggregated = aggregated.rename(columns={"Codi_barri": "barrio_id"})
    
    # Calculate age in years
    aggregated["antiguedad_anos"] = reference_year - aggregated["anyo_construccion_promedio"]
    
    # Calculate percentage of old buildings (pre-1950)
    pre_1950 = df_parsed[df_parsed["year_midpoint"] < 1950].groupby("Codi_barri")["Nombre"].sum()
    total = df_parsed.groupby("Codi_barri")["Nombre"].sum()
    pct_old = (pre_1950 / total * 100).fillna(0)
    
    aggregated["pct_edificios_pre1950"] = aggregated["barrio_id"].map(pct_old).fillna(0)
    
    # Add metadata
    aggregated["source"] = "opendatabcn_est-cadastre"
    aggregated["etl_loaded_at"] = datetime.now().isoformat()
    
    # Ensure barrio_id is integer
    aggregated["barrio_id"] = aggregated["barrio_id"].astype(int)
    
    print(f"✓ Aggregated to {len(aggregated)} neighborhoods")
    return aggregated


def load_barrio_names(db_path: Path) -> pd.DataFrame:
    """
    Load neighborhood names from dim_barrios to add to output.
    
    Args:
        db_path: Path to SQLite database
        
    Returns:
        DataFrame with barrio_id and barrio_nombre
    """
    import sqlite3
    
    if not db_path.exists():
        print(f"Warning: Database not found at {db_path}, skipping name lookup")
        return pd.DataFrame(columns=["barrio_id", "barrio_nombre"])
    
    print(f"Loading neighborhood names from database...")
    conn = sqlite3.connect(db_path)
    query = "SELECT barrio_id, barrio_nombre FROM dim_barrios ORDER BY barrio_id;"
    
    try:
        barrio_names = pd.read_sql_query(query, conn)
        print(f"✓ Loaded names for {len(barrio_names)} neighborhoods")
        return barrio_names
    except Exception as e:
        print(f"Warning: Could not load names from database: {e}")
        return pd.DataFrame(columns=["barrio_id", "barrio_nombre"])
    finally:
        conn.close()


def save_structural_attributes(
    df: pd.DataFrame,
    output_path: Path,
) -> None:
    """
    Save structural attributes to CSV file.
    
    Args:
        df: DataFrame with structural attributes
        output_path: Path where to save the CSV
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Order columns for readability
    column_order = [
        "barrio_id",
        "barrio_nombre",
        "anyo_construccion_promedio",
        "antiguedad_anos",
        "num_edificios",
        "anyo_min",
        "anyo_max",
        "year_p25",
        "year_median",
        "year_p75",
        "pct_edificios_pre1950",
        "source",
        "etl_loaded_at",
    ]
    
    # Only include columns that exist
    available_cols = [col for col in column_order if col in df.columns]
    df_ordered = df[available_cols]
    
    # Round numeric columns for readability
    numeric_cols = df_ordered.select_dtypes(include=["float64"]).columns
    df_ordered[numeric_cols] = df_ordered[numeric_cols].round(2)
    
    # Save to CSV
    df_ordered.to_csv(output_path, index=False)
    print(f"✓ Saved structural attributes to: {output_path}")
    print(f"  Records: {len(df_ordered)}")
    print(f"  Columns: {', '.join(available_cols)}")


def main() -> int:
    """Main execution function."""
    # Paths
    data_raw = PROJECT_ROOT / "data" / "raw"
    data_processed = PROJECT_ROOT / "data" / "processed"
    
    construction_year_csv = data_raw / "opendatabcn" / "opendatabcn_est-cadastre-edificacions-any-const_20251114_162852_617168.csv"
    database_path = data_processed / "database.db"
    output_csv = data_raw / "barrio_structural_attributes.csv"
    
    print("=" * 80)
    print("STRUCTURAL ATTRIBUTES EXTRACTION - Phase 1: Building Age")
    print("=" * 80)
    print()
    
    try:
        # Load and process data
        df_raw = load_building_age_data(construction_year_csv)
        df_aggregated = aggregate_to_neighborhoods(df_raw, reference_year=2025)
        
        # Add neighborhood names
        barrio_names = load_barrio_names(database_path)
        if not barrio_names.empty:
            df_aggregated = df_aggregated.merge(
                barrio_names,
                on="barrio_id",
                how="left"
            )
        else:
            df_aggregated["barrio_nombre"] = None
        
        # Save output
        save_structural_attributes(df_aggregated, output_csv)
        
        # Print summary statistics
        print()
        print("SUMMARY STATISTICS")
        print("-" * 80)
        print(f"Average construction year: {df_aggregated['anyo_construccion_promedio'].mean():.1f}")
        print(f"Average building age: {df_aggregated['antiguedad_anos'].mean():.1f} years")
        print(f"Oldest neighborhood avg: {df_aggregated['anyo_construccion_promedio'].min():.1f}")
        print(f"Newest neighborhood avg: {df_aggregated['anyo_construccion_promedio'].max():.1f}")
        print(f"Total buildings counted: {df_aggregated['num_edificios'].sum():,}")
        print()
        print("✅ Extraction complete!")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error during extraction: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
