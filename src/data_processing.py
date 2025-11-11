"""Data cleaning, normalization and validation utilities for the ETL pipeline."""

from __future__ import annotations

import logging
import math
import re
import unicodedata
from datetime import datetime
from typing import Dict, Iterable, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

NORMALIZATION_PATTERN = re.compile(r"[^a-z0-9]+")
LEADING_INDEX_PATTERN = re.compile(r"^\d+[\.,]?\s*")
AEI_SUFFIX_PATTERN = re.compile(r"-AEI.*$")
FOOTNOTE_PATTERN = re.compile(r"\s*\(\d+\)$")


def _normalize_text(value: Optional[str]) -> str:
    """Return a normalized key for matching barrio names."""

    if value is None:
        return ""
    value = str(value).strip().lower()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = NORMALIZATION_PATTERN.sub("", value)
    return value


def _clean_barrio_label(label: Optional[str]) -> str:
    """Clean barrio labels coming from legacy housing datasets."""

    if label is None:
        return ""
    label = str(label).strip()
    label = LEADING_INDEX_PATTERN.sub("", label)
    label = AEI_SUFFIX_PATTERN.sub("", label)
    label = FOOTNOTE_PATTERN.sub("", label)
    label = re.sub(r"\s+", " ", label)
    return label.strip()


def prepare_dim_barrios(
    demographics: pd.DataFrame,
    dataset_id: str,
    reference_time: datetime,
) -> pd.DataFrame:
    """Build the barrios dimension from the raw demographics dataframe."""

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
            }
        )
    )

    dim["barrio_id"] = pd.to_numeric(dim["barrio_id"], errors="coerce").astype("Int64")
    dim["distrito_id"] = pd.to_numeric(dim["distrito_id"], errors="coerce").astype("Int64")
    dim = dim.dropna(subset=["barrio_id"])

    dim["barrio_nombre_normalizado"] = dim["barrio_nombre"].apply(_normalize_text)
    dim["codi_barri"] = dim["barrio_id"].astype(str).str.zfill(2)
    dim["codi_districte"] = dim["distrito_id"].astype(str).str.zfill(2)
    dim["municipio"] = "Barcelona"
    dim["ambito"] = "barri"
    dim["geometry_json"] = None
    dim["source_dataset"] = dataset_id
    timestamp = reference_time.isoformat()
    dim["etl_created_at"] = timestamp
    dim["etl_updated_at"] = timestamp

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


def prepare_fact_demografia(
    demographics: pd.DataFrame,
    dim_barrios: pd.DataFrame,
    dataset_id: str,
    reference_time: datetime,
    source: str = "opendatabcn",
) -> pd.DataFrame:
    """Aggregate demographic census data by barrio and year."""

    df = demographics.copy()
    for column in ("Valor", "año", "Codi_Barri"):
        if column not in df.columns:
            raise ValueError(f"Demographics dataframe missing column '{column}'")

    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce")
    df = df.dropna(subset=["Valor", "año", "Codi_Barri"])
    df["año"] = pd.to_numeric(df["año"], errors="coerce").astype("Int64")
    df["Codi_Barri"] = pd.to_numeric(df["Codi_Barri"], errors="coerce").astype("Int64")

    pivot = (
        df.pivot_table(
            values="Valor",
            index=["año", "Codi_Barri"],
            columns="SEXE",
            aggfunc="sum",
            fill_value=0,
        )
        .rename(columns={1: "poblacion_hombres", 2: "poblacion_mujeres"})
        .reset_index()
    )

    for sex_column in ("poblacion_hombres", "poblacion_mujeres"):
        if sex_column not in pivot.columns:
            pivot[sex_column] = 0

    pivot["poblacion_total"] = (
        pivot.get("poblacion_hombres", 0) + pivot.get("poblacion_mujeres", 0)
    )

    fact = pivot.rename(columns={"Codi_Barri": "barrio_id", "año": "anio"})

    # Join to ensure only known barrios are kept
    fact = fact.merge(
        dim_barrios[["barrio_id", "barrio_nombre_normalizado"]],
        on="barrio_id",
        how="inner",
    )

    fact["hogares_totales"] = pd.NA
    fact["edad_media"] = pd.NA
    fact["porc_inmigracion"] = pd.NA
    fact["densidad_hab_km2"] = pd.NA
    fact["dataset_id"] = dataset_id
    fact["source"] = source
    fact["etl_loaded_at"] = reference_time.isoformat()

    fact = fact[
        [
            "barrio_id",
            "anio",
            "poblacion_total",
            "poblacion_hombres",
            "poblacion_mujeres",
            "hogares_totales",
            "edad_media",
            "porc_inmigracion",
            "densidad_hab_km2",
            "dataset_id",
            "source",
            "etl_loaded_at",
        ]
    ].sort_values(["anio", "barrio_id"])

    logger.info(
        "Tabla de hechos demográficos preparada con %s registros", len(fact)
    )
    return fact.reset_index(drop=True)


