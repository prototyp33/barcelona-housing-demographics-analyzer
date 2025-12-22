"""
Procesa datos de Inside Airbnb y crea fact_presion_turistica.

Fuentes:
- Inside Airbnb: listings.csv (información de propiedades)
- Inside Airbnb: calendar.csv (disponibilidad y precios por fecha)
- Inside Airbnb: reviews.csv (reviews por listing)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


def _load_airbnb_listings(raw_data_path: Path) -> pd.DataFrame:
    """
    Carga datos de listings de Inside Airbnb.
    
    Busca archivos CSV con 'listings' en el nombre dentro del directorio de airbnb.
    
    Args:
        raw_data_path: Directorio base donde se encuentran los datos raw
            (por ejemplo, ``data/raw/airbnb`` o ``data/raw/insideairbnb``).
    
    Returns:
        DataFrame con datos de listings de Airbnb.
    """
    # Buscar archivos de listings en varios directorios posibles
    search_paths = [
        raw_data_path / "airbnb",
        raw_data_path / "insideairbnb",
        raw_data_path.parent / "airbnb",
        raw_data_path.parent / "insideairbnb",
    ]
    
    frames = []
    for search_path in search_paths:
        if not search_path.exists():
            continue
        
        # Buscar archivos CSV que contengan 'listings' en el nombre
        csv_files = list(search_path.glob("*listings*.csv*"))
        
        for path in csv_files:
            try:
                logger.info("Cargando listings desde: %s", path)
                # Manejar archivos comprimidos
                if path.suffix == ".gz":
                    import gzip
                    df = pd.read_csv(path, compression="gzip", low_memory=False)
                else:
                    df = pd.read_csv(path, low_memory=False)
                
                logger.info("Listings cargados: %s registros, %s columnas", len(df), len(df.columns))
                frames.append(df)
            except Exception as exc:
                logger.warning("Error leyendo listings CSV %s: %s", path, exc)
    
    if not frames:
        logger.warning("No se pudieron cargar archivos de listings de Airbnb")
        return pd.DataFrame()
    
    df = pd.concat(frames, ignore_index=True)
    logger.info("Total listings cargados: %s registros", len(df))
    
    return df


def _load_airbnb_calendar(raw_data_path: Path) -> pd.DataFrame:
    """
    Carga datos de calendar de Inside Airbnb.
    
    Busca archivos CSV con 'calendar' en el nombre dentro del directorio de airbnb.
    
    Args:
        raw_data_path: Directorio base donde se encuentran los datos raw.
    
    Returns:
        DataFrame con datos de calendar de Airbnb.
    """
    search_paths = [
        raw_data_path / "airbnb",
        raw_data_path / "insideairbnb",
        raw_data_path.parent / "airbnb",
        raw_data_path.parent / "insideairbnb",
    ]
    
    frames = []
    for search_path in search_paths:
        if not search_path.exists():
            continue
        
        csv_files = list(search_path.glob("*calendar*.csv*"))
        
        for path in csv_files:
            try:
                logger.info("Cargando calendar desde: %s", path)
                if path.suffix == ".gz":
                    import gzip
                    df = pd.read_csv(path, compression="gzip", low_memory=False)
                else:
                    df = pd.read_csv(path, low_memory=False)
                
                logger.info("Calendar cargado: %s registros", len(df))
                frames.append(df)
            except Exception as exc:
                logger.warning("Error leyendo calendar CSV %s: %s", path, exc)
    
    if not frames:
        logger.warning("No se pudieron cargar archivos de calendar de Airbnb")
        return pd.DataFrame()
    
    df = pd.concat(frames, ignore_index=True)
    logger.info("Total calendar cargado: %s registros", len(df))
    
    return df


def _load_airbnb_reviews(raw_data_path: Path) -> pd.DataFrame:
    """
    Carga datos de reviews de Inside Airbnb.
    
    Busca archivos CSV con 'reviews' en el nombre dentro del directorio de airbnb.
    
    Args:
        raw_data_path: Directorio base donde se encuentran los datos raw.
    
    Returns:
        DataFrame con datos de reviews de Airbnb.
    """
    search_paths = [
        raw_data_path / "airbnb",
        raw_data_path / "insideairbnb",
        raw_data_path.parent / "airbnb",
        raw_data_path.parent / "insideairbnb",
    ]
    
    frames = []
    for search_path in search_paths:
        if not search_path.exists():
            continue
        
        csv_files = list(search_path.glob("*reviews*.csv*"))
        
        for path in csv_files:
            try:
                logger.info("Cargando reviews desde: %s", path)
                if path.suffix == ".gz":
                    import gzip
                    df = pd.read_csv(path, compression="gzip", low_memory=False)
                else:
                    df = pd.read_csv(path, low_memory=False)
                
                logger.info("Reviews cargados: %s registros", len(df))
                frames.append(df)
            except Exception as exc:
                logger.warning("Error leyendo reviews CSV %s: %s", path, exc)
    
    if not frames:
        logger.warning("No se pudieron cargar archivos de reviews de Airbnb")
        return pd.DataFrame()
    
    df = pd.concat(frames, ignore_index=True)
    logger.info("Total reviews cargados: %s registros", len(df))
    
    return df


def _map_neighbourhood_to_barrio_id(
    neighbourhood: str,
    barrios_df: pd.DataFrame
) -> Optional[int]:
    """
    Mapea un nombre de neighbourhood de Airbnb a barrio_id.
    
    Args:
        neighbourhood: Nombre del neighbourhood según Inside Airbnb.
        barrios_df: DataFrame con dimensión de barrios.
    
    Returns:
        barrio_id si se encuentra, None si no.
    """
    if pd.isna(neighbourhood) or not neighbourhood:
        return None
    
    # Normalizar nombre
    from src.transform.cleaners import HousingCleaner
    cleaner = HousingCleaner()
    neighbourhood_norm = cleaner.normalize_neighborhoods(str(neighbourhood))
    
    # Buscar coincidencia exacta normalizada
    match = barrios_df[
        barrios_df["barrio_nombre_normalizado"] == neighbourhood_norm
    ]
    
    if not match.empty:
        return int(match.iloc[0]["barrio_id"])
    
    # Buscar coincidencia parcial (case-insensitive)
    match = barrios_df[
        barrios_df["barrio_nombre_normalizado"].str.contains(
            neighbourhood_norm[:10], case=False, na=False, regex=False
        )
    ]
    
    if not match.empty:
        return int(match.iloc[0]["barrio_id"])
    
    return None


def _map_listings_to_barrios_geocoding(
    listings_df: pd.DataFrame,
    barrios_df: pd.DataFrame
) -> pd.Series:
    """
    Mapea listings a barrios usando geocodificación con geometrías.
    
    Usa las coordenadas (latitude, longitude) de los listings y las geometrías
    de dim_barrios para determinar en qué barrio está cada listing.
    
    Args:
        listings_df: DataFrame con listings de Airbnb (debe tener 'latitude', 'longitude').
        barrios_df: DataFrame con dimensión de barrios (debe tener 'geometry_json').
    
    Returns:
        Series con barrio_id para cada listing (None si no se puede mapear).
    """
    try:
        import json
        from shapely.geometry import shape, Point
        import geopandas as gpd
    except ImportError:
        logger.warning(
            "shapely o geopandas no están instalados. "
            "Usando mapeo por nombre de neighbourhood en lugar de geocodificación."
        )
        return pd.Series([None] * len(listings_df), index=listings_df.index)
    
    # Verificar que tenemos las columnas necesarias
    if "latitude" not in listings_df.columns or "longitude" not in listings_df.columns:
        logger.warning("Listings no tienen columnas latitude/longitude, usando mapeo por nombre")
        return pd.Series([None] * len(listings_df), index=listings_df.index)
    
    if "geometry_json" not in barrios_df.columns:
        logger.warning("Barrios no tienen geometry_json, usando mapeo por nombre")
        return pd.Series([None] * len(listings_df), index=listings_df.index)
    
    # Filtrar barrios con geometrías válidas
    barrios_with_geom = barrios_df[
        barrios_df["geometry_json"].notna()
    ].copy()
    
    if barrios_with_geom.empty:
        logger.warning("No hay barrios con geometrías válidas, usando mapeo por nombre")
        return pd.Series([None] * len(listings_df), index=listings_df.index)
    
    # Crear GeoDataFrame de barrios
    geometries = []
    barrio_ids = []
    
    for _, row in barrios_with_geom.iterrows():
        try:
            geom_json = json.loads(row["geometry_json"])
            geom = shape(geom_json)  # Convertir GeoJSON a Shapely geometry
            geometries.append(geom)
            barrio_ids.append(row["barrio_id"])
        except Exception as e:
            logger.debug("Error parseando geometría para barrio %s: %s", row["barrio_id"], e)
            continue
    
    if not geometries:
        logger.warning("No se pudieron parsear geometrías, usando mapeo por nombre")
        return pd.Series([None] * len(listings_df), index=listings_df.index)
    
    barrios_gdf = gpd.GeoDataFrame(
        {"barrio_id": barrio_ids},
        geometry=geometries,
        crs="EPSG:4326"
    )
    
    # Crear GeoDataFrame de listings
    listings_with_coords = listings_df[
        listings_df["latitude"].notna() &
        listings_df["longitude"].notna()
    ].copy()
    
    if listings_with_coords.empty:
        logger.warning("No hay listings con coordenadas válidas")
        return pd.Series([None] * len(listings_df), index=listings_df.index)
    
    listings_points = gpd.GeoDataFrame(
        listings_with_coords[["id"]],
        geometry=gpd.points_from_xy(
            listings_with_coords["longitude"],
            listings_with_coords["latitude"]
        ),
        crs="EPSG:4326"
    )
    
    # Spatial join: encontrar en qué barrio está cada punto
    joined = gpd.sjoin(
        listings_points,
        barrios_gdf,
        how="left",
        predicate="within"
    )
    
    # Crear serie de resultados
    result = pd.Series([None] * len(listings_df), index=listings_df.index, dtype="Int64")
    result.loc[joined.index] = joined["barrio_id"].values
    
    mapped_count = result.notna().sum()
    logger.info(
        "Geocodificación: %s de %s listings mapeados a barrios (%.1f%%)",
        mapped_count,
        len(listings_df),
        mapped_count / len(listings_df) * 100 if len(listings_df) > 0 else 0
    )
    
    return result


def prepare_presion_turistica(
    raw_data_path: Path,
    barrios_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Prepara tabla fact_presion_turistica desde datos brutos de Inside Airbnb.
    
    Args:
        raw_data_path: Directorio base donde se encuentran los datos raw de Airbnb.
        barrios_df: DataFrame con dimensión de barrios (debe incluir barrio_id,
            barrio_nombre_normalizado).
    
    Returns:
        DataFrame con columnas:
        - barrio_id
        - anio
        - mes
        - num_listings_airbnb
        - pct_entire_home
        - precio_noche_promedio
        - tasa_ocupacion
        - num_reviews_mes
    
    Raises:
        ValueError: Si faltan columnas clave en ``barrios_df``.
    """
    if barrios_df.empty:
        raise ValueError("barrios_df no puede estar vacío en prepare_presion_turistica")
    
    required_dim_cols = {"barrio_id", "barrio_nombre_normalizado"}
    missing_dim = required_dim_cols - set(barrios_df.columns)
    if missing_dim:
        raise ValueError(
            f"Dimensión de barrios incompleta para presión turística. "
            f"Faltan columnas: {sorted(missing_dim)}"
        )
    
    # 1. Cargar datos de listings
    listings_df = _load_airbnb_listings(raw_data_path)
    
    if listings_df.empty:
        logger.warning("No se encontraron datos de listings de Airbnb")
        return pd.DataFrame(columns=[
            "barrio_id", "anio", "mes", "num_listings_airbnb",
            "pct_entire_home", "precio_noche_promedio",
            "tasa_ocupacion", "num_reviews_mes"
        ])
    
    # 2. Mapear listings a barrios usando geocodificación (preferido) o nombre
    # Intentar primero geocodificación con geometrías
    listings_df["barrio_id"] = _map_listings_to_barrios_geocoding(listings_df, barrios_df)
    
    # Si la geocodificación no funcionó o hay listings sin mapear, usar mapeo por nombre
    unmapped_mask = listings_df["barrio_id"].isna()
    if unmapped_mask.any():
        logger.info(
            "%s listings sin mapear por geocodificación, intentando mapeo por nombre",
            unmapped_mask.sum()
        )
        
        # Inside Airbnb usa columnas como 'neighbourhood', 'neighbourhood_cleansed', etc.
        neighbourhood_col = None
        for col in ["neighbourhood_cleansed", "neighbourhood", "neighbourhood_group_cleansed"]:
            if col in listings_df.columns:
                neighbourhood_col = col
                break
        
        if neighbourhood_col:
            listings_df.loc[unmapped_mask, "barrio_id"] = listings_df.loc[unmapped_mask, neighbourhood_col].apply(
                lambda x: _map_neighbourhood_to_barrio_id(x, barrios_df)
            )
    
    # Filtrar solo los que tienen barrio_id válido
    total_listings = len(listings_df)
    listings_df = listings_df[listings_df["barrio_id"].notna()].copy()
    
    mapped_pct = len(listings_df) / total_listings * 100 if total_listings > 0 else 0
    logger.info(
        "Mapeo de listings: %s de %s listings mapeados a barrios (%.1f%%)",
        len(listings_df),
        total_listings,
        mapped_pct
    )
    
    if listings_df.empty:
        logger.warning("No se pudieron mapear listings a barrios")
        return pd.DataFrame(columns=[
            "barrio_id", "anio", "mes", "num_listings_airbnb",
            "pct_entire_home", "precio_noche_promedio",
            "tasa_ocupacion", "num_reviews_mes"
        ])
    
    # 3. Extraer fecha de last_scraped o host_since para determinar año/mes
    # Inside Airbnb típicamente tiene 'last_scraped' con formato 'YYYY-MM-DD'
    date_col = None
    for col in ["last_scraped", "host_since", "first_review", "last_review"]:
        if col in listings_df.columns:
            date_col = col
            break
    
    if date_col:
        listings_df[date_col] = pd.to_datetime(listings_df[date_col], errors="coerce")
        listings_df["anio"] = listings_df[date_col].dt.year
        listings_df["mes"] = listings_df[date_col].dt.month
    else:
        # Si no hay fecha, usar año/mes actual o del archivo
        logger.warning("No se encontró columna de fecha en listings, usando año/mes actual")
        from datetime import datetime
        now = datetime.now()
        listings_df["anio"] = now.year
        listings_df["mes"] = now.month
    
    # 4. Calcular métricas por barrio, año y mes
    # num_listings_airbnb: número total de listings
    # pct_entire_home: porcentaje de listings que son "Entire home/apt"
    # precio_noche_promedio: precio promedio por noche
    
    # Identificar columna de room_type
    room_type_col = None
    for col in ["room_type", "room_type_category"]:
        if col in listings_df.columns:
            room_type_col = col
            break
    
    # Identificar columna de precio
    price_col = None
    for col in ["price", "price_native"]:
        if col in listings_df.columns:
            price_col = col
            break
    
    # Limpiar precio (remover símbolos $, €, comas, etc.)
    if price_col and price_col in listings_df.columns:
        listings_df[price_col] = (
            listings_df[price_col]
            .astype(str)
            .str.replace("$", "", regex=False)
            .str.replace("€", "", regex=False)
            .str.replace(",", "", regex=False)
            .str.replace(" ", "", regex=False)
        )
        listings_df[price_col] = pd.to_numeric(listings_df[price_col], errors="coerce")
    
    # Agrupar por barrio, año y mes
    groupby_cols = ["barrio_id", "anio", "mes"]
    
    agg_dict = {
        "id": "count"  # Contar listings (asumiendo que hay columna 'id')
    }
    
    # Si hay columna de room_type, calcular pct_entire_home
    if room_type_col:
        listings_df["is_entire_home"] = (
            listings_df[room_type_col].str.contains("Entire", case=False, na=False)
        )
        agg_dict["is_entire_home"] = "sum"
    
    # Si hay columna de precio, calcular promedio
    if price_col:
        agg_dict[price_col] = "mean"
    
    # Agregar
    result = listings_df.groupby(groupby_cols, as_index=False).agg(agg_dict)
    
    # Renombrar columnas
    result = result.rename(columns={
        "id": "num_listings_airbnb",
        price_col: "precio_noche_promedio" if price_col else None
    })
    
    # Calcular pct_entire_home
    if room_type_col and "is_entire_home" in result.columns:
        result["pct_entire_home"] = (
            result["is_entire_home"] / result["num_listings_airbnb"] * 100
        )
        result = result.drop(columns=["is_entire_home"])
    else:
        result["pct_entire_home"] = None
    
    # 5. Cargar calendar para calcular tasa_ocupacion
    calendar_df = _load_airbnb_calendar(raw_data_path)
    
    if not calendar_df.empty and "listing_id" in calendar_df.columns:
        # Calendar típicamente tiene: listing_id, date, available, price
        calendar_df["date"] = pd.to_datetime(calendar_df["date"], errors="coerce")
        calendar_df["anio"] = calendar_df["date"].dt.year
        calendar_df["mes"] = calendar_df["date"].dt.month
        
        # Mapear listing_id a barrio_id
        listings_map = listings_df.set_index("id")["barrio_id"].to_dict()
        calendar_df["barrio_id"] = calendar_df["listing_id"].map(listings_map)
        calendar_df = calendar_df[calendar_df["barrio_id"].notna()].copy()
        
        # Calcular tasa de ocupación (días no disponibles / días totales)
        if "available" in calendar_df.columns:
            calendar_df["is_occupied"] = (
                calendar_df["available"].str.lower() == "f"  # 'f' = false = ocupado
            )
            
            ocupacion = calendar_df.groupby(groupby_cols, as_index=False).agg({
                "is_occupied": "mean"
            })
            ocupacion = ocupacion.rename(columns={"is_occupied": "tasa_ocupacion"})
            
            # Merge con result
            result = result.merge(
                ocupacion,
                on=groupby_cols,
                how="left"
            )
        else:
            result["tasa_ocupacion"] = None
    else:
        result["tasa_ocupacion"] = None
    
    # 6. Cargar reviews para calcular num_reviews_mes
    reviews_df = _load_airbnb_reviews(raw_data_path)
    
    if not reviews_df.empty and "listing_id" in reviews_df.columns:
        reviews_df["date"] = pd.to_datetime(reviews_df["date"], errors="coerce")
        reviews_df["anio"] = reviews_df["date"].dt.year
        reviews_df["mes"] = reviews_df["date"].dt.month
        
        # Mapear listing_id a barrio_id
        reviews_df["barrio_id"] = reviews_df["listing_id"].map(listings_map)
        reviews_df = reviews_df[reviews_df["barrio_id"].notna()].copy()
        
        # Contar reviews por barrio, año y mes
        reviews_count = reviews_df.groupby(groupby_cols, as_index=False).size()
        reviews_count = reviews_count.rename(columns={"size": "num_reviews_mes"})
        
        # Merge con result
        result = result.merge(
            reviews_count,
            on=groupby_cols,
            how="left"
        )
    else:
        result["num_reviews_mes"] = None
    
    # 7. Rellenar valores nulos y asegurar tipos correctos
    result["num_listings_airbnb"] = result["num_listings_airbnb"].fillna(0).astype(int)
    result["pct_entire_home"] = result["pct_entire_home"].fillna(0.0).astype(float)
    result["precio_noche_promedio"] = result["precio_noche_promedio"].fillna(0.0).astype(float)
    result["tasa_ocupacion"] = result["tasa_ocupacion"].fillna(0.0).astype(float)
    result["num_reviews_mes"] = result["num_reviews_mes"].fillna(0).astype(int)
    
    # 8. Filtrar solo registros válidos (con barrio_id, año y mes)
    result = result[
        result["barrio_id"].notna() &
        result["anio"].notna() &
        result["mes"].notna()
    ].copy()
    
    # Asegurar tipos
    result["barrio_id"] = result["barrio_id"].astype(int)
    result["anio"] = result["anio"].astype(int)
    result["mes"] = result["mes"].astype(int)
    
    logger.info(
        "Presión turística: %s registros procesados para %s barrios únicos",
        len(result),
        result["barrio_id"].nunique()
    )
    
    return result

