"""
Processing module for Mobility and Accessibility features.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point, shape

logger = logging.getLogger(__name__)

def prepare_movilidad(
    raw_data_dir: Path,
    barrios_df: pd.DataFrame,
    reference_time: Optional[datetime] = None
) -> pd.DataFrame:
    """
    Prepares the fact_movilidad table by aggregating transit stops and calculating proximity.
    """
    if reference_time is None:
        reference_time = datetime.now()
    
    logger.info("Starting mobility feature engineering...")
    
    # 1. Prepare Barrios GeoDataFrame
    if 'geometry_json' not in barrios_df.columns:
        logger.error("barrios_df must contain 'geometry_json' for spatial analysis.")
        return pd.DataFrame()
    
    # Filter only valid geometries
    valid_barrios = barrios_df.dropna(subset=['geometry_json']).copy()
    valid_barrios['geometry'] = valid_barrios['geometry_json'].apply(lambda x: shape(json.loads(x)))
    gdf_barrios = gpd.GeoDataFrame(valid_barrios, geometry='geometry', crs="EPSG:4326")
    
    # Project to a local CRS for accurate distance calculations (UTM 31N for Barcelona)
    gdf_barrios_proj = gdf_barrios.to_crs(epsg=25831)
    centroids = gdf_barrios_proj.centroid
    
    # 2. Load Transit Data
    # Find latest bus and rail stops
    bus_files = sorted((raw_data_dir / "tmb").glob("barcelona_bus_stops_*.csv"))
    rail_files = sorted((raw_data_dir / "tmb").glob("barcelona_rail_stops_*.csv"))
    
    if not bus_files or not rail_files:
        logger.warning(f"Transit data missing in {raw_data_dir / 'tmb'}. Skipping mobility processing.")
        return pd.DataFrame()
    
    df_bus = pd.read_csv(bus_files[-1])
    df_rail = pd.read_csv(rail_files[-1])
    
    # Convert to GeoDataFrames
    # Bus stops columns: LONGITUD, LATITUD (or similar from OpenData BCN confirmed in previous step)
    # Actually TMB extractor uses LONGITUD and LATITUD
    gdf_bus = gpd.GeoDataFrame(
        df_bus, 
        geometry=gpd.points_from_xy(df_bus.LONGITUD, df_bus.LATITUD),
        crs="EPSG:4326"
    ).to_crs(epsg=25831)
    
    gdf_rail = gpd.GeoDataFrame(
        df_rail, 
        geometry=gpd.points_from_xy(df_rail.LONGITUD, df_rail.LATITUD),
        crs="EPSG:4326"
    ).to_crs(epsg=25831)
    
    # 3. Aggregate Counts by Barrio
    # Spatial join: which points are in which polygon
    bus_in_barrios = gpd.sjoin(gdf_bus, gdf_barrios_proj, how='inner', predicate='within')
    bus_counts = bus_in_barrios.groupby('barrio_id').size().rename('estaciones_bus')
    
    rail_in_barrios = gpd.sjoin(gdf_rail, gdf_barrios_proj, how='inner', predicate='within')
    rail_counts = rail_in_barrios.groupby('barrio_id').size().rename('estaciones_metro')
    
    # 4. Calculate Proximity (Distance to nearest)
    # For each barrio centroid, find distance to nearest stop
    def min_dist(point, other_gdf):
        return other_gdf.distance(point).min()
    
    logger.info("Calculating proximity distances...")
    dist_bus = centroids.apply(lambda p: min_dist(p, gdf_bus)).rename('dist_bus_m')
    dist_rail = centroids.apply(lambda p: min_dist(p, gdf_rail)).rename('dist_metro_m')
    
    # 5. Combine results
    results = gdf_barrios[['barrio_id']].copy()
    results = results.merge(bus_counts, on='barrio_id', how='left').fillna(0)
    results = results.merge(rail_counts, on='barrio_id', how='left').fillna(0)
    
    results['dist_bus_m'] = dist_bus.values
    results['dist_metro_m'] = dist_rail.values
    
    # 6. Calculate Accessibility Score (v3)
    # Normalize distances (closer is better)
    # Higher score = Better accessibility
    # Using log scale for distances to handle outliers
    results['bus_score'] = 1 / (1 + np.log1p(results['dist_bus_m'] / 100))
    results['rail_score'] = 1 / (1 + np.log1p(results['dist_metro_m'] / 200))
    
    # Weighted average: Rails are more valuable than individual bus stops for property value
    results['access_score'] = (results['rail_score'] * 0.7 + results['bus_score'] * 0.3)
    
    # 7. Finalize fact_movilidad schema
    results['anio'] = reference_time.year
    results['mes'] = reference_time.month
    results['estaciones_bicing'] = 0 # Placeholder if not loaded
    results['tiempo_medio_centro_minutos'] = np.nan # Requires routing, out of scope for now
    
    # Map back to fact_movilidad structure
    fact_movilidad = results[[
        'barrio_id', 'anio', 'mes', 
        'estaciones_metro', 'estaciones_bus', 'estaciones_bicing',
        'dist_metro_m', 'dist_bus_m', 'access_score'
    ]].copy()
    
    fact_movilidad['etl_loaded_at'] = reference_time.isoformat()
    fact_movilidad['source'] = "tmb_bcn_spatial"
    
    logger.info(f"Mobility features engineered for {len(fact_movilidad)} barrios.")
    return fact_movilidad
