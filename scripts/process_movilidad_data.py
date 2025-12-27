#!/usr/bin/env python3
"""
Script para procesar datos de movilidad (Bicing y ATM) y poblar fact_movilidad.

Fuentes:
- Bicing: API GBFS (sin autenticación)
- ATM: API de Autoritat del Transport Metropolità (requiere API key, opcional)

Este script:
1. Lee datos de estaciones Bicing
2. Geocodifica estaciones → barrios usando dim_barrios.geometry_json
3. Agrega por barrio: número de estaciones, capacidad, uso promedio
4. Calcula tiempo medio al centro (usando distancias geográficas)
5. Inserta datos en fact_movilidad

Uso:
    python scripts/process_movilidad_data.py
"""

import json
import logging
import sqlite3
import sys
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

import pandas as pd
import numpy as np

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Directorio del proyecto
PROJECT_ROOT = Path(__file__).parent.parent


def load_bicing_data(filepath: Path) -> pd.DataFrame:
    """
    Carga el CSV de estaciones Bicing o equipamientos AMB.
    
    Args:
        filepath: Ruta al archivo CSV.
    
    Returns:
        DataFrame con las estaciones/equipamientos.
    """
    logger.info(f"Cargando datos: {filepath}")
    df = pd.read_csv(filepath, encoding="utf-8")
    logger.info(f"Registros cargados: {len(df)}")
    
    # Si son datos de AMB, filtrar solo Barcelona ciudad
    if "amb_equipaments" in str(filepath) or "amb_infraestructures" in str(filepath):
        logger.info("Filtrando equipamientos de Barcelona ciudad...")
        
        # Buscar columna de municipios
        municipio_col = None
        for col in df.columns:
            if "municipi" in col.lower():
                municipio_col = col
                break
        
        if municipio_col:
            # Filtrar solo Barcelona (puede estar como string, lista, etc.)
            initial_count = len(df)
            
            # Intentar diferentes formatos
            df_filtered = df[
                df[municipio_col].astype(str).str.contains("Barcelona", case=False, na=False)
            ].copy()
            
            if len(df_filtered) < initial_count:
                logger.info(f"Filtrados {initial_count - len(df_filtered)} registros fuera de Barcelona ciudad")
                logger.info(f"Registros de Barcelona: {len(df_filtered)}")
                df = df_filtered
        
        # Filtrar solo equipamientos relacionados con transporte/movilidad
        # Buscar en título, subtítulo o ámbito
        transport_keywords = ["metro", "bus", "transporte", "estación", "estacio", "parada", "bicing"]
        
        if "titol" in df.columns or "subambit" in df.columns or "ambit" in df.columns:
            mask = pd.Series([False] * len(df), index=df.index)
            
            for col in ["titol", "subambit", "ambit"]:
                if col in df.columns:
                    col_mask = df[col].astype(str).str.lower().str.contains(
                        "|".join(transport_keywords), case=False, na=False
                    )
                    mask = mask | col_mask
            
            if mask.any():
                df = df[mask].copy()
                logger.info(f"Filtrados {len(df)} equipamientos relacionados con transporte")
    
    return df


def get_barrios_with_geometries(conn: sqlite3.Connection) -> pd.DataFrame:
    """
    Obtiene los barrios con sus geometrías desde la BD.
    
    Args:
        conn: Conexión a la base de datos.
    
    Returns:
        DataFrame con barrio_id, barrio_nombre, geometry_json.
    """
    query = """
    SELECT barrio_id, barrio_nombre, geometry_json
    FROM dim_barrios
    WHERE geometry_json IS NOT NULL
    """
    df = pd.read_sql_query(query, conn)
    logger.info(f"Barrios con geometrías: {len(df)}")
    return df


