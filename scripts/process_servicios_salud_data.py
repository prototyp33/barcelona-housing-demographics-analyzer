"""
Script para procesar datos de servicios sanitarios y cargarlos en fact_servicios_salud.

Procesa:
- Centros de salud y hospitales
- Farmacias
- Calcula densidad por barrio
"""

from __future__ import annotations

import logging
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent


def load_servicios_salud_data(csv_path: Path) -> pd.DataFrame:
    """
    Carga datos de servicios sanitarios desde CSV.
    
    Args:
        csv_path: Ruta al archivo CSV.
    
    Returns:
        DataFrame con datos de servicios sanitarios.
    """
    logger.info(f"Cargando datos de servicios sanitarios: {csv_path}")
    
    try:
        df = pd.read_csv(csv_path)
        logger.info(f"Registros cargados: {len(df)}")
        return df
    except Exception as e:
        logger.error(f"Error cargando datos: {e}")
        return pd.DataFrame()


def get_barrios_geometries(conn: sqlite3.Connection) -> gpd.GeoDataFrame:
    """
    Obtiene geometrías de barrios desde la BD.
    
    Args:
        conn: Conexión a la base de datos.
    
    Returns:
        GeoDataFrame con barrios y geometrías.
    """
    query = """
    SELECT barrio_id, barrio_nombre, codi_barri, geometry_json
    FROM dim_barrios
    WHERE geometry_json IS NOT NULL
    """
    
    df = pd.read_sql_query(query, conn)
    
    if df.empty:
        return gpd.GeoDataFrame()
    
    # Convertir geometry_json a geometrías
    geometries = []
    for _, row in df.iterrows():
        try:
            import json
            geom_dict = json.loads(row["geometry_json"])
            geom = gpd.GeoSeries.from_wkt([geom_dict.get("wkt", "")])[0]
            geometries.append(geom)
        except Exception:
            geometries.append(None)
    
    df["geometry"] = geometries
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")
    
    logger.info(f"Barrios con geometrías válidas: {len(gdf)}")
    return gdf


def get_barrios_with_area(conn: sqlite3.Connection) -> pd.DataFrame:
    """
    Obtiene barrios con área calculada desde geometrías.
    
    Args:
        conn: Conexión a la base de datos.
    
    Returns:
        DataFrame con barrio_id y area_km2.
    """
    barrios_gdf = get_barrios_geometries(conn)
    
    if barrios_gdf.empty:
        return pd.DataFrame()
    
    # Convertir a proyección métrica para calcular área
    barrios_gdf_m = barrios_gdf.to_crs("EPSG:3857")  # Web Mercator
    barrios_gdf_m["area_m2"] = barrios_gdf_m.geometry.area
    barrios_gdf_m["area_km2"] = barrios_gdf_m["area_m2"] / 1_000_000
    
    return pd.DataFrame({
        "barrio_id": barrios_gdf_m["barrio_id"],
        "area_km2": barrios_gdf_m["area_km2"]
    })


def get_poblacion_by_barrio(conn: sqlite3.Connection, anio: int) -> pd.DataFrame:
    """
    Obtiene población por barrio para un año específico.
    
    Args:
        conn: Conexión a la base de datos.
        anio: Año de referencia.
    
    Returns:
        DataFrame con barrio_id y poblacion_total.
    """
    query = """
    SELECT barrio_id, poblacion_total
    FROM fact_demografia
    WHERE anio = ?
    """
    
    df = pd.read_sql_query(query, conn, params=(anio,))
    logger.info(f"Población cargada para {len(df)} barrios (año {anio})")
    return df


