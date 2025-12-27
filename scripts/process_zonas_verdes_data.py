#!/usr/bin/env python3
"""
Script para procesar datos de zonas verdes y poblar fact_medio_ambiente.

Fuentes:
- Open Data BCN: Parques y jardines
- Open Data BCN: Arbolado

Este script:
1. Lee datos de zonas verdes extraídos
2. Geocodifica a barrios usando geometry_json
3. Calcula m² de zonas verdes por habitante
4. Inserta datos en fact_medio_ambiente

Uso:
    python scripts/process_zonas_verdes_data.py
"""

import json
import logging
import sqlite3
import sys
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from shapely import wkt

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Directorio del proyecto
PROJECT_ROOT = Path(__file__).parent.parent


def load_zonas_verdes_data(filepath: Path) -> pd.DataFrame:
    """
    Carga el CSV de datos de zonas verdes.
    
    Args:
        filepath: Ruta al archivo CSV.
    
    Returns:
        DataFrame con los datos de zonas verdes.
    """
    logger.info(f"Cargando datos de zonas verdes: {filepath}")
    df = pd.read_csv(filepath, encoding="utf-8")
    logger.info(f"Registros cargados: {len(df)}")
    return df


def get_barrios_geometries(conn: sqlite3.Connection) -> gpd.GeoDataFrame:
    """
    Obtiene las geometrías de los barrios desde la BD.
    
    Args:
        conn: Conexión a la base de datos.
    
    Returns:
        GeoDataFrame con barrios y geometrías.
    """
    query = """
    SELECT 
        barrio_id,
        barrio_nombre,
        codi_barri,
        geometry_json
    FROM dim_barrios
    WHERE geometry_json IS NOT NULL
    """
    
    df = pd.read_sql_query(query, conn)
    
    if df.empty:
        logger.warning("No hay barrios con geometrías en la BD")
        return gpd.GeoDataFrame()
    
    # Parsear geometry_json a geometrías Shapely
    geometries = []
    for idx, row in df.iterrows():
        try:
            if isinstance(row["geometry_json"], str):
                geom_dict = json.loads(row["geometry_json"])
                # Asumir formato GeoJSON
                if geom_dict.get("type") == "Polygon":
                    coords = geom_dict["coordinates"][0]
                    from shapely.geometry import Polygon
                    geom = Polygon(coords)
                elif geom_dict.get("type") == "MultiPolygon":
                    from shapely.geometry import MultiPolygon
                    polygons = [Polygon(ring[0]) for ring in geom_dict["coordinates"]]
                    geom = MultiPolygon(polygons)
                else:
                    logger.warning(f"Tipo de geometría no soportado: {geom_dict.get('type')}")
                    geom = None
            else:
                geom = None
        except Exception as e:
            logger.warning(f"Error parseando geometría para barrio {row['barrio_id']}: {e}")
            geom = None
        
        geometries.append(geom)
    
    df["geometry"] = geometries
    
    # Filtrar barrios sin geometría válida
    df = df[df["geometry"].notna()].copy()
    
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")
    logger.info(f"Barrios con geometrías válidas: {len(gdf)}")
    
    return gdf