def _map_by_municipio_name(
    df_stations: pd.DataFrame,
    df_barrios: pd.DataFrame
) -> pd.Series:
    """
    Mapea estaciones a barrios por nombre de municipio (fallback si no hay coordenadas).
    
    Args:
        df_stations: DataFrame con estaciones.
        df_barrios: DataFrame con barrios.
    
    Returns:
        Series con barrio_id.
    """
    # Buscar columna de municipio
    municipio_col = None
    for col in df_stations.columns:
        if "municipi" in col.lower() or "municipio" in col.lower():
            municipio_col = col
            break
    
    if municipio_col is None:
        logger.warning("No se encontró columna de municipio para mapeo por nombre")
        return pd.Series([None] * len(df_stations), index=df_stations.index, dtype="Int64")
    
    # Filtrar solo registros de Barcelona
    df_bcn = df_stations[
        df_stations[municipio_col].astype(str).str.contains("Barcelona", case=False, na=False)
    ].copy()
    
    if df_bcn.empty:
        logger.warning("No se encontraron registros de Barcelona")
        return pd.Series([None] * len(df_stations), index=df_stations.index, dtype="Int64")
    
    # Para AMB, los equipamientos pueden estar en cualquier municipio del área metropolitana
    # Por ahora, asignamos None si no es Barcelona ciudad
    result = pd.Series([None] * len(df_stations), index=df_stations.index, dtype="Int64")
    
    logger.info(f"Registros de Barcelona encontrados: {len(df_bcn)} de {len(df_stations)}")
    logger.warning("⚠️  Mapeo por municipio no es preciso. Se recomienda usar datos con coordenadas geográficas.")
    
    return result


def _parse_geoloc_field(value) -> tuple[Optional[float], Optional[float]]:
    """
    Parsea un campo de geolocalización que puede estar en varios formatos.
    
    Args:
        value: Valor del campo (puede ser string, dict, list, etc.)
    
    Returns:
        Tupla (lat, lon) o (None, None) si no se puede parsear
    """
    import json
    
    if pd.isna(value):
        return (None, None)
    
    # Si es string, intentar parsear como JSON
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            # AMB usa formato [[lon, lat]] (array anidado)
            if isinstance(parsed, list) and len(parsed) > 0:
                first_item = parsed[0]
                if isinstance(first_item, (list, tuple)) and len(first_item) >= 2:
                    # Formato [[lon, lat]]
                    return (float(first_item[1]), float(first_item[0]))  # GeoJSON: [lon, lat] -> (lat, lon)
                elif len(parsed) >= 2:
                    # Formato [lon, lat]
                    return (float(parsed[1]), float(parsed[0]))
            elif isinstance(parsed, dict):
                if "lat" in parsed and "lon" in parsed:
                    return (float(parsed["lat"]), float(parsed["lon"]))
                elif "latitude" in parsed and "longitude" in parsed:
                    return (float(parsed["latitude"]), float(parsed["longitude"]))
        except (json.JSONDecodeError, ValueError):
            # Intentar parsear como "lat,lon" o "lon,lat"
            try:
                parts = value.split(",")
                if len(parts) == 2:
                    lat = float(parts[0].strip())
                    lon = float(parts[1].strip())
                    # Asumir que si lat > lon, están intercambiados (GeoJSON format)
                    if abs(lat) > abs(lon) and abs(lat) < 90:
                        return (lat, lon)
                    else:
                        return (lon, lat)  # Intercambiar si parece GeoJSON
            except (ValueError, IndexError):
                pass
    
    # Si es lista o tupla
    elif isinstance(value, (list, tuple)):
        try:
            # AMB puede usar formato [[lon, lat]] (array anidado)
            if len(value) > 0 and isinstance(value[0], (list, tuple)) and len(value[0]) >= 2:
                # Formato [[lon, lat]]
                return (float(value[0][1]), float(value[0][0]))
            elif len(value) >= 2:
                # Formato [lon, lat]
                return (float(value[1]), float(value[0]))  # GeoJSON: [lon, lat]
        except (ValueError, TypeError, IndexError):
            pass
    
    # Si es dict
    elif isinstance(value, dict):
        if "lat" in value and "lon" in value:
            try:
                return (float(value["lat"]), float(value["lon"]))
            except (ValueError, TypeError):
                pass
        elif "latitude" in value and "longitude" in value:
            try:
                return (float(value["latitude"]), float(value["longitude"]))
            except (ValueError, TypeError):
                pass
    
    return (None, None)


