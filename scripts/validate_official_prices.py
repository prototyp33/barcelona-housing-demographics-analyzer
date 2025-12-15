#!/usr/bin/env python3
"""
Validation script for official_prices_2015_2024.csv

Performs data quality checks specific to financial time series:
- Temporal continuity (missing quarters)
- Financial logic (sales > rental, price ranges)
- Missing neighborhoods detection
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def load_official_prices(csv_path: Path) -> pd.DataFrame:
    """Load the official prices CSV."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Official prices file not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df):,} records from {csv_path.name}")
    return df


def load_dim_barrios() -> pd.DataFrame:
    """Load all 73 neighborhoods from database."""
    import sqlite3
    
    db_path = PROJECT_ROOT / "data" / "processed" / "database.db"
    if not db_path.exists():
        print("Warning: Database not found, cannot verify missing neighborhoods")
        return pd.DataFrame()
    
    conn = sqlite3.connect(db_path)
    query = "SELECT barrio_id, barrio_nombre, codi_barri FROM dim_barrios ORDER BY barrio_id;"
    dim_barrios = pd.read_sql_query(query, conn)
    conn.close()
    
    return dim_barrios


def check_temporal_continuity(df: pd.DataFrame) -> Dict:
    """
    Check for missing quarters (gaps) in time series.
    
    Key neighborhoods should have continuous quarterly data.
    """
    print("\nCHECKING TEMPORAL CONTINUITY")
    print("-" * 80)
    
    # Expected quarters per year
    expected_quarters = ['Q1', 'Q2', 'Q3', 'Q4']
    
    # Group by barrio and year
    coverage = df.groupby(['barrio_id', 'barrio_nombre', 'year'])['quarter'].apply(list).reset_index()
    
    # Find gaps
    gaps = []
    for _, row in coverage.iterrows():
        barrio_id = row['barrio_id']
        barrio_name = row['barrio_nombre']
        year = row['year']
        quarters = row['quarter']
        
        missing = set(expected_quarters) - set(quarters)
        if missing:
            gaps.append({
                'barrio_id': barrio_id,
                'barrio_nombre': barrio_name,
                'year': year,
                'quarters_missing': sorted(missing),
                'quarters_present': sorted(quarters)
            })
    
    # Check completeness by barrio
    barrio_summary = df.groupby('barrio_id').agg({
        'year': lambda x: f"{x.min()}-{x.max()}",
        'quarter': 'count',
        'barrio_nombre': 'first'
    }).reset_index()
    
    barrio_summary.columns = ['barrio_id', 'year_range', 'num_quarters', 'barrio_nombre']
    
    # Expected: 10 years × 4 quarters = 40 quarters max
    barrio_summary['completeness_pct'] = (barrio_summary['num_quarters'] / 40 * 100).round(1)
    
    # Identify neighborhoods with significant gaps
    incomplete = barrio_summary[barrio_summary['completeness_pct'] < 90].sort_values('completeness_pct')
    
    passed = len(gaps) == 0
    
    result = {
        'name': 'Temporal Continuity Check',
        'passed': passed,
        'total_gaps': len(gaps),
        'gaps_detail': gaps[:20],  # Top 20 gaps
        'incomplete_neighborhoods': incomplete.to_dict('records'),
        'barrio_summary': barrio_summary.to_dict('records'),
        'message': f"{'✓ PASS' if passed else '⚠ WARNING'}: {len(gaps)} quarter gaps found across all neighborhoods"
    }
    
    return result


