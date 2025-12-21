#!/usr/bin/env python3
"""
Enriquece el dataset MACRO v0.1 con features de fact_renta y fact_demografia_ampliada.

Este script:
1. Carga el dataset MACRO actual (gracia_merged_agg_barrio_anio_dataset.csv)
2. Enriquece con fact_renta (renta_promedio, renta_mediana por barrio×año)
3. Enriquece con fact_demografia_ampliada (agregaciones demográficas por barrio×año)
4. Guarda el dataset enriquecido para MACRO v0.2

Uso:
    python3 spike-data-validation/scripts/enrich_macro_dataset_v02.py \
        --input spike-data-validation/data/processed/gracia_merged_agg_barrio_anio_dataset.csv \
        --output spike-data-validation/data/processed/gracia_merged_agg_barrio_anio_dataset_v02.csv
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Dict

import pandas as pd
import sqlite3

logger = logging.getLogger(__name__)

# Rutas por defecto
DEFAULT_INPUT = Path("spike-data-validation/data/processed/gracia_merged_agg_barrio_anio_dataset.csv")
DEFAULT_OUTPUT = Path("spike-data-validation/data/processed/gracia_merged_agg_barrio_anio_dataset_v02.csv")
DEFAULT_DB = Path("data/processed/database.db")


def setup_logging() -> None:
    """Configura logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def load_renta_features(db_path: Path) -> pd.DataFrame:
    """
    Carga y agrega features de fact_renta por barrio×año.
    
    Args:
        db_path: Ruta a la base de datos SQLite
        
    Returns:
        DataFrame con features de renta agregadas por barrio_id × anio
    """
    logger.info("Cargando features de fact_renta...")
    
    if not db_path.exists():
        logger.warning(f"Base de datos no encontrada: {db_path}")
        return pd.DataFrame()
    
    conn = sqlite3.connect(str(db_path))
    
    try:
        # Agregar fact_renta por barrio×año
        query = """
            SELECT 
                barrio_id,
                anio,
                AVG(renta_promedio) as renta_promedio_barrio,
                AVG(renta_mediana) as renta_mediana_barrio,
                AVG(renta_min) as renta_min_barrio,
                AVG(renta_max) as renta_max_barrio,
                COUNT(*) as n_secciones_renta
            FROM fact_renta
            GROUP BY barrio_id, anio
            ORDER BY barrio_id, anio
        """
        
        df_renta = pd.read_sql_query(query, conn)
        
        logger.info(f"  ✅ {len(df_renta)} registros de renta cargados")
        logger.info(f"     Cobertura: {df_renta['anio'].min()}-{df_renta['anio'].max()}")
        logger.info(f"     Barrios: {df_renta['barrio_id'].nunique()}")
        
        return df_renta
        
    finally:
        conn.close()


def load_demografia_features(db_path: Path) -> pd.DataFrame:
    """
    Carga y agrega features de fact_demografia_ampliada por barrio×año.
    
    Args:
        db_path: Ruta a la base de datos SQLite
        
    Returns:
        DataFrame con features demográficas agregadas por barrio_id × anio
    """
    logger.info("Cargando features de fact_demografia_ampliada...")
    
    if not db_path.exists():
        logger.warning(f"Base de datos no encontrada: {db_path}")
        return pd.DataFrame()
    
    conn = sqlite3.connect(str(db_path))
    
    try:
        # Agregar fact_demografia_ampliada por barrio×año
        # Calcular métricas demográficas relevantes
        query = """
            SELECT 
                barrio_id,
                anio,
                SUM(poblacion) as poblacion_total,
                -- Proporción por sexo
                SUM(CASE WHEN sexo = 'hombre' THEN poblacion ELSE 0 END) * 1.0 / SUM(poblacion) as prop_hombres,
                SUM(CASE WHEN sexo = 'mujer' THEN poblacion ELSE 0 END) * 1.0 / SUM(poblacion) as prop_mujeres,
                -- Proporción por grupo de edad
                SUM(CASE WHEN grupo_edad = '0-17' THEN poblacion ELSE 0 END) * 1.0 / SUM(poblacion) as prop_0_17,
                SUM(CASE WHEN grupo_edad = '18-34' THEN poblacion ELSE 0 END) * 1.0 / SUM(poblacion) as prop_18_34,
                SUM(CASE WHEN grupo_edad = '35-49' THEN poblacion ELSE 0 END) * 1.0 / SUM(poblacion) as prop_35_49,
                SUM(CASE WHEN grupo_edad = '50-64' THEN poblacion ELSE 0 END) * 1.0 / SUM(poblacion) as prop_50_64,
                SUM(CASE WHEN grupo_edad = '65+' THEN poblacion ELSE 0 END) * 1.0 / SUM(poblacion) as prop_65_plus,
                -- Proporción por nacionalidad
                SUM(CASE WHEN nacionalidad = 'España' THEN poblacion ELSE 0 END) * 1.0 / SUM(poblacion) as prop_espana,
                SUM(CASE WHEN nacionalidad != 'España' THEN poblacion ELSE 0 END) * 1.0 / SUM(poblacion) as prop_extranjeros
            FROM fact_demografia_ampliada
            GROUP BY barrio_id, anio
            ORDER BY barrio_id, anio
        """
        
        df_demo = pd.read_sql_query(query, conn)
        
        logger.info(f"  ✅ {len(df_demo)} registros demográficos cargados")
        if len(df_demo) > 0:
            logger.info(f"     Cobertura: {df_demo['anio'].min()}-{df_demo['anio'].max()}")
            logger.info(f"     Barrios: {df_demo['barrio_id'].nunique()}")
        
        return df_demo
        
    finally:
        conn.close()


