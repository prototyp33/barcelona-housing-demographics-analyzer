#!/usr/bin/env python3
"""
Validate master table quality and generate quality report.

Checks for:
- Missing data patterns
- Abrupt changes
- Outliers
- Data completeness
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict, List

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def validate_master_table(df: pd.DataFrame) -> Dict:
    """
    Validate master table and generate quality report.
    
    Args:
        df: Master table DataFrame
    
    Returns:
        Dictionary with validation results
    """
    results = {
        'total_records': len(df),
        'barrios': df['barrio_id'].nunique(),
        'years': sorted(df['anio'].unique()),
        'issues': []
    }
    
    # 1. Check for missing data patterns
    missing_price_years = df[df['precio_m2_venta_promedio'].isna()].groupby('anio').size()
    if len(missing_price_years) > 0:
        results['issues'].append({
            'type': 'missing_data',
            'severity': 'medium',
            'description': f'Años con precios faltantes: {missing_price_years.to_dict()}',
            'affected_years': missing_price_years.index.tolist()
        })
    
    # 2. Check for abrupt changes
    if 'cambio_extremo_venta' in df.columns:
        extreme_changes = df[df['cambio_extremo_venta'] == 1]
        if len(extreme_changes) > 0:
            results['issues'].append({
                'type': 'extreme_changes',
                'severity': 'high',
                'description': f'{len(extreme_changes)} cambios extremos (>100%) en precio de venta',
                'affected_barrios': extreme_changes['barrio_nombre'].unique().tolist(),
                'affected_years': extreme_changes['anio'].unique().tolist()
            })
    
    # 3. Check for outliers
    if 'outlier_precio_venta' in df.columns:
        outliers = df[df['outlier_precio_venta'] == 1]
        if len(outliers) > 0:
            results['issues'].append({
                'type': 'outliers',
                'severity': 'medium',
                'description': f'{len(outliers)} outliers estadísticos detectados',
                'affected_barrios': outliers['barrio_nombre'].unique().tolist()
            })
    
    # 4. Check data completeness
    if 'completitud_datos' in df.columns:
        low_completeness = df[df['completitud_datos'] < 50]
        if len(low_completeness) > 0:
            results['issues'].append({
                'type': 'low_completeness',
                'severity': 'medium',
                'description': f'{len(low_completeness)} registros con completitud <50%',
                'avg_completeness': df['completitud_datos'].mean()
            })
    
    # 5. Check for data gaps by barrio
    all_years = set(df['anio'].unique())
    barrios_with_gaps = []
    
    for barrio_id in df['barrio_id'].unique():
        barrio_data = df[df['barrio_id'] == barrio_id]
        barrio_years = set(barrio_data['anio'].unique())
        missing_years = all_years - barrio_years
        
        if missing_years:
            barrios_with_gaps.append({
                'barrio_id': barrio_id,
                'barrio_nombre': barrio_data['barrio_nombre'].iloc[0],
                'missing_years': sorted(missing_years),
                'coverage_pct': (len(barrio_years) / len(all_years)) * 100
            })
    
    if barrios_with_gaps:
        results['issues'].append({
            'type': 'data_gaps',
            'severity': 'low',
            'description': f'{len(barrios_with_gaps)} barrios con años faltantes',
            'barrios': barrios_with_gaps[:10]  # Top 10
        })
    
    return results


def print_validation_report(results: Dict):
    """Print validation report."""
    print("=" * 80)
    print("VALIDACIÓN DE CALIDAD - TABLA MAESTRA")
    print("=" * 80)
    
    print(f"\n📊 Resumen General:")
    print(f"   Total registros: {results['total_records']:,}")
    print(f"   Barrios: {results['barrios']}")
    print(f"   Años: {results['years'][0]:.0f} - {results['years'][-1]:.0f} ({len(results['years'])} años)")
    
    print(f"\n🔍 Problemas Detectados: {len(results['issues'])}")
    
    for i, issue in enumerate(results['issues'], 1):
        severity_icon = {
            'high': '🔴',
            'medium': '🟠',
            'low': '🟡'
        }.get(issue['severity'], '⚪')
        
        print(f"\n{i}. {severity_icon} {issue['type'].upper()} ({issue['severity']})")
        print(f"   {issue['description']}")
        
        if 'affected_barrios' in issue and len(issue['affected_barrios']) > 0:
            print(f"   Barrios afectados: {', '.join(issue['affected_barrios'][:5])}")
            if len(issue['affected_barrios']) > 5:
                print(f"   ... y {len(issue['affected_barrios']) - 5} más")
        
        if 'affected_years' in issue:
            print(f"   Años afectados: {issue['affected_years']}")
    
    # Overall quality score
    if results['issues']:
        high_severity = sum(1 for i in results['issues'] if i['severity'] == 'high')
        medium_severity = sum(1 for i in results['issues'] if i['severity'] == 'medium')
        
        if high_severity == 0 and medium_severity == 0:
            quality_score = "✅ BUENA"
        elif high_severity == 0:
            quality_score = "🟠 ACEPTABLE"
        else:
            quality_score = "🔴 REQUIERE ATENCIÓN"
        
        print(f"\n📈 Calidad General: {quality_score}")
    else:
        print(f"\n📈 Calidad General: ✅ EXCELENTE (sin problemas detectados)")


def main():
    """Main validation function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate master table quality')
    parser.add_argument('--input', type=str,
                       default='data/exports/looker_studio/master_table_barcelona_housing.csv',
                       help='Input CSV file')
    
    args = parser.parse_args()
    
    input_path = PROJECT_ROOT / args.input
    
    if not input_path.exists():
        print(f"❌ File not found: {input_path}")
        return 1
    
    print(f"📂 Loading: {input_path}")
    df = pd.read_csv(input_path)
    
    print(f"✅ Loaded {len(df):,} rows")
    print(f"🔍 Validating...")
    
    results = validate_master_table(df)
    print_validation_report(results)
    
    # Export issues to CSV
    if results['issues']:
        issues_df = pd.DataFrame(results['issues'])
        output_path = PROJECT_ROOT / "data" / "exports" / "anomalies" / "quality_issues.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        issues_df.to_csv(output_path, index=False)
        print(f"\n💾 Issues exported to: {output_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
