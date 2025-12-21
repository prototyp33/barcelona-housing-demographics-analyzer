#!/usr/bin/env python3
"""
Matching Idealista ↔ Catastro a nivel EDIFICIO (no vivienda individual).

Estrategia:
1. Agrupar Catastro por referencia_catastral (edificio completo)
2. Agregar características del edificio (media, suma, etc.)
3. Matching Idealista → edificio más cercano geográficamente
4. Usar características agregadas del edificio para modelo

Ventajas:
- Un edificio puede tener múltiples viviendas (más realista)
- Reduce problema de granularidad edificio-vs-vivienda
- Mantiene variación geográfica (no solo barrio)

Uso:
    python3 match_idealista_catastro_by_building.py \
        --idealista spike-data-validation/data/processed/fase2/idealista_gracia_comet.csv \
        --catastro spike-data-validation/data/processed/catastro_gracia_real.csv \
        --output spike-data-validation/data/processed/fase2/idealista_catastro_matched_by_building.csv
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd
from geopy.distance import geodesic

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


def aggregate_catastro_by_building(df_catastro: pd.DataFrame) -> pd.DataFrame:
    """
    Agrupa Catastro por edificio (referencia_catastral) y agrega características.
    
    Args:
        df_catastro: DataFrame de Catastro con múltiples registros por edificio
        
    Returns:
        DataFrame agregado por edificio con características agregadas
    """
    logger.info("Agregando Catastro por edificio...")
    
    # Agrupar por referencia_catastral
    agg_dict = {
        # Características numéricas: media
        'superficie_m2': 'mean',
        'ano_construccion': 'mean',
        'plantas': 'mean',
        
        # Coordenadas: primera (todas deberían ser iguales por edificio)
        'lat': 'first',
        'lon': 'first',
        
        # Información del edificio: primera
        'direccion_normalizada': 'first',
        'direccion': 'first',
        'barrio_id': 'first',
        'barrio_nombre': 'first',
        
        # Contar viviendas/registros por edificio
    }
    
    df_agg = df_catastro.groupby('referencia_catastral').agg(agg_dict).reset_index()
    
    # Añadir contador de viviendas
    viviendas_count = df_catastro.groupby('referencia_catastral').size().reset_index(name='n_viviendas')
    df_agg = df_agg.merge(viviendas_count, on='referencia_catastral', how='left')
    
    # Renombrar columnas agregadas
    df_agg = df_agg.rename(columns={
        'superficie_m2': 'superficie_m2_edificio_mean',
        'ano_construccion': 'ano_construccion_edificio_mean',
        'plantas': 'plantas_edificio_mean',
    })
    
    logger.info(f"  ✅ {len(df_agg)} edificios únicos (de {len(df_catastro)} registros)")
    logger.info(f"  Promedio: {df_catastro.groupby('referencia_catastral').size().mean():.1f} registros/edificio")
    
    return df_agg


def find_closest_building(
    idealista_lat: float,
    idealista_lon: float,
    df_buildings: pd.DataFrame,
    max_distance: float = 300.0
) -> Optional[Tuple[int, pd.Series, float]]:
    """
    Encuentra el edificio Catastro más cercano a una propiedad Idealista.
    
    Args:
        idealista_lat, idealista_lon: Coordenadas de Idealista
        df_buildings: DataFrame de edificios Catastro agregados
        max_distance: Distancia máxima en metros
        
    Returns:
        Tupla (idx, building_row, distance_m) o None
    """
    if pd.isna(idealista_lat) or pd.isna(idealista_lon):
        return None
    
    min_distance = float('inf')
    closest_building = None
    closest_idx = None
    
    for idx, building_row in df_buildings.iterrows():
        building_lat = building_row.get('lat')
        building_lon = building_row.get('lon')
        
        if pd.isna(building_lat) or pd.isna(building_lon):
            continue
        
        try:
            distance = geodesic(
                (idealista_lat, idealista_lon),
                (building_lat, building_lon)
            ).meters
            
            if distance < min_distance and distance <= max_distance:
                min_distance = distance
                closest_building = building_row
                closest_idx = idx
        except Exception as e:
            logger.debug(f"Error calculando distancia: {e}")
            continue
    
    if closest_building is not None:
        return (closest_idx, closest_building, min_distance)
    
    return None


def match_idealista_to_buildings(
    df_idealista: pd.DataFrame,
    df_buildings: pd.DataFrame,
    max_distance: float = 300.0
) -> pd.DataFrame:
    """
    Realiza matching Idealista → edificios Catastro.
    
    Args:
        df_idealista: DataFrame de Idealista (con lat/lon)
        df_buildings: DataFrame de edificios Catastro agregados
        max_distance: Distancia máxima en metros
        
    Returns:
        DataFrame con matches
    """
    logger.info("=" * 70)
    logger.info("MATCHING IDEALISTA → EDIFICIOS CATASTRO")
    logger.info("=" * 70)
    
    matches = []
    
    # Cargar coordenadas de Idealista si no están
    if 'lat' not in df_idealista.columns or 'lon' not in df_idealista.columns:
        # Intentar cargar archivo con coordenadas
        coords_file = INPUT_IDEALISTA.parent / f"{INPUT_IDEALISTA.stem}_with_coords.csv"
        if coords_file.exists():
            logger.info(f"Cargando coordenadas desde: {coords_file}")
            df_idealista_coords = pd.read_csv(coords_file)
            df_idealista = df_idealista.merge(
                df_idealista_coords[['link', 'lat', 'lon']],
                on='link',
                how='left'
            )
        else:
            logger.warning("No se encontraron coordenadas. Usando solo matching por barrio.")
    
    logger.info(f"Buscando matches entre {len(df_idealista)} propiedades Idealista y {len(df_buildings)} edificios Catastro...")
    
    for idx, idealista_row in df_idealista.iterrows():
        idealista_lat = idealista_row.get('lat')
        idealista_lon = idealista_row.get('lon')
        
        match_row = idealista_row.to_dict()
        
        # Buscar edificio más cercano
        if pd.notna(idealista_lat) and pd.notna(idealista_lon):
            closest = find_closest_building(
                idealista_lat, idealista_lon, df_buildings, max_distance
            )
            
            if closest:
                building_idx, building_row, distance = closest
                
                # Añadir datos del edificio
                match_row.update({
                    'catastro_referencia_catastral': building_row.get('referencia_catastral'),
                    'catastro_direccion_normalizada': building_row.get('direccion_normalizada'),
                    'catastro_superficie_m2_edificio_mean': building_row.get('superficie_m2_edificio_mean'),
                    'catastro_ano_construccion_edificio_mean': building_row.get('ano_construccion_edificio_mean'),
                    'catastro_plantas_edificio_mean': building_row.get('plantas_edificio_mean'),
                    'catastro_n_viviendas': building_row.get('n_viviendas'),
                    'catastro_lat': building_row.get('lat'),
                    'catastro_lon': building_row.get('lon'),
                    'catastro_barrio_id': building_row.get('barrio_id'),
                    'catastro_barrio_nombre': building_row.get('barrio_nombre'),
                    'match_distance_m': distance,
                    'match_method': 'building_geographic',
                    'matched': True
                })
            else:
                # Sin match geográfico, intentar por barrio
                idealista_barrio = idealista_row.get('localidad', '')
                # Normalización básica de barrio
                barrio_match = None
                for _, building_row in df_buildings.iterrows():
                    building_barrio = building_row.get('barrio_nombre', '')
                    if idealista_barrio and building_barrio:
                        # Matching simple por nombre de barrio
                        if any(word in idealista_barrio.lower() for word in building_barrio.lower().split()):
                            barrio_match = building_row
                            break
                
                if barrio_match is not None:
                    match_row.update({
                        'catastro_referencia_catastral': barrio_match.get('referencia_catastral'),
                        'catastro_direccion_normalizada': barrio_match.get('direccion_normalizada'),
                        'catastro_superficie_m2_edificio_mean': barrio_match.get('superficie_m2_edificio_mean'),
                        'catastro_ano_construccion_edificio_mean': barrio_match.get('ano_construccion_edificio_mean'),
                        'catastro_plantas_edificio_mean': barrio_match.get('plantas_edificio_mean'),
                        'catastro_n_viviendas': barrio_match.get('n_viviendas'),
                        'catastro_lat': barrio_match.get('lat'),
                        'catastro_lon': barrio_match.get('lon'),
                        'catastro_barrio_id': barrio_match.get('barrio_id'),
                        'catastro_barrio_nombre': barrio_match.get('barrio_nombre'),
                        'match_distance_m': float('inf'),
                        'match_method': 'building_barrio',
                        'matched': True
                    })
                else:
                    match_row.update({
                        'matched': False,
                        'match_method': 'no_match'
                    })
        else:
            # Sin coordenadas, matching por barrio
            idealista_barrio = idealista_row.get('localidad', '')
            barrio_match = None
            for _, building_row in df_buildings.iterrows():
                building_barrio = building_row.get('barrio_nombre', '')
                if idealista_barrio and building_barrio:
                    if any(word in idealista_barrio.lower() for word in building_barrio.lower().split()):
                        barrio_match = building_row
                        break
            
            if barrio_match is not None:
                match_row.update({
                    'catastro_referencia_catastral': barrio_match.get('referencia_catastral'),
                    'catastro_direccion_normalizada': barrio_match.get('direccion_normalizada'),
                    'catastro_superficie_m2_edificio_mean': barrio_match.get('superficie_m2_edificio_mean'),
                    'catastro_ano_construccion_edificio_mean': barrio_match.get('ano_construccion_edificio_mean'),
                    'catastro_plantas_edificio_mean': barrio_match.get('plantas_edificio_mean'),
                    'catastro_n_viviendas': barrio_match.get('n_viviendas'),
                    'catastro_lat': barrio_match.get('lat'),
                    'catastro_lon': barrio_match.get('lon'),
                    'catastro_barrio_id': barrio_match.get('barrio_id'),
                    'catastro_barrio_nombre': barrio_match.get('barrio_nombre'),
                    'match_distance_m': float('inf'),
                    'match_method': 'building_barrio',
                    'matched': True
                })
            else:
                match_row.update({
                    'matched': False,
                    'match_method': 'no_match'
                })
        
        matches.append(match_row)
        
        if (idx + 1) % 50 == 0:
            logger.info(f"  Procesadas {idx + 1}/{len(df_idealista)} propiedades...")
    
    df_matched = pd.DataFrame(matches)
    
    # Calcular métricas
    matched_count = df_matched['matched'].sum() if 'matched' in df_matched.columns else 0
    match_rate = matched_count / len(df_matched) * 100
    
    logger.info("=" * 70)
    logger.info("RESULTADOS DEL MATCHING")
    logger.info("=" * 70)
    logger.info(f"Total propiedades Idealista: {len(df_idealista)}")
    logger.info(f"Matches encontrados: {matched_count} ({match_rate:.1f}%)")
    logger.info(f"Sin match: {len(df_matched) - matched_count} ({100 - match_rate:.1f}%)")
    
    if matched_count > 0:
        if 'match_distance_m' in df_matched.columns:
            valid_distances = df_matched[df_matched['match_distance_m'] != float('inf')]['match_distance_m']
            if len(valid_distances) > 0:
                logger.info(f"Distancia promedio (geográfico): {valid_distances.mean():.1f} m")
        
        if 'match_method' in df_matched.columns:
            logger.info(f"\nMétodo de matching:")
            print(df_matched['match_method'].value_counts())
    
    return df_matched


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Matching Idealista ↔ Catastro a nivel EDIFICIO"
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
        "--output",
        type=Path,
        default=OUTPUT_DIR / "idealista_catastro_matched_by_building.csv",
        help="Archivo CSV de salida"
    )
    parser.add_argument(
        "--max-distance",
        type=float,
        default=300.0,
        help="Distancia máxima en metros (default: 300)"
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
    
    # Agregar Catastro por edificio
    df_buildings = aggregate_catastro_by_building(df_catastro)
    
    # Realizar matching
    df_matched = match_idealista_to_buildings(
        df_idealista,
        df_buildings,
        max_distance=args.max_distance
    )
    
    # Guardar resultados
    df_matched.to_csv(args.output, index=False)
    logger.info(f"✅ Matches guardados: {args.output}")
    
    # Guardar métricas
    metrics = {
        'timestamp': datetime.now().isoformat(),
        'total_idealista': len(df_idealista),
        'total_catastro_registros': len(df_catastro),
        'total_catastro_edificios': len(df_buildings),
        'matched_count': int(df_matched['matched'].sum()) if 'matched' in df_matched.columns else 0,
        'match_rate': float(df_matched['matched'].sum() / len(df_matched) * 100) if 'matched' in df_matched.columns else 0.0,
        'max_distance_m': float(args.max_distance),
    }
    
    if df_matched['matched'].sum() > 0:
        matched_df = df_matched[df_matched['matched']]
        if 'match_distance_m' in matched_df.columns:
            valid_distances = matched_df[matched_df['match_distance_m'] != float('inf')]['match_distance_m']
            if len(valid_distances) > 0:
                metrics.update({
                    'avg_distance_m': float(valid_distances.mean()),
                    'min_distance_m': float(valid_distances.min()),
                    'max_distance_m': float(valid_distances.max()),
                })
        
        if 'match_method' in matched_df.columns:
            metrics['match_methods'] = matched_df['match_method'].value_counts().to_dict()
    
    metrics_file = args.output.parent / f"{args.output.stem}_metrics.json"
    with open(metrics_file, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✅ Métricas guardadas: {metrics_file}")
    logger.info("=" * 70)
    logger.info("✅ Proceso completado")


if __name__ == "__main__":
    main()

