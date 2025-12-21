#!/usr/bin/env python3
"""
Filtra y limpia el dataset de matching para eliminar outliers y propiedades no-residenciales.

Basado en la investigación de correlaciones negativas:
1. Filtrar outliers (superficie, precio/m²)
2. Filtrar propiedades no-residenciales
3. Filtrar matches de baja calidad
4. Eliminar duplicados

Uso:
    python3 filter_clean_dataset.py \
        --input spike-data-validation/data/processed/fase2/idealista_catastro_matched_improved.csv \
        --output spike-data-validation/data/processed/fase2/dataset_micro_hedonic_cleaned.csv
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any, Dict

import pandas as pd

logger = logging.getLogger(__name__)

# Rutas por defecto
INPUT_FILE = Path("spike-data-validation/data/processed/fase2/idealista_catastro_matched_improved.csv")
OUTPUT_DIR = Path("spike-data-validation/data/processed/fase2")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def setup_logging() -> None:
    """Configura logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def filter_non_residential(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filtra propiedades no-residenciales (locales, oficinas, garajes).
    
    Args:
        df: DataFrame con propiedades
        
    Returns:
        DataFrame filtrado
    """
    logger.info("Filtrando propiedades no-residenciales...")
    
    initial_count = len(df)
    
    # Keywords no-residenciales
    non_residential_keywords = [
        'local', 'comercial', 'oficina', 'despacho', 'garaje', 
        'parking', 'trastero', 'nave', 'almacén'
    ]
    
    if 'descripcion' in df.columns:
        desc_lower = df['descripcion'].str.lower().fillna('')
        mask_non_res = desc_lower.str.contains('|'.join(non_residential_keywords), na=False)
        df_filtered = df[~mask_non_res].copy()
    else:
        df_filtered = df.copy()
    
    filtered_count = initial_count - len(df_filtered)
    logger.info(f"  ✅ Eliminadas {filtered_count} propiedades no-residenciales ({filtered_count/initial_count*100:.1f}%)")
    
    return df_filtered


def filter_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filtra outliers en superficie y precio/m².
    
    Args:
        df: DataFrame con propiedades
        
    Returns:
        DataFrame filtrado
    """
    logger.info("Filtrando outliers...")
    
    initial_count = len(df)
    
    # Calcular precio_m2 si no existe
    if 'precio_m2' not in df.columns:
        df['precio_m2'] = df['precio'] / df['superficie_m2']
    
    # Filtros de outliers
    # 1. Superficie razonable para vivienda (30-300 m²)
    mask_surface = (df['superficie_m2'] >= 30) & (df['superficie_m2'] <= 300)
    
    # 2. Precio/m² razonable para Gràcia (2,000-15,000 €/m²)
    mask_price = (df['precio_m2'] >= 2000) & (df['precio_m2'] <= 15000)
    
    # 3. Habitaciones razonables (1-6)
    if 'habitaciones' in df.columns:
        mask_rooms = (df['habitaciones'] >= 1) & (df['habitaciones'] <= 6)
    else:
        mask_rooms = pd.Series([True] * len(df), index=df.index)
    
    # Aplicar todos los filtros
    df_filtered = df[mask_surface & mask_price & mask_rooms].copy()
    
    filtered_count = initial_count - len(df_filtered)
    logger.info(f"  ✅ Eliminadas {filtered_count} propiedades con outliers ({filtered_count/initial_count*100:.1f}%)")
    logger.info(f"     Superficie: {initial_count - mask_surface.sum()} eliminadas")
    logger.info(f"     Precio/m²: {initial_count - mask_price.sum()} eliminadas")
    if 'habitaciones' in df.columns:
        logger.info(f"     Habitaciones: {initial_count - mask_rooms.sum()} eliminadas")
    
    return df_filtered


def filter_low_quality_matches(df: pd.DataFrame, min_score: float = 0.6) -> pd.DataFrame:
    """
    Filtra matches de baja calidad.
    
    Args:
        df: DataFrame con matches
        min_score: Score mínimo para mantener match
        
    Returns:
        DataFrame filtrado
    """
    logger.info(f"Filtrando matches de baja calidad (score < {min_score})...")
    
    initial_count = len(df)
    
    if 'match_score' in df.columns:
        df_filtered = df[df['match_score'] >= min_score].copy()
        filtered_count = initial_count - len(df_filtered)
        logger.info(f"  ✅ Eliminadas {filtered_count} propiedades con match score bajo ({filtered_count/initial_count*100:.1f}%)")
    else:
        df_filtered = df.copy()
        logger.info("  ⚠️  No se encontró columna 'match_score', saltando filtro")
    
    return df_filtered


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Elimina duplicados basados en link de Idealista.
    
    Args:
        df: DataFrame con propiedades
        
    Returns:
        DataFrame sin duplicados
    """
    logger.info("Eliminando duplicados...")
    
    initial_count = len(df)
    
    if 'link' in df.columns:
        # Mantener el primero de cada duplicado
        df_filtered = df.drop_duplicates(subset=['link'], keep='first').copy()
        filtered_count = initial_count - len(df_filtered)
        logger.info(f"  ✅ Eliminados {filtered_count} duplicados ({filtered_count/initial_count*100:.1f}%)")
    else:
        df_filtered = df.copy()
        logger.info("  ⚠️  No se encontró columna 'link', saltando eliminación de duplicados")
    
    return df_filtered


def clean_dataset(df: pd.DataFrame, min_match_score: float = 0.6) -> pd.DataFrame:
    """
    Aplica todos los filtros de limpieza al dataset.
    
    Args:
        df: DataFrame original
        min_match_score: Score mínimo para matches
        
    Returns:
        DataFrame limpio
    """
    logger.info("=" * 70)
    logger.info("LIMPIEZA DE DATASET")
    logger.info("=" * 70)
    logger.info(f"Dataset inicial: {len(df)} observaciones")
    
    # Aplicar filtros en orden
    df_clean = df.copy()
    
    # 1. Eliminar duplicados
    df_clean = remove_duplicates(df_clean)
    
    # 2. Filtrar propiedades no-residenciales
    df_clean = filter_non_residential(df_clean)
    
    # 3. Filtrar outliers
    df_clean = filter_outliers(df_clean)
    
    # 4. Filtrar matches de baja calidad
    df_clean = filter_low_quality_matches(df_clean, min_match_score)
    
    logger.info("=" * 70)
    logger.info(f"Dataset final: {len(df_clean)} observaciones")
    logger.info(f"Reducción: {len(df) - len(df_clean)} observaciones eliminadas ({((len(df) - len(df_clean))/len(df)*100):.1f}%)")
    logger.info("=" * 70)
    
    return df_clean


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Filtra y limpia dataset de matching"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=INPUT_FILE,
        help="Archivo CSV de entrada"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_DIR / "dataset_micro_hedonic_cleaned.csv",
        help="Archivo CSV de salida"
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.6,
        help="Score mínimo para matches (default: 0.6)"
    )
    
    args = parser.parse_args()
    setup_logging()
    
    # Cargar datos
    logger.info(f"Cargando datos: {args.input}")
    df = pd.read_csv(args.input)
    logger.info(f"  ✅ {len(df)} observaciones cargadas")
    
    # Limpiar dataset
    df_clean = clean_dataset(df, min_match_score=args.min_score)
    
    # Guardar dataset limpio
    df_clean.to_csv(args.output, index=False)
    logger.info(f"✅ Dataset limpio guardado: {args.output}")
    
    # Calcular estadísticas finales
    if 'precio_m2' not in df_clean.columns:
        df_clean['precio_m2'] = df_clean['precio'] / df_clean['superficie_m2']
    
    logger.info("\n📊 Estadísticas del Dataset Limpio:")
    logger.info(f"   Precio/m²: {df_clean['precio_m2'].mean():,.0f} €/m² (mediana: {df_clean['precio_m2'].median():,.0f})")
    logger.info(f"   Superficie: {df_clean['superficie_m2'].mean():.1f} m² (mediana: {df_clean['superficie_m2'].median():.1f})")
    if 'habitaciones' in df_clean.columns:
        logger.info(f"   Habitaciones: {df_clean['habitaciones'].mean():.1f} (mediana: {df_clean['habitaciones'].median():.1f})")
    
    # Calcular correlaciones
    corr_sup = df_clean['superficie_m2'].corr(df_clean['precio_m2'])
    logger.info(f"\n📊 Correlaciones:")
    logger.info(f"   superficie_m2 - precio_m2: {corr_sup:.3f} {'✅' if corr_sup > 0 else '❌'}")
    if 'habitaciones' in df_clean.columns:
        corr_hab = df_clean['habitaciones'].corr(df_clean['precio_m2'])
        logger.info(f"   habitaciones - precio_m2: {corr_hab:.3f} {'✅' if corr_hab > 0 else '❌'}")


if __name__ == "__main__":
    main()

