#!/usr/bin/env python3
"""
Script para procesar datos de equipamientos educativos y poblar fact_educacion.

Fuente: Open Data BCN - Equipament Educació
Este script:
1. Lee el CSV de equipamientos educativos extraído
2. Geocodifica coordenadas → barrio usando dim_barrios.geometry_json
3. Clasifica equipamientos por tipo (infantil, primaria, secundaria, FP, universidad)
4. Agrega por barrio y año
5. Inserta datos en fact_educacion

Uso:
    python scripts/process_educacion_data.py
"""

import json
import logging
import sqlite3
import sys
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

import pandas as pd

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Directorio del proyecto
PROJECT_ROOT = Path(__file__).parent.parent


def load_equipamientos_csv(filepath: Path) -> pd.DataFrame:
    """
    Carga el CSV de equipamientos educativos.
    
    Args:
        filepath: Ruta al archivo CSV.
    
    Returns:
        DataFrame con los equipamientos.
    """
    logger.info(f"Cargando CSV: {filepath}")
    df = pd.read_csv(filepath, encoding="utf-8")
    logger.info(f"Equipamientos cargados: {len(df)}")
    logger.info(f"Columnas: {df.columns.tolist()}")
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


def geocode_equipamientos_to_barrios(
    df_equipamientos: pd.DataFrame,
    df_barrios: pd.DataFrame
) -> pd.Series:
    """
    Geocodifica equipamientos a barrios usando coordenadas y geometrías.
    
    Args:
        df_equipamientos: DataFrame con equipamientos (debe tener lat/lon).
        df_barrios: DataFrame con barrios y geometrías.
    
    Returns:
        Series con barrio_id para cada equipamiento (None si no se puede mapear).
    """
    try:
        from shapely.geometry import shape, Point
        import geopandas as gpd
    except ImportError:
        logger.error("shapely o geopandas no están instalados. Instalar con: pip install shapely geopandas")
        return pd.Series([None] * len(df_equipamientos), index=df_equipamientos.index, dtype="Int64")
    
    # Verificar columnas de coordenadas
    coord_columns = ["latitud", "longitud", "latitude", "longitude", "coord_x", "coord_y"]
    lat_col = None
    lon_col = None
    
    for col in df_equipamientos.columns:
        col_lower = col.lower()
        if col_lower in ["latitud", "latitude", "coord_y"]:
            lat_col = col
        elif col_lower in ["longitud", "longitude", "coord_x"]:
            lon_col = col
    
    if lat_col is None or lon_col is None:
        logger.warning(f"No se encontraron columnas de coordenadas. Columnas disponibles: {df_equipamientos.columns.tolist()}")
        # Intentar mapeo por nombre de barrio si hay columna de barrio
        if "nom_barri" in df_equipamientos.columns or "barrio" in df_equipamientos.columns:
            return _map_by_barrio_name(df_equipamientos, df_barrios)
        return pd.Series([None] * len(df_equipamientos), index=df_equipamientos.index, dtype="Int64")
    
    # Filtrar equipamientos con coordenadas válidas
    df_with_coords = df_equipamientos[
        df_equipamientos[lat_col].notna() &
        df_equipamientos[lon_col].notna()
    ].copy()
    
    if df_with_coords.empty:
        logger.warning("No hay equipamientos con coordenadas válidas")
        return pd.Series([None] * len(df_equipamientos), index=df_equipamientos.index, dtype="Int64")
    
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
        return pd.Series([None] * len(df_equipamientos), index=df_equipamientos.index, dtype="Int64")
    
    barrios_gdf = gpd.GeoDataFrame(
        {"barrio_id": barrio_ids},
        geometry=geometries,
        crs="EPSG:4326"
    )
    
    # Crear GeoDataFrame de equipamientos
    equipamientos_points = gpd.GeoDataFrame(
        df_with_coords[["nom_equipament"] if "nom_equipament" in df_with_coords.columns else []],
        geometry=gpd.points_from_xy(
            df_with_coords[lon_col],
            df_with_coords[lat_col]
        ),
        crs="EPSG:4326"
    )
    
    # Spatial join
    joined = gpd.sjoin(
        equipamientos_points,
        barrios_gdf,
        how="left",
        predicate="within"
    )
    
    # Crear serie de resultados
    result = pd.Series([None] * len(df_equipamientos), index=df_equipamientos.index, dtype="Int64")
    result.loc[joined.index] = joined["barrio_id"].values
    
    mapped = result.notna().sum()
    logger.info(f"Equipamientos mapeados a barrios: {mapped} de {len(df_equipamientos)}")
    
    return result


