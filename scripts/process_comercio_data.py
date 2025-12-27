"""
Script para procesar datos de comercio y cargarlos en fact_comercio.

Procesa:
- Locales comerciales
- Terrazas y licencias
- Calcula densidad comercial y tasa de ocupación por barrio
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


def load_comercio_data(csv_path: Path) -> pd.DataFrame:
    """
    Carga datos de comercio desde CSV.
    
    Args:
        csv_path: Ruta al archivo CSV.
    
    Returns:
        DataFrame con datos de comercio.
    """
    logger.info(f"Cargando datos de comercio: {csv_path}")
    
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
    Geocodifica establecimientos comerciales a barrios.
    
    Intenta primero usar codi_barri si está disponible (más eficiente),
    luego usa geocodificación espacial como fallback.
    
    Args:
        df: DataFrame con coordenadas o codi_barri.
        barrios_gdf: GeoDataFrame con barrios y geometrías.
        conn: Conexión a BD para mapeo por codi_barri.
    
    Returns:
        DataFrame con barrio_id asignado.
    """
    logger.info("Geocodificando establecimientos comerciales a barrios...")
    
    if df.empty:
        return df
    
    # Método 1: Usar codi_barri si está disponible (más eficiente)
    # Buscar columnas que puedan contener el código de barrio (case-insensitive)
    barrio_col = None
    for col in df.columns:
        col_lower = col.lower()
        if col_lower in ["codi_barri", "barri", "addresses_neighborhood_id", "neighborhood_id"]:
            barrio_col = col
            break
    # También buscar variantes específicas en mayúsculas
    if barrio_col is None:
        for col in ["CODI_BARRI", "Codi_Barri"]:
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
        if col_lower in ["latitud", "lat", "latitude", "y"] or col in ["LATITUD", "Latitud"]:
            lat_col = col
        elif col_lower in ["longitud", "lon", "lng", "longitude", "x"] or col in ["LONGITUD", "Longitud"]:
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
    Agrega establecimientos comerciales por barrio y calcula métricas.
    
    Args:
        df: DataFrame con establecimientos comerciales geocodificados.
        poblacion_df: DataFrame con población por barrio.
        area_df: DataFrame con área por barrio.
        anio: Año de referencia.
    
    Returns:
        DataFrame agregado por barrio con métricas calculadas.
    """
    logger.info("Agregando datos de comercio por barrio...")
    
    if df.empty:
        return pd.DataFrame()
    
    # Filtrar solo registros con barrio_id asignado
    df_with_barrio = df[df["barrio_id"].notna()].copy()
    
    if df_with_barrio.empty:
        logger.warning("No hay registros con barrio_id asignado")
        return pd.DataFrame()
    
    # Determinar tipo de establecimiento
    if "tipo_comercio" in df_with_barrio.columns:
        locales_mask = df_with_barrio["tipo_comercio"] == "local_comercial"
        terrazas_mask = df_with_barrio["tipo_comercio"] == "terraza"
    else:
        # Intentar inferir del nombre o tipo
        if "tipo_actividad" in df_with_barrio.columns:
            tipo_lower = df_with_barrio["tipo_actividad"].astype(str).str.lower()
            locales_mask = ~tipo_lower.str.contains("terrassa|terraza|terrace", na=False)
            terrazas_mask = tipo_lower.str.contains("terrassa|terraza|terrace", na=False)
        elif "nombre" in df_with_barrio.columns:
            nombre_lower = df_with_barrio["nombre"].astype(str).str.lower()
            locales_mask = ~nombre_lower.str.contains("terrassa|terraza|terrace", na=False)
            terrazas_mask = nombre_lower.str.contains("terrassa|terraza|terrace", na=False)
        else:
            # Si no hay información, asumir que todos son locales comerciales
            locales_mask = pd.Series([True] * len(df_with_barrio), index=df_with_barrio.index)
            terrazas_mask = pd.Series([False] * len(df_with_barrio), index=df_with_barrio.index)
    
    # Contar por tipo y barrio
    locales_count = (
        df_with_barrio[locales_mask]
        .groupby("barrio_id")
        .size()
        .reset_index(name="num_locales_comerciales")
    )
    
    terrazas_count = (
        df_with_barrio[terrazas_mask]
        .groupby("barrio_id")
        .size()
        .reset_index(name="num_terrazas")
    )
    
    # Crear DataFrame base con todos los barrios
    barrios_df = pd.DataFrame({"barrio_id": df_with_barrio["barrio_id"].unique()})
    
    # Merge con conteos
    df_agg = barrios_df.merge(locales_count, on="barrio_id", how="left")
    df_agg = df_agg.merge(terrazas_count, on="barrio_id", how="left")
    
    # Rellenar NaN con 0
    df_agg["num_locales_comerciales"] = df_agg["num_locales_comerciales"].fillna(0).astype(int)
    df_agg["num_terrazas"] = df_agg["num_terrazas"].fillna(0).astype(int)
    
    # Por ahora, asumir que todas las terrazas tienen licencia
    df_agg["num_licencias"] = df_agg["num_terrazas"]
    
    # Calcular total
    df_agg["total_establecimientos"] = (
        df_agg["num_locales_comerciales"] +
        df_agg["num_terrazas"]
    )
    
    # Calcular tasa de ocupación (si hay información de estado)
    if "estado" in df_with_barrio.columns or "ocupacion" in df_with_barrio.columns:
        estado_col = "estado" if "estado" in df_with_barrio.columns else "ocupacion"
        estado_lower = df_with_barrio[locales_mask][estado_col].astype(str).str.lower()
        ocupados_mask = estado_lower.str.contains("ocupado|activo|abierto|open", na=False)
        
        ocupados_count = (
            df_with_barrio[locales_mask & ocupados_mask]
            .groupby("barrio_id")
            .size()
            .reset_index(name="num_locales_ocupados")
        )
        
        df_agg = df_agg.merge(ocupados_count, on="barrio_id", how="left")
        df_agg["num_locales_ocupados"] = df_agg["num_locales_ocupados"].fillna(0).astype(int)
        
        # Calcular tasa de ocupación
        df_agg["tasa_ocupacion_locales"] = (
            df_agg["num_locales_ocupados"] / df_agg["num_locales_comerciales"]
        ).replace([float("inf"), float("-inf")], None)
        
        df_agg["pct_locales_ocupados"] = (
            df_agg["tasa_ocupacion_locales"] * 100
        ).replace([float("inf"), float("-inf")], None)
    else:
        df_agg["tasa_ocupacion_locales"] = None
        df_agg["pct_locales_ocupados"] = None
    
    # Merge con población y área
    df_agg = df_agg.merge(poblacion_df, on="barrio_id", how="left")
    df_agg = df_agg.merge(area_df, on="barrio_id", how="left")
    
    # Calcular densidades
    df_agg["densidad_comercial_por_km2"] = (
        df_agg["total_establecimientos"] / df_agg["area_km2"]
    ).replace([float("inf"), float("-inf")], None)
    
    df_agg["densidad_comercial_por_1000hab"] = (
        df_agg["total_establecimientos"] / df_agg["poblacion_total"] * 1000
    ).replace([float("inf"), float("-inf")], None)
    
    # Asegurar tipos correctos
    df_agg["barrio_id"] = df_agg["barrio_id"].astype(int)
    df_agg["anio"] = anio
    
    logger.info(f"Datos agregados para {len(df_agg)} barrios")
    
    return df_agg


def insert_into_fact_comercio(
    conn: sqlite3.Connection,
    df_agg: pd.DataFrame,
    anio: int
) -> int:
    """
    Inserta los datos en fact_comercio.
    
    Args:
        conn: Conexión a la base de datos.
        df_agg: DataFrame con datos por barrio.
        anio: Año de los datos.
    
    Returns:
        Número de registros insertados.
    """
    logger.info("Insertando datos en fact_comercio...")
    
    cursor = conn.cursor()
    
    # Eliminar datos existentes del año
    cursor.execute("DELETE FROM fact_comercio WHERE anio = ?", (anio,))
    deleted = cursor.rowcount
    logger.info(f"Eliminados {deleted} registros existentes del año {anio}")
    
    inserted = 0
    
    for _, row in df_agg.iterrows():
        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO fact_comercio
                (barrio_id, anio, num_locales_comerciales, num_terrazas, num_licencias,
                 total_establecimientos, densidad_comercial_por_km2,
                 densidad_comercial_por_1000hab, tasa_ocupacion_locales,
                 pct_locales_ocupados, source, etl_loaded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(row["barrio_id"]),
                    int(row["anio"]),
                    int(row.get("num_locales_comerciales", 0)) if pd.notna(row.get("num_locales_comerciales", 0)) else 0,
                    int(row.get("num_terrazas", 0)) if pd.notna(row.get("num_terrazas", 0)) else 0,
                    int(row.get("num_licencias", 0)) if pd.notna(row.get("num_licencias", 0)) else 0,
                    int(row.get("total_establecimientos", 0)) if pd.notna(row.get("total_establecimientos", 0)) else 0,
                    row.get("densidad_comercial_por_km2") if pd.notna(row.get("densidad_comercial_por_km2")) else None,
                    row.get("densidad_comercial_por_1000hab") if pd.notna(row.get("densidad_comercial_por_1000hab")) else None,
                    row.get("tasa_ocupacion_locales") if pd.notna(row.get("tasa_ocupacion_locales")) else None,
                    row.get("pct_locales_ocupados") if pd.notna(row.get("pct_locales_ocupados")) else None,
                    "opendata_bcn_comercio",
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
        SUM(num_locales_comerciales) as total_locales,
        SUM(num_terrazas) as total_terrazas,
        SUM(num_licencias) as total_licencias,
        SUM(total_establecimientos) as total_establecimientos
    FROM fact_comercio
    WHERE anio = ?
    """
    
    df = pd.read_sql_query(query, conn, params=(anio,))
    
    logger.info(f"\nResumen ({anio}):")
    logger.info(f"  Barrios con datos: {df.iloc[0]['total_barrios']}")
    logger.info(f"  Total locales comerciales: {df.iloc[0]['total_locales']}")
    logger.info(f"  Total terrazas: {df.iloc[0]['total_terrazas']}")
    logger.info(f"  Total licencias: {df.iloc[0]['total_licencias']}")
    logger.info(f"  Total establecimientos: {df.iloc[0]['total_establecimientos']}")


