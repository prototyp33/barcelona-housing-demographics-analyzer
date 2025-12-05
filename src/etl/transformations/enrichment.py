"""Transformaciones de enriquecimiento con fuentes auxiliares (Portal de Dades, Idealista)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .utils import (
    _extract_year_from_temps,
    _load_portaldades_csv,
    _map_territorio_to_barrio_id,
    logger,
)


def prepare_portaldades_precios(
    portaldades_dir: Path,
    dim_barrios: pd.DataFrame,
    reference_time: datetime,
    metadata_file: Optional[Path] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Procesa archivos de precios del Portal de Dades y los prepara para ``fact_precios``.

    Args:
        portaldades_dir: Directorio donde están los archivos CSV del Portal de Dades.
        dim_barrios: DataFrame con la dimensión de barrios.
        reference_time: Timestamp de referencia para ETL.
        metadata_file: Archivo CSV con metadatos de indicadores (opcional).

    Returns:
        Tupla ``(venta_df, alquiler_df)`` con precios de venta y alquiler.
    """
    venta_records: List[Dict[str, Any]] = []
    alquiler_records: List[Dict[str, Any]] = []

    indicadores_metadata: Dict[str, Dict[str, str]] = {}
    if metadata_file and metadata_file.exists():
        try:
            metadata_df = pd.read_csv(metadata_file)
            for _, row in metadata_df.iterrows():
                indicadores_metadata[row["id_indicador"]] = {
                    "nombre": row.get("nombre", ""),
                    "categoria": row.get("categoria", "estadístiques"),
                }
        except Exception as exc:  # noqa: BLE001
            logger.warning("Error cargando metadatos: %s", exc)

    csv_files = list(portaldades_dir.glob("portaldades_*.csv"))

    venta_ids = {
        "bxtvnxvukh",
        "hostlmjrdo",
        "mrslyp5pcq",
        "idjhkx1ruj",
        "u25rr7oxh6",
        "cq4causxvu",
        "la6s9fp57r",
        "9ap8lewvtt",
        "bhl3ulphi5",
    }

    alquiler_ids = {
        "b37xv8wcjh",
        "5ibudgqbrb",
        "4waxpjj3uo",
        "jc3tvqfyum",
    }

    logger.info("Procesando %s archivos del Portal de Dades...", len(csv_files))

    for csv_file in csv_files:
        file_id = csv_file.stem.split("_")[-1]

        is_venta = file_id in venta_ids
        is_alquiler = file_id in alquiler_ids

        if not (is_venta or is_alquiler):
            continue

        try:
            df = _load_portaldades_csv(csv_file)

            if df.empty or "VALUE" not in df.columns:
                logger.debug("Archivo %s vacío o sin columna VALUE", csv_file.name)
                continue

            required_cols = [
                "Dim-00:TEMPS",
                "Dim-01:TERRITORI",
                "Dim-01:TERRITORI (type)",
                "VALUE",
            ]
            if not all(column in df.columns for column in required_cols):
                logger.warning(
                    "Archivo %s no tiene todas las columnas requeridas",
                    csv_file.name,
                )
                continue

            df = df[df["Dim-01:TERRITORI (type)"].isin(["Barri", "Districte"])]

            if df.empty:
                continue

            df["anio"] = df["Dim-00:TEMPS"].apply(_extract_year_from_temps)
            df = df.dropna(subset=["anio", "VALUE"])

            df["barrio_id"] = df.apply(
                lambda row: _map_territorio_to_barrio_id(
                    row["Dim-01:TERRITORI"],
                    row["Dim-01:TERRITORI (type)"],
                    dim_barrios,
                ),
                axis=1,
            )

            df = df.dropna(subset=["barrio_id"])

            if df.empty:
                logger.debug("No se pudieron mapear territorios en %s", csv_file.name)
                continue

            nombre_indicador = indicadores_metadata.get(file_id, {}).get(
                "nombre",
                csv_file.name,
            )
            is_precio_m2 = (
                "superfície" in nombre_indicador.lower()
                or "m²" in nombre_indicador
                or "m2" in nombre_indicador.lower()
            )

            for _, row in df.iterrows():
                record: Dict[str, Any] = {
                    "barrio_id": int(row["barrio_id"]),
                    "anio": int(row["anio"]),
                    "periodo": str(int(row["anio"])),
                    "trimestre": pd.NA,
                    "precio_m2_venta": pd.NA,
                    "precio_mes_alquiler": pd.NA,
                    "dataset_id": file_id,
                    "source": "portaldades",
                    "etl_loaded_at": reference_time.isoformat(),
                }

                if is_venta:
                    if is_precio_m2:
                        record["precio_m2_venta"] = float(row["VALUE"])
                        venta_records.append(record)
                elif is_alquiler:
                    if not is_precio_m2:
                        record["precio_mes_alquiler"] = float(row["VALUE"])
                        alquiler_records.append(record)

            logger.debug("Procesado %s: %s registros válidos", csv_file.name, len(df))

        except Exception as exc:  # noqa: BLE001
            logger.warning("Error procesando %s: %s", csv_file.name, exc)
            continue

    venta_df = pd.DataFrame(venta_records) if venta_records else pd.DataFrame()
    alquiler_df = pd.DataFrame(alquiler_records) if alquiler_records else pd.DataFrame()

    if not venta_df.empty:
        logger.info(
            "Preparados %s registros de precios de VENTA del Portal de Dades",
            len(venta_df),
        )
    if not alquiler_df.empty:
        logger.info(
            "Preparados %s registros de precios de ALQUILER del Portal de Dades",
            len(alquiler_df),
        )

    return venta_df, alquiler_df