def _map_by_barrio_name(
    df_equipamientos: pd.DataFrame,
    df_barrios: pd.DataFrame
) -> pd.Series:
    """
    Mapea equipamientos a barrios por nombre (fallback si no hay coordenadas).
    
    Args:
        df_equipamientos: DataFrame con equipamientos.
        df_barrios: DataFrame con barrios.
    
    Returns:
        Series con barrio_id.
    """
    barrio_col = None
    for col in df_equipamientos.columns:
        if "barri" in col.lower() or "barrio" in col.lower():
            barrio_col = col
            break
    
    if barrio_col is None:
        return pd.Series([None] * len(df_equipamientos), index=df_equipamientos.index, dtype="Int64")
    
    # Crear mapeo nombre -> barrio_id
    name_to_id = dict(zip(df_barrios["barrio_nombre"], df_barrios["barrio_id"]))
    
    result = df_equipamientos[barrio_col].map(name_to_id)
    mapped = result.notna().sum()
    logger.info(f"Equipamientos mapeados por nombre: {mapped} de {len(df_equipamientos)}")
    
    return result


def classify_tipo_educacion(tipo_equipament: str) -> Optional[str]:
    """
    Clasifica un tipo de equipamiento en categoría educativa.
    
    Args:
        tipo_equipament: Tipo de equipamiento según el dataset.
    
    Returns:
        Categoría ('infantil', 'primaria', 'secundaria', 'fp', 'universidad') o None.
    """
    if pd.isna(tipo_equipament):
        return None
    
    tipo_lower = str(tipo_equipament).lower()
    
    tipos_map = {
        "infantil": ["infantil", "bressol", "guarderia", "escola bressol"],
        "primaria": ["primària", "primaria", "escola primària"],
        "secundaria": ["secundària", "secundaria", "eso", "institut"],
        "fp": ["formació professional", "formacion profesional", "fp", "cicles formatius"],
        "universidad": ["universitat", "universidad", "campus", "universitari"],
    }
    
    for categoria, keywords in tipos_map.items():
        if any(keyword in tipo_lower for keyword in keywords):
            return categoria
    
    return None


def aggregate_by_barrio(
    df_equipamientos: pd.DataFrame,
    barrio_ids: pd.Series,
    anio: int
) -> pd.DataFrame:
    """
    Agrega equipamientos por barrio y tipo.
    
    Args:
        df_equipamientos: DataFrame con equipamientos.
        barrio_ids: Series con barrio_id para cada equipamiento.
        anio: Año de los datos.
    
    Returns:
        DataFrame agregado por barrio.
    """
    logger.info("Agregando equipamientos por barrio...")
    
    # Añadir barrio_id al DataFrame
    df = df_equipamientos.copy()
    df["barrio_id"] = barrio_ids
    
    # Filtrar solo equipamientos con barrio válido
    df_valid = df[df["barrio_id"].notna()].copy()
    logger.info(f"Equipamientos con barrio válido: {len(df_valid)} de {len(df)}")
    
    # Clasificar tipos
    tipo_col = None
    for col in df_valid.columns:
        if "tipus" in col.lower() or "tipo" in col.lower():
            tipo_col = col
            break
    
    if tipo_col:
        df_valid["categoria"] = df_valid[tipo_col].apply(classify_tipo_educacion)
    else:
        logger.warning("No se encontró columna de tipo de equipamiento")
        df_valid["categoria"] = None
    
    # Agregar por barrio y categoría
    results = []
    
    for barrio_id in df_valid["barrio_id"].unique():
        df_barrio = df_valid[df_valid["barrio_id"] == barrio_id]
        
        counts = {
            "barrio_id": int(barrio_id),
            "anio": anio,
            "num_centros_infantil": len(df_barrio[df_barrio["categoria"] == "infantil"]),
            "num_centros_primaria": len(df_barrio[df_barrio["categoria"] == "primaria"]),
            "num_centros_secundaria": len(df_barrio[df_barrio["categoria"] == "secundaria"]),
            "num_centros_fp": len(df_barrio[df_barrio["categoria"] == "fp"]),
            "num_centros_universidad": len(df_barrio[df_barrio["categoria"] == "universidad"]),
            "total_centros_educativos": len(df_barrio),
        }
        
        results.append(counts)
    
    df_agg = pd.DataFrame(results)
    logger.info(f"Barrios con equipamientos: {len(df_agg)}")
    
    return df_agg


