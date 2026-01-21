"""
Processing module for Air Quality data.

Processes raster/map data from OpenData BCN and aggregates to barrio level.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

try:
    import geopandas as gpd
    from shapely import wkt
    from shapely.geometry import shape
    GEOPANDAS_AVAILABLE = True
except ImportError:
    GEOPANDAS_AVAILABLE = False
    logger.warning("geopandas/shapely no disponibles. Procesamiento espacial deshabilitado.")


def _parse_concentration_range(rang_str: str) -> Optional[float]:
    """
    Parsea un rango de concentración y retorna el valor medio.
    
    Ejemplos:
    - "20-30 µg/m³" -> 25.0
    - "10-20 µg/m³" -> 15.0
    - "30-40 µg/m³" -> 35.0
    
    Args:
        rang_str: String con el rango (ej: "20-30 µg/m³")
    
    Returns:
        Valor medio del rango o None si no se puede parsear.
    """
    if not rang_str or pd.isna(rang_str):
        return None
    
    # Buscar patrón "min-max" en el string
    match = re.search(r'(\d+)\s*-\s*(\d+)', str(rang_str))
    if match:
        min_val = float(match.group(1))
        max_val = float(match.group(2))
        return (min_val + max_val) / 2.0
    
    # Si es un valor único
    match = re.search(r'(\d+)', str(rang_str))
    if match:
        return float(match.group(1))
    
    return None


def _load_air_quality_map(csv_path: Path) -> Optional[pd.DataFrame]:
    """
    Carga el archivo CSV de mapas de inmisión de calidad del aire.
    
    Args:
        csv_path: Ruta al archivo CSV con datos de calidad del aire.
    
    Returns:
        DataFrame con columnas: TRAM, Rang, GEOM_WKT, concentration_value
    """
    if not csv_path.exists():
        logger.warning(f"Archivo no encontrado: {csv_path}")
        return pd.DataFrame()
    
    try:
        logger.info(f"Cargando archivo de calidad del aire: {csv_path.name}")
        df = pd.read_csv(csv_path, encoding='utf-8')
        
        if df.empty:
            logger.warning("Archivo de calidad del aire está vacío")
            return pd.DataFrame()
        
        # Parsear concentración del rango
        df['concentration_value'] = df['Rang'].apply(_parse_concentration_range)
        
        # Filtrar filas sin concentración válida
        df = df[df['concentration_value'].notna()].copy()
        
        logger.info(f"✓ Cargados {len(df)} tramos de calidad del aire")
        return df
        
    except Exception as e:
        logger.error(f"Error cargando archivo de calidad del aire: {e}")
        return pd.DataFrame()


def _aggregate_to_barrios(
    air_quality_gdf: gpd.GeoDataFrame,
    barrios_gdf: gpd.GeoDataFrame
) -> pd.DataFrame:
    """
    Agrega datos de calidad del aire a nivel de barrio mediante intersección espacial.
    
    Args:
        air_quality_gdf: GeoDataFrame con tramos de calidad del aire.
        barrios_gdf: GeoDataFrame con geometrías de barrios.
    
    Returns:
        DataFrame con calidad del aire agregada por barrio.
    """
    if not GEOPANDAS_AVAILABLE:
        logger.error("geopandas no disponible. No se puede procesar datos espaciales.")
        return pd.DataFrame()
    
    try:
        # Asegurar que ambos GeoDataFrames usan el mismo CRS
        if air_quality_gdf.crs != barrios_gdf.crs:
            logger.info(f"Reproyectando air_quality_gdf de {air_quality_gdf.crs} a {barrios_gdf.crs}")
            air_quality_gdf = air_quality_gdf.to_crs(barrios_gdf.crs)
        
        # Realizar intersección espacial
        # Para cada barrio, encontrar todos los tramos que lo intersectan
        logger.info("Realizando intersección espacial...")
        intersections = gpd.sjoin(
            barrios_gdf[['barrio_id', 'geometry']],
            air_quality_gdf[['concentration_value', 'geometry']],
            how='left',
            predicate='intersects'
        )
        
        # Agregar por barrio: calcular media ponderada por área de intersección
        results = []
        
        for barrio_id in barrios_gdf['barrio_id'].unique():
            barrio_geom = barrios_gdf[barrios_gdf['barrio_id'] == barrio_id]['geometry'].iloc[0]
            barrio_intersections = intersections[intersections['barrio_id'] == barrio_id]
            
            if barrio_intersections.empty:
                continue
            
            # Calcular área de intersección para cada tramo
            concentrations = []
            weights = []
            
            for idx, row in barrio_intersections.iterrows():
                if pd.notna(row['concentration_value']):
                    tram_geom = row['geometry']
                    try:
                        intersection = barrio_geom.intersection(tram_geom)
                        if not intersection.is_empty:
                            area = intersection.area
                            concentrations.append(row['concentration_value'])
                            weights.append(area)
                    except Exception as e:
                        logger.debug(f"Error calculando intersección para barrio {barrio_id}: {e}")
                        # Fallback: usar concentración sin ponderar
                        concentrations.append(row['concentration_value'])
                        weights.append(1.0)
            
            if concentrations:
                # Calcular media ponderada
                if sum(weights) > 0:
                    weighted_mean = np.average(concentrations, weights=weights)
                else:
                    weighted_mean = np.mean(concentrations)
                
                results.append({
                    'barrio_id': barrio_id,
                    'concentration_mean': weighted_mean
                })
        
        if results:
            df_result = pd.DataFrame(results)
            logger.info(f"✓ Agregados datos para {len(df_result)} barrios")
            return df_result
        else:
            logger.warning("No se pudieron agregar datos a ningún barrio")
            return pd.DataFrame()
            
    except Exception as e:
        logger.error(f"Error en agregación espacial: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return pd.DataFrame()


def prepare_calidad_aire(
    raw_data_path: Path,
    barrios_df: pd.DataFrame,
    reference_time: Optional[datetime] = None
) -> pd.DataFrame:
    """
    Prepara tabla fact_calidad_aire desde datos brutos de mapas de inmisión.
    
    Args:
        raw_data_path: Directorio base donde se encuentran los datos raw.
        barrios_df: DataFrame con dimensión de barrios (debe incluir barrio_id,
            barrio_nombre_normalizado, geometry_json).
        reference_time: Timestamp de referencia para etl_loaded_at.
    
    Returns:
        DataFrame con columnas:
        - barrio_id
        - anio
        - no2_mean (o pm25_mean según el contaminante del archivo)
        - pm25_mean
        - pm10_mean
        - o3_mean
        - stations_nearby
        - max_distance_m
        - etl_loaded_at
    """
    if reference_time is None:
        reference_time = datetime.utcnow()
    
    if barrios_df.empty:
        raise ValueError("barrios_df no puede estar vacío en prepare_calidad_aire")
    
    required_dim_cols = {"barrio_id", "barrio_nombre_normalizado", "geometry_json"}
    missing_dim = required_dim_cols - set(barrios_df.columns)
    if missing_dim:
        raise ValueError(
            f"Dimensión de barrios incompleta para calidad del aire. "
            f"Faltan columnas: {sorted(missing_dim)}"
        )
    
    logger.info("=== Procesando datos de calidad del aire ===")
    
    # 1. Buscar archivo de mapas de inmisión
    opendata_dir = raw_data_path / "opendatabcn"
    air_quality_files = list(opendata_dir.glob("*qualitat-aire*.csv"))
    air_quality_files.extend(list(opendata_dir.glob("*calidad-aire*.csv")))
    air_quality_files.extend(list(raw_data_path.glob("**/*qualitat-aire*.csv")))
    
    if not air_quality_files:
        logger.warning("No se encontraron archivos de calidad del aire")
        return pd.DataFrame()
    
    # Usar el archivo más reciente
    latest_file = max(air_quality_files, key=lambda p: p.stat().st_mtime)
    logger.info(f"Usando archivo: {latest_file.name}")
    
    # 2. Cargar datos
    df_air = _load_air_quality_map(latest_file)
    if df_air.empty:
        logger.warning("No se pudieron cargar datos de calidad del aire")
        return pd.DataFrame()
    
    # 3. Procesar espacialmente si geopandas está disponible
    if not GEOPANDAS_AVAILABLE:
        logger.warning("geopandas no disponible. No se puede procesar datos espaciales.")
        return pd.DataFrame()
    
    try:
        # Crear GeoDataFrame de tramos de calidad del aire
        air_quality_gdf = df_air.copy()
        air_quality_gdf['geometry'] = air_quality_gdf['GEOM_WKT'].apply(
            lambda x: wkt.loads(x) if x and pd.notna(x) else None
        )
        air_quality_gdf = air_quality_gdf[air_quality_gdf['geometry'].notna()]
        air_quality_gdf = gpd.GeoDataFrame(air_quality_gdf, geometry='geometry')
        
        # Establecer CRS (asumiendo EPSG:25831 para Barcelona, ajustar si es necesario)
        # Los datos WKT parecen estar en coordenadas UTM
        air_quality_gdf.set_crs(epsg=25831, inplace=True)
        
        # Crear GeoDataFrame de barrios
        barrios_gdf = barrios_df.copy()
        barrios_gdf['geometry'] = barrios_gdf['geometry_json'].apply(
            lambda x: shape(json.loads(x)) if x and pd.notna(x) else None
        )
        barrios_gdf = barrios_gdf[barrios_gdf['geometry'].notna()]
        barrios_gdf = gpd.GeoDataFrame(barrios_gdf, geometry='geometry', crs='EPSG:4326')
        barrios_gdf = barrios_gdf.to_crs(epsg=25831)  # Reproject to UTM for accurate calculations
        
        # 4. Agregar a nivel de barrio
        df_aggregated = _aggregate_to_barrios(air_quality_gdf, barrios_gdf)
        
        if df_aggregated.empty:
            logger.warning("No se pudieron agregar datos a barrios")
            return pd.DataFrame()
        
        # 5. Preparar formato final para fact_calidad_aire
        # Nota: El archivo actual parece ser NO2 (basado en rangos típicos)
        # Si hay múltiples archivos, se pueden combinar
        fact_calidad_aire = df_aggregated.copy()
        fact_calidad_aire['anio'] = 2025  # Año por defecto, ajustar según archivo
        fact_calidad_aire['no2_mean'] = fact_calidad_aire['concentration_mean']
        fact_calidad_aire['pm25_mean'] = None  # No disponible en este archivo
        fact_calidad_aire['pm10_mean'] = None
        fact_calidad_aire['o3_mean'] = None
        fact_calidad_aire['stations_nearby'] = 0  # No disponible en mapas
        fact_calidad_aire['max_distance_m'] = None
        fact_calidad_aire['etl_loaded_at'] = reference_time.isoformat()
        
        # Seleccionar columnas finales
        fact_calidad_aire = fact_calidad_aire[[
            'barrio_id',
            'anio',
            'no2_mean',
            'pm25_mean',
            'pm10_mean',
            'o3_mean',
            'stations_nearby',
            'max_distance_m',
            'etl_loaded_at'
        ]]
        
        logger.info(f"✓ Calidad del aire procesada: {len(fact_calidad_aire)} registros")
        return fact_calidad_aire
        
    except Exception as e:
        logger.error(f"Error procesando calidad del aire: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return pd.DataFrame()