def enrich_macro_dataset(
    df_macro: pd.DataFrame,
    df_renta: pd.DataFrame,
    df_demo: pd.DataFrame
) -> pd.DataFrame:
    """
    Enriquece el dataset MACRO con features de renta y demografía.
    
    Args:
        df_macro: Dataset MACRO original
        df_renta: Features de renta por barrio×año
        df_demo: Features demográficas por barrio×año
        
    Returns:
        Dataset MACRO enriquecido
    """
    logger.info("Enriqueciendo dataset MACRO...")
    
    df_enriched = df_macro.copy()
    initial_count = len(df_enriched)
    
    # Merge con fact_renta
    if not df_renta.empty:
        logger.info(f"  Merging con fact_renta ({len(df_renta)} registros)...")
        df_enriched = df_enriched.merge(
            df_renta,
            on=['barrio_id', 'anio'],
            how='left'
        )
        
        # Verificar cuántos matches
        renta_matched = df_enriched['renta_promedio_barrio'].notna().sum()
        logger.info(f"    ✅ {renta_matched}/{len(df_enriched)} registros con datos de renta ({renta_matched/len(df_enriched)*100:.1f}%)")
    else:
        logger.warning("  ⚠️  No hay datos de renta disponibles")
    
    # Merge con fact_demografia_ampliada
    if not df_demo.empty:
        logger.info(f"  Merging con fact_demografia_ampliada ({len(df_demo)} registros)...")
        df_enriched = df_enriched.merge(
            df_demo,
            on=['barrio_id', 'anio'],
            how='left'
        )
        
        # Verificar cuántos matches
        demo_matched = df_enriched['poblacion_total'].notna().sum()
        logger.info(f"    ✅ {demo_matched}/{len(df_enriched)} registros con datos demográficos ({demo_matched/len(df_enriched)*100:.1f}%)")
    else:
        logger.warning("  ⚠️  No hay datos demográficos disponibles")
    
    logger.info(f"  ✅ Dataset enriquecido: {len(df_enriched)} observaciones (inicial: {initial_count})")
    
    return df_enriched


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Enriquece dataset MACRO con features de renta y demografía"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="Archivo CSV del dataset MACRO v0.1"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Archivo CSV de salida (dataset MACRO v0.2)"
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB,
        help="Ruta a la base de datos SQLite"
    )
    
    args = parser.parse_args()
    setup_logging()
    
    logger.info("=" * 70)
    logger.info("ENRIQUECIMIENTO DATASET MACRO v0.2")
    logger.info("=" * 70)
    
    # Cargar dataset MACRO original
    logger.info(f"Cargando dataset MACRO: {args.input}")
    if not args.input.exists():
        logger.error(f"Archivo no encontrado: {args.input}")
        return 1
    
    df_macro = pd.read_csv(args.input)
    logger.info(f"  ✅ {len(df_macro)} observaciones cargadas")
    logger.info(f"     Columnas: {df_macro.columns.tolist()}")
    
    # Cargar features de renta
    df_renta = load_renta_features(args.db)
    
    # Cargar features demográficas
    df_demo = load_demografia_features(args.db)
    
    # Enriquecer dataset
    df_enriched = enrich_macro_dataset(df_macro, df_renta, df_demo)
    
    # Guardar dataset enriquecido
    args.output.parent.mkdir(parents=True, exist_ok=True)
    df_enriched.to_csv(args.output, index=False)
    logger.info(f"✅ Dataset enriquecido guardado: {args.output}")
    
    # Resumen de features añadidas
    logger.info("\n📊 Resumen de Features Añadidas:")
    original_cols = set(df_macro.columns)
    new_cols = set(df_enriched.columns) - original_cols
    
    if new_cols:
        logger.info(f"  Nuevas columnas ({len(new_cols)}):")
        for col in sorted(new_cols):
            non_null = df_enriched[col].notna().sum()
            pct = non_null / len(df_enriched) * 100
            logger.info(f"    - {col}: {non_null}/{len(df_enriched)} no nulos ({pct:.1f}%)")
    else:
        logger.warning("  ⚠️  No se añadieron nuevas columnas")
    
    logger.info("=" * 70)
    logger.info("✅ Proceso completado")
    
    return 0


if __name__ == "__main__":
    exit(main())

