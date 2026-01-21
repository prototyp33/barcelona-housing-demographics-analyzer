#!/usr/bin/env python3
"""
Análisis de Riesgo de Gentrificación (Semáforo 2025).

Cruza datos de Renta Bruta e Índice Gini (2023) con subidas de alquiler (2025)
para detectar barrios en riesgo de exclusión o gentrificación acelerada.
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
import psycopg2
from dotenv import load_dotenv
from pathlib import Path

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
ID_RENTAL = 'b37xv8wcjh'  # Alquiler medio mensual Incasòl

def analyze_gentrification():
    logger.info("=" * 60)
    logger.info("🚦 Iniciando Análisis: Semáforo de Gentrificación 2025")
    logger.info("=" * 60)

    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        logger.info("✅ Conectado a PostgreSQL")
    except Exception as e:
        logger.error(f"❌ Error al conectar a PostgreSQL: {e}")
        return

    try:
        # 1. Obtener datos de Renta y Gini (2023 - Último disponible)
        query_renta = """
            SELECT barrio_id, anio, renta_bruta_llar, indice_gini, ratio_p80_p20
            FROM fact_renta_avanzada
            WHERE anio = 2023
        """
        df_renta = pd.read_sql_query(query_renta, conn)
        
        # 2. Obtener precios de Alquiler (2023 y 2025)
        query_precios = f"""
            SELECT barrio_id, anio, AVG(precio_mes_alquiler) as avg_rent
            FROM fact_precios
            WHERE dataset_id = '{ID_RENTAL}' AND anio IN (2023, 2025)
            GROUP BY barrio_id, anio
        """
        df_precios = pd.read_sql_query(query_precios, conn)
        
        # 3. Obtener nombres de barrios
        barrios = pd.read_sql_query("SELECT barrio_id, barrio_nombre, distrito_nombre FROM dim_barrios", conn)

        if df_renta.empty or df_precios.empty:
            logger.warning("⚠️ Datos insuficientes para el análisis.")
            return

        # 4. Procesar subida de alquiler (2023 -> 2025)
        df_pivot = df_precios.pivot(index='barrio_id', columns='anio', values='avg_rent').reset_index()
        df_pivot.columns = ['barrio_id', 'rent_2023', 'rent_2025']
        df_pivot['rent_increase_pct'] = ((df_pivot['rent_2025'] - df_pivot['rent_2023']) / df_pivot['rent_2023']) * 100

        # 5. Mergear todo
        df_risk = pd.merge(df_pivot, df_renta, on='barrio_id')
        df_risk = pd.merge(df_risk, barrios, on='barrio_id')

        # 6. Definir lógica del Semáforo
        # Umbrales
        RENT_INCREASE_HIGH = 10.0  # >10% en 2 años
        GINI_HIGH = 35.0          # Índice Gini alto (>35 en escala 0-100)
        # Umbral de vulnerabilidad: Por debajo de 60k€/año por hogar (aproximadamente percentil 60 en BCN)
        INCOME_VULNERABLE = 60000 

        def calculate_risk(row):
            is_vulnerable = row['renta_bruta_llar'] < INCOME_VULNERABLE
            high_increase = row['rent_increase_pct'] > RENT_INCREASE_HIGH
            high_gini = row['indice_gini'] > GINI_HIGH
            
            # Gentrificación: Presión alta en zonas vulnerables
            if is_vulnerable and high_increase:
                return 'CRÍTICO 🔴'
            # Riesgo alto: O mucha subida, o zona vulnerable con desigualdad
            if high_increase or (is_vulnerable and high_gini):
                return 'ALTO 🟠'
            # Riesgo medio: Desigualdad alta o zona vulnerable
            if high_gini or is_vulnerable:
                return 'MEDIO 🟡'
            return 'BAJO 🟢'

        df_risk['nivel_riesgo'] = df_risk.apply(calculate_risk, axis=1)

        # 7. Ordenar por criticidad (Aumento alquiler + Gini)
        df_risk = df_risk.sort_values(['nivel_riesgo', 'rent_increase_pct'], ascending=[False, False])

        # Exportar
        output_dir = PROJECT_ROOT / "data" / "exports" / "analysis"
        output_dir.mkdir(parents=True, exist_ok=True)
        file_path = output_dir / "gentrification_risk_2025.csv"
        df_risk.to_csv(file_path, index=False)
        
        logger.info(f"✅ Análisis completado. Resultados guardados en: {file_path}")

        # --- RESUMEN ESTRATÉGICO ---
        logger.info("\n" + "=" * 60)
        logger.info("🚦 SEMÁFORO DE GENTRIFICACIÓN 2025")
        logger.info("=" * 60)
        
        for nivel in ['CRÍTICO 🔴', 'ALTO 🟠', 'MEDIO 🟡']:
            subset = df_risk[df_risk['nivel_riesgo'] == nivel]
            if not subset.empty:
                logger.info(f"\n{nivel} ({len(subset)} barrios):")
                for _, row in subset.head(5).iterrows():
                    logger.info(f"  • {row['barrio_nombre']} ({row['distrito_nombre']}): "
                                f"Alquiler +{row['rent_increase_pct']:.1f}%, Gini: {row['indice_gini']:.1f}, "
                                f"Renta: {row['renta_bruta_llar']:.0f}€")

        # Guardar para Looker
        looker_path = PROJECT_ROOT / "data" / "exports" / "looker_studio" / "gentrification_master.csv"
        df_risk.to_csv(looker_path, index=False)
        logger.info(f"\n✅ Tabla de Gentrificación exportada para Looker: {looker_path}")

    except Exception as e:
        logger.error(f"❌ Error durante el análisis: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    analyze_gentrification()
