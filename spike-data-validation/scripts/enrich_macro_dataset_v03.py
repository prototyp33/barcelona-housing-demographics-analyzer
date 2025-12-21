#!/usr/bin/env python3
"""
Enriquece el dataset MACRO v0.2 con features optimizadas de fact_renta y fact_demografia_ampliada.

Este script:
1. Carga el dataset MACRO v0.2 actual
2. Enriquece con fact_renta (variables relevantes identificadas en Fase 1)
3. Enriquece con fact_demografia_ampliada (variables relevantes identificadas en Fase 1)
4. Valida integridad de datos (nulos, duplicados)
5. Guarda el dataset enriquecido para MACRO v0.3

Variables incluidas basadas en Fase 1 (|corr| > 0.3):
- Renta: renta_euros_mean, renta_promedio_mean, renta_mediana_mean, renta_min_mean
- Demografía: poblacion_total, prop_hombres, prop_mujeres, prop_18_34, prop_50_64

Uso:
    python3 spike-data-validation/scripts/enrich_macro_dataset_v03.py \
        --input spike-data-validation/data/processed/gracia_merged_agg_barrio_anio_dataset_v02.csv \
        --output spike-data-validation/data/processed/gracia_merged_agg_barrio_anio_dataset_v03.csv
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
DEFAULT_INPUT = Path("spike-data-validation/data/processed/gracia_merged_agg_barrio_anio_dataset_v02.csv")
DEFAULT_OUTPUT = Path("spike-data-validation/data/processed/gracia_merged_agg_barrio_anio_dataset_v03.csv")
DEFAULT_DB = Path("data/processed/database.db")


def setup_logging() -> None:
    """Configura logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def load_renta_features(db_path: Path) -> pd.DataFrame:
    """
    Carga features de fact_renta relevantes identificadas en Fase 1.
    
    Variables incluidas (|corr| > 0.3):
    - renta_euros_mean: r=0.312, p=0.037
    - renta_promedio_mean: r=0.312, p=0.037
    - renta_mediana_mean: r=0.310, p=0.038
    - renta_min_mean: r=0.342, p=0.022 (mayor correlación)
    
    Args:
        db_path: Ruta a la base de datos SQLite
        
    Returns:
        DataFrame con features de renta agregadas por barrio_id × anio
    """
    logger.info("Cargando features de fact_renta (v0.3 - optimizado)...")
    
    if not db_path.exists():
        logger.warning(f"Base de datos no encontrada: {db_path}")
        return pd.DataFrame()
    
    conn = sqlite3.connect(str(db_path))
    
    try:
        # Agregar fact_renta por barrio×año
        # Incluir solo variables relevantes identificadas en Fase 1
        query = """
            SELECT 
                barrio_id,
                anio,
                AVG(renta_euros) as renta_euros_mean,
                AVG(renta_promedio) as renta_promedio_mean,
                AVG(renta_mediana) as renta_mediana_mean,
                AVG(renta_min) as renta_min_mean,
                COUNT(*) as n_secciones_renta
            FROM fact_renta
            GROUP BY barrio_id, anio
            ORDER BY barrio_id, anio
        """
        
        df_renta = pd.read_sql_query(query, conn)
        
        logger.info(f"  ✅ {len(df_renta)} registros de renta cargados")
        if len(df_renta) > 0:
            logger.info(f"     Cobertura: {df_renta['anio'].min()}-{df_renta['anio'].max()}")
            logger.info(f"     Barrios: {df_renta['barrio_id'].nunique()}")
            logger.info(f"     Variables: renta_euros_mean, renta_promedio_mean, renta_mediana_mean, renta_min_mean")
        
        return df_renta
        
    finally:
        conn.close()


