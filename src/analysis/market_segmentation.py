"""Utilidades para trabajar con la segmentación de mercado K-Means v0.

Este módulo NO recalcula el modelo de clustering; asume que los clusters
han sido estimados previamente (por ejemplo, en el notebook
`notebooks/analysis/01_market_segmentation_v0.ipynb`) y expone funciones
para:

- Construir una tabla de mapeo barrio -> submercado.
- Enriquecer otros DataFrames con el identificador de submercado.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd


SubmarketVersion = Literal["v0"]


@dataclass(frozen=True)
class SubmarketMetadata:
    """
    Metadatos básicos asociados a una segmentación de submercados.

    Args:
        version: Versión lógica del modelo de submercados (por ahora, solo \"v0\").
        target_year: Año de referencia usado para estimar el modelo.
        k_opt: Número óptimo de clusters utilizado en K-Means.
    """

    version: SubmarketVersion
    target_year: int
    k_opt: int


def build_submarket_mapping(
    features_with_clusters: pd.DataFrame,
    metadata: SubmarketMetadata,
) -> pd.DataFrame:
    """
    Construye una tabla de mapeo barrio -> submercado a partir de un DataFrame.

    Esta función está pensada para usarse directamente desde el notebook de
    segmentación, tomando el DataFrame final que contiene una columna
    ``cluster_label`` producida por K-Means.

    El resultado puede guardarse en disco (CSV/Parquet) o utilizarse como
    tabla auxiliar en otros análisis.

    Args:
        features_with_clusters:
            DataFrame que contiene, al menos, las columnas:
            ``barrio_id``, ``barrio_nombre``, ``codi_barri`` y
            ``cluster_label``.
        metadata:
            Metadatos de la segmentación (versión, año objetivo y k_opt).

    Returns:
        DataFrame con las columnas:

        - ``barrio_id``
        - ``barrio_nombre``
        - ``codi_barri``
        - ``submarket_id`` (entero, copia de ``cluster_label``)
        - ``submarket_version`` (por ejemplo, \"v0\")
        - ``target_year``
        - ``k_opt``

    Raises:
        ValueError:
            Si faltan columnas obligatorias en ``features_with_clusters``.
    """
    required_columns = {"barrio_id", "barrio_nombre", "codi_barri", "cluster_label"}
    missing = required_columns - set(features_with_clusters.columns)
    if missing:
        raise ValueError(
            f"El DataFrame de entrada no contiene las columnas requeridas: {missing}",
        )

    df = features_with_clusters[list(required_columns)].copy()

    df = df.rename(columns={"cluster_label": "submarket_id"})
    df["submarket_version"] = metadata.version
    df["target_year"] = metadata.target_year
    df["k_opt"] = metadata.k_opt

    # Ordenar columnas para facilitar lectura y merges posteriores
    column_order = [
        "barrio_id",
        "barrio_nombre",
        "codi_barri",
        "submarket_id",
        "submarket_version",
        "target_year",
        "k_opt",
    ]
    return df[column_order].sort_values(["submarket_id", "barrio_id"]).reset_index(
        drop=True,
    )


def assign_submarket(
    df: pd.DataFrame,
    mapping: pd.DataFrame,
    on: str = "barrio_id",
    how: str = "left",
) -> pd.DataFrame:
    """
    Enriquece un DataFrame con el identificador de submercado.

    Esta función es la puerta de entrada recomendada para que otros módulos
    (p. ej. análisis causal bayesiano o gentrificación) incorporen la
    información de submercado sin tener que recalcular el clustering.

    Args:
        df:
            DataFrame a enriquecer. Debe contener la columna indicada en ``on``,
            típicamente ``barrio_id`` o ``codi_barri``.
        mapping:
            DataFrame de mapeo producido por :func:`build_submarket_mapping`,
            o un equivalente que contenga al menos:
            ``on`` y ``submarket_id``.
        on:
            Nombre de la columna clave para realizar el merge
            (por defecto, ``barrio_id``).
        how:
            Tipo de join a utilizar. Por defecto ``left`` para preservar
            todas las filas de ``df``.

    Returns:
        Copia de ``df`` con las columnas de submercado añadidas
        (``submarket_id``, ``submarket_version``, ``target_year``, ``k_opt``)
        cuando estén presentes en ``mapping``.

    Raises:
        ValueError:
            Si ``mapping`` no contiene la columna indicada en ``on`` o la
            columna ``submarket_id``.
    """
    if on not in df.columns:
        raise ValueError(
            f"El DataFrame de entrada no contiene la columna clave '{on}' requerida "
            "para asignar submercados.",
        )

    if on not in mapping.columns:
        raise ValueError(
            f"El mapping de submercados no contiene la columna clave '{on}'.",
        )

    if "submarket_id" not in mapping.columns:
        raise ValueError(
            "El mapping de submercados debe contener la columna 'submarket_id'.",
        )

    # Seleccionar solo columnas de submercado para evitar colisiones
    submarket_cols = [
        column
        for column in [
            on,
            "submarket_id",
            "submarket_version",
            "target_year",
            "k_opt",
        ]
        if column in mapping.columns
    ]

    mapping_subset = mapping[submarket_cols].drop_duplicates(subset=[on]).copy()

    # Realizar merge preservando el DataFrame original
    enriched = df.merge(mapping_subset, on=on, how=how)
    return enriched