def geocode_to_barrios(
    df: pd.DataFrame,
    barrios_gdf: gpd.GeoDataFrame,
    conn: Optional[sqlite3.Connection] = None
) -> pd.DataFrame:
    """
    Geocodifica puntos de zonas verdes a barrios.
    
    Intenta primero usar codi_barri si está disponible (más eficiente),
    luego usa geocodificación espacial como fallback.
    
    Args:
        df: DataFrame con coordenadas (latitud, longitud) o codi_barri.
        barrios_gdf: GeoDataFrame con barrios y geometrías.
        conn: Conexión a BD para mapeo por codi_barri.
    
    Returns:
        DataFrame con barrio_id asignado.
    """
    logger.info("Geocodificando zonas verdes a barrios...")
    
    if df.empty:
        return df
    
    # Método 1: Usar codi_barri si está disponible (más eficiente)
    if "codi_barri" in df.columns or "barri" in df.columns:
        barrio_col = "codi_barri" if "codi_barri" in df.columns else "barri"
        
        if conn is not None:
            # Obtener mapeo codi_barri -> barrio_id
            query = "SELECT barrio_id, codi_barri FROM dim_barrios"
            barrio_mapping_df = pd.read_sql_query(query, conn)
            
            # Convertir codi_barri a numérico para matching
            df[barrio_col] = pd.to_numeric(df[barrio_col], errors="coerce")
            barrio_mapping_df["codi_barri"] = pd.to_numeric(barrio_mapping_df["codi_barri"], errors="coerce")
            
            # Mapear
            df_result = df.merge(
                barrio_mapping_df,
                left_on=barrio_col,
                right_on="codi_barri",
                how="left"
            )
            
            logger.info(
                f"Geocodificación por codi_barri completada: "
                f"{df_result['barrio_id'].notna().sum()}/{len(df_result)} "
                f"registros asignados a barrios"
            )
            
            return df_result
    
    # Método 2: Geocodificación espacial (fallback)
    # Buscar columnas de coordenadas
    lat_col = None
    lon_col = None
    
    for col in df.columns:
        col_lower = col.lower()
        if col_lower in ["latitud", "lat", "latitude", "y"]:
            lat_col = col
        elif col_lower in ["longitud", "lon", "lng", "longitude", "x"]:
            lon_col = col
    
    if lat_col is None or lon_col is None:
        logger.error("No se encontraron columnas de coordenadas ni codi_barri")
        return df
    
    # Crear GeoDataFrame de puntos
    points = []
    for _, row in df.iterrows():
        if pd.notna(row[lat_col]) and pd.notna(row[lon_col]):
            points.append(Point(row[lon_col], row[lat_col]))
        else:
            points.append(None)
    
    df["geometry"] = points
    df_points = df[df["geometry"].notna()].copy()
    
    if df_points.empty:
        logger.warning("No hay puntos válidos para geocodificar")
        return df
    
    gdf_points = gpd.GeoDataFrame(df_points, geometry="geometry", crs="EPSG:4326")
    
    # Spatial join con barrios
    gdf_joined = gpd.sjoin(gdf_points, barrios_gdf, how="left", predicate="within")
    
    # Convertir de vuelta a DataFrame
    df_result = pd.DataFrame(gdf_joined.drop(columns=["geometry", "index_right"]))
    
    logger.info(
        f"Geocodificación espacial completada: "
        f"{df_result['barrio_id'].notna().sum()}/{len(df_result)} "
        f"puntos asignados a barrios"
    )
    
    return df_result


def get_poblacion_by_barrio(conn: sqlite3.Connection, anio: int) -> pd.DataFrame:
    """
    Obtiene la población por barrio para un año.
    
    Args:
        conn: Conexión a la base de datos.
        anio: Año de referencia.
    
    Returns:
        DataFrame con barrio_id y poblacion_total.
    """
    query = """
    SELECT 
        barrio_id,
        MAX(poblacion_total) as poblacion_total
    FROM fact_demografia
    WHERE anio = ?
    GROUP BY barrio_id
    """
    
    df = pd.read_sql_query(query, conn, params=[anio])
    logger.info(f"Población cargada para {len(df)} barrios (año {anio})")
    return df


