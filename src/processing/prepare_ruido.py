"""
Procesa datos de contaminación acústica y crea fact_ruido.

Fuentes:
- Mapas Estratégicos de Ruido (MER): Rásteres con niveles Ld, Ln, Lden
- Red de monitorización: Datos de sensores
- Datasets CSV agregados por barrio
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


def _load_ruido_data(raw_data_path: Path) -> pd.DataFrame:
    """
    Carga datos de ruido desde archivos CSV en el directorio ruido.
    
    Args:
        raw_data_path: Directorio base donde se encuentran los datos raw.
    
    Returns:
        DataFrame con datos de ruido.
    """
    search_paths = [
        raw_data_path / "ruido",
        raw_data_path.parent / "ruido",
        raw_data_path,
    ]
    
    frames = []
    
    for search_path in search_paths:
        if not search_path.exists():
            continue
        
        # Buscar archivos CSV relacionados con ruido
        csv_files = list(search_path.glob("*ruido*.csv"))
        csv_files.extend(list(search_path.glob("*soroll*.csv")))
        csv_files.extend(list(search_path.glob("*noise*.csv")))
        
        for csv_file in csv_files:
            try:
                logger.info("Cargando datos de ruido desde: %s", csv_file)
                df = pd.read_csv(csv_file, low_memory=False)
                logger.info("Datos cargados: %s registros, %s columnas", len(df), len(df.columns))
                frames.append(df)
            except Exception as exc:
                logger.warning("Error leyendo CSV de ruido %s: %s", csv_file, exc)
    
    if not frames:
        logger.warning("No se pudieron cargar archivos de ruido")
        return pd.DataFrame()
    
    df = pd.concat(frames, ignore_index=True)
    logger.info("Total datos de ruido cargados: %s registros", len(df))
    
    return df


def _map_barrio_from_ruido_data(
    df: pd.DataFrame,
    barrios_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Mapea nombres de barrios en datos de ruido a barrio_id.
    
    Args:
        df: DataFrame con datos de ruido.
        barrios_df: DataFrame con dimensión de barrios.
    
    Returns:
        DataFrame con columna barrio_id añadida.
    """
    from src.transform.cleaners import HousingCleaner
    
    cleaner = HousingCleaner()
    
    # Buscar columna de barrio en datos de ruido
    barrio_col = None
    for col in ["barrio", "barri", "neighbourhood", "barrio_nombre", "nom_barri"]:
        if col in df.columns:
            barrio_col = col
            break
    
    if barrio_col is None:
        # Buscar por codi_barri
        codi_col = None
        for col in ["codi_barri", "barrio_id"]:
            if col in df.columns:
                codi_col = col
                break
        
        if codi_col:
            # Mapear directamente por código
            df["barrio_id"] = pd.to_numeric(df[codi_col], errors="coerce")
            return df
        else:
            logger.warning("No se encontró columna de barrio en datos de ruido")
            df["barrio_id"] = None
            return df
    
    # Normalizar nombres de barrios
    df["barrio_nombre_normalizado"] = df[barrio_col].apply(
        lambda x: cleaner.normalize_neighborhoods(str(x)) if pd.notna(x) else ""
    )
    
    # Merge con barrios_df
    merged = df.merge(
        barrios_df[["barrio_id", "barrio_nombre_normalizado"]],
        left_on="barrio_nombre_normalizado",
        right_on="barrio_nombre_normalizado",
        how="left"
    )
    
    # Si hay registros sin mapear, intentar por nombre directo (case-insensitive)
    unmapped = merged["barrio_id"].isna()
    if unmapped.any():
        df_unmapped = df[unmapped].copy()
        df_unmapped["barrio_nombre_lower"] = df_unmapped[barrio_col].astype(str).str.lower().str.strip()
        
        barrios_lower = barrios_df.copy()
        barrios_lower["barrio_nombre_lower"] = barrios_df["barrio_nombre"].astype(str).str.lower().str.strip()
        
        df_unmapped_mapped = df_unmapped.merge(
            barrios_lower[["barrio_id", "barrio_nombre_lower"]],
            left_on="barrio_nombre_lower",
            right_on="barrio_nombre_lower",
            how="left"
        )
        
        merged.loc[unmapped, "barrio_id"] = df_unmapped_mapped["barrio_id"].values
    
    missing_fk = merged["barrio_id"].isna().sum()
    if missing_fk:
        logger.warning(
            "Ruido: %s registros sin mapeo a barrio_id", missing_fk
        )
    
    return merged