def geocode_stations_to_barrios(
    df_stations: pd.DataFrame,
    df_barrios: pd.DataFrame
) -> pd.Series:
    """
    Geocodifica estaciones a barrios usando coordenadas y geometrías.
    
    Args:
        df_stations: DataFrame con estaciones (debe tener lat/lon).
        df_barrios: DataFrame con barrios y geometrías.
    
    Returns:
        Series con barrio_id para cada estación (None si no se puede mapear).
    """
    try:
        from shapely.geometry import shape, Point
        import geopandas as gpd
    except ImportError:
        logger.error("shapely o geopandas no están instalados. Instalar con: pip install shapely geopandas")
        return pd.Series([None] * len(df_stations), index=df_stations.index, dtype="Int64")
    
    # Buscar columnas de coordenadas
    lat_col = None
    lon_col = None
    
    for col in df_stations.columns:
        col_lower = col.lower()
        if col_lower in ["lat", "latitude", "latitud", "coord_y"]:
            lat_col = col
        elif col_lower in ["lon", "longitude", "longitud", "lng", "coord_x"]:
            lon_col = col
    
    # Si no encontramos coordenadas directas, buscar en campos anidados de AMB
    if lat_col is None or lon_col is None:
        # AMB usa campos como "localitzacio.localitzacio_geolocalitzacio"
        geoloc_col = None
        for col in df_stations.columns:
            if "geolocalitzacio" in col.lower() or "geolocalizacion" in col.lower():
                geoloc_col = col
                break
        
        if geoloc_col and df_stations[geoloc_col].notna().any():
            # Intentar parsear coordenadas del campo geolocalización
            # Puede ser un string con formato "lat,lon" o un dict/JSON
            logger.info(f"Encontrado campo de geolocalización: {geoloc_col}")
            try:
                # Intentar parsear como JSON si es string
                coords_parsed = df_stations[geoloc_col].apply(
                    lambda x: _parse_geoloc_field(x) if pd.notna(x) else (None, None)
                )
                df_stations["_parsed_lat"] = coords_parsed.apply(lambda x: x[0])
                df_stations["_parsed_lon"] = coords_parsed.apply(lambda x: x[1])
                
                if df_stations["_parsed_lat"].notna().any():
                    lat_col = "_parsed_lat"
                    lon_col = "_parsed_lon"
                    logger.info(f"Coordenadas parseadas de {geoloc_col}: {df_stations[lat_col].notna().sum()} registros")
            except Exception as e:
                logger.warning(f"Error parseando campo geolocalización: {e}")
    
    if lat_col is None or lon_col is None:
        logger.warning(f"No se encontraron columnas de coordenadas directas. Intentando mapeo por nombre...")
        # Intentar mapeo por nombre de municipio/barrio como fallback
        return _map_by_municipio_name(df_stations, df_barrios)
    
    # Filtrar estaciones con coordenadas válidas
    df_with_coords = df_stations[
        df_stations[lat_col].notna() &
        df_stations[lon_col].notna()
    ].copy()
    
    if df_with_coords.empty:
        logger.warning("No hay estaciones con coordenadas válidas")
        return pd.Series([None] * len(df_stations), index=df_stations.index, dtype="Int64")
    
    # Crear GeoDataFrame de barrios
    geometries = []
    barrio_ids = []
    
    for _, row in df_barrios.iterrows():
        try:
            geom_json = json.loads(row["geometry_json"])
            geom = shape(geom_json)
            geometries.append(geom)
            barrio_ids.append(row["barrio_id"])
        except Exception as e:
            logger.debug(f"Error parseando geometría para barrio {row['barrio_id']}: {e}")
            continue
    
    if not geometries:
        logger.warning("No se pudieron parsear geometrías de barrios")
        return pd.Series([None] * len(df_stations), index=df_stations.index, dtype="Int64")
    
    barrios_gdf = gpd.GeoDataFrame(
        {"barrio_id": barrio_ids},
        geometry=geometries,
        crs="EPSG:4326"
    )
    
    # Crear GeoDataFrame de estaciones
    stations_points = gpd.GeoDataFrame(
        df_with_coords[[col for col in ["station_id", "name"] if col in df_with_coords.columns]],
        geometry=gpd.points_from_xy(
            df_with_coords[lon_col],
            df_with_coords[lat_col]
        ),
        crs="EPSG:4326"
    )
    
    # Spatial join
    joined = gpd.sjoin(
        stations_points,
        barrios_gdf,
        how="left",
        predicate="within"
    )
    
    # Crear serie de resultados
    result = pd.Series([None] * len(df_stations), index=df_stations.index, dtype="Int64")
    result.loc[joined.index] = joined["barrio_id"].values
    
    mapped = result.notna().sum()
    logger.info(f"Estaciones mapeadas a barrios: {mapped} de {len(df_stations)}")
    
    # Log de distribución por barrio para diagnóstico
    if mapped > 0:
        barrio_counts = result.value_counts().head(10)
        logger.info(f"Top 10 barrios por número de estaciones:")
        for barrio_id, count in barrio_counts.items():
            if pd.notna(barrio_id):
                logger.info(f"  Barrio {barrio_id}: {count} estaciones")
    
    # Verificar si hay estaciones fuera de Barcelona
    if mapped < len(df_with_coords):
        logger.warning(f"{len(df_with_coords) - mapped} estaciones con coordenadas válidas no se mapearon a ningún barrio")
        logger.warning("Esto puede indicar que están fuera de los límites de Barcelona (área metropolitana)")
    
    return result