def _prepare_venta_prices(
    venta: pd.DataFrame,
    dim_barrios: pd.DataFrame,
    dataset_id: str,
    reference_time: datetime,
) -> pd.DataFrame:
    if venta is None or venta.empty:
        return pd.DataFrame(
            columns=
            [
                "barrio_id",
                "anio",
                "periodo",
                "trimestre",
                "precio_m2_venta",
                "precio_mes_alquiler",
                "dataset_id",
                "source",
                "etl_loaded_at",
            ]
        )

    venta_df = venta.copy()
    value_columns = [
        col for col in venta_df.columns if isinstance(col, str) and col.isdigit()
    ]
    value_column = value_columns[0] if value_columns else "Valor"

    venta_df[value_column] = (
        venta_df[value_column]
        .apply(lambda x: np.nan if str(x).strip().lower() in {"n.d.", ""} else x)
        .astype(str)
        .str.replace(".", "", regex=False)
    )
    # Reintroduce decimal separator
    venta_df[value_column] = (
        venta_df[value_column]
        .str.replace(",", ".", regex=False)
        .apply(lambda v: v.replace(" ", ""))
    )
    venta_df[value_column] = pd.to_numeric(venta_df[value_column], errors="coerce")

    venta_df["año"] = pd.to_numeric(venta_df.get("año"), errors="coerce").astype("Int64")

    venta_df["barrio_nombre_limpio"] = venta_df["Barris"].apply(_clean_barrio_label)
    venta_df["match_key"] = venta_df["barrio_nombre_limpio"].apply(_normalize_text)

    dim_lookup = dim_barrios[["barrio_id", "barrio_nombre_normalizado"]].rename(
        columns={"barrio_nombre_normalizado": "match_key"}
    )

    merged = venta_df.merge(dim_lookup, on="match_key", how="left")

    unmatched = merged[merged["barrio_id"].isna()]
    if not unmatched.empty:
        logger.warning(
            "%s registros de venta no pudieron asociarse a un barrio: %s",
            len(unmatched),
            sorted(unmatched["Barris"].unique()),
        )
    source_series = (
        merged["source"] if "source" in merged.columns else pd.Series(index=merged.index, dtype="object")
    )
    source_series = source_series.fillna("opendatabcn_idealista")

    merged = merged.dropna(subset=["barrio_id", value_column, "año"])

    result = pd.DataFrame(
        {
            "barrio_id": merged["barrio_id"].astype(int),
            "anio": merged["año"].astype(int),
            "periodo": merged["año"].astype(str),
            "trimestre": pd.NA,
            "precio_m2_venta": merged[value_column],
            "precio_mes_alquiler": pd.NA,
            "dataset_id": dataset_id,
            "source": source_series.loc[merged.index],
            "etl_loaded_at": reference_time.isoformat(),
        }
    )

    return result


def prepare_fact_precios(
    venta: pd.DataFrame,
    dim_barrios: pd.DataFrame,
    dataset_id_venta: str,
    reference_time: datetime,
    alquiler: Optional[pd.DataFrame] = None,
    dataset_id_alquiler: Optional[str] = None,
) -> pd.DataFrame:
    """Build the housing prices fact table."""

    fact_venta = _prepare_venta_prices(venta, dim_barrios, dataset_id_venta, reference_time)

    # Placeholder for alquiler data: currently no reliable price dataset available.
    if alquiler is not None and not alquiler.empty:
        logger.warning(
            "Datos de alquiler encontrados pero sin métrica de precio identificable. Se omiten."
        )

    fact = fact_venta
    fact = fact.sort_values(["anio", "barrio_id"]).reset_index(drop=True)
    logger.info("Tabla de hechos de precios preparada con %s registros", len(fact))
    return fact

