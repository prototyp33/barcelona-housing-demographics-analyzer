#!/usr/bin/env python3
"""
Matching Idealista ↔ Catastro a nivel CUADRÍCULA GEOGRÁFICA.

Estrategia:
1. Dividir área de Gràcia en cuadrículas (ej: 100m × 100m)
2. Agregar Catastro por cuadrícula
3. Agregar Idealista por cuadrícula
4. Matching: cuadrícula Idealista → cuadrícula Catastro
5. Usar características agregadas de la cuadrícula para modelo

Ventajas:
- Balance entre precisión geográfica y agregación
- Reduce ruido de matching individual
- Mantiene variación espacial (más fino que barrio)

Uso:
    python3 match_idealista_catastro_by_grid.py \
        --idealista spike-data-validation/data/processed/fase2/idealista_gracia_comet.csv \
        --catastro spike-data-validation/data/processed/catastro_gracia_real.csv \
        --grid-size 100 \
        --output spike-data-validation/data/processed/fase2/idealista_catastro_matched_by_grid.csv
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Rutas por defecto
INPUT_IDEALISTA = Path("spike-data-validation/data/processed/fase2/idealista_gracia_comet.csv")
INPUT_CATASTRO = Path("spike-data-validation/data/processed/catastro_gracia_real.csv")
OUTPUT_DIR = Path("spike-data-validation/data/processed/fase2")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def setup_logging() -> None:
    """Configura logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def assign_grid_cell(lat: float, lon: float, grid_size_m: float = 100.0) -> tuple[int, int]:
    """
    Asigna coordenadas a una celda de cuadrícula.
    
    Args:
        lat, lon: Coordenadas
        grid_size_m: Tamaño de la cuadrícula en metros
        
    Returns:
        Tupla (grid_x, grid_y) identificando la celda
    """
    # Aproximación: 1 grado lat ≈ 111,000 m, 1 grado lon ≈ 111,000 * cos(lat) m
    # Para Barcelona (lat ≈ 41.4°): 1 grado lon ≈ 83,000 m
    
    if pd.isna(lat) or pd.isna(lon):
        return (np.nan, np.nan)
    
    # Convertir metros a grados (aproximado)
    lat_deg_per_m = 1.0 / 111000.0
    lon_deg_per_m = 1.0 / (111000.0 * np.cos(np.radians(lat)))
    
    grid_size_deg_lat = grid_size_m * lat_deg_per_m
    grid_size_deg_lon = grid_size_m * lon_deg_per_m
    
    # Calcular celda (usar punto de referencia para normalizar)
    ref_lat = 41.4  # Aproximado centro de Barcelona
    ref_lon = 2.15
    
    grid_x = int((lon - ref_lon) / grid_size_deg_lon)
    grid_y = int((lat - ref_lat) / grid_size_deg_lat)
    
    return (grid_x, grid_y)


def aggregate_by_grid(
    df: pd.DataFrame,
    lat_col: str = 'lat',
    lon_col: str = 'lon',
    grid_size_m: float = 100.0,
    prefix: str = ''
) -> pd.DataFrame:
    """
    Agrega DataFrame por cuadrícula geográfica.
    
    Args:
        df: DataFrame con coordenadas
        lat_col, lon_col: Nombres de columnas de coordenadas
        grid_size_m: Tamaño de cuadrícula en metros
        prefix: Prefijo para columnas agregadas
        
    Returns:
        DataFrame agregado por cuadrícula
    """
    logger.info(f"Agregando por cuadrícula {grid_size_m}m × {grid_size_m}m...")
    
    # Asignar celdas de cuadrícula
    df = df.copy()
    df['grid_cell'] = df.apply(
        lambda row: assign_grid_cell(row[lat_col], row[lon_col], grid_size_m),
        axis=1
    )
    
    # Separar grid_x y grid_y
    df['grid_x'] = df['grid_cell'].apply(lambda x: x[0] if isinstance(x, tuple) else np.nan)
    df['grid_y'] = df['grid_cell'].apply(lambda x: x[1] if isinstance(x, tuple) else np.nan)
    
    # Filtrar filas sin coordenadas válidas
    df_valid = df[df['grid_x'].notna() & df['grid_y'].notna()].copy()
    
    if len(df_valid) == 0:
        logger.warning("No hay coordenadas válidas para agregar")
        return pd.DataFrame()
    
    # Agregar por cuadrícula
    agg_dict = {}
    
    # Columnas numéricas: media
    numeric_cols = ['superficie_m2', 'ano_construccion', 'plantas']
    for col in numeric_cols:
        if col in df_valid.columns:
            agg_dict[col] = 'mean'
    
    # Coordenadas: centro de la cuadrícula (media)
    if lat_col in df_valid.columns:
        agg_dict[lat_col] = 'mean'
    if lon_col in df_valid.columns:
        agg_dict[lon_col] = 'mean'
    
    # Información categórica: primera o moda
    categorical_cols = ['barrio_id', 'barrio_nombre', 'direccion_normalizada']
    for col in categorical_cols:
        if col in df_valid.columns:
            agg_dict[col] = 'first'
    
    # Contar observaciones por cuadrícula
    df_agg = df_valid.groupby(['grid_x', 'grid_y']).agg(agg_dict).reset_index()
    df_agg['n_obs'] = df_valid.groupby(['grid_x', 'grid_y']).size().values
    
    # Renombrar columnas agregadas
    if prefix:
        rename_dict = {}
        for col in numeric_cols:
            if col in df_agg.columns:
                rename_dict[col] = f"{prefix}_{col}_mean"
        df_agg = df_agg.rename(columns=rename_dict)
    
    logger.info(f"  ✅ {len(df_agg)} cuadrículas (de {len(df_valid)} observaciones)")
    logger.info(f"  Promedio: {df_valid.groupby(['grid_x', 'grid_y']).size().mean():.1f} obs/cuadrícula")
    
    return df_agg