def calculate_time_to_center(
    df_stations: pd.DataFrame,
    barrio_ids: pd.Series,
    center_lat: float = 41.3851,
    center_lon: float = 2.1734
) -> pd.Series:
    """
    Calcula tiempo estimado al centro de Barcelona.
    
    Usa distancia geográfica y velocidad promedio (20 km/h para transporte público).
    
    Args:
        df_stations: DataFrame con estaciones.
        barrio_ids: Series con barrio_id para cada estación.
        center_lat: Latitud del centro (Plaza Catalunya).
        center_lon: Longitud del centro.
    
    Returns:
        Series con tiempo en minutos.
    """
    try:
        from geopy.distance import geodesic
    except ImportError:
        logger.warning("geopy no está instalado. No se calculará tiempo al centro.")
        return pd.Series([None] * len(df_stations), index=df_stations.index)
    
    # Buscar columnas de coordenadas
    lat_col = None
    lon_col = None
    
    for col in df_stations.columns:
        col_lower = col.lower()
        if col_lower in ["lat", "latitude", "latitud"]:
            lat_col = col
        elif col_lower in ["lon", "longitude", "longitud", "lng"]:
            lon_col = col
    
    if lat_col is None or lon_col is None:
        return pd.Series([None] * len(df_stations), index=df_stations.index)
    
    times = []
    for _, row in df_stations.iterrows():
        if pd.isna(row[lat_col]) or pd.isna(row[lon_col]):
            times.append(None)
            continue
        
        try:
            station_point = (row[lat_col], row[lon_col])
            center_point = (center_lat, center_lon)
            distance_km = geodesic(station_point, center_point).kilometers
            
            # Velocidad promedio transporte público: 20 km/h
            time_minutes = (distance_km / 20) * 60
            times.append(round(time_minutes, 1))
        except Exception:
            times.append(None)
    
    return pd.Series(times, index=df_stations.index)