def _calculate_ruido_from_raster(
    raster_path: Path,
    barrios_gdf
) -> Optional[pd.DataFrame]:
    """
    Calcula niveles de ruido por barrio a partir de un mapa ráster.
    
    Esta función requiere rasterio y geopandas. Si no están disponibles,
    retorna None y se usará el fallback de datos CSV.
    
    Args:
        raster_path: Ruta al archivo ráster (GeoTIFF).
        barrios_gdf: GeoDataFrame con geometrías de barrios.
    
    Returns:
        DataFrame con niveles de ruido por barrio, o None si no se puede procesar.
    """
    try:
        import rasterio
        from rasterio.mask import mask
        import geopandas as gpd
        import numpy as np
    except ImportError:
        logger.warning(
            "rasterio/geopandas no disponibles. No se puede procesar ráster. "
            "Usando datos CSV como fallback."
        )
        return None
    
    try:
        logger.info("Procesando ráster de ruido: %s", raster_path)
        
        with rasterio.open(raster_path) as src:
            # Leer el ráster completo
            data = src.read(1)  # Leer primera banda
            
            # Crear máscara para cada barrio
            results = []
            
            for idx, barrio in barrios_gdf.iterrows():
                barrio_id = barrio["barrio_id"]
                geometry = barrio["geometry"]
                
                try:
                    # Extraer valores del ráster dentro de la geometría del barrio
                    out_image, out_transform = mask(src, [geometry], crop=True)
                    values = out_image[0]
                    
                    # Filtrar valores válidos (no nodata)
                    valid_values = values[values != src.nodata]
                    
                    if len(valid_values) > 0:
                        # Calcular estadísticas
                        nivel_medio = float(np.mean(valid_values))
                        nivel_max = float(np.max(valid_values))
                        nivel_min = float(np.min(valid_values))
                        
                        results.append({
                            "barrio_id": barrio_id,
                            "nivel_lden_medio": nivel_medio,
                            "nivel_ld_dia": nivel_medio,  # Aproximación si no hay bandas separadas
                            "nivel_ln_noche": nivel_medio,  # Aproximación
                        })
                
                except Exception as e:
                    logger.debug("Error procesando barrio %s: %s", barrio_id, e)
                    continue
            
            if results:
                df = pd.DataFrame(results)
                logger.info("✓ Ráster procesado: %s barrios", len(df))
                return df
            
    except Exception as e:
        logger.warning("Error procesando ráster: %s", e)
        return None
    
    return None


