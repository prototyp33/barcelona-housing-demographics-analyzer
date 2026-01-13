#!/usr/bin/env python3
"""
Create a master consolidated table for Looker Studio.

This script creates a single comprehensive CSV file that combines:
- Neighborhood information (dim_barrios)
- Prices (fact_precios)
- Demographics (fact_demografia_ampliada aggregated)
- Income (fact_renta)
- Environmental data (fact_calidad_aire, fact_ruido)
- Tourism (fact_turismo_intensidad)
- Security (fact_seguridad)
- And more...

This makes it much easier to use in Looker Studio without complex blends.
"""

import sys
import logging
from pathlib import Path
from typing import Optional
import os

import pandas as pd
import numpy as np
import psycopg2
from dotenv import load_dotenv

# --- 1. DICCIONARIO DE INTELIGENCIA DE MERCADO ---
# Define rangos lógicos y comportamientos esperados por barrio
CONTEXT_RULES = {
    # La Marina del Prat Vermell (Zona en desarrollo / Gentrificación)
    '12': {
        'name': 'la Marina del Prat Vermell',
        'min_logic': 1200,  # Menos de esto suele ser suelo industrial/no habitable
        'max_logic': 3500,  # Techo lógico actual
        'risk_factor': 'GENTRIFICATION_AREA'
    },
    # Vallvidrera (Zona Heterogénea: Lujo vs Autoconstrucción)
    '22': {
        'name': 'Vallvidrera, el Tibidabo i les Planes',
        'min_logic': 2500,  # Menos de esto suele ser sub-zona Les Planes
        'max_logic': 8000,
        'risk_factor': 'HIGH_HETEROGENEITY'
    },
    # Torre Baró (Zona Periférica / Impacto Obra Nueva)
    '54': {
        'name': 'Torre Baró',
        'min_logic': 600,
        'max_logic': 1800,  # Más de esto suele ser distorsión por Obra Nueva
        'risk_factor': 'NEW_BUILD_DISTORTION'
    }
}

# Rangos generales por distrito (fallback para validación de umbrales)
DISTRICT_RULES = {
    "Sarrià-Sant Gervasi": {"min": 2500, "max": 8000, "risk": "LUXURY_AREA"},
    "Les Corts": {"min": 2500, "max": 7500, "risk": "LUXURY_AREA"},
    "Eixample": {"min": 2000, "max": 6500, "risk": "CENTRAL_PREMIUM"},
    "Nou Barris": {"min": 800, "max": 2800, "risk": "PERIPHERAL_LOW"},
    "Sant Martí": {"min": 1500, "max": 5000, "risk": "DEVELOPING_TECH"},
    "Ciutat Vella": {"min": 1800, "max": 6000, "risk": "TOURISM_IMPACT"},
    "Sants-Montjuïc": {"min": 1500, "max": 4500, "risk": "MIXED_DEVELOPMENT"},
    "Horta-Guinardó": {"min": 1500, "max": 4000, "risk": "RESIDENTIAL_STABLE"},
    "Sant Andreu": {"min": 1500, "max": 3800, "risk": "RESIDENTIAL_UPCOMING"},
    "Gràcia": {"min": 2000, "max": 5500, "risk": "GENTRIFIED_BOHEMIAN"}
}

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# PostgreSQL connection config
POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "database": os.getenv("POSTGRES_DATABASE", "barcelona_housing"),
    "user": os.getenv("POSTGRES_USER", os.getenv("USER", "postgres")),
    "password": os.getenv("POSTGRES_PASSWORD", ""),
    "port": int(os.getenv("POSTGRES_PORT", "5432"))
}

EXPORT_BASE = PROJECT_ROOT / "data" / "exports" / "looker_studio"


def get_connection():
    """Get PostgreSQL connection."""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Error connecting to PostgreSQL: {e}")
        raise