def aggregate_by_barrio(
    df_stations: pd.DataFrame,
    barrio_ids: pd.Series,
    times_to_center: pd.Series,
    anio: int,
    mes: Optional[int] = None
) -> pd.DataFrame:
    """
    Agrega estaciones por barrio.
    
    Args:
        df_stations: DataFrame con estaciones.
        barrio_ids: Series con barrio_id para cada estación.
        times_to_center: Series con tiempo al centro en minutos.
        anio: Año de los datos.
        mes: Mes de los datos (opcional).
    
    Returns:
        DataFrame agregado por barrio.
    """
    logger.info("Agregando estaciones por barrio...")
    
    df = df_stations.copy()
    df["barrio_id"] = barrio_ids
    df["tiempo_centro"] = times_to_center
    
    # Filtrar solo estaciones con barrio válido
    df_valid = df[df["barrio_id"].notna()].copy()
    logger.info(f"Estaciones con barrio válido: {len(df_valid)} de {len(df)}")
    
    results = []
    
    for barrio_id in df_valid["barrio_id"].unique():
        df_barrio = df_valid[df_valid["barrio_id"] == barrio_id]
        
        # Contar estaciones Bicing
        estaciones_bicing = len(df_barrio)
        
        # Calcular capacidad total (si hay columna capacity)
        capacidad = 0
        if "capacity" in df_barrio.columns:
            capacidad = df_barrio["capacity"].sum()
        elif "num_bikes_available" in df_barrio.columns:
            # Usar número de bicis disponibles como proxy de capacidad
            capacidad = df_barrio["num_bikes_available"].max() * estaciones_bicing
        
        # Calcular uso promedio (si hay datos de estado)
        uso_promedio = None
        if "num_bikes_available" in df_barrio.columns:
            uso_promedio = df_barrio["num_bikes_available"].mean()
        
        # Tiempo medio al centro
        tiempo_medio = df_barrio["tiempo_centro"].mean() if df_barrio["tiempo_centro"].notna().any() else None
        
        results.append({
            "barrio_id": int(barrio_id),
            "anio": anio,
            "mes": mes if mes else 0,  # 0 indica datos anuales
            "estaciones_metro": 0,  # TODO: añadir cuando tengamos datos ATM
            "estaciones_fgc": 0,  # TODO: añadir cuando tengamos datos ATM
            "paradas_bus": 0,  # TODO: añadir cuando tengamos datos ATM
            "estaciones_bicing": estaciones_bicing,
            "capacidad_bicing": int(capacidad) if capacidad else None,
            "uso_bicing_promedio": round(uso_promedio, 2) if uso_promedio else None,
            "tiempo_medio_centro_minutos": round(tiempo_medio, 1) if tiempo_medio else None,
        })
    
    df_agg = pd.DataFrame(results)
    logger.info(f"Barrios con estaciones: {len(df_agg)}")
    
    return df_agg


def insert_into_fact_movilidad(
    conn: sqlite3.Connection,
    df_agg: pd.DataFrame
) -> int:
    """
    Inserta los datos en fact_movilidad.
    
    Args:
        conn: Conexión a la base de datos.
        df_agg: DataFrame agregado por barrio.
    
    Returns:
        Número de registros insertados.
    """
    logger.info("Insertando datos en fact_movilidad...")
    
    cursor = conn.cursor()
    inserted = 0
    
    # Eliminar datos del año/mes actual para evitar duplicados
    anio = df_agg["anio"].iloc[0] if not df_agg.empty else datetime.now().year
    mes = df_agg["mes"].iloc[0] if not df_agg.empty else 0
    
    cursor.execute("DELETE FROM fact_movilidad WHERE anio = ? AND mes = ?", (anio, mes))
    deleted = cursor.rowcount
    logger.info(f"Eliminados {deleted} registros existentes del año {anio}, mes {mes}")
    
    for _, row in df_agg.iterrows():
        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO fact_movilidad
                (barrio_id, anio, mes, estaciones_metro, estaciones_fgc, paradas_bus,
                 estaciones_bicing, capacidad_bicing, uso_bicing_promedio, tiempo_medio_centro_minutos,
                 source, etl_loaded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(row["barrio_id"]),
                    int(row["anio"]),
                    int(row["mes"]),
                    int(row["estaciones_metro"]),
                    int(row["estaciones_fgc"]),
                    int(row["paradas_bus"]),
                    int(row["estaciones_bicing"]),
                    row["capacidad_bicing"],
                    row["uso_bicing_promedio"],
                    row["tiempo_medio_centro_minutos"],
                    "bicing_gbfs",
                    datetime.now().isoformat(),
                )
            )
            inserted += 1
        except sqlite3.Error as e:
            logger.error(f"Error insertando barrio {row['barrio_id']}: {e}")
    
    conn.commit()
    logger.info(f"Registros insertados: {inserted}")
    return inserted