def insert_into_fact_educacion(
    conn: sqlite3.Connection,
    df_agg: pd.DataFrame
) -> int:
    """
    Inserta los datos en fact_educacion.
    
    Args:
        conn: Conexión a la base de datos.
        df_agg: DataFrame agregado por barrio.
    
    Returns:
        Número de registros insertados.
    """
    logger.info("Insertando datos en fact_educacion...")
    
    cursor = conn.cursor()
    inserted = 0
    
    # Eliminar datos del año actual para evitar duplicados
    anio = df_agg["anio"].iloc[0] if not df_agg.empty else datetime.now().year
    cursor.execute("DELETE FROM fact_educacion WHERE anio = ?", (anio,))
    deleted = cursor.rowcount
    logger.info(f"Eliminados {deleted} registros existentes del año {anio}")
    
    for _, row in df_agg.iterrows():
        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO fact_educacion
                (barrio_id, anio, num_centros_infantil, num_centros_primaria,
                 num_centros_secundaria, num_centros_fp, num_centros_universidad,
                 total_centros_educativos, source, etl_loaded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(row["barrio_id"]),
                    int(row["anio"]),
                    int(row["num_centros_infantil"]),
                    int(row["num_centros_primaria"]),
                    int(row["num_centros_secundaria"]),
                    int(row["num_centros_fp"]),
                    int(row["num_centros_universidad"]),
                    int(row["total_centros_educativos"]),
                    "opendata_bcn_educacion",
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
        SUM(total_centros_educativos) as total_centros,
        AVG(total_centros_educativos) as avg_centros_por_barrio
    FROM fact_educacion
    WHERE anio = ?
    """
    result = pd.read_sql_query(query, conn, params=[anio])
    
    if not result.empty:
        row = result.iloc[0]
        logger.info(f"\nResumen ({anio}):")
        logger.info(f"  Barrios con datos: {int(row['barrios'])}")
        logger.info(f"  Total centros: {int(row['total_centros'])}")
        logger.info(f"  Promedio por barrio: {row['avg_centros_por_barrio']:.1f}")


def main() -> int:
    """Función principal."""
    # Buscar archivo CSV más reciente
    educacion_dir = PROJECT_ROOT / "data" / "raw" / "educacion"
    csv_files = list(educacion_dir.glob("*equipament*.csv")) if educacion_dir.exists() else []
    
    if not csv_files:
        logger.error(f"No se encontraron archivos CSV en {educacion_dir}")
        logger.info("Ejecutar primero: python -c 'from src.extraction.educacion_extractor import EducacionExtractor; e = EducacionExtractor(); e.extract_equipamientos()'")
        return 1
    
    csv_path = max(csv_files, key=lambda p: p.stat().st_mtime)
    db_path = PROJECT_ROOT / "data" / "processed" / "database.db"
    
    if not db_path.exists():
        logger.error(f"Base de datos no encontrada: {db_path}")
        return 1
    
    try:
        # Cargar datos
        df_equipamientos = load_equipamientos_csv(csv_path)
        
        # Conectar a BD
        conn = sqlite3.connect(db_path)
        
        # Obtener barrios con geometrías
        df_barrios = get_barrios_with_geometries(conn)
        
        if df_barrios.empty:
            logger.error("No hay barrios con geometrías en la BD. Ejecutar scripts/load_geometries.py primero")
            conn.close()
            return 1
        
        # Geocodificar equipamientos a barrios
        barrio_ids = geocode_equipamientos_to_barrios(df_equipamientos, df_barrios)
        
        # Agregar por barrio
        anio = datetime.now().year  # Usar año actual
        df_agg = aggregate_by_barrio(df_equipamientos, barrio_ids, anio)
        
        # Insertar en BD
        inserted = insert_into_fact_educacion(conn, df_agg)
        
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