def create_master_table(conn) -> pd.DataFrame:
    """
    Create a master consolidated table combining all key metrics.
    
    Returns:
        DataFrame with one row per barrio per year.
    """
    logger.info("Creating master consolidated table...")
    
    query = """
    WITH 
    -- Agregar demografía por barrio y año
    demografia_agg AS (
        SELECT 
            barrio_id,
            anio,
            SUM(poblacion) AS poblacion_total,
            SUM(CASE WHEN sexo IN ('Home', 'Hombre') THEN poblacion ELSE 0 END) AS poblacion_hombres,
            SUM(CASE WHEN sexo IN ('Dona', 'Mujer') THEN poblacion ELSE 0 END) AS poblacion_mujeres,
            COUNT(DISTINCT grupo_edad) AS grupos_edad_distintos,
            COUNT(DISTINCT nacionalidad) AS nacionalidades_distintas
        FROM fact_demografia_ampliada
        GROUP BY barrio_id, anio
    ),
    
    -- Precios con estadísticas para detectar alta variabilidad
    precios_stats AS (
        SELECT 
            barrio_id,
            anio,
            -- Estadísticas para precio_m2_venta
            AVG(precio_m2_venta) AS precio_m2_venta_mean,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY precio_m2_venta) AS precio_m2_venta_median,
            STDDEV(precio_m2_venta) AS precio_m2_venta_stddev,
            COUNT(precio_m2_venta) AS num_registros_venta,
            -- Estadísticas para precio_mes_alquiler
            AVG(precio_mes_alquiler) AS precio_mes_alquiler_mean,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY precio_mes_alquiler) AS precio_mes_alquiler_median,
            STDDEV(precio_mes_alquiler) AS precio_mes_alquiler_stddev,
            COUNT(precio_mes_alquiler) AS num_registros_alquiler,
            COUNT(*) AS num_registros_precios,
            MAX(dataset_id) AS dataset_id
        FROM fact_precios
        WHERE precio_m2_venta IS NOT NULL OR precio_mes_alquiler IS NOT NULL
        GROUP BY barrio_id, anio
    ),
    
    -- Precios agregados usando mediana cuando CV > 50%, promedio en caso contrario
    precios_agg AS (
        SELECT 
            barrio_id,
            anio,
            -- Calcular CV y decidir qué usar para precio_m2_venta
            CASE 
                WHEN precio_m2_venta_mean > 0 AND precio_m2_venta_stddev IS NOT NULL 
                     AND precio_m2_venta_stddev > 0 
                     AND (precio_m2_venta_stddev / precio_m2_venta_mean * 100) > 50
                     AND num_registros_venta >= 3
                THEN precio_m2_venta_median  -- Alta variabilidad: usar mediana
                ELSE precio_m2_venta_mean     -- Baja variabilidad: usar promedio
            END AS precio_m2_venta_promedio,
            CASE 
                WHEN precio_m2_venta_mean > 0 AND precio_m2_venta_stddev IS NOT NULL 
                     AND precio_m2_venta_stddev > 0 
                     AND (precio_m2_venta_stddev / precio_m2_venta_mean * 100) > 50
                     AND num_registros_venta >= 3
                THEN 1  -- Flag: usa mediana
                ELSE 0  -- Flag: usa promedio
            END AS usa_mediana_venta,
            CASE 
                WHEN precio_m2_venta_mean > 0 AND precio_m2_venta_stddev IS NOT NULL 
                     AND precio_m2_venta_stddev > 0
                THEN (precio_m2_venta_stddev / precio_m2_venta_mean * 100)
                ELSE NULL
            END AS cv_precio_venta,
            -- Calcular CV y decidir qué usar para precio_mes_alquiler
            CASE 
                WHEN precio_mes_alquiler_mean > 0 AND precio_mes_alquiler_stddev IS NOT NULL 
                     AND precio_mes_alquiler_stddev > 0 
                     AND (precio_mes_alquiler_stddev / precio_mes_alquiler_mean * 100) > 50
                     AND num_registros_alquiler >= 3
                THEN precio_mes_alquiler_median
                ELSE precio_mes_alquiler_mean
            END AS precio_mes_alquiler_promedio,
            CASE 
                WHEN precio_mes_alquiler_mean > 0 AND precio_mes_alquiler_stddev IS NOT NULL 
                     AND precio_mes_alquiler_stddev > 0 
                     AND (precio_mes_alquiler_stddev / precio_mes_alquiler_mean * 100) > 50
                     AND num_registros_alquiler >= 3
                THEN 1
                ELSE 0
            END AS usa_mediana_alquiler,
            CASE 
                WHEN precio_mes_alquiler_mean > 0 AND precio_mes_alquiler_stddev IS NOT NULL 
                     AND precio_mes_alquiler_stddev > 0
                THEN (precio_mes_alquiler_stddev / precio_mes_alquiler_mean * 100)
                ELSE NULL
            END AS cv_precio_alquiler,
            num_registros_precios,
            dataset_id
        FROM precios_stats
    ),
    
    -- Turismo agregado por barrio y año
    turismo_agg AS (
        SELECT 
            barrio_id,
            anio,
            SUM(num_establecimientos_turisticos) AS total_establecimientos_turisticos,
            COUNT(*) AS num_registros_turismo
        FROM fact_turismo_intensidad
        WHERE num_establecimientos_turisticos IS NOT NULL
        GROUP BY barrio_id, anio
    ),
    
    -- Seguridad agregada por barrio y año
    seguridad_agg AS (
        SELECT 
            barrio_id,
            anio,
            AVG(tasa_criminalidad_1000hab) AS tasa_criminalidad_promedio,
            SUM(COALESCE(delitos_patrimonio, 0) + COALESCE(delitos_seguridad_personal, 0)) AS total_delitos
        FROM fact_seguridad
        WHERE tasa_criminalidad_1000hab IS NOT NULL
        GROUP BY barrio_id, anio
    ),
    
    -- Calidad de aire (último año disponible)
    calidad_aire_latest AS (
        SELECT DISTINCT ON (barrio_id)
            barrio_id,
            anio,
            no2_mean AS calidad_aire_no2_mean,
            pm25_mean AS calidad_aire_pm25_mean,
            pm10_mean AS calidad_aire_pm10_mean
        FROM fact_calidad_aire
        ORDER BY barrio_id, anio DESC
    ),
    
    -- Ruido (último año disponible)
    ruido_latest AS (
        SELECT DISTINCT ON (barrio_id)
            barrio_id,
            anio AS ruido_anio,
            nivel_lden_medio AS ruido_lden_medio
        FROM fact_ruido
        WHERE nivel_lden_medio IS NOT NULL
        ORDER BY barrio_id, anio DESC
    )
    
    -- Tabla maestra: combinación de todas las fuentes
    SELECT 
        -- Información de barrio (de dim_barrios)
        b.barrio_id,
        b.barrio_nombre,
        b.distrito_nombre,
        b.municipio,
        b.codi_barri,
        b.centroide_lat,
        b.centroide_lon,
        b.area_km2,
        
        -- Año
        p.anio,
        
        -- Precios
        p.precio_m2_venta_promedio,
        p.precio_mes_alquiler_promedio,
        p.num_registros_precios,
        p.usa_mediana_venta,
        p.usa_mediana_alquiler,
        p.cv_precio_venta,
        p.cv_precio_alquiler,
        p.dataset_id,
        
        -- Demografía
        d.poblacion_total,
        d.poblacion_hombres,
        d.poblacion_mujeres,
        d.grupos_edad_distintos,
        d.nacionalidades_distintas,
        
        -- Renta (último año disponible por barrio)
        r.renta_mediana,
        r.renta_promedio,
        r.renta_euros,
        
        -- Turismo
        t.total_establecimientos_turisticos,
        t.num_registros_turismo,
        
        -- Seguridad
        s.tasa_criminalidad_promedio,
        s.total_delitos,
        
        -- Calidad ambiental (último año disponible)
        ca.calidad_aire_no2_mean,
        ca.calidad_aire_pm25_mean,
        ca.calidad_aire_pm10_mean,
        
        -- Ruido (último año disponible)
        ru.ruido_lden_medio,
        
        -- Educación (último año disponible)
        e.num_centros_total,
        
        -- Movilidad (último año disponible)
        m.distancia_metro_km,
        m.num_estaciones_metro,
        m.num_estaciones_bus
        
    FROM dim_barrios b
    
    -- Cross join con años disponibles en precios
    CROSS JOIN (
        SELECT DISTINCT anio 
        FROM fact_precios 
        WHERE anio IS NOT NULL
        ORDER BY anio
    ) years
    
    -- Join con precios
    LEFT JOIN precios_agg p 
        ON b.barrio_id = p.barrio_id 
        AND years.anio = p.anio
    
    -- Join con demografía
    LEFT JOIN demografia_agg d 
        ON b.barrio_id = d.barrio_id 
        AND years.anio = d.anio
    
    -- Join con renta (último año disponible)
    LEFT JOIN LATERAL (
        SELECT renta_mediana, renta_promedio, renta_euros
        FROM fact_renta
        WHERE barrio_id = b.barrio_id
        ORDER BY anio DESC
        LIMIT 1
    ) r ON true
    
    -- Join con turismo
    LEFT JOIN turismo_agg t 
        ON b.barrio_id = t.barrio_id 
        AND years.anio = t.anio
    
    -- Join con seguridad
    LEFT JOIN seguridad_agg s 
        ON b.barrio_id = s.barrio_id 
        AND years.anio = s.anio
    
    -- Join con calidad de aire (último año disponible)
    LEFT JOIN calidad_aire_latest ca 
        ON b.barrio_id = ca.barrio_id
    
    -- Join con ruido (último año disponible)
    LEFT JOIN ruido_latest ru 
        ON b.barrio_id = ru.barrio_id
    
    -- Join con educación (último año disponible)
    LEFT JOIN LATERAL (
        SELECT 
            total_centros_educativos AS num_centros_total
        FROM fact_educacion
        WHERE barrio_id = b.barrio_id
        ORDER BY anio DESC
        LIMIT 1
    ) e ON true
    
    -- Join con movilidad (último año disponible - promedio)
    LEFT JOIN LATERAL (
        SELECT 
            AVG(dist_metro_m) / 1000.0 AS distancia_metro_km,
            AVG(estaciones_metro) AS num_estaciones_metro,
            AVG(estaciones_bus) AS num_estaciones_bus
        FROM fact_movilidad
        WHERE barrio_id = b.barrio_id
        GROUP BY barrio_id, anio
        ORDER BY anio DESC
        LIMIT 1
    ) m ON true
    
    WHERE p.anio IS NOT NULL  -- Solo incluir años con datos de precios
    
    ORDER BY b.barrio_id, years.anio
    """
    
    df = pd.read_sql_query(query, conn)
    
    # Clean column names
    df.columns = df.columns.str.replace(' ', '_').str.lower().str.strip()
    
    # Calculate derived metrics
    if 'poblacion_total' in df.columns and 'area_km2' in df.columns:
        df['densidad_poblacion'] = df['poblacion_total'] / df['area_km2'].replace(0, None)
    
    if 'precio_m2_venta_promedio' in df.columns and 'renta_mediana' in df.columns:
        # Affordability: años de renta necesarios para comprar 70m²
        df['anios_renta_para_comprar_70m2'] = (df['precio_m2_venta_promedio'] * 70) / (df['renta_mediana'] * 12)
    
    # Add flag combinado para alta variabilidad
    if 'usa_mediana_venta' in df.columns and 'usa_mediana_alquiler' in df.columns:
        df['usa_mediana'] = ((df['usa_mediana_venta'] == 1) | (df['usa_mediana_alquiler'] == 1)).astype(int)
        logger.info(f"Alta variabilidad detectada: {df['usa_mediana'].sum()} registros usan mediana")
    
    # Add data quality flags
    df = add_data_quality_flags(df)
    
    # Validate and flag anomalies
    df = validate_and_flag_anomalies(df)
    
    logger.info(f"Master table created: {len(df):,} rows, {len(df.columns)} columns")
    
    return df


