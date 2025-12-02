"""Transformaciones para dimensiones (dimensiones territoriales, barrios, etc.)."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from .utils import cleaner, logger


def _load_geojson_for_barrios(geojson_path: Optional[Path]) -> Optional[Dict[int, str]]:
    """
    Carga un archivo GeoJSON y crea un diccionario que mapea ``barrio_id`` a geometría JSON.

    Args:
        geojson_path: Ruta al archivo GeoJSON.

    Returns:
        Diccionario ``{barrio_id: geometry_json_string}`` o ``None`` si no se puede cargar.
    """
    if geojson_path is None or not geojson_path.exists():
        return None

    try:
        with open(geojson_path, "r", encoding="utf-8") as file:
            geojson_data = json.load(file)

        if geojson_data.get("type") != "FeatureCollection":
            logger.warning("GeoJSON no es FeatureCollection: %s", geojson_path)
            return None

        geometry_map: Dict[int, str] = {}
        features = geojson_data.get("features", [])

        for feature in features:
            if feature.get("type") != "Feature":
                continue

            properties = feature.get("properties", {})
            geometry = feature.get("geometry")

            barrio_id: Optional[int] = None
            if "codi_barri" in properties:
                barrio_id = properties.get("codi_barri")
            elif "Codi_Barri" in properties:
                barrio_id = properties.get("Codi_Barri")

            if barrio_id is None or geometry is None:
                continue

            try:
                barrio_id_int = int(barrio_id)
            except (ValueError, TypeError):
                continue

            geometry_json_str = json.dumps(geometry, ensure_ascii=False)
            geometry_map[barrio_id_int] = geometry_json_str

        logger.info("GeoJSON cargado: %s features mapeados a barrios", len(geometry_map))
        return geometry_map
    except Exception as exc:  # noqa: BLE001
        logger.warning("Error cargando GeoJSON %s: %s", geojson_path, exc)
        return None


def prepare_dim_barrios(
    demographics: pd.DataFrame,
    dataset_id: str,
    reference_time: datetime,
    geojson_path: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Construye la dimensión de barrios a partir del DataFrame demográfico raw.

    Args:
        demographics: DataFrame con datos demográficos.
        dataset_id: ID del dataset de origen.
        reference_time: Timestamp de referencia para el ETL.
        geojson_path: Ruta opcional al archivo GeoJSON con geometrías de barrios.

    Returns:
        DataFrame con la dimensión de barrios normalizada.
    """
    columns_list = [
        "Codi_Barri",
        "Nom_Barri",
        "Codi_Districte",
        "Nom_Districte",
    ]
    missing = set(columns_list) - set(demographics.columns)
    if missing:
        raise ValueError(f"Demographics dataframe missing columns: {missing}")

    dim = (
        demographics[columns_list]
        .drop_duplicates()
        .rename(
            columns={
                "Codi_Barri": "barrio_id",
                "Nom_Barri": "barrio_nombre",
                "Codi_Districte": "distrito_id",
                "Nom_Districte": "distrito_nombre",
            },
        )
    )

    dim["barrio_id"] = pd.to_numeric(dim["barrio_id"], errors="coerce").astype("Int64")
    dim["distrito_id"] = pd.to_numeric(dim["distrito_id"], errors="coerce").astype(
        "Int64",
    )
    dim = dim.dropna(subset=["barrio_id"])

    dim["barrio_nombre"] = dim["barrio_nombre"].apply(cleaner._fix_mojibake)
    dim["distrito_nombre"] = dim["distrito_nombre"].apply(cleaner._fix_mojibake)

    dim["barrio_nombre_normalizado"] = dim["barrio_nombre"].apply(
        cleaner.normalize_neighborhoods,
    )
    dim["codi_barri"] = dim["barrio_id"].astype(str).str.zfill(2)
    dim["codi_districte"] = dim["distrito_id"].astype(str).str.zfill(2)
    dim["municipio"] = "Barcelona"
    dim["ambito"] = "barri"
    dim["geometry_json"] = None
    dim["source_dataset"] = dataset_id
    timestamp = reference_time.isoformat()
    dim["etl_created_at"] = timestamp
    dim["etl_updated_at"] = timestamp

    if geojson_path:
        geometry_map = _load_geojson_for_barrios(geojson_path)
        if geometry_map:
            dim["geometry_json"] = dim["barrio_id"].map(geometry_map)
            geometries_loaded = dim["geometry_json"].notna().sum()
            logger.info(
                "Geometrías cargadas desde GeoJSON: %s de %s barrios",
                geometries_loaded,
                len(dim),
            )
        else:
            logger.warning("No se pudieron cargar geometrías del GeoJSON")
    else:
        logger.debug(
            "No se proporcionó ruta a GeoJSON, geometry_json permanece como None",
        )

    dim = dim[
        [
            "barrio_id",
            "barrio_nombre",
            "barrio_nombre_normalizado",
            "distrito_id",
            "distrito_nombre",
            "municipio",
            "ambito",
            "codi_districte",
            "codi_barri",
            "geometry_json",
            "source_dataset",
            "etl_created_at",
            "etl_updated_at",
        ]
    ].sort_values("barrio_id")

    logger.info("Dimensión de barrios preparada con %s registros", len(dim))
    return dim.reset_index(drop=True)


__all__ = ["prepare_dim_barrios"]