def prepare_idealista_oferta(
    idealista_df: pd.DataFrame,
    dim_barrios: pd.DataFrame,
    dataset_id: str,
    reference_time: datetime,
    source: str = "idealista_api",
) -> pd.DataFrame:
    """
    Procesa datos de oferta inmobiliaria de Idealista y los agrega por barrio.

    Args:
        idealista_df: DataFrame con datos raw de Idealista (de ``extract_offer_by_barrio``).
        dim_barrios: DataFrame con la dimensión de barrios.
        dataset_id: ID del dataset.
        reference_time: Timestamp de referencia.
        source: Fuente de los datos.

    Returns:
        DataFrame procesado con datos agregados por barrio.
    """
    if idealista_df.empty:
        logger.warning("DataFrame de Idealista vacío")
        return pd.DataFrame()

    df = idealista_df.copy()

    barrio_col: Optional[str] = None
    for column in ["barrio_idealista", "barrio_busqueda", "district", "distrito"]:
        if column in df.columns:
            barrio_col = column
            break

    if barrio_col is None:
        logger.warning("No se encontró columna de barrio en datos de Idealista")
        return pd.DataFrame()

    logger.info("Mapeando barrios de Idealista usando columna '%s'...", barrio_col)

    df["barrio_id"] = df[barrio_col].apply(
        lambda value: (
            _map_territorio_to_barrio_id(str(value), "Barri", dim_barrios)
            if pd.notna(value)
            else None
        ),
    )

    df = df.dropna(subset=["barrio_id"])

    if df.empty:
        logger.warning("No se pudieron mapear barrios de Idealista a barrio_id")
        return pd.DataFrame()

    logger.info("✓ %s propiedades mapeadas a %s barrios", len(df), df["barrio_id"].nunique())

    if "fecha_extraccion" in df.columns:
        df["fecha"] = pd.to_datetime(df["fecha_extraccion"], errors="coerce")
    elif "fecha_publicacion" in df.columns:
        df["fecha"] = pd.to_datetime(df["fecha_publicacion"], errors="coerce")
    else:
        df["fecha"] = pd.to_datetime(reference_time)

    df["anio"] = df["fecha"].dt.year
    df["mes"] = df["fecha"].dt.month

    numeric_cols = ["precio", "precio_m2", "superficie", "habitaciones", "banos"]
    for column in numeric_cols:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

    group_cols = ["barrio_id", "operacion", "anio", "mes"]

    agg_dict: Dict[str, Tuple[str, str]] = {}

    if "precio" in df.columns:
        agg_dict["precio_medio"] = ("precio", "mean")
        agg_dict["precio_mediano"] = ("precio", "median")
        agg_dict["precio_min"] = ("precio", "min")
        agg_dict["precio_max"] = ("precio", "max")

    if "precio_m2" in df.columns:
        agg_dict["precio_m2_medio"] = ("precio_m2", "mean")
        agg_dict["precio_m2_mediano"] = ("precio_m2", "median")

    if "superficie" in df.columns:
        agg_dict["superficie_media"] = ("superficie", "mean")
        agg_dict["superficie_mediana"] = ("superficie", "median")

    if "habitaciones" in df.columns:
        agg_dict["habitaciones_media"] = ("habitaciones", "mean")

    agg_dict["num_anuncios"] = ("precio", "count")

    if "tipologia" in df.columns:
        _ = (
            df.groupby(group_cols + ["tipologia"])
            .size()
            .reset_index(name="num_anuncios_tipologia")
        )

    aggregated = df.groupby(group_cols).agg(agg_dict).reset_index()

    aggregated.columns = [
        column[0] if column[1] == "" else f"{column[0]}_{column[1]}"
        for column in aggregated.columns
    ]

    aggregated = aggregated.merge(
        dim_barrios[["barrio_id", "barrio_nombre_normalizado"]],
        on="barrio_id",
        how="inner",
    )

    aggregated["dataset_id"] = dataset_id
    aggregated["source"] = source
    aggregated["etl_loaded_at"] = reference_time.isoformat()

    aggregated = aggregated.sort_values(
        ["anio", "mes", "barrio_id", "operacion"],
    ).reset_index(drop=True)

    logger.info(
        "Datos de Idealista preparados: %s registros (%s barrios, %s operaciones, %s años)",
        len(aggregated),
        aggregated["barrio_id"].nunique(),
        aggregated["operacion"].nunique() if "operacion" in aggregated.columns else 0,
        aggregated["anio"].nunique(),
    )

    return aggregated


__all__ = ["prepare_portaldades_precios", "prepare_idealista_oferta"]