def validate_data(conn: sqlite3.Connection, anio: int) -> None:
    """
    Valida los datos insertados.
    
    Args:
        conn: Conexión a la base de datos.
        anio: Año de los datos.
    """
    logger.info("Validando datos insertados...")
    
    query = """
    SELECT 
        COUNT(*) as barrios,
        SUM(estaciones_bicing) as total_estaciones_bicing,
        AVG(tiempo_medio_centro_minutos) as avg_tiempo_centro
    FROM fact_movilidad
    WHERE anio = ?
    """
    result = pd.read_sql_query(query, conn, params=[anio])
    
    if not result.empty:
        row = result.iloc[0]
        logger.info(f"\nResumen ({anio}):")
        logger.info(f"  Barrios con datos: {int(row['barrios']) if pd.notna(row['barrios']) else 0}")
        total_bicing = row['total_estaciones_bicing']
        if pd.notna(total_bicing):
            logger.info(f"  Total estaciones Bicing: {int(total_bicing)}")
        else:
            logger.info(f"  Total estaciones Bicing: 0")
        if pd.notna(row['avg_tiempo_centro']):
            logger.info(f"  Tiempo medio al centro: {row['avg_tiempo_centro']:.1f} min")


def main() -> int:
    """Función principal."""
    # Buscar archivo CSV más reciente de Bicing o AMB
    bicing_dir = PROJECT_ROOT / "data" / "raw" / "bicing"
    amb_dir = PROJECT_ROOT / "data" / "raw" / "atm_amb"
    
    csv_files = []
    if bicing_dir.exists():
        csv_files.extend(list(bicing_dir.glob("*station_information*.csv")))
    if amb_dir.exists():
        csv_files.extend(list(amb_dir.glob("*infraestructures*.csv")))
        csv_files.extend(list(amb_dir.glob("*equipaments*.csv")))
    
    if not csv_files:
        logger.error(f"No se encontraron archivos CSV en {bicing_dir} o {amb_dir}")
        logger.info("Ejecutar primero:")
        logger.info("  - Bicing: python -c 'from src.extraction.movilidad_extractor import BicingExtractor; e = BicingExtractor(); e.extract_all()'")
        logger.info("  - AMB: python -c 'from src.extraction.movilidad_extractor import ATMExtractor; e = ATMExtractor(); e.extract_all()'")
        return 1
    
    csv_path = max(csv_files, key=lambda p: p.stat().st_mtime)
    db_path = PROJECT_ROOT / "data" / "processed" / "database.db"
    
    if not db_path.exists():
        logger.error(f"Base de datos no encontrada: {db_path}")
        return 1
    
    try:
        # Cargar datos
        df_stations = load_bicing_data(csv_path)
        
        # Conectar a BD
        conn = sqlite3.connect(db_path)
        
        # Obtener barrios con geometrías
        df_barrios = get_barrios_with_geometries(conn)
        
        if df_barrios.empty:
            logger.error("No hay barrios con geometrías en la BD. Ejecutar scripts/load_geometries.py primero")
            conn.close()
            return 1
        
        # Geocodificar estaciones a barrios
        barrio_ids = geocode_stations_to_barrios(df_stations, df_barrios)
        
        # Calcular tiempo al centro
        times_to_center = calculate_time_to_center(df_stations, barrio_ids)
        
        # Agregar por barrio
        anio = datetime.now().year
        df_agg = aggregate_by_barrio(df_stations, barrio_ids, times_to_center, anio)
        
        # Insertar en BD
        inserted = insert_into_fact_movilidad(conn, df_agg)
        
        # Validar
        validate_data(conn, anio)
        
        conn.close()
        
        logger.info(f"\n✅ Procesamiento completado: {inserted} barrios actualizados")
        return 0
        
    except Exception as e:
        logger.error(f"Error durante el procesamiento: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

