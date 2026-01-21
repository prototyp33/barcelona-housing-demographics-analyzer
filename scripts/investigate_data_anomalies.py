#!/usr/bin/env python3
"""
Investigate data anomalies in master table.

Identifies:
- Abrupt changes year-over-year
- Missing data patterns
- Structural issues in data aggregation
- Outliers and suspicious values
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def load_master_table() -> pd.DataFrame:
    """Load master table from CSV."""
    csv_path = PROJECT_ROOT / "data" / "exports" / "looker_studio" / "master_table_barcelona_housing.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Master table not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.replace(' ', '_').str.lower().str.strip()
    return df


def detect_abrupt_changes(df: pd.DataFrame, threshold_pct: float = 50.0) -> pd.DataFrame:
    """
    Detect abrupt year-over-year changes in prices.
    
    Args:
        df: Master table DataFrame
        threshold_pct: Percentage change threshold to flag as abrupt
    
    Returns:
        DataFrame with abrupt changes
    """
    df_sorted = df.sort_values(['barrio_id', 'anio']).copy()
    
    # Calculate year-over-year percentage change
    df_sorted['precio_change_pct'] = df_sorted.groupby('barrio_id')['precio_m2_venta_promedio'].pct_change(fill_method=None) * 100
    df_sorted['alquiler_change_pct'] = df_sorted.groupby('barrio_id')['precio_mes_alquiler_promedio'].pct_change(fill_method=None) * 100
    
    # Detect abrupt changes
    abrupt_venta = df_sorted[
        (df_sorted['precio_change_pct'].abs() > threshold_pct) & 
        df_sorted['precio_change_pct'].notna()
    ].copy()
    
    abrupt_alquiler = df_sorted[
        (df_sorted['alquiler_change_pct'].abs() > threshold_pct) & 
        df_sorted['alquiler_change_pct'].notna()
    ].copy()
    
    return abrupt_venta, abrupt_alquiler


def analyze_data_gaps(df: pd.DataFrame) -> Dict:
    """
    Analyze gaps in data coverage.
    
    Returns:
        Dictionary with gap analysis
    """
    gaps_analysis = {}
    
    # For each barrio, identify missing years
    for barrio_id in df['barrio_id'].unique():
        barrio_data = df[df['barrio_id'] == barrio_id].sort_values('anio')
        barrio_name = barrio_data['barrio_nombre'].iloc[0]
        
        # Expected years (all years in dataset)
        all_years = sorted(df['anio'].unique())
        barrio_years = sorted(barrio_data['anio'].unique())
        missing_years = [y for y in all_years if y not in barrio_years]
        
        # Years with null prices
        years_with_null_prices = barrio_data[
            barrio_data['precio_m2_venta_promedio'].isna()
        ]['anio'].tolist()
        
        # Years with zero or very low prices (potential data issues)
        years_with_low_prices = barrio_data[
            (barrio_data['precio_m2_venta_promedio'] < 500) & 
            barrio_data['precio_m2_venta_promedio'].notna()
        ]['anio'].tolist()
        
        if missing_years or years_with_null_prices or years_with_low_prices:
            gaps_analysis[barrio_id] = {
                'barrio_nombre': barrio_name,
                'missing_years': missing_years,
                'null_price_years': years_with_null_prices,
                'low_price_years': years_with_low_prices,
                'total_years': len(barrio_years),
                'expected_years': len(all_years)
            }
    
    return gaps_analysis


def analyze_price_distribution_by_year(df: pd.DataFrame) -> pd.DataFrame:
    """Analyze price distribution statistics by year."""
    stats_by_year = df.groupby('anio')['precio_m2_venta_promedio'].agg([
        'count', 'mean', 'std', 'min', 'max', 
        lambda x: x.quantile(0.25), lambda x: x.quantile(0.75)
    ]).reset_index()
    stats_by_year.columns = ['anio', 'count', 'mean', 'std', 'min', 'max', 'q25', 'q75']
    stats_by_year['cv'] = stats_by_year['std'] / stats_by_year['mean'] * 100  # Coefficient of variation
    return stats_by_year


def identify_outliers(df: pd.DataFrame, z_threshold: float = 3.0) -> pd.DataFrame:
    """
    Identify outliers using Z-score method.
    
    Args:
        df: Master table DataFrame
        z_threshold: Z-score threshold (default 3.0 = 3 standard deviations)
    
    Returns:
        DataFrame with outliers flagged
    """
    df_outliers = df.copy()
    
    # Calculate Z-scores for prices by year (to account for inflation/trends)
    for year in df['anio'].unique():
        year_mask = df['anio'] == year
        year_prices = df.loc[year_mask, 'precio_m2_venta_promedio'].dropna()
        
        if len(year_prices) > 1:
            mean_price = year_prices.mean()
            std_price = year_prices.std()
            
            if std_price > 0:
                z_scores = (df.loc[year_mask, 'precio_m2_venta_promedio'] - mean_price) / std_price
                df_outliers.loc[year_mask, 'z_score'] = z_scores
    
    outliers = df_outliers[
        (df_outliers['z_score'].abs() > z_threshold) & 
        df_outliers['z_score'].notna()
    ].copy()
    
    return outliers


def main():
    """Main analysis function."""
    print("=" * 80)
    print("INVESTIGACIÓN DE ANOMALÍAS EN DATOS")
    print("=" * 80)
    
    # Load data
    print("\n📂 Cargando tabla maestra...")
    df = load_master_table()
    print(f"   ✅ Cargados {len(df):,} registros")
    print(f"   📅 Años: {df['anio'].min():.0f} - {df['anio'].max():.0f}")
    print(f"   🏘️ Barrios: {df['barrio_id'].nunique()}")
    
    # 1. Detect abrupt changes
    print("\n" + "=" * 80)
    print("1. DETECCIÓN DE CAMBIOS ABRUPTOS (>50% año a año)")
    print("=" * 80)
    
    abrupt_venta, abrupt_alquiler = detect_abrupt_changes(df, threshold_pct=50.0)
    
    print(f"\n📊 Cambios abruptos en PRECIO DE VENTA: {len(abrupt_venta)}")
    if len(abrupt_venta) > 0:
        print("\nTop 15 cambios más extremos:")
        top_changes = abrupt_venta.nlargest(15, 'precio_change_pct', keep='all')
        for idx, row in top_changes.iterrows():
            print(f"   {row['barrio_nombre']:30s} | Año {row['anio']:.0f} | "
                  f"Cambio: {row['precio_change_pct']:+7.1f}% | "
                  f"Precio: {row['precio_m2_venta_promedio']:,.0f} €/m²")
    
    print(f"\n📊 Cambios abruptos en PRECIO DE ALQUILER: {len(abrupt_alquiler)}")
    if len(abrupt_alquiler) > 0:
        print("\nTop 15 cambios más extremos:")
        top_changes = abrupt_alquiler.nlargest(15, 'alquiler_change_pct', keep='all')
        for idx, row in top_changes.iterrows():
            print(f"   {row['barrio_nombre']:30s} | Año {row['anio']:.0f} | "
                  f"Cambio: {row['alquiler_change_pct']:+7.1f}% | "
                  f"Precio: {row['precio_mes_alquiler_promedio']:,.0f} €/mes")
    
    # 2. Analyze data gaps
    print("\n" + "=" * 80)
    print("2. ANÁLISIS DE LAGUNAS DE DATOS")
    print("=" * 80)
    
    gaps = analyze_data_gaps(df)
    barrios_with_gaps = {k: v for k, v in gaps.items() if v['missing_years'] or v['null_price_years']}
    
    print(f"\n📊 Barrios con lagunas de datos: {len(barrios_with_gaps)}")
    if len(barrios_with_gaps) > 0:
        print("\nTop 10 barrios con más problemas:")
        sorted_gaps = sorted(barrios_with_gaps.items(), 
                           key=lambda x: len(x[1]['missing_years']) + len(x[1]['null_price_years']), 
                           reverse=True)
        for barrio_id, info in sorted_gaps[:10]:
            issues = []
            if info['missing_years']:
                issues.append(f"{len(info['missing_years'])} años faltantes")
            if info['null_price_years']:
                issues.append(f"{len(info['null_price_years'])} años con precios nulos")
            if info['low_price_years']:
                issues.append(f"{len(info['low_price_years'])} años con precios sospechosamente bajos")
            
            print(f"   {info['barrio_nombre']:30s} | {', '.join(issues)}")
    
    # 3. Price distribution by year
    print("\n" + "=" * 80)
    print("3. DISTRIBUCIÓN DE PRECIOS POR AÑO")
    print("=" * 80)
    
    price_stats = analyze_price_distribution_by_year(df)
    print("\nEstadísticas de precios por año:")
    print(price_stats.to_string(index=False))
    
    # Identify years with high variability (potential data quality issues)
    high_cv_years = price_stats[price_stats['cv'] > 50]
    if len(high_cv_years) > 0:
        print("\n⚠️ Años con alta variabilidad (CV > 50%):")
        for _, row in high_cv_years.iterrows():
            print(f"   Año {row['anio']:.0f}: CV = {row['cv']:.1f}% | "
                  f"Rango: {row['min']:,.0f} - {row['max']:,.0f} €/m²")
    
    # 4. Identify outliers
    print("\n" + "=" * 80)
    print("4. DETECCIÓN DE OUTLIERS (Z-score > 3)")
    print("=" * 80)
    
    outliers = identify_outliers(df, z_threshold=3.0)
    print(f"\n📊 Outliers detectados: {len(outliers)}")
    if len(outliers) > 0:
        print("\nTop 15 outliers más extremos:")
        top_outliers = outliers.nlargest(15, 'z_score', keep='all')
        for idx, row in top_outliers.iterrows():
            print(f"   {row['barrio_nombre']:30s} | Año {row['anio']:.0f} | "
                  f"Z-score: {row['z_score']:+6.2f} | "
                  f"Precio: {row['precio_m2_venta_promedio']:,.0f} €/m²")
    
    # 5. Summary and recommendations
    print("\n" + "=" * 80)
    print("5. RESUMEN Y RECOMENDACIONES")
    print("=" * 80)
    
    print("\n📋 Resumen de problemas detectados:")
    print(f"   • Cambios abruptos en venta: {len(abrupt_venta)}")
    print(f"   • Cambios abruptos en alquiler: {len(abrupt_alquiler)}")
    print(f"   • Barrios con lagunas: {len(barrios_with_gaps)}")
    print(f"   • Outliers estadísticos: {len(outliers)}")
    
    print("\n💡 Recomendaciones:")
    print("   1. Verificar cambios abruptos >100% - pueden ser errores de datos")
    print("   2. Investigar barrios con múltiples años faltantes")
    print("   3. Revisar outliers extremos para validar si son reales o errores")
    print("   4. Considerar suavizar datos con medias móviles para visualizaciones")
    print("   5. Documentar años con alta variabilidad como períodos de transición")
    
    # Export results
    output_dir = PROJECT_ROOT / "data" / "exports" / "anomalies"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    abrupt_venta.to_csv(output_dir / "abrupt_changes_venta.csv", index=False)
    abrupt_alquiler.to_csv(output_dir / "abrupt_changes_alquiler.csv", index=False)
    outliers.to_csv(output_dir / "outliers.csv", index=False)
    
    print(f"\n✅ Resultados exportados a: {output_dir}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