def match_by_grid(
    df_idealista: pd.DataFrame,
    df_catastro: pd.DataFrame,
    grid_size_m: float = 100.0
) -> pd.DataFrame:
    """
    Realiza matching Idealista ↔ Catastro por cuadrícula geográfica.
    
    Args:
        df_idealista: DataFrame de Idealista
        df_catastro: DataFrame de Catastro
        grid_size_m: Tamaño de cuadrícula en metros
        
    Returns:
        DataFrame con matches agregados por cuadrícula
    """
    logger.info("=" * 70)
    logger.info("MATCHING POR CUADRÍCULA GEOGRÁFICA")
    logger.info("=" * 70)
    
    # Cargar coordenadas de Idealista si no están
    if 'lat' not in df_idealista.columns or 'lon' not in df_idealista.columns:
        coords_file = INPUT_IDEALISTA.parent / f"{INPUT_IDEALISTA.stem}_with_coords.csv"
        if coords_file.exists():
            logger.info(f"Cargando coordenadas desde: {coords_file}")
            df_idealista_coords = pd.read_csv(coords_file)
            df_idealista = df_idealista.merge(
                df_idealista_coords[['link', 'lat', 'lon']],
                on='link',
                how='left'
            )
    
    # Agregar por cuadrícula
    df_idealista_grid = aggregate_by_grid(
        df_idealista,
        lat_col='lat',
        lon_col='lon',
        grid_size_m=grid_size_m,
        prefix='idealista'
    )
    
    df_catastro_grid = aggregate_by_grid(
        df_catastro,
        lat_col='lat',
        lon_col='lon',
        grid_size_m=grid_size_m,
        prefix='catastro'
    )
    
    if len(df_idealista_grid) == 0 or len(df_catastro_grid) == 0:
        logger.error("No se pudieron crear cuadrículas")
        return pd.DataFrame()
    
    # Matching: unir por cuadrícula
    df_matched = df_idealista_grid.merge(
        df_catastro_grid,
        on=['grid_x', 'grid_y'],
        how='left',
        suffixes=('_idealista', '_catastro')
    )
    
    # Marcar matches (verificar si hay columnas de Catastro)
    catastro_cols = [col for col in df_matched.columns if col.startswith('catastro_') or col.endswith('_catastro')]
    if catastro_cols:
        # Usar primera columna de Catastro para verificar match
        df_matched['matched'] = df_matched[catastro_cols[0]].notna()
    else:
        # Si no hay columnas de Catastro, verificar por lat
        lat_col = 'lat_catastro' if 'lat_catastro' in df_matched.columns else 'lat'
        df_matched['matched'] = df_matched[lat_col].notna() if lat_col in df_matched.columns else False
    
    logger.info("=" * 70)
    logger.info("RESULTADOS DEL MATCHING")
    logger.info("=" * 70)
    logger.info(f"Cuadrículas Idealista: {len(df_idealista_grid)}")
    logger.info(f"Cuadrículas Catastro: {len(df_catastro_grid)}")
    logger.info(f"Matches: {df_matched['matched'].sum()}/{len(df_matched)} ({df_matched['matched'].sum()/len(df_matched)*100:.1f}%)")
    
    return df_matched


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Matching Idealista ↔ Catastro por CUADRÍCULA GEOGRÁFICA"
    )
    parser.add_argument(
        "--idealista",
        type=Path,
        default=INPUT_IDEALISTA,
        help="Archivo CSV de Idealista"
    )
    parser.add_argument(
        "--catastro",
        type=Path,
        default=INPUT_CATASTRO,
        help="Archivo CSV de Catastro"
    )
    parser.add_argument(
        "--grid-size",
        type=float,
        default=100.0,
        help="Tamaño de cuadrícula en metros (default: 100)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_DIR / "idealista_catastro_matched_by_grid.csv",
        help="Archivo CSV de salida"
    )
    
    args = parser.parse_args()
    setup_logging()
    
    # Cargar datos
    logger.info(f"Cargando Idealista: {args.idealista}")
    df_idealista = pd.read_csv(args.idealista)
    logger.info(f"  ✅ {len(df_idealista)} propiedades cargadas")
    
    logger.info(f"Cargando Catastro: {args.catastro}")
    df_catastro = pd.read_csv(args.catastro)
    logger.info(f"  ✅ {len(df_catastro)} registros cargados")
    
    # Realizar matching por cuadrícula
    df_matched = match_by_grid(
        df_idealista,
        df_catastro,
        grid_size_m=args.grid_size
    )
    
    # Guardar resultados
    df_matched.to_csv(args.output, index=False)
    logger.info(f"✅ Matches guardados: {args.output}")
    
    # Guardar métricas
    metrics = {
        'timestamp': datetime.now().isoformat(),
        'total_idealista': len(df_idealista),
        'total_catastro': len(df_catastro),
        'grid_size_m': float(args.grid_size),
        'matched_count': int(df_matched['matched'].sum()) if 'matched' in df_matched.columns else 0,
        'match_rate': float(df_matched['matched'].sum() / len(df_matched) * 100) if 'matched' in df_matched.columns else 0.0,
    }
    
    metrics_file = args.output.parent / f"{args.output.stem}_metrics.json"
    with open(metrics_file, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✅ Métricas guardadas: {metrics_file}")
    logger.info("=" * 70)
    logger.info("✅ Proceso completado")


if __name__ == "__main__":
    main()