def check_financial_logic(df: pd.DataFrame) -> Dict:
    """
    Validate financial logic:
    - Sales price should be much higher than rental (capitalization)
    - Price per m² should be in credible range
    """
    print("\nCHECKING FINANCIAL LOGIC")
    print("-" * 80)
    
    violations = []
    
    # Filter rows with both rental and sales data
    df_complete = df.dropna(subset=['preu_lloguer_mensual', 'preu_venda_total', 'preu_venda_m2'])
    
    # Check 1: Sales price should be >> rental price
    # Typical rental yield: 3-5% annually, so annual rent ≈ 3-5% of sale price
    # Monthly rent × 12 / sale_price should be < 0.10 (10%)
    df_complete['annual_rent'] = df_complete['preu_lloguer_mensual'] * 12
    df_complete['rent_to_price_ratio'] = df_complete['annual_rent'] / (df_complete['preu_venda_total'] * 1000)  # venda_total is in thousands
    
    # Flag if rental seems too high relative to sales (unrealistic yield >15%)
    high_yield = df_complete[df_complete['rent_to_price_ratio'] > 0.15]
    
    for _, row in high_yield.head(10).iterrows():
        violations.append({
            'type': 'Rental/Sales Ratio',
            'barrio': row['barrio_nombre'],
            'year': row['year'],
            'quarter': row['quarter'],
            'rental_monthly': f"€{row['preu_lloguer_mensual']:.0f}",
            'sales_total': f"€{row['preu_venda_total']:.0f}K",
            'annual_yield': f"{row['rent_to_price_ratio']*100:.1f}%",
            'issue': 'Suspiciously high rental yield (>15%)'
        })
    
    # Check 2: Price per m² should be in credible range (€1,000 - €10,000/m²)
    credible_min = 1000
    credible_max = 10000
    
    too_low = df_complete[df_complete['preu_venda_m2'] < credible_min]
    too_high = df_complete[df_complete['preu_venda_m2'] > credible_max]
    
    for _, row in too_low.head(5).iterrows():
        violations.append({
            'type': 'Price/m² Too Low',
            'barrio': row['barrio_nombre'],
            'year': row['year'],
            'quarter': row['quarter'],
            'price_m2': f"€{row['preu_venda_m2']:.0f}/m²",
            'issue': f'Below credible minimum (€{credible_min}/m²)'
        })
    
    for _, row in too_high.head(5).iterrows():
        violations.append({
            'type': 'Price/m² Too High',
            'barrio': row['barrio_nombre'],
            'year': row['year'],
            'quarter': row['quarter'],
            'price_m2': f"€{row['preu_venda_m2']:.0f}/m²",
            'issue': f'Above credible maximum (€{credible_max}/m²)'
        })
    
    # Summary stats
    price_m2_stats = {
        'mean': df_complete['preu_venda_m2'].mean(),
        'median': df_complete['preu_venda_m2'].median(),
        'min': df_complete['preu_venda_m2'].min(),
        'max': df_complete['preu_venda_m2'].max(),
        'pct_below_min': (df_complete['preu_venda_m2'] < credible_min).sum() / len(df_complete) * 100,
        'pct_above_max': (df_complete['preu_venda_m2'] > credible_max).sum() / len(df_complete) * 100
    }
    
    rent_yield_stats = {
        'mean': df_complete['rent_to_price_ratio'].mean() * 100,
        'median': df_complete['rent_to_price_ratio'].median() * 100,
        'min': df_complete['rent_to_price_ratio'].min() * 100,
        'max': df_complete['rent_to_price_ratio'].max() * 100,
        'pct_high_yield': (df_complete['rent_to_price_ratio'] > 0.15).sum() / len(df_complete) * 100
    }
    
    passed = len(violations) < 10  # Allow some anomalies
    
    result = {
        'name': 'Financial Logic Check',
        'passed': passed,
        'violations': violations,
        'price_m2_stats': price_m2_stats,
        'rent_yield_stats': rent_yield_stats,
        'message': f"{'✓ PASS' if passed else '⚠ WARNING'}: {len(violations)} financial logic violations found"
    }
    
    return result


def detect_missing_neighborhoods(df: pd.DataFrame, dim_barrios: pd.DataFrame) -> Dict:
    """
    Identify exactly which neighborhoods are missing from the dataset.
    """
    print("\nDETECTING MISSING NEIGHBORHOODS ('Barrios Fantasma')")
    print("-" * 80)
    
    if dim_barrios.empty:
        return {
            'name': 'Missing Neighborhoods Detection',
            'passed': None,
            'message': '⚠ SKIP: Cannot verify - database not available'
        }
    
    # Neighborhoods in database
    all_barrios = set(dim_barrios['barrio_id'].unique())
    
    # Neighborhoods in dataset
    present_barrios = set(df['barrio_id'].unique())
    
    # Missing neighborhoods
    missing_barrios = all_barrios - present_barrios
    
    missing_details = []
    if missing_barrios:
        missing_info = dim_barrios[dim_barrios['barrio_id'].isin(missing_barrios)]
        missing_details = missing_info.to_dict('records')
    
    passed = len(missing_barrios) <= 2  # We know 2 are expected
    
    result = {
        'name': 'Missing Neighborhoods Detection',
        'passed': passed,
        'total_expected': len(all_barrios),
        'total_present': len(present_barrios),
        'total_missing': len(missing_barrios),
        'missing_barrios': missing_details,
        'coverage_pct': len(present_barrios) / len(all_barrios) * 100,
        'message': f"{'✓ PASS' if passed else '✗ FAIL'}: {len(missing_barrios)} neighborhoods missing (expected ≤2)"
    }
    
    return result


