#!/usr/bin/env python3
"""
Análisis del Gap de Negociación (Asking vs Transaction).

Este script compara los precios de oferta (Idealista) con los precios reales
de transacción (Incasòl) para determinar el margen de negociación por barrio.
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
import psycopg2
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime

# Configuración de rutas
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración de PostgreSQL
POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "database": os.getenv("POSTGRES_DATABASE", "barcelona_housing"),
    "user": os.getenv("POSTGRES_USER", os.getenv("USER", "postgres")),
    "password": os.getenv("POSTGRES_PASSWORD", ""),
    "port": int(os.getenv("POSTGRES_PORT", "5432"))
}

# IDs de Datasets
ID_ASKING = 'bhl3ulphi5'      # VENTA_OFERTA_M2 (Idealista)
ID_TRANSACTION = 'u25rr7oxh6' # VENTA_REGISTRADA_M2 (Incasòl)
ID_TRANSACTION_ALT = 'mrslyp5pcq' # VENTA_POR_TIPO_M2 (Fallback)

def run_gap_analysis():
    logger.info("=" * 60)
    logger.info("🚀 Iniciando Análisis de Gap de Negociación")
    logger.info("=" * 60)

    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        logger.info("✅ Conectado a PostgreSQL")
    except Exception as e:
        logger.error(f"❌ Error al conectar a PostgreSQL: {e}")
        return

    try:
        # 1. Obtener nombres de barrios
        barrios = pd.read_sql_query("SELECT barrio_id, barrio_nombre, distrito_nombre FROM dim_barrios", conn)
        
        # 2. Obtener precios de oferta (Asking)
        query_asking = f"""
            SELECT barrio_id, anio, AVG(precio_m2_venta) as asking_price
            FROM fact_precios
            WHERE dataset_id = '{ID_ASKING}' AND precio_m2_venta IS NOT NULL
            GROUP BY barrio_id, anio
        """
        df_asking = pd.read_sql_query(query_asking, conn)
        
        # 2.1 Obtener volumen de anuncios (Idealista) para filtrado de ruido
        query_volume = """
            SELECT barrio_id, anio, AVG(num_anuncios) as avg_num_anuncios
            FROM fact_oferta_idealista
            WHERE operacion = 'sale'
            GROUP BY barrio_id, anio
        """
        df_volume = pd.read_sql_query(query_volume, conn)
        
        # 3. Obtener precios de transacción (Real)
        query_trans = f"""
            SELECT barrio_id, anio, AVG(precio_m2_venta) as transaction_price
            FROM fact_precios
            WHERE dataset_id IN ('{ID_TRANSACTION}', '{ID_TRANSACTION_ALT}') 
              AND precio_m2_venta IS NOT NULL
            GROUP BY barrio_id, anio
        """
        df_trans = pd.read_sql_query(query_trans, conn)
        
        if df_asking.empty or df_trans.empty:
            logger.warning("⚠️ No se encontraron datos suficientes para realizar la comparativa.")
            logger.info(f"Registros Asking: {len(df_asking)}")
            logger.info(f"Registros Transaction: {len(df_trans)}")
            return

        # 4. Mergear datos
        df_gap = pd.merge(df_asking, df_trans, on=['barrio_id', 'anio'], how='inner')
        df_gap = pd.merge(df_gap, barrios, on='barrio_id', how='left')
        
        # Mergear volumen de anuncios si existe
        if not df_volume.empty:
            df_gap = pd.merge(df_gap, df_volume, on=['barrio_id', 'anio'], how='left')
        else:
            df_gap['avg_num_anuncios'] = np.nan

        # 5. Calcular métricas de Gap
        df_gap['gap_absolute'] = df_gap['asking_price'] - df_gap['transaction_price']
        df_gap['gap_percent'] = (df_gap['gap_absolute'] / df_gap['asking_price']) * 100
        
        # 6. Filtrar el año más reciente con datos
        latest_year = df_gap['anio'].max()
        df_latest = df_gap[df_gap['anio'] == latest_year].copy()
        
        # --- LIMPIEZA DE RUIDO ---
        # 1. Filtro por Volumen (mínimo 15 anuncios promedio al mes para ser fiable)
        VOLUME_THRESHOLD = 15
        # 2. Filtro por Gaps Extremos (más de 50% o menos de -40% suelen ser anomalías de datos)
        GAP_UPPER_BOUND = 50.0
        GAP_LOWER_BOUND = -40.0
        
        # Marcar barrios con bajo volumen
        df_latest['low_volume'] = (df_latest['avg_num_anuncios'] < VOLUME_THRESHOLD) | df_latest['avg_num_anuncios'].isna()
        # Marcar barrios con gaps extremos
        df_latest['extreme_gap'] = (df_latest['gap_percent'] > GAP_UPPER_BOUND) | (df_latest['gap_percent'] < GAP_LOWER_BOUND)
        
        # Filtrar para el resumen estratégico (solo barrios con volumen suficiente y sin gaps extremos)
        df_strategic = df_latest[~df_latest['low_volume'] & ~df_latest['extreme_gap']].copy()
        
        # 7. Ordenar por Gap Porcentual
        df_latest = df_latest.sort_values('gap_percent', ascending=False)
        df_strategic = df_strategic.sort_values('gap_percent', ascending=False)
        
        # Exportar resultados
        output_dir = PROJECT_ROOT / "data" / "exports" / "analysis"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = output_dir / f"negotiation_gap_{latest_year}.csv"
        df_gap.to_csv(file_path, index=False)
        
        logger.info(f"✅ Análisis completado. Resultados guardados en: {file_path}")
        
        # --- RESUMEN ESTRATÉGICO ---
        logger.info("\n" + "=" * 60)
        logger.info(f"📊 RESUMEN ESTRATÉGICO (SIN RUIDO) - AÑO {latest_year}")
        logger.info(f"Filtro: Barrios con > {VOLUME_THRESHOLD} anuncios promedio/mes")
        logger.info("=" * 60)
        
        avg_gap = df_strategic['gap_percent'].mean()
        logger.info(f"Margen de Negociación Promedio en Barcelona (Filtrado): {avg_gap:.2f}%")
        
        logger.info("\n🏆 TOP 5 BARRIOS CON MÁS MARGEN (Oportunidades Reales):")
        for _, row in df_strategic.head(5).iterrows():
            logger.info(f"  • {row['barrio_nombre']} ({row['distrito_nombre']}): {row['gap_percent']:.1f}% "
                        f"(Oferta: {row['asking_price']:.0f}€ vs Real: {row['transaction_price']:.0f}€, "
                        f"Anuncios: {row['avg_num_anuncios']:.1f})")
            
        logger.info("\n📉 TOP 5 BARRIOS CON MENOS MARGEN (Precios más ajustados):")
        for _, row in df_strategic.tail(5).iloc[::-1].iterrows():
            logger.info(f"  • {row['barrio_nombre']} ({row['distrito_nombre']}): {row['gap_percent']:.1f}% "
                        f"(Oferta: {row['asking_price']:.0f}€ vs Real: {row['transaction_price']:.0f}€, "
                        f"Anuncios: {row['avg_num_anuncios']:.1f})")

        # Reportar barrios filtrados por ruido
        noise_barrios = df_latest[df_latest['low_volume'] | df_latest['extreme_gap']]
        if not noise_barrios.empty:
            logger.info(f"\n⚠️ SE HAN FILTRADO {len(noise_barrios)} BARRIOS POR RUIDO/ANOMALÍAS:")
            for _, row in noise_barrios.iterrows():
                reason = "Bajo Volumen" if row['low_volume'] else "Gap Extremo"
                vol_str = f"{row['avg_num_anuncios']:.1f}" if pd.notna(row['avg_num_anuncios']) else "N/A"
                logger.info(f"  • {row['barrio_nombre']}: Gap {row['gap_percent']:.1f}% ({reason}, Vol: {vol_str})")

        # Guardar también una versión para Looker
        looker_path = PROJECT_ROOT / "data" / "exports" / "looker_studio" / "negotiation_gap_master.csv"
        df_gap.to_csv(looker_path, index=False)
        logger.info(f"✅ Tabla de Gap exportada para Looker: {looker_path}")

    except Exception as e:
        logger.error(f"❌ Error durante el análisis: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    run_gap_analysis()