def aggregate_by_barrio(
    df: pd.DataFrame,
    poblacion_df: pd.DataFrame,
    anio: int
) -> pd.DataFrame:
    """
    Agrega datos de zonas verdes por barrio y calcula m² por habitante.
    
    Args:
        df: DataFrame con zonas verdes geocodificadas.
        poblacion_df: DataFrame con población por barrio.
        anio: Año de los datos.
    
    Returns:
        DataFrame agregado por barrio.
    """
    logger.info("Agregando datos de zonas verdes por barrio...")
    
    if df.empty:
        return pd.DataFrame()
    
    # Filtrar solo registros con barrio_id asignado
    df_with_barrio = df[df["barrio_id"].notna()].copy()
    
    if df_with_barrio.empty:
        logger.warning("No hay registros con barrio_id asignado")
        return pd.DataFrame()
    
    # Buscar columna de superficie
    superficie_col = None
    for col in df_with_barrio.columns:
        if "superficie" in col.lower() or "area" in col.lower():
            superficie_col = col
            break
    
    # Agregar por barrio
    # Contar parques/jardines y árboles según tipo_zona_verde
    if "tipo_zona_verde" in df_with_barrio.columns:
        # Contar por tipo
        parques_count = df_with_barrio[df_with_barrio["tipo_zona_verde"] == "parque_jardin"].groupby("barrio_id").size()
        arboles_count = df_with_barrio[df_with_barrio["tipo_zona_verde"] == "arbol"].groupby("barrio_id").size()
        
        # Sumar superficie si está disponible
        if superficie_col:
            superficie_sum = df_with_barrio.groupby("barrio_id")[superficie_col].sum()
        else:
            superficie_sum = pd.Series(0.0, index=df_with_barrio.groupby("barrio_id").groups.keys())
        
        # Crear DataFrame agregado
        df_agg = pd.DataFrame({
            "barrio_id": df_with_barrio.groupby("barrio_id").groups.keys()
        })
        df_agg = df_agg.set_index("barrio_id")
        df_agg["num_parques_jardines"] = parques_count.fillna(0).astype(int)
        df_agg["num_arboles"] = arboles_count.fillna(0).astype(int)
        df_agg["superficie_zonas_verdes_m2"] = superficie_sum.fillna(0.0)
        df_agg = df_agg.reset_index()
    else:
        # Si no hay tipo_zona_verde, intentar determinar por el nombre del archivo o contar todos
        # Por defecto, asumir que son árboles si no hay información
        arboles_count = df_with_barrio.groupby("barrio_id").size()
        
        if superficie_col:
            superficie_sum = df_with_barrio.groupby("barrio_id")[superficie_col].sum()
        else:
            superficie_sum = pd.Series(0.0, index=df_with_barrio.groupby("barrio_id").groups.keys())
        
        df_agg = pd.DataFrame({
            "barrio_id": df_with_barrio.groupby("barrio_id").groups.keys()
        })
        df_agg = df_agg.set_index("barrio_id")
        df_agg["num_parques_jardines"] = 0
        df_agg["num_arboles"] = arboles_count.fillna(0).astype(int)
        df_agg["superficie_zonas_verdes_m2"] = superficie_sum.fillna(0.0)
        df_agg = df_agg.reset_index()
    
    # Asegurar tipos correctos
    df_agg["barrio_id"] = df_agg["barrio_id"].astype(int)
    df_agg["anio"] = anio
    
    if "num_parques_jardines" not in df_agg.columns:
        df_agg["num_parques_jardines"] = 0
    if "num_arboles" not in df_agg.columns:
        df_agg["num_arboles"] = 0
    if "superficie_zonas_verdes_m2" not in df_agg.columns:
        df_agg["superficie_zonas_verdes_m2"] = 0.0
    
    # Calcular m² por habitante
    df_agg = df_agg.merge(poblacion_df, on="barrio_id", how="left")
    
    df_agg["m2_zonas_verdes_por_habitante"] = (
        df_agg["superficie_zonas_verdes_m2"] / df_agg["poblacion_total"]
    ).replace([float("inf"), float("-inf")], None)
    
    logger.info(f"Datos agregados para {len(df_agg)} barrios")
    
    return df_agg