def apply_quality_context(row):
    """
    Evalúa la calidad y el contexto de cada dato basándose en reglas de negocio.
    Retorna una Serie con 3 nuevas columnas.
    """
    # 1. Normalizar inputs
    codi = str(row.get('codi_barri', '')).split('.')[0]
    distrito = row.get('distrito_nombre', '')
    price = row.get('precio_m2_venta_promedio', 0)
    n_count = row.get('num_registros_precios', 0)
    dataset_id = row.get('dataset_id', '')
    
    # 2. Valores por defecto
    flags = []
    confidence = 'HIGH'
    context = 'STANDARD'
    
    # 3. Reglas Universales (N pequeño o Imputación)
    if dataset_id == 'IMPUTACION_DISTRITO_RATIO':
        flags.append('DISTRICT_IMPUTED')
        confidence = 'MEDIUM'
        
    if pd.notna(n_count) and n_count < 5 and n_count > 0:
        flags.append('LOW_SAMPLE_SIZE')
        confidence = 'LOW'
        
    # 4. Reglas Específicas por Barrio (Contexto)
    if codi in CONTEXT_RULES:
        rule = CONTEXT_RULES[codi]
        context = rule['risk_factor']
        
        # Validación de precios lógicos (si hay precio)
        if pd.notna(price) and price > 0:
            if price < rule['min_logic']:
                flags.append('PRICE_BELOW_LOGIC')
                if rule['risk_factor'] == 'HIGH_HETEROGENEITY':
                    confidence = 'MEDIUM'
                else:
                    confidence = 'LOW'
            elif price > rule['max_logic']:
                flags.append('PRICE_ABOVE_LOGIC')
                if rule['risk_factor'] == 'NEW_BUILD_DISTORTION':
                    confidence = 'LOW'
                    flags.append('LIKELY_NEW_BUILD')
    
    # 5. Fallback a Reglas de Distrito (si no hay reglas de barrio específicas)
    elif distrito in DISTRICT_RULES:
        dist_ctx = DISTRICT_RULES[distrito]
        # context = dist_ctx['risk'] # Opcional: sobreescribir context con el del distrito
        
        if pd.notna(price) and price > 0:
            if price < dist_ctx['min']:
                flags.append('PRICE_BELOW_DISTRICT_MIN')
                if confidence != 'LOW': confidence = 'MEDIUM'
            elif price > dist_ctx['max']:
                flags.append('PRICE_ABOVE_DISTRICT_MAX')
                if confidence != 'LOW': confidence = 'MEDIUM'

    # 6. Formateo final
    flags_str = ' | '.join(flags) if flags else 'OK'
    
    return pd.Series([confidence, context, flags_str])


