"""
Análisis del Mercado Inmobiliario de Barcelona

Análisis completo de precios de venta y alquiler:
1. Distribución de precios (histogramas, boxplots, test de normalidad)
2. Evolución temporal (2012-2025) indexada base 100
3. Impacto COVID vs inflación
4. Yield (rentabilidad bruta) por barrio
"""
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from scipy import stats
from datetime import datetime

# Configuración de visualización
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (16, 10)
plt.rcParams['font.size'] = 10

def load_price_data():
    """Carga datos de precios desde master.db"""
    db_path = Path("data/master.db")
    conn = sqlite3.connect(db_path)
    
    query = """
    SELECT 
        p.anio,
        p.barrio_id,
        b.barrio_nombre,
        b.distrito_nombre,
        p.precio_m2_venta,
        p.precio_mes_alquiler
    FROM fact_precios p
    LEFT JOIN dim_barrios b ON p.barrio_id = b.barrio_id
    WHERE p.precio_m2_venta IS NOT NULL OR p.precio_mes_alquiler IS NOT NULL
    ORDER BY p.anio, b.barrio_nombre
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    print(f"Datos cargados: {len(df):,} registros")
    print(f"Años: {df['anio'].min()} - {df['anio'].max()}")
    print(f"Barrios: {df['barrio_id'].nunique()}")
    
    return df

def analyze_distribution(df):
    """Analiza la distribución de precios"""
    print("\n" + "="*80)
    print("1. ANÁLISIS DE DISTRIBUCIÓN DE PRECIOS")
    print("="*80)
    
    # Crear figura con subplots
    fig = plt.figure(figsize=(18, 12))
    
    # ============================================================
    # PRECIOS DE VENTA
    # ============================================================
    venta_data = df['precio_m2_venta'].dropna()
    
    # Histograma + KDE
    ax1 = plt.subplot(3, 3, 1)
    ax1.hist(venta_data, bins=50, edgecolor='black', alpha=0.7, density=True)
    venta_data.plot(kind='kde', ax=ax1, color='red', linewidth=2)
    ax1.set_xlabel('Precio Venta (€/m²)')
    ax1.set_ylabel('Densidad')
    ax1.set_title('Distribución de Precios de Venta')
    ax1.axvline(venta_data.median(), color='green', linestyle='--', label=f'Mediana: {venta_data.median():.0f}')
    ax1.legend()
    
    # Histograma LOG
    ax2 = plt.subplot(3, 3, 2)
    log_venta = np.log(venta_data)
    ax2.hist(log_venta, bins=50, edgecolor='black', alpha=0.7, density=True)
    log_venta.plot(kind='kde', ax=ax2, color='red', linewidth=2)
    ax2.set_xlabel('Log(Precio Venta)')
    ax2.set_ylabel('Densidad')
    ax2.set_title('Distribución Log-Normal de Venta')
    
    # Q-Q Plot
    ax3 = plt.subplot(3, 3, 3)
    stats.probplot(venta_data, dist="norm", plot=ax3)
    ax3.set_title('Q-Q Plot: Venta vs Normal')
    
    # Boxplot por año
    ax4 = plt.subplot(3, 3, 4)
    df_venta = df[df['precio_m2_venta'].notna()].copy()
    df_venta.boxplot(column='precio_m2_venta', by='anio', ax=ax4)
    ax4.set_xlabel('Año')
    ax4.set_ylabel('Precio Venta (€/m²)')
    ax4.set_title('Boxplot de Precios de Venta por Año')
    plt.sca(ax4)
    plt.xticks(rotation=45)
    
    # ============================================================
    # PRECIOS DE ALQUILER
    # ============================================================
    alquiler_data = df['precio_mes_alquiler'].dropna()
    
    # Histograma + KDE
    ax5 = plt.subplot(3, 3, 5)
    ax5.hist(alquiler_data, bins=50, edgecolor='black', alpha=0.7, density=True)
    alquiler_data.plot(kind='kde', ax=ax5, color='blue', linewidth=2)
    ax5.set_xlabel('Precio Alquiler (€/mes)')
    ax5.set_ylabel('Densidad')
    ax5.set_title('Distribución de Precios de Alquiler')
    ax5.axvline(alquiler_data.median(), color='green', linestyle='--', label=f'Mediana: {alquiler_data.median():.0f}')
    ax5.legend()
    
    # Histograma LOG
    ax6 = plt.subplot(3, 3, 6)
    log_alquiler = np.log(alquiler_data)
    ax6.hist(log_alquiler, bins=50, edgecolor='black', alpha=0.7, density=True)
    log_alquiler.plot(kind='kde', ax=ax6, color='blue', linewidth=2)
    ax6.set_xlabel('Log(Precio Alquiler)')
    ax6.set_ylabel('Densidad')
    ax6.set_title('Distribución Log-Normal de Alquiler')
    
    # Q-Q Plot
    ax7 = plt.subplot(3, 3, 7)
    stats.probplot(alquiler_data, dist="norm", plot=ax7)
    ax7.set_title('Q-Q Plot: Alquiler vs Normal')
    
    # Boxplot por año
    ax8 = plt.subplot(3, 3, 8)
    df_alquiler = df[df['precio_mes_alquiler'].notna()].copy()
    df_alquiler.boxplot(column='precio_mes_alquiler', by='anio', ax=ax8)
    ax8.set_xlabel('Año')
    ax8.set_ylabel('Precio Alquiler (€/mes)')
    ax8.set_title('Boxplot de Precios de Alquiler por Año')
    plt.sca(ax8)
    plt.xticks(rotation=45)
    
    # Violin plot comparativo
    ax9 = plt.subplot(3, 3, 9)
    # Preparar datos para violin plot
    venta_norm = (venta_data - venta_data.mean()) / venta_data.std()
    alquiler_norm = (alquiler_data - alquiler_data.mean()) / alquiler_data.std()
    
    violin_data = pd.DataFrame({
        'Precio Normalizado': list(venta_norm) + list(alquiler_norm),
        'Tipo': ['Venta']*len(venta_norm) + ['Alquiler']*len(alquiler_norm)
    })
    
    sns.violinplot(data=violin_data, x='Tipo', y='Precio Normalizado', ax=ax9)
    ax9.set_title('Comparación de Distribuciones (Normalizado)')
    
    plt.tight_layout()
    plt.savefig('reports/analisis_distribucion_precios.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("\n📊 Gráfico guardado: reports/analisis_distribucion_precios.png")
    
    # Tests estadísticos
    print("\n" + "-"*80)
    print("TESTS DE NORMALIDAD")
    print("-"*80)
    
    # Shapiro-Wilk test (muestra aleatoria si hay muchos datos)
    sample_size = min(5000, len(venta_data))
    venta_sample = venta_data.sample(sample_size, random_state=42)
    alquiler_sample = alquiler_data.sample(min(sample_size, len(alquiler_data)), random_state=42)
    
    shapiro_venta = stats.shapiro(venta_sample)
    shapiro_alquiler = stats.shapiro(alquiler_sample)
    
    print(f"\nPRECIOS DE VENTA:")
    print(f"  Shapiro-Wilk: W={shapiro_venta.statistic:.4f}, p-value={shapiro_venta.pvalue:.4e}")
    print(f"  {'✗ NO normal' if shapiro_venta.pvalue < 0.05 else '✓ Normal'} (α=0.05)")
    
    # Test en escala logarítmica
    log_venta_sample = np.log(venta_sample)
    shapiro_log_venta = stats.shapiro(log_venta_sample)
    print(f"  Log-escala: W={shapiro_log_venta.statistic:.4f}, p-value={shapiro_log_venta.pvalue:.4e}")
    print(f"  {'✓ Log-Normal' if shapiro_log_venta.pvalue > shapiro_venta.pvalue else '✗ No Log-Normal'}")
    
    print(f"\nPRECIOS DE ALQUILER:")
    print(f"  Shapiro-Wilk: W={shapiro_alquiler.statistic:.4f}, p-value={shapiro_alquiler.pvalue:.4e}")
    print(f"  {'✗ NO normal' if shapiro_alquiler.pvalue < 0.05 else '✓ Normal'} (α=0.05)")
    
    log_alquiler_sample = np.log(alquiler_sample)
    shapiro_log_alquiler = stats.shapiro(log_alquiler_sample)
    print(f"  Log-escala: W={shapiro_log_alquiler.statistic:.4f}, p-value={shapiro_log_alquiler.pvalue:.4e}")
    print(f"  {'✓ Log-Normal' if shapiro_log_alquiler.pvalue > shapiro_alquiler.pvalue else '✗ No Log-Normal'}")
    
    # Estadísticas descriptivas
    print("\n" + "-"*80)
    print("ESTADÍSTICAS DESCRIPTIVAS")
    print("-"*80)
    
    print(f"\nPRECIOS DE VENTA (€/m²):")
    print(f"  Media: {venta_data.mean():,.2f}")
    print(f"  Mediana: {venta_data.median():,.2f}")
    print(f"  Desv. Std: {venta_data.std():,.2f}")
    print(f"  Min: {venta_data.min():,.2f}")
    print(f"  Max: {venta_data.max():,.2f}")
    print(f"  Q1: {venta_data.quantile(0.25):,.2f}")
    print(f"  Q3: {venta_data.quantile(0.75):,.2f}")
    print(f"  Skewness: {venta_data.skew():.2f}")
    print(f"  Kurtosis: {venta_data.kurtosis():.2f}")
    
    print(f"\nPRECIOS DE ALQUILER (€/mes):")
    print(f"  Media: {alquiler_data.mean():,.2f}")
    print(f"  Mediana: {alquiler_data.median():,.2f}")
    print(f"  Desv. Std: {alquiler_data.std():,.2f}")
    print(f"  Min: {alquiler_data.min():,.2f}")
    print(f"  Max: {alquiler_data.max():,.2f}")
    print(f"  Q1: {alquiler_data.quantile(0.25):,.2f}")
    print(f"  Q3: {alquiler_data.quantile(0.75):,.2f}")
    print(f"  Skewness: {alquiler_data.skew():.2f}")
    print(f"  Kurtosis: {alquiler_data.kurtosis():.2f}")

def analyze_temporal_evolution(df):
    """Analiza la evolución temporal de precios"""
    print("\n" + "="*80)
    print("2. EVOLUCIÓN TEMPORAL DE PRECIOS (BASE 100)")
    print("="*80)
    
    # Calcular promedios anuales
    yearly_avg = df.groupby('anio').agg({
        'precio_m2_venta': 'mean',
        'precio_mes_alquiler': 'mean'
    }).reset_index()
    
    # Indexar a base 100 (año 2015)
    base_year = 2015
    if base_year in yearly_avg['anio'].values:
        base_venta = yearly_avg[yearly_avg['anio'] == base_year]['precio_m2_venta'].values[0]
        base_alquiler = yearly_avg[yearly_avg['anio'] == base_year]['precio_mes_alquiler'].values[0]
        
        yearly_avg['index_venta'] = (yearly_avg['precio_m2_venta'] / base_venta) * 100
        yearly_avg['index_alquiler'] = (yearly_avg['precio_mes_alquiler'] / base_alquiler) * 100
    else:
        # Usar primer año disponible
        base_venta = yearly_avg['precio_m2_venta'].iloc[0]
        base_alquiler = yearly_avg['precio_mes_alquiler'].iloc[0]
        yearly_avg['index_venta'] = (yearly_avg['precio_m2_venta'] / base_venta) * 100
        yearly_avg['index_alquiler'] = (yearly_avg['precio_mes_alquiler'] / base_alquiler) * 100
    
    # Inflación España (datos aproximados)
    inflation_data = {
        2012: 100.0,
        2013: 101.4,
        2014: 101.2,
        2015: 100.0,  # Base
        2016: 99.8,
        2017: 101.8,
        2018: 103.5,
        2019: 104.3,
        2020: 103.6,  # COVID
        2021: 107.0,
        2022: 116.0,
        2023: 120.0,
        2024: 123.5,
        2025: 126.0
    }
    
    yearly_avg['inflacion'] = yearly_avg['anio'].map(inflation_data)
    
    # Crear gráfico
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12))
    
    # Gráfico 1: Índices
    ax1.plot(yearly_avg['anio'], yearly_avg['index_venta'], marker='o', linewidth=2.5, 
             label='Precio Venta', color='#2E86AB', markersize=8)
    ax1.plot(yearly_avg['anio'], yearly_avg['index_alquiler'], marker='s', linewidth=2.5,
             label='Precio Alquiler', color='#A23B72', markersize=8)
    ax1.plot(yearly_avg['anio'], yearly_avg['inflacion'], marker='^', linewidth=2,
             label='Inflación (IPC)', color='#F18F01', linestyle='--', markersize=8)
    
    # Marcar COVID
    ax1.axvline(x=2020, color='red', linestyle=':', alpha=0.5, linewidth=2)
    ax1.text(2020, ax1.get_ylim()[1]*0.95, 'COVID-19', rotation=90, 
             verticalalignment='top', color='red', fontsize=10)
    
    ax1.axhline(y=100, color='gray', linestyle='--', alpha=0.3)
    ax1.set_xlabel('Año', fontsize=12)
    ax1.set_ylabel('Índice (Base 100)', fontsize=12)
    ax1.set_title('Evolución de Precios Inmobiliarios vs Inflación (Base 100 = 2015)', 
                  fontsize=14, fontweight='bold')
    ax1.legend(fontsize=11, loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # Gráfico 2: Precios absolutos
    ax2_twin = ax2.twinx()
    
    ax2.plot(yearly_avg['anio'], yearly_avg['precio_m2_venta'], marker='o', linewidth=2.5,
             label='Precio Venta (€/m²)', color='#2E86AB', markersize=8)
    ax2_twin.plot(yearly_avg['anio'], yearly_avg['precio_mes_alquiler'], marker='s', linewidth=2.5,
                  label='Precio Alquiler (€/mes)', color='#A23B72', markersize=8)
    
    ax2.axvline(x=2020, color='red', linestyle=':', alpha=0.5, linewidth=2)
    
    ax2.set_xlabel('Año', fontsize=12)
    ax2.set_ylabel('Precio Venta (€/m²)', fontsize=12, color='#2E86AB')
    ax2_twin.set_ylabel('Precio Alquiler (€/mes)', fontsize=12, color='#A23B72')
    ax2.set_title('Evolución de Precios Absolutos', fontsize=14, fontweight='bold')
    
    ax2.tick_params(axis='y', labelcolor='#2E86AB')
    ax2_twin.tick_params(axis='y', labelcolor='#A23B72')
    
    # Combinar leyendas
    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2_twin.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, fontsize=11, loc='upper left')
    
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('reports/evolucion_temporal_precios.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("\n📊 Gráfico guardado: reports/evolucion_temporal_precios.png")
    
    # Análisis post-COVID
    print("\n" + "-"*80)
    print("IMPACTO COVID-19 (2020-2024)")
    print("-"*80)
    
    pre_covid = yearly_avg[yearly_avg['anio'] == 2019].iloc[0]
    post_covid_2024 = yearly_avg[yearly_avg['anio'] == 2024].iloc[0]
    
    cambio_venta = ((post_covid_2024['precio_m2_venta'] / pre_covid['precio_m2_venta']) - 1) * 100
    cambio_alquiler = ((post_covid_2024['precio_mes_alquiler'] / pre_covid['precio_mes_alquiler']) - 1) * 100
    cambio_inflacion = ((post_covid_2024['inflacion'] / pre_covid['inflacion']) - 1) * 100
    
    print(f"\nCambio 2019 → 2024:")
    print(f"  Precio Venta: {cambio_venta:+.1f}%")
    print(f"  Precio Alquiler: {cambio_alquiler:+.1f}%")
    print(f"  Inflación: {cambio_inflacion:+.1f}%")
    
    print(f"\nPrecio Venta vs Inflación: {cambio_venta - cambio_inflacion:+.1f} puntos porcentuales")
    print(f"Precio Alquiler vs Inflación: {cambio_alquiler - cambio_inflacion:+.1f} puntos porcentuales")
    
    if cambio_venta > cambio_inflacion:
        print(f"\n✓ Los precios de venta crecieron {cambio_venta - cambio_inflacion:.1f}pp POR ENCIMA de la inflación")
    else:
        print(f"\n✗ Los precios de venta crecieron {abs(cambio_venta - cambio_inflacion):.1f}pp POR DEBAJO de la inflación")
    
    return yearly_avg

def calculate_yield(df):
    """Calcula el yield (rentabilidad bruta) por barrio"""
    print("\n" + "="*80)
    print("3. YIELD (RENTABILIDAD BRUTA) POR BARRIO")
    print("="*80)
    
    # Filtrar datos más recientes (2023-2024)
    df_recent = df[df['anio'].isin([2023, 2024])].copy()
    
    # Calcular yield por barrio
    yield_data = df_recent.groupby(['barrio_id', 'barrio_nombre', 'distrito_nombre']).agg({
        'precio_m2_venta': 'mean',
        'precio_mes_alquiler': 'mean'
    }).reset_index()
    
    # Yield = (Alquiler Anual / Precio Venta) * 100
    # Asumiendo 70m² como superficie promedio
    superficie_promedio = 70
    
    yield_data['precio_venta_vivienda'] = yield_data['precio_m2_venta'] * superficie_promedio
    yield_data['alquiler_anual'] = yield_data['precio_mes_alquiler'] * 12
    yield_data['yield_pct'] = (yield_data['alquiler_anual'] / yield_data['precio_venta_vivienda']) * 100
    
    # Eliminar NaN
    yield_data = yield_data.dropna(subset=['yield_pct'])
    
    # Ordenar por yield
    yield_data = yield_data.sort_values('yield_pct', ascending=False)
    
    print(f"\nDatos calculados para {len(yield_data)} barrios")
    print(f"Superficie asumida: {superficie_promedio} m²")
    
    # Top 10 y Bottom 10
    print("\n" + "-"*80)
    print("TOP 10 BARRIOS - MAYOR RENTABILIDAD")
    print("-"*80)
    print(f"{'Barrio':<30} {'Distrito':<20} {'Yield':>8} {'Venta (€/m²)':>12} {'Alquiler (€/mes)':>15}")
    print("-"*80)
    
    for _, row in yield_data.head(10).iterrows():
        print(f"{row['barrio_nombre']:<30} {row['distrito_nombre']:<20} {row['yield_pct']:>7.2f}% "
              f"{row['precio_m2_venta']:>11,.0f} {row['precio_mes_alquiler']:>14,.0f}")
    
    print("\n" + "-"*80)
    print("BOTTOM 10 BARRIOS - MENOR RENTABILIDAD")
    print("-"*80)
    print(f"{'Barrio':<30} {'Distrito':<20} {'Yield':>8} {'Venta (€/m²)':>12} {'Alquiler (€/mes)':>15}")
    print("-"*80)
    
    for _, row in yield_data.tail(10).iterrows():
        print(f"{row['barrio_nombre']:<30} {row['distrito_nombre']:<20} {row['yield_pct']:>7.2f}% "
              f"{row['precio_m2_venta']:>11,.0f} {row['precio_mes_alquiler']:>14,.0f}")
    
    # Visualización
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 10))
    
    # Gráfico 1: Top 15 y Bottom 15
    top_bottom = pd.concat([yield_data.head(15), yield_data.tail(15)])
    
    colors = ['green' if y > yield_data['yield_pct'].median() else 'red' 
              for y in top_bottom['yield_pct']]
    
    ax1.barh(range(len(top_bottom)), top_bottom['yield_pct'], color=colors, alpha=0.7)
    ax1.set_yticks(range(len(top_bottom)))
    ax1.set_yticklabels(top_bottom['barrio_nombre'], fontsize=9)
    ax1.set_xlabel('Yield (%)', fontsize=12)
    ax1.set_title('Rentabilidad Bruta por Barrio (Top 15 + Bottom 15)', 
                  fontsize=14, fontweight='bold')
    ax1.axvline(yield_data['yield_pct'].median(), color='blue', linestyle='--', 
                label=f'Mediana: {yield_data["yield_pct"].median():.2f}%')
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='x')
    
    # Gráfico 2: Scatter Precio vs Yield
    ax2.scatter(yield_data['precio_m2_venta'], yield_data['yield_pct'], 
                alpha=0.6, s=100, c=yield_data['yield_pct'], cmap='RdYlGn')
    
    # Añadir etiquetas para barrios extremos
    for _, row in yield_data.head(5).iterrows():
        ax2.annotate(row['barrio_nombre'], 
                    (row['precio_m2_venta'], row['yield_pct']),
                    fontsize=8, alpha=0.7)
    
    ax2.set_xlabel('Precio Venta (€/m²)', fontsize=12)
    ax2.set_ylabel('Yield (%)', fontsize=12)
    ax2.set_title('Relación Precio de Venta vs Rentabilidad', 
                  fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    # Línea de tendencia
    z = np.polyfit(yield_data['precio_m2_venta'], yield_data['yield_pct'], 1)
    p = np.poly1d(z)
    ax2.plot(yield_data['precio_m2_venta'], p(yield_data['precio_m2_venta']), 
             "r--", alpha=0.5, label=f'Tendencia: y={z[0]:.4f}x+{z[1]:.2f}')
    ax2.legend()
    
    plt.tight_layout()
    plt.savefig('reports/yield_rentabilidad_barrios.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("\n📊 Gráfico guardado: reports/yield_rentabilidad_barrios.png")
    
    # Estadísticas
    print("\n" + "-"*80)
    print("ESTADÍSTICAS DE YIELD")
    print("-"*80)
    print(f"  Media: {yield_data['yield_pct'].mean():.2f}%")
    print(f"  Mediana: {yield_data['yield_pct'].median():.2f}%")
    print(f"  Desv. Std: {yield_data['yield_pct'].std():.2f}%")
    print(f"  Min: {yield_data['yield_pct'].min():.2f}% ({yield_data.iloc[-1]['barrio_nombre']})")
    print(f"  Max: {yield_data['yield_pct'].max():.2f}% ({yield_data.iloc[0]['barrio_nombre']})")
    
    return yield_data

def main():
    """Ejecuta el análisis completo"""
    print("="*80)
    print("ANÁLISIS DEL MERCADO INMOBILIARIO DE BARCELONA")
    print("="*80)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Crear directorio de reportes
    Path('reports').mkdir(exist_ok=True)
    
    # Cargar datos
    df = load_price_data()
    
    # Análisis 1: Distribución
    analyze_distribution(df)
    
    # Análisis 2: Evolución temporal
    yearly_data = analyze_temporal_evolution(df)
    
    # Análisis 3: Yield
    yield_data = calculate_yield(df)
    
    print("\n" + "="*80)
    print("✅ ANÁLISIS COMPLETADO")
    print("="*80)
    print("\nReportes generados:")
    print("  1. reports/analisis_distribucion_precios.png")
    print("  2. reports/evolucion_temporal_precios.png")
    print("  3. reports/yield_rentabilidad_barrios.png")

if __name__ == "__main__":
    main()