def insert_into_fact_medio_ambiente(
    conn: sqlite3.Connection,
    df_agg: pd.DataFrame,
    anio: int
) -> int:
    """
    Inserta los datos en fact_medio_ambiente.
    
    Args:
        conn: Conexión a la base de datos.
        df_agg: DataFrame con datos por barrio.
        anio: Año de los datos.
    
    Returns:
        Número de registros insertados.
    """
    logger.info("Insertando datos en fact_medio_ambiente...")
    
    cursor = conn.cursor()
    inserted = 0
    
    # Eliminar datos del año actual para evitar duplicados
    cursor.execute("DELETE FROM fact_medio_ambiente WHERE anio = ?", (anio,))
    deleted = cursor.rowcount
    logger.info(f"Eliminados {deleted} registros existentes del año {anio}")
    
    for _, row in df_agg.iterrows():
        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO fact_medio_ambiente
                (barrio_id, anio, superficie_zonas_verdes_m2, num_parques_jardines,
                 num_arboles, m2_zonas_verdes_por_habitante, source, etl_loaded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(row["barrio_id"]),
                    int(row["anio"]),
                    row.get("superficie_zonas_verdes_m2") if pd.notna(row.get("superficie_zonas_verdes_m2")) else None,
                    int(row.get("num_parques_jardines", 0)) if pd.notna(row.get("num_parques_jardines", 0)) else 0,
                    int(row.get("num_arboles", 0)) if pd.notna(row.get("num_arboles", 0)) else 0,
                    row.get("m2_zonas_verdes_por_habitante") if pd.notna(row.get("m2_zonas_verdes_por_habitante")) else None,
                    "opendata_bcn_zonas_verdes",
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
        SUM(superficie_zonas_verdes_m2) as total_superficie,
        SUM(num_parques_jardines) as total_parques,
        SUM(num_arboles) as total_arboles,
        AVG(m2_zonas_verdes_por_habitante) as avg_m2_por_habitante
    FROM fact_medio_ambiente
    WHERE anio = ?
    """
    result = pd.read_sql_query(query, conn, params=[anio])
    
    if not result.empty:
        row = result.iloc[0]
        logger.info(f"\nResumen ({anio}):")
        logger.info(f"  Barrios con datos: {int(row['barrios'])}")
        if row["total_superficie"]:
            logger.info(f"  Superficie total: {row['total_superficie']:.0f} m²")
        if row["total_parques"]:
            logger.info(f"  Total parques/jardines: {int(row['total_parques'])}")
        if row["total_arboles"]:
            logger.info(f"  Total árboles: {int(row['total_arboles'])}")
        if row["avg_m2_por_habitante"]:
            logger.info(f"  Promedio m² por habitante: {row['avg_m2_por_habitante']:.2f} m²")


def main() -> int:
    """Función principal."""
    # Buscar archivos CSV de zonas verdes (parques y arbolado)
    zonas_verdes_dir = PROJECT_ROOT / "data" / "raw" / "zonasverdes"
    csv_files_parques = list(zonas_verdes_dir.glob("*parques*.csv")) if zonas_verdes_dir.exists() else []
    csv_files_arbolado = list(zonas_verdes_dir.glob("*arbolado*.csv")) if zonas_verdes_dir.exists() else []
    
    if not csv_files_parques and not csv_files_arbolado:
        logger.error(f"No se encontraron archivos CSV en {zonas_verdes_dir}")
        logger.info("Ejecutar primero: python -c 'from src.extraction.zonas_verdes_extractor import ZonasVerdesExtractor; e = ZonasVerdesExtractor(); e.extract_all()'")
        return 1
    
    # Procesar parques y arbolado por separado y luego combinar
    dfs_to_process = []
    
    if csv_files_parques:
        csv_path_parques = max(csv_files_parques, key=lambda p: p.stat().st_mtime)
        logger.info(f"Procesando parques desde: {csv_path_parques.name}")
        df_parques = load_zonas_verdes_data(csv_path_parques)
        df_parques["tipo_zona_verde"] = "parque_jardin"
        dfs_to_process.append(df_parques)
    
    if csv_files_arbolado:
        # Priorizar arbrat-zona que tiene más datos y codi_barri
        arbrat_files = [f for f in csv_files_arbolado if "arbrat-zona" in f.name]
        if arbrat_files:
            csv_path_arbolado = max(arbrat_files, key=lambda p: p.stat().st_mtime)
        else:
            csv_path_arbolado = max(csv_files_arbolado, key=lambda p: p.stat().st_mtime)
        logger.info(f"Procesando arbolado desde: {csv_path_arbolado.name}")
        df_arbolado = load_zonas_verdes_data(csv_path_arbolado)
        df_arbolado["tipo_zona_verde"] = "arbol"
        dfs_to_process.append(df_arbolado)
    
    # Combinar todos los DataFrames
    if not dfs_to_process:
        logger.error("No hay datos para procesar")
        return 1
    
    df = pd.concat(dfs_to_process, ignore_index=True)
    logger.info(f"Total registros combinados: {len(df)}")
    
    db_path = PROJECT_ROOT / "data" / "processed" / "database.db"
    
    if not db_path.exists():
        logger.error(f"Base de datos no encontrada: {db_path}")
        return 1
    
    try:
        # Conectar a BD
        conn = sqlite3.connect(db_path)
        
        # Obtener geometrías de barrios
        barrios_gdf = get_barrios_geometries(conn)
        
        if barrios_gdf.empty:
            logger.error("No hay barrios con geometrías en la BD")
            conn.close()
            return 1
        
        # Geocodificar a barrios (pasar conn para mapeo por codi_barri)
        df_geocoded = geocode_to_barrios(df, barrios_gdf, conn)
        
        # Obtener población
        anio = datetime.now().year
        poblacion_df = get_poblacion_by_barrio(conn, anio)
        
        if poblacion_df.empty:
            logger.warning(f"No hay datos de población para el año {anio}, usando último año disponible")
            query = """
            SELECT 
                barrio_id,
                MAX(poblacion_total) as poblacion_total
            FROM fact_demografia
            GROUP BY barrio_id
            """
            poblacion_df = pd.read_sql_query(query, conn)
        
        # Agregar por barrio
        df_agg = aggregate_by_barrio(df_geocoded, poblacion_df, anio)
        
        if df_agg.empty:
            logger.error("No se generaron datos agregados")
            conn.close()
            return 1
        
        # Insertar en BD
        inserted = insert_into_fact_medio_ambiente(conn, df_agg, anio)
        
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