def load_demografia_features(db_path: Path) -> pd.DataFrame:
    """
    Carga features de fact_demografia_ampliada relevantes identificadas en Fase 1.
    
    Variables incluidas (|corr| > 0.3):
    - poblacion_total: r=0.915, p=0.029 (muy alta correlación)
    - prop_hombres: r=0.658, p=0.227
    - prop_mujeres: r=-0.658, p=0.227
    - prop_18_34: r=0.763, p=0.134
    - prop_50_64: r=-0.941, p=0.017 (muy alta correlación negativa)
    
    Args:
        db_path: Ruta a la base de datos SQLite
        
    Returns:
        DataFrame con features demográficas agregadas por barrio_id × anio
    """
    logger.info("Cargando features de fact_demografia_ampliada (v0.3 - optimizado)...")
    
    if not db_path.exists():
        logger.warning(f"Base de datos no encontrada: {db_path}")
        return pd.DataFrame()
    
    conn = sqlite3.connect(str(db_path))
    
    try:
        # Agregar fact_demografia_ampliada por barrio×año
        # Incluir solo variables relevantes identificadas en Fase 1
        query = """
            SELECT 
                barrio_id,
                anio,
                SUM(poblacion) as poblacion_total,
                -- Proporción por sexo (variables relevantes)
                SUM(CASE WHEN sexo = 'hombre' THEN poblacion ELSE 0 END) * 1.0 / SUM(poblacion) as prop_hombres,
                SUM(CASE WHEN sexo = 'mujer' THEN poblacion ELSE 0 END) * 1.0 / SUM(poblacion) as prop_mujeres,
                -- Proporción por grupo de edad (solo variables relevantes)
                SUM(CASE WHEN grupo_edad = '18-34' THEN poblacion ELSE 0 END) * 1.0 / SUM(poblacion) as prop_18_34,
                SUM(CASE WHEN grupo_edad = '50-64' THEN poblacion ELSE 0 END) * 1.0 / SUM(poblacion) as prop_50_64
            FROM fact_demografia_ampliada
            WHERE poblacion IS NOT NULL
            GROUP BY barrio_id, anio
            HAVING SUM(poblacion) > 0
            ORDER BY barrio_id, anio
        """
        
        df_demo = pd.read_sql_query(query, conn)
        
        logger.info(f"  ✅ {len(df_demo)} registros demográficos cargados")
        if len(df_demo) > 0:
            logger.info(f"     Cobertura: {df_demo['anio'].min()}-{df_demo['anio'].max()}")
            logger.info(f"     Barrios: {df_demo['barrio_id'].nunique()}")
            logger.info(f"     Variables: poblacion_total, prop_hombres, prop_mujeres, prop_18_34, prop_50_64")
        
        return df_demo
        
    finally:
        conn.close()


def validate_data_integrity(df: pd.DataFrame, original_count: int) -> Dict[str, any]:
    """
    Valida integridad de datos después del enriquecimiento.
    
    Args:
        df: DataFrame enriquecido
        original_count: Número de registros originales
        
    Returns:
        Diccionario con resultados de validación
    """
    logger.info("Validando integridad de datos...")
    
    validation_results = {
        "total_records": len(df),
        "original_count": original_count,
        "records_lost": original_count - len(df),
        "duplicates": 0,
        "null_counts": {},
        "validation_passed": True
    }
    
    # Verificar duplicados
    key_cols = ['barrio_id', 'anio']
    if all(col in df.columns for col in key_cols):
        duplicates = df.duplicated(subset=key_cols).sum()
        validation_results["duplicates"] = int(duplicates)
        
        if duplicates > 0:
            logger.warning(f"  ⚠️  {duplicates} duplicados encontrados en (barrio_id, anio)")
            validation_results["validation_passed"] = False
        else:
            logger.info(f"  ✅ Sin duplicados en (barrio_id, anio)")
    
    # Verificar pérdida de registros
    if validation_results["records_lost"] > 0:
        logger.warning(f"  ⚠️  {validation_results['records_lost']} registros perdidos")
        validation_results["validation_passed"] = False
    else:
        logger.info(f"  ✅ No se perdieron registros")
    
    # Contar nulos en nuevas columnas (solo las añadidas en v0.3)
    new_columns = [col for col in df.columns if any(x in col.lower() for x in ['renta_euros_mean', 'renta_promedio_mean', 'renta_mediana_mean', 'renta_min_mean', 'prop_hombres', 'prop_mujeres', 'prop_18_34', 'prop_50_64', 'poblacion_total']) and not col.endswith('_x') and not col.endswith('_y') and not col.endswith('_new')]
    for col in new_columns:
        null_count = df[col].isna().sum()
        null_pct = (null_count / len(df)) * 100 if len(df) > 0 else 0
        validation_results["null_counts"][col] = {
            "null_count": int(null_count),
            "null_percentage": float(null_pct)
        }
        
        if null_pct > 50:
            logger.warning(f"  ⚠️  {col}: {null_count}/{len(df)} nulos ({null_pct:.1f}%)")
        else:
            logger.info(f"  ✅ {col}: {null_count}/{len(df)} nulos ({null_pct:.1f}%)")
    
    if validation_results["validation_passed"]:
        logger.info("  ✅ Validación de integridad: PASADA")
    else:
        logger.warning("  ⚠️  Validación de integridad: FALLIDA (revisar warnings)")
    
    return validation_results