def geocode_to_barrios(
    df: pd.DataFrame,
    barrios_gdf: gpd.GeoDataFrame,
    conn: Optional[sqlite3.Connection] = None
) -> pd.DataFrame:
    """
    Geocodifica servicios sanitarios a barrios.
    
    Intenta primero usar codi_barri si está disponible (más eficiente),
    luego usa geocodificación espacial como fallback.
    
    Args:
        df: DataFrame con coordenadas o codi_barri.
        barrios_gdf: GeoDataFrame con barrios y geometrías.
        conn: Conexión a BD para mapeo por codi_barri.
    
    Returns:
        DataFrame con barrio_id asignado.
    """
    logger.info("Geocodificando servicios sanitarios a barrios...")
    
    if df.empty:
        return df
    
    # Método 1: Usar codi_barri si está disponible (más eficiente)
    # Buscar columnas que puedan contener el código de barrio
    barrio_col = None
    for col in ["codi_barri", "barri", "addresses_neighborhood_id", "neighborhood_id"]:
        if col in df.columns:
            barrio_col = col
            break
    
    if barrio_col and conn is not None:
        # Obtener mapeo codi_barri -> barrio_id
        query = "SELECT barrio_id, codi_barri FROM dim_barrios"
        barrio_mapping_df = pd.read_sql_query(query, conn)
        
        # Convertir a numérico para matching
        df[barrio_col] = pd.to_numeric(df[barrio_col], errors="coerce")
        barrio_mapping_df["codi_barri"] = pd.to_numeric(
            barrio_mapping_df["codi_barri"], errors="coerce"
        )
        
        # Mapear
        df_result = df.merge(
            barrio_mapping_df,
            left_on=barrio_col,
            right_on="codi_barri",
            how="left"
        )
        
        logger.info(
            f"Geocodificación por {barrio_col} completada: "
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


def aggregate_by_barrio(
    df: pd.DataFrame,
    poblacion_df: pd.DataFrame,
    area_df: pd.DataFrame,
    anio: int
) -> pd.DataFrame:
    """
    Agrega servicios sanitarios por barrio y calcula densidades.
    
    Args:
        df: DataFrame con servicios sanitarios geocodificados.
        poblacion_df: DataFrame con población por barrio.
        area_df: DataFrame con área por barrio.
        anio: Año de referencia.
    
    Returns:
        DataFrame agregado por barrio con métricas calculadas.
    """
    logger.info("Agregando datos de servicios sanitarios por barrio...")
    
    if df.empty:
        return pd.DataFrame()
    
    # Filtrar solo registros con barrio_id asignado
    df_with_barrio = df[df["barrio_id"].notna()].copy()
    
    if df_with_barrio.empty:
        logger.warning("No hay registros con barrio_id asignado")
        return pd.DataFrame()
    
    # Determinar tipo de servicio
    if "tipo_servicio" in df_with_barrio.columns:
        centros_mask = df_with_barrio["tipo_servicio"] == "centro_salud_hospital"
        farmacias_mask = df_with_barrio["tipo_servicio"] == "farmacia"
    else:
        # Intentar inferir del nombre o tipo
        if "tipo" in df_with_barrio.columns:
            tipo_lower = df_with_barrio["tipo"].str.lower()
            centros_mask = tipo_lower.str.contains("hospital|centro|salud|sanitat", na=False)
            farmacias_mask = tipo_lower.str.contains("farmacia|pharmacy", na=False)
        else:
            # Si no hay información, contar todos como centros
            centros_mask = pd.Series([True] * len(df_with_barrio), index=df_with_barrio.index)
            farmacias_mask = pd.Series([False] * len(df_with_barrio), index=df_with_barrio.index)
    
    # Contar por tipo y barrio
    centros_count = (
        df_with_barrio[centros_mask]
        .groupby("barrio_id")
        .size()
        .reset_index(name="num_centros_salud")
    )
    
    farmacias_count = (
        df_with_barrio[farmacias_mask]
        .groupby("barrio_id")
        .size()
        .reset_index(name="num_farmacias")
    )
    
    # Crear DataFrame base con todos los barrios
    barrios_df = pd.DataFrame({"barrio_id": df_with_barrio["barrio_id"].unique()})
    
    # Merge con conteos
    df_agg = barrios_df.merge(centros_count, on="barrio_id", how="left")
    df_agg = df_agg.merge(farmacias_count, on="barrio_id", how="left")
    
    # Rellenar NaN con 0
    df_agg["num_centros_salud"] = df_agg["num_centros_salud"].fillna(0).astype(int)
    df_agg["num_farmacias"] = df_agg["num_farmacias"].fillna(0).astype(int)
    
    # Por ahora, asumir que todos los centros son centros de salud (no hospitales)
    # Esto se puede refinar después con más información
    df_agg["num_hospitales"] = 0
    
    # Calcular total
    df_agg["total_servicios_sanitarios"] = (
        df_agg["num_centros_salud"] +
        df_agg["num_hospitales"] +
        df_agg["num_farmacias"]
    )
    
    # Merge con población y área
    df_agg = df_agg.merge(poblacion_df, on="barrio_id", how="left")
    df_agg = df_agg.merge(area_df, on="barrio_id", how="left")
    
    # Calcular densidades
    df_agg["densidad_servicios_por_km2"] = (
        df_agg["total_servicios_sanitarios"] / df_agg["area_km2"]
    ).replace([float("inf"), float("-inf")], None)
    
    df_agg["densidad_servicios_por_1000hab"] = (
        df_agg["total_servicios_sanitarios"] / df_agg["poblacion_total"] * 1000
    ).replace([float("inf"), float("-inf")], None)
    
    # Asegurar tipos correctos
    df_agg["barrio_id"] = df_agg["barrio_id"].astype(int)
    df_agg["anio"] = anio
    
    logger.info(f"Datos agregados para {len(df_agg)} barrios")
    
    return df_agg


def insert_into_fact_servicios_salud(
    conn: sqlite3.Connection,
    df_agg: pd.DataFrame,
    anio: int
) -> int:
    """
    Inserta los datos en fact_servicios_salud.
    
    Args:
        conn: Conexión a la base de datos.
        df_agg: DataFrame con datos por barrio.
        anio: Año de los datos.
    
    Returns:
        Número de registros insertados.
    """
    logger.info("Insertando datos en fact_servicios_salud...")
    
    cursor = conn.cursor()
    
    # Eliminar datos existentes del año
    cursor.execute("DELETE FROM fact_servicios_salud WHERE anio = ?", (anio,))
    deleted = cursor.rowcount
    logger.info(f"Eliminados {deleted} registros existentes del año {anio}")
    
    inserted = 0
    
    for _, row in df_agg.iterrows():
        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO fact_servicios_salud
                (barrio_id, anio, num_centros_salud, num_hospitales, num_farmacias,
                 total_servicios_sanitarios, densidad_servicios_por_km2,
                 densidad_servicios_por_1000hab, source, etl_loaded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(row["barrio_id"]),
                    int(row["anio"]),
                    int(row.get("num_centros_salud", 0)) if pd.notna(row.get("num_centros_salud", 0)) else 0,
                    int(row.get("num_hospitales", 0)) if pd.notna(row.get("num_hospitales", 0)) else 0,
                    int(row.get("num_farmacias", 0)) if pd.notna(row.get("num_farmacias", 0)) else 0,
                    int(row.get("total_servicios_sanitarios", 0)) if pd.notna(row.get("total_servicios_sanitarios", 0)) else 0,
                    row.get("densidad_servicios_por_km2") if pd.notna(row.get("densidad_servicios_por_km2")) else None,
                    row.get("densidad_servicios_por_1000hab") if pd.notna(row.get("densidad_servicios_por_1000hab")) else None,
                    "opendata_bcn_servicios_salud",
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
        anio: Año de referencia.
    """
    logger.info("Validando datos insertados...")
    
    query = """
    SELECT 
        COUNT(*) as total_barrios,
        SUM(num_centros_salud) as total_centros,
        SUM(num_hospitales) as total_hospitales,
        SUM(num_farmacias) as total_farmacias,
        SUM(total_servicios_sanitarios) as total_servicios
    FROM fact_servicios_salud
    WHERE anio = ?
    """
    
    df = pd.read_sql_query(query, conn, params=(anio,))
    
    logger.info(f"\nResumen ({anio}):")
    logger.info(f"  Barrios con datos: {df.iloc[0]['total_barrios']}")
    logger.info(f"  Total centros de salud: {df.iloc[0]['total_centros']}")
    logger.info(f"  Total hospitales: {df.iloc[0]['total_hospitales']}")
    logger.info(f"  Total farmacias: {df.iloc[0]['total_farmacias']}")
    logger.info(f"  Total servicios sanitarios: {df.iloc[0]['total_servicios']}")


def main() -> int:
    """Función principal."""
    # Buscar archivos CSV de servicios sanitarios
    servicios_dir = PROJECT_ROOT / "data" / "raw" / "serviciossalud"
    csv_files_centros = list(servicios_dir.glob("*centros*.csv")) if servicios_dir.exists() else []
    csv_files_farmacias = list(servicios_dir.glob("*farmacias*.csv")) if servicios_dir.exists() else []
    
    if not csv_files_centros and not csv_files_farmacias:
        logger.error(f"No se encontraron archivos CSV en {servicios_dir}")
        logger.info(
            "Ejecutar primero: python -c "
            "'from src.extraction.servicios_salud_extractor import ServiciosSaludExtractor; "
            "e = ServiciosSaludExtractor(); e.extract_all()'"
        )
        return 1
    
    # Procesar centros y farmacias por separado y luego combinar
    dfs_to_process = []
    
    if csv_files_centros:
        # Excluir archivos genéricos que no son específicos de servicios sanitarios
        excluded_files = ["fitxer_entitats", "sanitat-farmacies"]  # fitxer_entitats es genérico, sanitat-farmacies es de farmacias
        csv_files_centros = [f for f in csv_files_centros if not any(excluded in f.name for excluded in excluded_files)]
        
        if not csv_files_centros:
            logger.warning("No hay archivos válidos de centros de salud después de filtrar")
        else:
            # Priorizar archivo más completo (más registros)
            def get_record_count(path):
                try:
                    return len(pd.read_csv(path))
                except:
                    return 0
            
            csv_path_centros = max(csv_files_centros, key=get_record_count)
            logger.info(f"Procesando centros desde: {csv_path_centros.name} ({get_record_count(csv_path_centros)} registros)")
        df_centros = load_servicios_salud_data(csv_path_centros)
        df_centros["tipo_servicio"] = "centro_salud_hospital"
        dfs_to_process.append(df_centros)
    
    if csv_files_farmacias:
        csv_path_farmacias = max(csv_files_farmacias, key=lambda p: p.stat().st_mtime)
        logger.info(f"Procesando farmacias desde: {csv_path_farmacias.name}")
        df_farmacias = load_servicios_salud_data(csv_path_farmacias)
        df_farmacias["tipo_servicio"] = "farmacia"
        dfs_to_process.append(df_farmacias)
    
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
        
        # Obtener áreas de barrios
        area_df = get_barrios_with_area(conn)
        
        if area_df.empty:
            logger.error("No se pudieron calcular áreas de barrios")
            conn.close()
            return 1
        
        # Geocodificar a barrios
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
        df_agg = aggregate_by_barrio(df_geocoded, poblacion_df, area_df, anio)
        
        if df_agg.empty:
            logger.error("No se generaron datos agregados")
            conn.close()
            return 1
        
        # Insertar en BD
        inserted = insert_into_fact_servicios_salud(conn, df_agg, anio)
        
        # Validar
        validate_data(conn, anio)
        
        conn.close()
        
        logger.info(f"\n✅ Procesamiento completado: {inserted} barrios actualizados")
        return 0
        
    except Exception as e:
        logger.error(f"Error durante el procesamiento: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