def check_data_ranges(df: pd.DataFrame) -> Dict:
    """Check that prices are within expected ranges."""
    print("\nCHECKING PRICE RANGES")
    print("-" * 80)
    
    checks = []
    
    # Rental prices: €200 - €3,000/month is reasonable for Barcelona
    rental_min, rental_max = 200, 3000
    rental_ok = df['preu_lloguer_mensual'].between(rental_min, rental_max, inclusive='both')
    rental_outliers = df[~rental_ok & df['preu_lloguer_mensual'].notna()]
    
    checks.append({
        'field': 'preu_lloguer_mensual',
        'expected_range': f'€{rental_min}-€{rental_max}/month',
        'actual_range': f"€{df['preu_lloguer_mensual'].min():.0f}-€{df['preu_lloguer_mensual'].max():.0f}",
        'outliers': len(rental_outliers),
        'passed': len(rental_outliers) < 10
    })
    
    # Sales prices: €50K - €2M is reasonable
    sales_min, sales_max = 50, 2000  # in thousands
    sales_ok = df['preu_venda_total'].between(sales_min, sales_max, inclusive='both')
    sales_outliers = df[~sales_ok & df['preu_venda_total'].notna()]
    
    checks.append({
        'field': 'preu_venda_total',
        'expected_range': f'€{sales_min}K-€{sales_max}K',
        'actual_range': f"€{df['preu_venda_total'].min():.0f}K-€{df['preu_venda_total'].max():.0f}K",
        'outliers': len(sales_outliers),
        'passed': len(sales_outliers) < 10
    })
    
    passed = all(c['passed'] for c in checks)
    
    result = {
        'name': 'Price Range Check',
        'passed': passed,
        'checks': checks,
        'message': f"{'✓ PASS' if passed else '⚠ WARNING'}: Price ranges validated"
    }
    
    return result