def enrich_macro_dataset(
    df_macro: pd.DataFrame,
    df_renta: pd.DataFrame,
    df_demo: pd.DataFrame
) -> pd.DataFrame:
    """
    Enriquece el dataset MACRO con features de renta y demografía (v0.3 optimizado).
    
    Args:
        df_macro: Dataset MACRO v0.2 original
        df_renta: Features de renta por barrio×año
        df_demo: Features demográficas por barrio×año
        
    Returns:
        Dataset MACRO v0.3 enriquecido
    """
    logger.info("Enriqueciendo dataset MACRO v0.2 → v0.3...")
    
    df_enriched = df_macro.copy()
    initial_count = len(df_enriched)
    
    # Merge con fact_renta
    if not df_renta.empty:
        logger.info(f"  Merging con fact_renta ({len(df_renta)} registros)...")
        
        # Identificar columnas que ya existen en df_macro para evitar duplicados
        existing_renta_cols = [col for col in df_renta.columns if col in df_enriched.columns and col not in ['barrio_id', 'anio']]
        if existing_renta_cols:
            logger.info(f"    Columnas existentes detectadas: {existing_renta_cols}")
            logger.info(f"    Eliminando columnas existentes antes del merge...")
            df_renta_clean = df_renta.drop(columns=existing_renta_cols)
        else:
            df_renta_clean = df_renta
        
        df_enriched = df_enriched.merge(
            df_renta_clean,
            on=['barrio_id', 'anio'],
            how='left',
            suffixes=('', '_new')
        )
        
        # Eliminar columnas con sufijo _new si existen (duplicados)
        new_cols = [col for col in df_enriched.columns if col.endswith('_new')]
        if new_cols:
            df_enriched = df_enriched.drop(columns=new_cols)
        
        # Verificar cuántos matches
        renta_matched = df_enriched['renta_euros_mean'].notna().sum() if 'renta_euros_mean' in df_enriched.columns else 0
        logger.info(f"    ✅ {renta_matched}/{len(df_enriched)} registros con datos de renta ({renta_matched/len(df_enriched)*100:.1f}%)")
    else:
        logger.warning("  ⚠️  No hay datos de renta disponibles")
    
    # Merge con fact_demografia_ampliada
    if not df_demo.empty:
        logger.info(f"  Merging con fact_demografia_ampliada ({len(df_demo)} registros)...")
        
        # Identificar columnas que ya existen en df_enriched para evitar duplicados
        existing_demo_cols = [col for col in df_demo.columns if col in df_enriched.columns and col not in ['barrio_id', 'anio']]
        if existing_demo_cols:
            logger.info(f"    Columnas existentes detectadas: {existing_demo_cols}")
            logger.info(f"    Eliminando columnas existentes antes del merge...")
            df_demo_clean = df_demo.drop(columns=existing_demo_cols)
        else:
            df_demo_clean = df_demo
        
        df_enriched = df_enriched.merge(
            df_demo_clean,
            on=['barrio_id', 'anio'],
            how='left',
            suffixes=('', '_new')
        )
        
        # Eliminar columnas con sufijo _new si existen (duplicados)
        new_cols = [col for col in df_enriched.columns if col.endswith('_new')]
        if new_cols:
            df_enriched = df_enriched.drop(columns=new_cols)
        
        # Verificar cuántos matches
        demo_matched = df_enriched['poblacion_total'].notna().sum() if 'poblacion_total' in df_enriched.columns else 0
        logger.info(f"    ✅ {demo_matched}/{len(df_enriched)} registros con datos demográficos ({demo_matched/len(df_enriched)*100:.1f}%)")
        if demo_matched == 0:
            logger.warning(f"    ⚠️  No hay matches: fact_demografia_ampliada solo tiene datos para 2025")
    else:
        logger.warning("  ⚠️  No hay datos demográficos disponibles")
    
    logger.info(f"  ✅ Dataset enriquecido: {len(df_enriched)} observaciones (inicial: {initial_count})")
    
    # Validar integridad
    validation_results = validate_data_integrity(df_enriched, initial_count)
    
    return df_enriched


def main() -> int:
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Enriquece dataset MACRO v0.2 → v0.3 con features optimizadas"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="Archivo CSV del dataset MACRO v0.2"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Archivo CSV de salida (dataset MACRO v0.3)"
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
    logger.info("ENRIQUECIMIENTO DATASET MACRO v0.2 → v0.3")
    logger.info("=" * 70)
    logger.info("Variables basadas en Fase 1 (|corr| > 0.3):")
    logger.info("  - Renta: renta_euros_mean, renta_promedio_mean, renta_mediana_mean, renta_min_mean")
    logger.info("  - Demografía: poblacion_total, prop_hombres, prop_mujeres, prop_18_34, prop_50_64")
    logger.info("=" * 70)
    
    # Cargar dataset MACRO v0.2
    logger.info(f"Cargando dataset MACRO v0.2: {args.input}")
    if not args.input.exists():
        logger.error(f"Archivo no encontrado: {args.input}")
        logger.info("💡 Sugerencia: Ejecutar primero enrich_macro_dataset_v02.py si no existe v0.2")
        return 1
    
    df_macro = pd.read_csv(args.input)
    logger.info(f"  ✅ {len(df_macro)} observaciones cargadas")
    logger.info(f"     Columnas originales: {len(df_macro.columns)}")
    
    # Cargar features de renta (optimizadas)
    df_renta = load_renta_features(args.db)
    
    # Cargar features demográficas (optimizadas)
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
    logger.info("=" * 70)
    logger.info("📋 Próximo paso: Entrenar modelo MACRO v0.3 con train_macro_v03.py")
    
    return 0


if __name__ == "__main__":
    exit(main())
