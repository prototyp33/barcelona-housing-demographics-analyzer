#!/usr/bin/env python3
"""
Matching geográfico Idealista ↔ Catastro usando coordenadas (Fase 2 - Issue #202).

Este script implementa matching basado en distancia geográfica (coordenadas lat/lon)
y lo combina con matching heurístico para mejorar la calidad de los matches.

Mejoras sobre matching heurístico:
1. Matching geográfico por distancia (Haversine)
2. Geocoding de direcciones de Idealista (usando Nominatim/OpenStreetMap)
3. Combinación ponderada de scores (geográfico + heurístico)
4. Filtrado por distancia máxima (default: 50m)

Uso:
    python3 spike-data-validation/scripts/fase2/match_idealista_catastro_geographic.py \
        --idealista spike-data-validation/data/processed/fase2/idealista_gracia_comet.csv \
        --catastro spike-data-validation/data/processed/catastro_gracia_real.csv \
        --output spike-data-validation/data/processed/fase2/idealista_catastro_matched_geographic.csv \
        --max-distance 50
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from geopy.distance import geodesic
from geopy.geocoders import Nominatim

logger = logging.getLogger(__name__)

# Rutas por defecto
INPUT_IDEALISTA = Path("spike-data-validation/data/processed/fase2/idealista_gracia_comet.csv")
INPUT_CATASTRO = Path("spike-data-validation/data/processed/catastro_gracia_real.csv")
OUTPUT_DIR = Path("spike-data-validation/data/processed/fase2")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Variable global para función de matching heurístico (se importa en main)
calculate_heuristic_score = None

# Configuración geocoding
GEOCODER = Nominatim(user_agent="barcelona-housing-analyzer")
GEOCODING_DELAY = 1.0  # Segundos entre requests (respetar rate limits)


def setup_logging() -> None:
    """Configura logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def normalize_address(address: str) -> str:
    """
    Normaliza una dirección para geocoding.
    
    Args:
        address: Dirección a normalizar
        
    Returns:
        Dirección normalizada con "Barcelona, España" añadido
    """
    if pd.isna(address) or not address:
        return ""
    
    address = str(address).strip()
    
    # Si ya contiene "Barcelona", no añadir
    if "barcelona" in address.lower():
        return address
    
    # Añadir "Barcelona, España" para mejorar geocoding
    return f"{address}, Barcelona, España"