def prepare_ruido(
    raw_data_path: Path,
    barrios_df: pd.DataFrame,
    poblacion_df: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """
    Prepara tabla fact_ruido desde datos brutos de contaminación acústica.
    
    Args:
        raw_data_path: Directorio base donde se encuentran los datos raw de ruido.
        barrios_df: DataFrame con dimensión de barrios (debe incluir barrio_id,
            barrio_nombre_normalizado, geometry_json).
        poblacion_df: DataFrame opcional con datos de población por barrio y año.
            Se usa para calcular porcentaje de población expuesta a >65 dB(A).
            Debe tener columnas: barrio_id, anio, poblacion_total.
    
    Returns:
        DataFrame con columnas:
        - barrio_id
        - anio
        - nivel_lden_medio
        - nivel_ld_dia
        - nivel_ln_noche
        - pct_poblacion_expuesta_65db
    
    Raises:
        ValueError: Si faltan columnas clave en ``barrios_df``.
    """
    if barrios_df.empty:
        raise ValueError("barrios_df no puede estar vacío en prepare_ruido")
    
    required_dim_cols = {"barrio_id", "barrio_nombre_normalizado"}
    missing_dim = required_dim_cols - set(barrios_df.columns)
    if missing_dim:
        raise ValueError(
            f"Dimensión de barrios incompleta para ruido. "
            f"Faltan columnas: {sorted(missing_dim)}"
        )
    
    # 1. Cargar datos de ruido
    df = _load_ruido_data(raw_data_path)
    
    # 2. Intentar procesar rásteres si están disponibles
    raster_files = list(raw_data_path.glob("**/*.tif"))
    raster_files.extend(list(raw_data_path.glob("**/*.tiff")))
    raster_files.extend(list(raw_data_path.glob("**/*.geotiff")))
    
    raster_results = []
    if raster_files and "geometry_json" in barrios_df.columns:
        try:
            import geopandas as gpd
            from shapely import wkt
            
            # Crear GeoDataFrame de barrios
            barrios_gdf = barrios_df.copy()
            barrios_gdf["geometry"] = barrios_gdf["geometry_json"].apply(
                lambda x: wkt.loads(x) if x and pd.notna(x) else None
            )
            barrios_gdf = barrios_gdf[barrios_gdf["geometry"].notna()]
            barrios_gdf = gpd.GeoDataFrame(barrios_gdf, geometry="geometry")
            
            for raster_file in raster_files[:1]:  # Procesar solo el primero por ahora
                raster_df = _calculate_ruido_from_raster(raster_file, barrios_gdf)
                if raster_df is not None:
                    raster_results.append(raster_df)
        
        except ImportError:
            logger.info("geopandas/shapely no disponibles, omitiendo procesamiento de rásteres")
        except Exception as e:
            logger.warning("Error preparando GeoDataFrame para rásteres: %s", e)
    
    # 3. Si hay datos CSV, usarlos
    if not df.empty:
        # Mapear barrios
        df = _map_barrio_from_ruido_data(df, barrios_df)
        df = df[df["barrio_id"].notna()].copy()
    
    # 4. Combinar resultados de ráster y CSV
    if raster_results:
        df_raster = pd.concat(raster_results, ignore_index=True)
        if df.empty:
            df = df_raster
        else:
            # Merge: priorizar CSV si hay ambos
            df = df.merge(
                df_raster,
                on="barrio_id",
                how="left",
                suffixes=("", "_raster")
            )
            # Usar valores de ráster si faltan en CSV
            for col in ["nivel_lden_medio", "nivel_ld_dia", "nivel_ln_noche"]:
                if f"{col}_raster" in df.columns:
                    df[col] = df[col].fillna(df[f"{col}_raster"])
                    df = df.drop(columns=[f"{col}_raster"])
    
    if df.empty:
        logger.warning("No se encontraron datos de ruido procesables")
        return pd.DataFrame(columns=[
            "barrio_id", "anio",
            "nivel_lden_medio", "nivel_ld_dia", "nivel_ln_noche",
            "pct_poblacion_expuesta_65db"
        ])
    
    # 5. Extraer año
    anio_col = None
    for col in ["anio", "any", "year", "año"]:
        if col in df.columns:
            anio_col = col
            break
    
    if anio_col:
        df["anio"] = pd.to_numeric(df[anio_col], errors="coerce")
    else:
        logger.warning("No se encontró columna de año, usando año por defecto")
        from datetime import datetime
        df["anio"] = datetime.now().year
    
    # 6. Identificar columnas de niveles de ruido
    # Buscar columnas con niveles Ld, Ln, Lden
    lden_col = None
    ld_col = None
    ln_col = None
    
    for col in df.columns:
        col_lower = col.lower()
        if "lden" in col_lower or "lden" in col_lower:
            lden_col = col
        elif ("ld" in col_lower or "dia" in col_lower) and "lden" not in col_lower:
            ld_col = col
        elif "ln" in col_lower or "noche" in col_lower:
            ln_col = col
    
    # Mapear columnas encontradas
    if lden_col:
        df["nivel_lden_medio"] = pd.to_numeric(df[lden_col], errors="coerce")
    elif "nivel_lden_medio" not in df.columns:
        df["nivel_lden_medio"] = None
    
    if ld_col:
        df["nivel_ld_dia"] = pd.to_numeric(df[ld_col], errors="coerce")
    elif "nivel_ld_dia" not in df.columns:
        df["nivel_ld_dia"] = None
    
    if ln_col:
        df["nivel_ln_noche"] = pd.to_numeric(df[ln_col], errors="coerce")
    elif "nivel_ln_noche" not in df.columns:
        df["nivel_ln_noche"] = None
    
    # 7. Calcular porcentaje de población expuesta a >65 dB(A)
    if poblacion_df is not None and not poblacion_df.empty and "poblacion_total" in poblacion_df.columns:
        # Merge con población
        df = df.merge(
            poblacion_df[["barrio_id", "anio", "poblacion_total"]],
            on=["barrio_id", "anio"],
            how="left"
        )
        
        # Calcular porcentaje expuesto (simplificado: si nivel_lden > 65, asumir 100% expuesto)
        # En la realidad, esto requeriría datos más detallados de distribución espacial
        df["pct_poblacion_expuesta_65db"] = (
            (df["nivel_lden_medio"] > 65).astype(int) * 100.0
        ).fillna(0.0)
        
        df = df.drop(columns=["poblacion_total"])
    else:
        logger.info("No hay datos de población, pct_poblacion_expuesta_65db será None")
        df["pct_poblacion_expuesta_65db"] = None
    
    # 8. Agregar por barrio y año (por si hay múltiples registros)
    groupby_cols = ["barrio_id", "anio"]
    agg_dict = {
        "nivel_lden_medio": "mean",
        "nivel_ld_dia": "mean",
        "nivel_ln_noche": "mean",
    }
    
    if "pct_poblacion_expuesta_65db" in df.columns:
        agg_dict["pct_poblacion_expuesta_65db"] = "mean"
    
    result = df.groupby(groupby_cols, as_index=False).agg(agg_dict)
    
    # 9. Rellenar valores nulos y asegurar tipos correctos
    result["nivel_lden_medio"] = result["nivel_lden_medio"].fillna(0.0).astype(float)
    result["nivel_ld_dia"] = result["nivel_ld_dia"].fillna(0.0).astype(float)
    result["nivel_ln_noche"] = result["nivel_ln_noche"].fillna(0.0).astype(float)
    if "pct_poblacion_expuesta_65db" in result.columns:
        result["pct_poblacion_expuesta_65db"] = result["pct_poblacion_expuesta_65db"].fillna(0.0).astype(float)
    
    # 10. Filtrar solo registros válidos
    result = result[
        result["barrio_id"].notna() &
        result["anio"].notna()
    ].copy()
    
    # Asegurar tipos
    result["barrio_id"] = result["barrio_id"].astype(int)
    result["anio"] = result["anio"].astype(int)
    
    logger.info(
        "Ruido: %s registros procesados para %s barrios únicos",
        len(result),
        result["barrio_id"].nunique()
    )
    
    return result