def generate_summary_report(
    df: pd.DataFrame,
    temporal_result: Dict,
    financial_result: Dict,
    missing_result: Dict,
    ranges_result: Dict
) -> str:
    """Generate comprehensive validation report."""
    
    report = []
    report.append("=" * 80)
    report.append("OFFICIAL PRICES VALIDATION REPORT")
    report.append("=" * 80)
    report.append(f"Timestamp: {datetime.now().isoformat()}")
    report.append(f"Dataset: {len(df):,} records")
    report.append(f"Neighborhoods: {df['barrio_id'].nunique()}")
    report.append(f"Period: {df['year'].min()}-{df['year'].max()}")
    report.append("")
    
    # 1. Missing Neighborhoods ("Barrios Fantasma")
    report.append("1. BARRIOS FANTASMA (Missing Neighborhoods)")
    report.append("-" * 80)
    report.append(missing_result['message'])
    if missing_result.get('missing_barrios'):
        report.append(f"\nMissing {missing_result['total_missing']} neighborhoods:")
        for barrio in missing_result['missing_barrios']:
            report.append(f"  • ID {barrio['barrio_id']}: {barrio['barrio_nombre']} (Codi: {barrio.get('codi_barri', 'N/A')})")
        report.append(f"\nCoverage: {missing_result['coverage_pct']:.1f}% ({missing_result['total_present']}/{missing_result['total_expected']} barrios)")
    report.append("")
    
    # 2. Temporal Continuity
    report.append("2. CONTINUIDAD TEMPORAL (Quarter Gaps)")
    report.append("-" * 80)
    report.append(temporal_result['message'])
    
    if temporal_result['total_gaps'] > 0:
        report.append(f"\nFound {temporal_result['total_gaps']} quarter gaps (showing first 10):")
        for gap in temporal_result['gaps_detail'][:10]:
            report.append(f"  • {gap['barrio_nombre']} - {gap['year']}: Missing {', '.join(gap['quarters_missing'])}")
    
    # Show neighborhoods with <90% completeness
    incomplete = temporal_result.get('incomplete_neighborhoods', [])
    if incomplete:
        report.append(f"\nNeighborhoods with <90% temporal completeness:")
        for barrio in incomplete[:10]:
            report.append(f"  • {barrio['barrio_nombre']}: {barrio['completeness_pct']}% ({barrio['num_quarters']}/40 quarters)")
    
    report.append("")
    
    # 3. Financial Logic
    report.append("3. LÓGICA FINANCIERA")
    report.append("-" * 80)
    report.append(financial_result['message'])
    
    # Price/m² statistics
    pm2 = financial_result['price_m2_stats']
    report.append(f"\nPrice per m² Statistics:")
    report.append(f"  Mean: €{pm2['mean']:.0f}/m²")
    report.append(f"  Median: €{pm2['median']:.0f}/m²")
    report.append(f"  Range: €{pm2['min']:.0f} - €{pm2['max']:.0f}/m²")
    report.append(f"  Below €1,000/m²: {pm2['pct_below_min']:.1f}%")
    report.append(f"  Above €10,000/m²: {pm2['pct_above_max']:.1f}%")
    
    # Rental yield statistics
    ry = financial_result['rent_yield_stats']
    report.append(f"\nRental Yield Statistics:")
    report.append(f"  Mean: {ry['mean']:.2f}% annual")
    report.append(f"  Median: {ry['median']:.2f}% annual")
    report.append(f"  Range: {ry['min']:.2f}% - {ry['max']:.2f}%")
    report.append(f"  High yield (>15%): {ry['pct_high_yield']:.1f}%")
    
    if financial_result['violations']:
        report.append(f"\nFinancial Violations (showing first 10):")
        for v in financial_result['violations'][:10]:
            report.append(f"  • {v['barrio']} {v['year']}{v['quarter']}: {v['issue']}")
    
    report.append("")
    
    # 4. Price Ranges
    report.append("4. RANGOS DE PRECIOS")
    report.append("-" * 80)
    report.append(ranges_result['message'])
    for check in ranges_result['checks']:
        status = "✓" if check['passed'] else "✗"
        report.append(f"\n{status} {check['field']}:")
        report.append(f"  Expected: {check['expected_range']}")
        report.append(f"  Actual: {check['actual_range']}")
        report.append(f"  Outliers: {check['outliers']}")
    
    report.append("")
    
    # Final verdict
    report.append("=" * 80)
    all_passed = all([
        missing_result.get('passed', True),
        temporal_result.get('passed', True),
        financial_result.get('passed', True),
        ranges_result.get('passed', True)
    ])
    
    if all_passed:
        report.append("✅ ALL VALIDATIONS PASSED - Data quality sufficient for modeling")
    else:
        report.append("⚠️  SOME VALIDATIONS FAILED - Review warnings before modeling")
    report.append("=" * 80)
    
    return "\n".join(report)


def main() -> int:
    """Main execution."""
    csv_path = PROJECT_ROOT / "data" / "raw" / "official_prices_2015_2024.csv"
    
    print(f"Validating official prices: {csv_path}")
    print()
    
    try:
        # Load data
        df = load_official_prices(csv_path)
        dim_barrios = load_dim_barrios()
        
        # Run validations
        temporal_result = check_temporal_continuity(df)
        financial_result = check_financial_logic(df)
        missing_result = detect_missing_neighborhoods(df, dim_barrios)
        ranges_result = check_data_ranges(df)
        
        # Generate report
        report = generate_summary_report(
            df, temporal_result, financial_result, missing_result, ranges_result
        )
        
        # Print and save report
        print()
        print(report)
        
        # Save report
        report_dir = PROJECT_ROOT / "data" / "logs"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / "official_prices_validation.txt"
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        
        print()
        print(f"Report saved to: {report_path}")
        
        return 0
        
    except Exception as e:
        print(f"ERROR: Validation failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