def geocode_address(address: str, max_retries: int = 3) -> Optional[Tuple[float, float]]:
    """
    Geocodifica una dirección y retorna coordenadas (lat, lon).
    
    Args:
        address: Dirección a geocodificar
        max_retries: Número máximo de reintentos
        
    Returns:
        Tupla (lat, lon) o None si falla
    """
    if not address or pd.isna(address):
        return None
    
    address_normalized = normalize_address(address)
    
    for attempt in range(max_retries):
        try:
            time.sleep(GEOCODING_DELAY)  # Respetar rate limits
            location = GEOCODER.geocode(address_normalized, timeout=10)
            
            if location:
                return (location.latitude, location.longitude)
            else:
                logger.debug(f"No se encontró ubicación para: {address}")
                return None
                
        except Exception as e:
            logger.warning(f"Error en geocoding (intento {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(GEOCODING_DELAY * (attempt + 1))  # Backoff exponencial
            else:
                return None
    
    return None


def calculate_distance(
    lat1: float, lon1: float,
    lat2: float, lon2: float
) -> float:
    """
    Calcula distancia geográfica en metros usando fórmula de Haversine.
    
    Args:
        lat1, lon1: Coordenadas del punto 1
        lat2, lon2: Coordenadas del punto 2
        
    Returns:
        Distancia en metros
    """
    if pd.isna(lat1) or pd.isna(lon1) or pd.isna(lat2) or pd.isna(lon2):
        return float('inf')
    
    try:
        point1 = (lat1, lon1)
        point2 = (lat2, lon2)
        distance = geodesic(point1, point2).meters
        return distance
    except Exception as e:
        logger.warning(f"Error calculando distancia: {e}")
        return float('inf')


def calculate_geographic_score(distance_m: float, max_distance: float = 50.0) -> float:
    """
    Calcula score geográfico basado en distancia.
    
    Args:
        distance_m: Distancia en metros
        max_distance: Distancia máxima aceptable (default: 50m)
        
    Returns:
        Score entre 0 y 1 (1 = misma ubicación, 0 = >max_distance)
    """
    if distance_m > max_distance:
        return 0.0
    
    # Score lineal: 1.0 en distancia 0, 0.0 en max_distance
    score = 1.0 - (distance_m / max_distance)
    return max(0.0, score)


def match_by_coordinates(
    idealista_row: pd.Series,
    catastro_row: pd.Series,
    max_distance: float = 50.0
) -> Tuple[float, float]:
    """
    Calcula matching geográfico entre Idealista y Catastro.
    
    Args:
        idealista_row: Fila de Idealista (debe tener lat, lon)
        catastro_row: Fila de Catastro (debe tener lat, lon)
        max_distance: Distancia máxima en metros
        
    Returns:
        Tupla (distance_m, geographic_score)
    """
    # Obtener coordenadas de Idealista
    idealista_lat = idealista_row.get('lat')
    idealista_lon = idealista_row.get('lon')
    
    # Obtener coordenadas de Catastro (puede ser 'lat'/'lon' o 'catastro_lat'/'catastro_lon')
    catastro_lat = catastro_row.get('catastro_lat') or catastro_row.get('lat')
    catastro_lon = catastro_row.get('catastro_lon') or catastro_row.get('lon')
    
    # Verificar que ambas tienen coordenadas
    if pd.isna(idealista_lat) or pd.isna(idealista_lon):
        return (float('inf'), 0.0)
    
    if pd.isna(catastro_lat) or pd.isna(catastro_lon):
        return (float('inf'), 0.0)
    
    # Calcular distancia
    distance_m = calculate_distance(
        idealista_lat, idealista_lon,
        catastro_lat, catastro_lon
    )
    
    # Calcular score
    geographic_score = calculate_geographic_score(distance_m, max_distance)
    
    return (distance_m, geographic_score)


def geocode_idealista_addresses(df_idealista: pd.DataFrame) -> pd.DataFrame:
    """
    Geocodifica direcciones de Idealista y añade columnas lat/lon.
    
    Args:
        df_idealista: DataFrame de Idealista
        
    Returns:
        DataFrame con columnas lat y lon añadidas
    """
    df_result = df_idealista.copy()
    
    # Verificar si ya tiene coordenadas
    if 'lat' in df_result.columns and 'lon' in df_result.columns:
        if df_result['lat'].notna().any() and df_result['lon'].notna().any():
            logger.info("✅ Coordenadas ya presentes en Idealista")
            return df_result
    
    # Añadir columnas si no existen
    if 'lat' not in df_result.columns:
        df_result['lat'] = np.nan
    if 'lon' not in df_result.columns:
        df_result['lon'] = np.nan
    
    # Geocodificar direcciones
    logger.info(f"Geocodificando {len(df_result)} direcciones de Idealista...")
    logger.info("⚠️  Esto puede tardar varios minutos debido a rate limits")
    
    geocoded_count = 0
    for idx, row in df_result.iterrows():
        # Si ya tiene coordenadas, saltar
        if pd.notna(row.get('lat')) and pd.notna(row.get('lon')):
            continue
        
        # Intentar geocodificar desde localidad
        address = row.get('localidad', '')
        if address:
            coords = geocode_address(address)
            if coords:
                df_result.at[idx, 'lat'] = coords[0]
                df_result.at[idx, 'lon'] = coords[1]
                geocoded_count += 1
                
                if geocoded_count % 10 == 0:
                    logger.info(f"  Geocodificadas {geocoded_count}/{len(df_result)} direcciones...")
    
    logger.info(f"✅ Geocodificadas {geocoded_count} direcciones nuevas")
    logger.info(f"   Total con coordenadas: {df_result['lat'].notna().sum()}/{len(df_result)}")
    
    return df_result


def combine_scores(
    heuristic_score: float,
    geographic_score: float,
    geographic_weight: float = 0.6
) -> float:
    """
    Combina scores heurístico y geográfico.
    
    Args:
        heuristic_score: Score del matching heurístico (0-1)
        geographic_score: Score del matching geográfico (0-1)
        geographic_weight: Peso del score geográfico (0-1)
        
    Returns:
        Score combinado (0-1)
    """
    heuristic_weight = 1.0 - geographic_weight
    
    combined_score = (
        geographic_weight * geographic_score +
        heuristic_weight * heuristic_score
    )
    
    return combined_score


def match_idealista_catastro_geographic(
    df_idealista: pd.DataFrame,
    df_catastro: pd.DataFrame,
    max_distance: float = 50.0,
    geographic_weight: float = 0.6,
    min_combined_score: float = 0.5
) -> pd.DataFrame:
    """
    Realiza matching geográfico + heurístico entre Idealista y Catastro.
    
    Args:
        df_idealista: DataFrame de Idealista (con lat/lon)
        df_catastro: DataFrame de Catastro (con catastro_lat/catastro_lon)
        max_distance: Distancia máxima en metros
        geographic_weight: Peso del score geográfico (0-1)
        min_combined_score: Score mínimo para considerar match
        
    Returns:
        DataFrame con matches
    """
    logger.info("=" * 70)
    logger.info("MATCHING GEOGRÁFICO + HEURÍSTICO")
    logger.info("=" * 70)
    
    # Verificar que tenemos función de matching heurístico
    if calculate_heuristic_score is None:
        logger.error("No se pudo importar calculate_heuristic_score. Abortando.")
        raise ImportError("calculate_heuristic_score no disponible")
    
    matches = []
    
    logger.info(f"Buscando matches entre {len(df_idealista)} propiedades Idealista y {len(df_catastro)} edificios Catastro...")
    
    for idx_idealista, idealista_row in df_idealista.iterrows():
        best_match = None
        best_combined_score = 0.0
        best_distance = float('inf')
        
        # Verificar que Idealista tiene coordenadas
        idealista_lat = idealista_row.get('lat')
        idealista_lon = idealista_row.get('lon')
        
        if pd.isna(idealista_lat) or pd.isna(idealista_lon):
            # Si no tiene coordenadas, usar solo matching heurístico
            logger.debug(f"Propiedad {idx_idealista} sin coordenadas, usando solo matching heurístico")
            for idx_catastro, catastro_row in df_catastro.iterrows():
                heuristic_score = calculate_heuristic_score(idealista_row, catastro_row)
                if heuristic_score > best_combined_score:
                    best_combined_score = heuristic_score
                    best_match = (idx_catastro, catastro_row, 0.0, heuristic_score, float('inf'))
        else:
            # Buscar mejor match considerando distancia geográfica
            for idx_catastro, catastro_row in df_catastro.iterrows():
                # Calcular score heurístico
                heuristic_score = calculate_heuristic_score(idealista_row, catastro_row)
                
                # Calcular score geográfico
                distance_m, geographic_score = match_by_coordinates(
                    idealista_row, catastro_row, max_distance
                )
                
                # Combinar scores
                combined_score = combine_scores(
                    heuristic_score, geographic_score, geographic_weight
                )
                
                # Actualizar mejor match
                if combined_score > best_combined_score:
                    best_combined_score = combined_score
                    best_match = (
                        idx_catastro, catastro_row,
                        geographic_score, heuristic_score, distance_m
                    )
        
        # Si encontramos un match con score suficiente
        if best_match and best_combined_score >= min_combined_score:
            idx_catastro, catastro_row, geo_score, heur_score, distance = best_match
            
            # Crear fila combinada
            match_row = idealista_row.to_dict()
            match_row.update({
                'catastro_referencia_catastral': catastro_row.get('referencia_catastral'),
                'catastro_direccion_normalizada': catastro_row.get('direccion_normalizada'),
                'catastro_ano_construccion': catastro_row.get('ano_construccion'),
                'catastro_plantas': catastro_row.get('plantas'),
                'catastro_superficie_m2': catastro_row.get('superficie_m2'),
                'catastro_lat': catastro_row.get('lat') or catastro_row.get('catastro_lat'),
                'catastro_lon': catastro_row.get('lon') or catastro_row.get('catastro_lon'),
                'catastro_barrio_id': catastro_row.get('barrio_id'),
                'catastro_barrio_nombre': catastro_row.get('barrio_nombre'),
                'match_score_geographic': geo_score,
                'match_score_heuristic': heur_score,
                'match_score_combined': best_combined_score,
                'match_distance_m': distance,
                'match_method': 'geographic+heuristic' if distance < float('inf') else 'heuristic_only',
                'matched': True
            })
            matches.append(match_row)
        else:
            # Sin match
            match_row = idealista_row.to_dict()
            match_row.update({
                'matched': False,
                'match_score_combined': best_combined_score if best_match else 0.0
            })
            matches.append(match_row)
        
        if (idx_idealista + 1) % 50 == 0:
            logger.info(f"  Procesadas {idx_idealista + 1}/{len(df_idealista)} propiedades...")
    
    df_matched = pd.DataFrame(matches)
    
    # Calcular métricas
    matched_count = df_matched['matched'].sum() if 'matched' in df_matched.columns else len(df_matched)
    match_rate = matched_count / len(df_matched) * 100
    
    logger.info("=" * 70)
    logger.info("RESULTADOS DEL MATCHING")
    logger.info("=" * 70)
    logger.info(f"Total propiedades Idealista: {len(df_idealista)}")
    logger.info(f"Matches encontrados: {matched_count} ({match_rate:.1f}%)")
    logger.info(f"Sin match: {len(df_matched) - matched_count} ({100 - match_rate:.1f}%)")
    
    if matched_count > 0:
        avg_score = df_matched[df_matched['matched']]['match_score_combined'].mean()
        avg_distance = df_matched[df_matched['matched']]['match_distance_m'].mean()
        logger.info(f"Score promedio: {avg_score:.3f}")
        logger.info(f"Distancia promedio: {avg_distance:.1f} m")
    
    return df_matched


def main():
    """Función principal."""
    global calculate_heuristic_score
    
    # Importar funciones de matching heurístico
    import sys
    from pathlib import Path
    script_dir = Path(__file__).parent
    sys.path.insert(0, str(script_dir))
    
    try:
        from match_idealista_catastro_improved import (
            calculate_match_score as calculate_heuristic_score_fn,
            normalize_barrio_name,
            extract_barrio_from_localidad
        )
        calculate_heuristic_score = calculate_heuristic_score_fn
        logger.info("✅ Funciones de matching heurístico importadas correctamente")
    except ImportError as e:
        logger.error(f"❌ No se pudo importar funciones de matching heurístico: {e}")
        logger.error("   Asegúrate de que match_idealista_catastro_improved.py está en el mismo directorio")
        raise
    
    parser = argparse.ArgumentParser(
        description="Matching geográfico Idealista ↔ Catastro"
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
        default=OUTPUT_DIR / "idealista_catastro_matched_geographic.csv",
        help="Archivo CSV de salida"
    )
    parser.add_argument(
        "--max-distance",
        type=float,
        default=50.0,
        help="Distancia máxima en metros (default: 50)"
    )
    parser.add_argument(
        "--geographic-weight",
        type=float,
        default=0.6,
        help="Peso del score geográfico (0-1, default: 0.6)"
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.5,
        help="Score mínimo para considerar match (default: 0.5)"
    )
    parser.add_argument(
        "--skip-geocoding",
        action="store_true",
        help="Saltar geocoding (usar coordenadas existentes)"
    )
    
    args = parser.parse_args()
    setup_logging()
    
    # Cargar datos
    logger.info(f"Cargando Idealista: {args.idealista}")
    df_idealista = pd.read_csv(args.idealista)
    logger.info(f"  ✅ {len(df_idealista)} propiedades cargadas")
    
    # Si skip_geocoding, intentar cargar archivo con coordenadas
    if args.skip_geocoding:
        idealista_with_coords_file = args.idealista.parent / f"{args.idealista.stem}_with_coords.csv"
        if idealista_with_coords_file.exists():
            logger.info(f"  Cargando coordenadas desde: {idealista_with_coords_file}")
            df_idealista = pd.read_csv(idealista_with_coords_file)
            logger.info(f"  ✅ {df_idealista['lat'].notna().sum()}/{len(df_idealista)} propiedades con coordenadas")
        else:
            logger.warning(f"  ⚠️  Archivo con coordenadas no encontrado: {idealista_with_coords_file}")
            logger.warning(f"  Continuando sin coordenadas (solo matching heurístico)")
    
    logger.info(f"Cargando Catastro: {args.catastro}")
    df_catastro = pd.read_csv(args.catastro)
    logger.info(f"  ✅ {len(df_catastro)} edificios cargados")
    
    # Geocodificar Idealista si es necesario
    if not args.skip_geocoding:
        df_idealista = geocode_idealista_addresses(df_idealista)
        # Guardar Idealista con coordenadas
        idealista_with_coords = args.idealista.parent / f"{args.idealista.stem}_with_coords.csv"
        df_idealista.to_csv(idealista_with_coords, index=False)
        logger.info(f"  ✅ Idealista con coordenadas guardado: {idealista_with_coords}")
    
    # Realizar matching
    df_matched = match_idealista_catastro_geographic(
        df_idealista,
        df_catastro,
        max_distance=args.max_distance,
        geographic_weight=args.geographic_weight,
        min_combined_score=args.min_score
    )
    
    # Guardar resultados
    df_matched.to_csv(args.output, index=False)
    logger.info(f"✅ Matches guardados: {args.output}")
    
    # Guardar métricas
    metrics = {
        'timestamp': datetime.now().isoformat(),
        'total_idealista': len(df_idealista),
        'total_catastro': len(df_catastro),
        'matched_count': int(df_matched['matched'].sum()) if 'matched' in df_matched.columns else len(df_matched),
        'match_rate': float(df_matched['matched'].sum() / len(df_matched) * 100) if 'matched' in df_matched.columns else 100.0,
        'max_distance_threshold_m': float(args.max_distance),
        'geographic_weight': float(args.geographic_weight),
        'min_score': float(args.min_score),
    }
    
    if df_matched['matched'].sum() > 0:
        matched_df = df_matched[df_matched['matched']]
        metrics.update({
            'avg_combined_score': float(matched_df['match_score_combined'].mean()),
            'avg_geographic_score': float(matched_df['match_score_geographic'].mean()),
            'avg_heuristic_score': float(matched_df['match_score_heuristic'].mean()),
        })
        
        # Calcular estadísticas de distancia (solo para matches con distancia válida)
        valid_distances = matched_df[matched_df['match_distance_m'] != float('inf')]['match_distance_m']
        if len(valid_distances) > 0:
            metrics.update({
                'avg_distance_m': float(valid_distances.mean()),
                'min_distance_m': float(valid_distances.min()),
                'max_distance_m': float(valid_distances.max()),
                'matches_with_geographic_distance': int(len(valid_distances)),
            })
        else:
            metrics.update({
                'avg_distance_m': None,
                'min_distance_m': None,
                'max_distance_m': None,
                'matches_with_geographic_distance': 0,
            })
    
    metrics_file = args.output.parent / f"{args.output.stem}_metrics.json"
    with open(metrics_file, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✅ Métricas guardadas: {metrics_file}")
    logger.info("=" * 70)
    logger.info("✅ Proceso completado")


if __name__ == "__main__":
    main()