def main() -> int:
    """Función principal."""
    # Buscar archivos CSV de comercio
    comercio_dir = PROJECT_ROOT / "data" / "raw" / "comercio"
    csv_files_locales = list(comercio_dir.glob("*locales*.csv")) if comercio_dir.exists() else []
    csv_files_terrazas = list(comercio_dir.glob("*terrazas*.csv")) if comercio_dir.exists() else []
    
    if not csv_files_locales and not csv_files_terrazas:
        logger.error(f"No se encontraron archivos CSV en {comercio_dir}")
        logger.info(
            "Ejecutar primero: python -c "
            "'from src.extraction.comercio_extractor import ComercioExtractor; "
            "e = ComercioExtractor(); e.extract_all()'"
        )
        return 1
    
    # Procesar locales y terrazas por separado y luego combinar
    dfs_to_process = []
    
    if csv_files_locales:
        # Priorizar archivo más completo (más registros)
        def get_record_count(path):
            try:
                return len(pd.read_csv(path))
            except:
                return 0
        
        # Excluir archivos genéricos
        excluded_files = ["fitxer_entitats"]
        csv_files_locales = [f for f in csv_files_locales if not any(excluded in f.name for excluded in excluded_files)]
        
        if csv_files_locales:
            csv_path_locales = max(csv_files_locales, key=get_record_count)
            logger.info(f"Procesando locales desde: {csv_path_locales.name} ({get_record_count(csv_path_locales)} registros)")
            df_locales = load_comercio_data(csv_path_locales)
            df_locales["tipo_comercio"] = "local_comercial"
            # Normalizar columnas de barrio a minúsculas
            for col in df_locales.columns:
                if col.lower() in ["codi_barri", "barri"]:
                    df_locales.rename(columns={col: "codi_barri"}, inplace=True)
            dfs_to_process.append(df_locales)
    
    if csv_files_terrazas:
        csv_path_terrazas = max(csv_files_terrazas, key=lambda p: p.stat().st_mtime)
        logger.info(f"Procesando terrazas desde: {csv_path_terrazas.name}")
        df_terrazas = load_comercio_data(csv_path_terrazas)
        df_terrazas["tipo_comercio"] = "terraza"
        # Normalizar columnas de barrio a minúsculas
        for col in df_terrazas.columns:
            if col.lower() in ["codi_barri", "barri"]:
                df_terrazas.rename(columns={col: "codi_barri"}, inplace=True)
        dfs_to_process.append(df_terrazas)
    
    # Combinar todos los DataFrames
    if not dfs_to_process:
        logger.error("No hay datos para procesar")
        return 1
    
    df = pd.concat(dfs_to_process, ignore_index=True)
    logger.info(f"Total registros combinados: {len(df)}")
    if "tipo_comercio" in df.columns:
        logger.info(f"Distribución por tipo: {df['tipo_comercio'].value_counts().to_dict()}")
    
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
        inserted = insert_into_fact_comercio(conn, df_agg, anio)
        
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