def add_data_quality_flags(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add data quality flags to identify missing data and data quality issues.
    
    Args:
        df: Master table DataFrame
    
    Returns:
        DataFrame with quality flags added
    """
    df = df.copy()
    
    # 1. Aplicar Reglas de Calidad y Contexto Cualitativo (Nuevo)
    logger.info("Aplicando reglas de calidad y contexto cualitativo...")
    quality_columns = ['confidence_score', 'market_context', 'quality_flags']
    df[quality_columns] = df.apply(apply_quality_context, axis=1)
    
    # Rellenar nulos para Looker
    df['confidence_score'] = df['confidence_score'].fillna('HIGH')
    df['market_context'] = df['market_context'].fillna('STANDARD')
    df['quality_flags'] = df['quality_flags'].fillna('OK')
    
    # 2. Flags de datos faltantes (Originales)
    df['precio_venta_faltante'] = df['precio_m2_venta_promedio'].isna().astype(int)
    df['precio_alquiler_faltante'] = df['precio_mes_alquiler_promedio'].isna().astype(int)
    
    # Flag for missing demographic data
    df['demografia_faltante'] = df['poblacion_total'].isna().astype(int)
    
    # Flag for missing tourism data
    df['turismo_faltante'] = df['total_establecimientos_turisticos'].isna().astype(int)
    
    # Flag for missing security data
    df['seguridad_faltante'] = df['tasa_criminalidad_promedio'].isna().astype(int)
    
    # Overall data completeness score (0-100)
    quality_cols = [
        'precio_m2_venta_promedio', 'precio_mes_alquiler_promedio',
        'poblacion_total', 'total_establecimientos_turisticos',
        'tasa_criminalidad_promedio', 'renta_mediana'
    ]
    available_cols = [col for col in quality_cols if col in df.columns]
    df['completitud_datos'] = (df[available_cols].notna().sum(axis=1) / len(available_cols) * 100).round(1)
    
    # Flag for low data quality (<50% completeness)
    df['calidad_baja'] = (df['completitud_datos'] < 50).astype(int)
    
    return df


def validate_and_flag_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate data and flag anomalies (abrupt changes, outliers).
    
    Args:
        df: Master table DataFrame
    
    Returns:
        DataFrame with anomaly flags added
    """
    df = df.copy()
    df = df.sort_values(['barrio_id', 'anio']).reset_index(drop=True)
    
    # Calculate year-over-year changes
    df['precio_venta_change_pct'] = df.groupby('barrio_id')['precio_m2_venta_promedio'].pct_change(fill_method=None) * 100
    df['precio_alquiler_change_pct'] = df.groupby('barrio_id')['precio_mes_alquiler_promedio'].pct_change(fill_method=None) * 100
    
    # Flag abrupt changes (>50% or <-50%)
    df['cambio_abrupto_venta'] = (
        (df['precio_venta_change_pct'].abs() > 50) & 
        df['precio_venta_change_pct'].notna()
    ).astype(int)
    
    df['cambio_abrupto_alquiler'] = (
        (df['precio_alquiler_change_pct'].abs() > 50) & 
        df['precio_alquiler_change_pct'].notna()
    ).astype(int)
    
    # Flag very extreme changes (>100% or <-100%) - likely data errors
    df['cambio_extremo_venta'] = (
        (df['precio_venta_change_pct'].abs() > 100) & 
        df['precio_venta_change_pct'].notna()
    ).astype(int)
    
    df['cambio_extremo_alquiler'] = (
        (df['precio_alquiler_change_pct'].abs() > 100) & 
        df['precio_alquiler_change_pct'].notna()
    ).astype(int)
    
    # Detect outliers using Z-score (by year)
    df['z_score_precio_venta'] = np.nan
    for year in df['anio'].unique():
        year_mask = df['anio'] == year
        year_prices = df.loc[year_mask, 'precio_m2_venta_promedio'].dropna()
        
        if len(year_prices) > 1:
            mean_price = year_prices.mean()
            std_price = year_prices.std()
            
            if std_price > 0:
                z_scores = (df.loc[year_mask, 'precio_m2_venta_promedio'] - mean_price) / std_price
                df.loc[year_mask, 'z_score_precio_venta'] = z_scores
    
    # Flag outliers (Z-score > 3 or < -3)
    df['outlier_precio_venta'] = (
        (df['z_score_precio_venta'].abs() > 3) & 
        df['z_score_precio_venta'].notna()
    ).astype(int)
    
    # Overall anomaly flag
    df['tiene_anomalias'] = (
        (df['cambio_extremo_venta'] == 1) |
        (df['cambio_extremo_alquiler'] == 1) |
        (df['outlier_precio_venta'] == 1)
    ).astype(int)
    
    return df


def main() -> int:
    """Main function."""
    logger.info("=" * 60)
    logger.info("📊 Creating Master Table for Looker Studio")
    logger.info("=" * 60)
    
    try:
        conn = get_connection()
        logger.info("✅ Connected to PostgreSQL")
    except Exception as e:
        logger.error(f"❌ Failed to connect: {e}")
        return 1
    
    try:
        # Create master table
        df_master = create_master_table(conn)
        
        # Save to CSV
        output_path = EXPORT_BASE / "master_table_barcelona_housing.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        df_master.to_csv(output_path, index=False, encoding='utf-8-sig', lineterminator='\n')
        
        logger.info(f"\n✅ Master table exported: {output_path}")
        logger.info(f"   Rows: {len(df_master):,}")
        logger.info(f"   Columns: {len(df_master.columns)}")
        logger.info(f"   Size: {output_path.stat().st_size / 1024:.1f} KB")
        
        # Show sample
        logger.info("\n📋 Sample columns:")
        logger.info(f"   {', '.join(df_master.columns[:10])}...")
        
        # Show summary
        logger.info("\n📊 Summary:")
        logger.info(f"   Barrios: {df_master['barrio_id'].nunique()}")
        logger.info(f"   Años: {sorted(df_master['anio'].dropna().unique())}")
        logger.info(f"   Rango temporal: {int(df_master['anio'].min())} - {int(df_master['anio'].max())}")
        
        # Show data quality metrics
        if 'tiene_anomalias' in df_master.columns:
            logger.info("\n🔍 Data Quality Metrics:")
            logger.info(f"   Registros con anomalías: {df_master['tiene_anomalias'].sum()}")
            logger.info(f"   Cambios extremos (>100%): {df_master['cambio_extremo_venta'].sum() + df_master['cambio_extremo_alquiler'].sum()}")
            logger.info(f"   Outliers detectados: {df_master['outlier_precio_venta'].sum()}")
            logger.info(f"   Completitud promedio: {df_master['completitud_datos'].mean():.1f}%")
            
            # Show top problematic barrios
            problematic = df_master[df_master['tiene_anomalias'] == 1]
            if len(problematic) > 0:
                top_problematic = problematic.groupby('barrio_nombre')['tiene_anomalias'].sum().nlargest(5)
                logger.info(f"\n   Top 5 barrios con anomalías:")
                for barrio, count in top_problematic.items():
                    logger.info(f"      • {barrio}: {count} anomalía(s)")
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ Master table ready for Looker Studio!")
        logger.info("=" * 60)
        logger.info("\nUpload this single file to Looker Studio:")
        logger.info(f"   {output_path}")
        logger.info("\nNo need for blends - all data is in one table!")
        logger.info("\n💡 New features:")
        logger.info("   • Data quality flags added (completitud_datos, tiene_anomalias)")
        logger.info("   • Anomaly detection (cambio_extremo_*, outlier_*)")
        logger.info("   • Missing data flags (precio_venta_faltante, etc.)")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error creating master table: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
