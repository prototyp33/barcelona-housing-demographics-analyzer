"""Transformaciones demográficas (hechos y enriquecimientos relacionados con población)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .utils import (
    _append_tag,
    _edad_quinquenal_to_custom_group,
    _find_portaldades_file,
    _load_portaldades_csv,
    _map_continente_to_nacionalidad,
    _map_territorio_to_barrio_id,
    _parse_household_size,
    _extract_year_from_temps,
    cleaner,
    logger,
)


def prepare_fact_demografia(
    demographics: pd.DataFrame,
    dim_barrios: pd.DataFrame,
    dataset_id: str,
    reference_time: datetime,
    source: str = "opendatabcn",
) -> pd.DataFrame:
    """Agrega datos censales demográficos por barrio y año."""
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
        "Tabla de hechos demográficos preparada con %s registros",
        len(fact),
    )
    return fact.reset_index(drop=True)


def _compute_household_metrics(
    portaldades_dir: Path,
    dim_barrios: pd.DataFrame,
    fact_demografia: pd.DataFrame,
) -> pd.DataFrame:
    """Calcula promedios de tamaño de hogar y totales a nivel de barrio."""
    indicator_id = "hd7u1b68qj"
    dataset_path = _find_portaldades_file(portaldades_dir, indicator_id)
    if dataset_path is None:
        logger.debug(
            "No se encontró el dataset de hogares (%s) en %s",
            indicator_id,
            portaldades_dir,
        )
        return pd.DataFrame()

    try:
        raw_df = _load_portaldades_csv(dataset_path)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "No fue posible cargar el dataset de hogares %s: %s",
            dataset_path.name,
            exc,
        )
        return pd.DataFrame()

    if raw_df.empty:
        return pd.DataFrame()

    allowed_types = {"Barri", "Districte", "Municipi"}
    type_col = "Dim-01:TERRITORI (type)"
    value_col = "VALUE"
    category_col = "Dim-02:NOMBRE DE PERSONES DE LA LLAR"

    missing_cols = {type_col, value_col, category_col} - set(raw_df.columns)
    if missing_cols:
        logger.warning(
            "El dataset de hogares %s no contiene las columnas esperadas: %s",
            dataset_path.name,
            ", ".join(sorted(missing_cols)),
        )
        return pd.DataFrame()

    df = raw_df[raw_df[type_col].isin(allowed_types)].copy()
    if df.empty:
        return pd.DataFrame()

    df["anio"] = df["Dim-00:TEMPS"].apply(_extract_year_from_temps)
    df[value_col] = pd.to_numeric(df[value_col], errors="coerce")
    df["personas_hogar"] = df[category_col].apply(_parse_household_size)

    df = df.dropna(subset=["anio", value_col, "personas_hogar"])
    if df.empty:
        return pd.DataFrame()

    df["personas_estimadas"] = df[value_col] * df["personas_hogar"]

    aggregated = (
        df.groupby(["Dim-01:TERRITORI", type_col, "anio"], as_index=False)
        .agg(
            hogares_observados=(value_col, "sum"),
            personas_estimadas=("personas_estimadas", "sum"),
        )
        .assign(
            avg_size=lambda frame: frame.apply(
                lambda row: (
                    row["personas_estimadas"] / row["hogares_observados"]
                    if row["hogares_observados"]
                    else pd.NA
                ),
                axis=1,
            ),
        )
    )

    if aggregated.empty:
        return pd.DataFrame()

    population_by_year = (
        fact_demografia.set_index(["anio", "barrio_id"])["poblacion_total"].to_dict()
    )
    population_mean = (
        fact_demografia.groupby("barrio_id")["poblacion_total"].mean().to_dict()
    )

    district_lookup = (
        dim_barrios.assign(
            distrito_key=dim_barrios["distrito_nombre"].apply(
                cleaner.normalize_neighborhoods,
            ),
        )
        .groupby("distrito_key")["barrio_id"]
        .apply(list)
        .to_dict()
    )

    barrio_rows: List[Dict[str, object]] = []

    for _, row in aggregated.iterrows():
        territorio = row["Dim-01:TERRITORI"]
        tipo = row[type_col]
        year = int(row["anio"])
        hogares = float(row["hogares_observados"])
        avg_size = row["avg_size"] if not pd.isna(row["avg_size"]) else None
        priority = 1 if tipo == "Barri" else 0

        if tipo == "Barri":
            barrio_id = _map_territorio_to_barrio_id(territorio, tipo, dim_barrios)
            if barrio_id is None:
                continue
            barrio_rows.append(
                {
                    "barrio_id": int(barrio_id),
                    "anio": year,
                    "hogares_observados": hogares,
                    "avg_size": avg_size,
                    "priority": 2,
                },
            )
            continue

        if tipo == "Districte":
            key = cleaner.normalize_neighborhoods(territorio)
            barrio_ids = district_lookup.get(key, [])
        elif tipo == "Municipi":
            barrio_ids = dim_barrios["barrio_id"].astype(int).tolist()
        else:
            barrio_ids = []

        if not barrio_ids:
            continue

        weights: List[float] = []
        for barrio_id in barrio_ids:
            pop = population_by_year.get((year, int(barrio_id)))
            if pop is None or pd.isna(pop):
                pop = population_mean.get(int(barrio_id), 0.0)
            weights.append(float(pop) if pop is not None else 0.0)

        total_weight = sum(weights)
        if total_weight <= 0:
            weights = [1.0 for _ in barrio_ids]
            total_weight = float(len(barrio_ids))

        for barrio_id, weight in zip(barrio_ids, weights):
            share = hogares * (weight / total_weight) if total_weight else 0.0
            barrio_rows.append(
                {
                    "barrio_id": int(barrio_id),
                    "anio": year,
                    "hogares_observados": share,
                    "avg_size": avg_size,
                    "priority": priority,
                },
            )

    if not barrio_rows:
        return pd.DataFrame()

    households_df = pd.DataFrame(barrio_rows)

    def _mean_or_na(values: pd.Series) -> float | pd.NA:
        filtered = values.dropna()
        return filtered.mean() if not filtered.empty else pd.NA

    households_df = (
        households_df.sort_values("priority", ascending=False)
        .groupby(["barrio_id", "anio", "priority"], as_index=False)
        .agg(
            hogares_observados=("hogares_observados", "sum"),
            avg_size=("avg_size", _mean_or_na),
        )
    )
    households_df = households_df.sort_values(
        ["barrio_id", "anio", "priority"],
        ascending=[True, True, False],
    )
    households_df = households_df.drop_duplicates(
        subset=["barrio_id", "anio"],
        keep="first",
    ).drop(columns=["priority"])

    households_df["dataset_id"] = indicator_id
    households_df["source"] = "portaldades"
    return households_df


def _compute_foreign_purchase_share(
    portaldades_dir: Path,
    dim_barrios: pd.DataFrame,
) -> pd.DataFrame:
    """Calcula el porcentaje de compras de vivienda realizadas por compradores extranjeros."""
    indicator_id = "uuxbxa7onv"
    dataset_path = _find_portaldades_file(portaldades_dir, indicator_id)
    if dataset_path is None:
        return pd.DataFrame()

    try:
        df = _load_portaldades_csv(dataset_path)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "No fue posible cargar el dataset de nacionalidad de compradores %s: %s",
            dataset_path.name,
            exc,
        )
        return pd.DataFrame()

    type_col = "Dim-01:TERRITORI (type)"
    value_col = "VALUE"
    nationality_col = "Dim-02:GRUP DE NACIONALITAT DEL COMPRADOR"

    required_cols = {type_col, value_col, nationality_col}
    if not required_cols.issubset(df.columns):
        return pd.DataFrame()

    df = df[df[type_col] == "Barri"].copy()
    if df.empty:
        return pd.DataFrame()

    df["anio"] = df["Dim-00:TEMPS"].apply(_extract_year_from_temps)
    df[value_col] = pd.to_numeric(df[value_col], errors="coerce")
    df = df.dropna(subset=["anio", value_col])
    if df.empty:
        return pd.DataFrame()

    pivot = (
        df.pivot_table(
            index=["Dim-01:TERRITORI", "anio"],
            columns=nationality_col,
            values=value_col,
            aggfunc="sum",
            fill_value=0,
        )
        .reset_index()
    )

    numeric_cols = pivot.select_dtypes(include=[np.number]).columns
    pivot["total_transacciones"] = pivot[numeric_cols].sum(axis=1)
    estranger_col = "Estranger"
    if estranger_col not in pivot.columns:
        pivot[estranger_col] = 0.0

    pivot["porc_inmigracion"] = np.where(
        pivot["total_transacciones"] > 0,
        (pivot[estranger_col] / pivot["total_transacciones"]) * 100.0,
        np.nan,
    )

    pivot["barrio_id"] = pivot["Dim-01:TERRITORI"].apply(
        lambda terr: _map_territorio_to_barrio_id(str(terr), "Barri", dim_barrios),
    )
    pivot = pivot.dropna(subset=["barrio_id"])
    if pivot.empty:
        return pd.DataFrame()

    pivot["barrio_id"] = pivot["barrio_id"].astype(int)
    result = pivot[["barrio_id", "anio", "porc_inmigracion"]].copy()
    result["dataset_id"] = indicator_id
    result["source"] = "portaldades"
    return result


def _compute_building_age_proxy(
    portaldades_dir: Path,
    dim_barrios: pd.DataFrame,
) -> pd.DataFrame:
    """Obtiene la edad media del parque residencial como proxy de edad media demográfica."""
    indicator_id = "ydtnyd6qhm"
    dataset_path = _find_portaldades_file(portaldades_dir, indicator_id)
    if dataset_path is None:
        return pd.DataFrame()

    try:
        df = _load_portaldades_csv(dataset_path)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "No se pudo cargar el dataset de edad media de edificaciones %s: %s",
            dataset_path.name,
            exc,
        )
        return pd.DataFrame()

    type_col = "Dim-01:TERRITORI (type)"
    value_col = "VALUE"

    if type_col not in df.columns or value_col not in df.columns:
        return pd.DataFrame()

    df = df[df[type_col] == "Barri"].copy()
    if df.empty:
        return pd.DataFrame()

    df["anio"] = df["Dim-00:TEMPS"].apply(_extract_year_from_temps)
    df[value_col] = pd.to_numeric(df[value_col], errors="coerce")
    df = df.dropna(subset=[value_col])
    if df.empty:
        return pd.DataFrame()

    df["barrio_id"] = df["Dim-01:TERRITORI"].apply(
        lambda terr: _map_territorio_to_barrio_id(str(terr), "Barri", dim_barrios),
    )
    df = df.dropna(subset=["barrio_id"])
    if df.empty:
        return pd.DataFrame()

    df["barrio_id"] = df["barrio_id"].astype(int)
    df = df.rename(columns={value_col: "edad_media_proxy"})
    df["dataset_id"] = indicator_id
    df["source"] = "portaldades"
    return df[["barrio_id", "anio", "edad_media_proxy", "dataset_id", "source"]]


def _compute_area_by_barrio(
    portaldades_dir: Path,
    dim_barrios: pd.DataFrame,
) -> pd.DataFrame:
    """Obtiene la superficie de suelo (m²) por barrio para calcular densidad."""
    indicator_id = "wjnmk82jd9"
    dataset_path = _find_portaldades_file(portaldades_dir, indicator_id)
    if dataset_path is None:
        return pd.DataFrame()

    try:
        df = _load_portaldades_csv(dataset_path)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "No se pudo cargar el dataset de superficie de suelo %s: %s",
            dataset_path.name,
            exc,
        )
        return pd.DataFrame()

    type_col = "Dim-01:TERRITORI (type)"
    value_col = "VALUE"

    if type_col not in df.columns or value_col not in df.columns:
        return pd.DataFrame()

    df = df[df[type_col] == "Barri"].copy()
    if df.empty:
        return pd.DataFrame()

    df["anio"] = df["Dim-00:TEMPS"].apply(_extract_year_from_temps)
    df[value_col] = pd.to_numeric(df[value_col], errors="coerce")
    df = df.dropna(subset=[value_col])
    if df.empty:
        return pd.DataFrame()

    df["barrio_id"] = df["Dim-01:TERRITORI"].apply(
        lambda terr: _map_territorio_to_barrio_id(str(terr), "Barri", dim_barrios),
    )
    df = df.dropna(subset=["barrio_id"])
    if df.empty:
        return pd.DataFrame()

    df["barrio_id"] = df["barrio_id"].astype(int)
    df = df.rename(columns={value_col: "area_m2"})
    df["dataset_id"] = indicator_id
    df["source"] = "portaldades"
    return df[["barrio_id", "anio", "area_m2", "dataset_id", "source"]]


def _compute_age_metrics_from_raw(
    raw_base_dir: Path,
    dim_barrios: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calcula métricas demográficas basadas en edad desde los datos raw.

    Calcula por barrio y año:
    - pct_mayores_65: Porcentaje de población ≥65 años.
    - pct_menores_15: Porcentaje de población <15 años.
    - indice_envejecimiento: (Población 65+ / Población 0-14) * 100.
    """
    opendata_dir = Path(raw_base_dir) / "opendatabcn"

    if not opendata_dir.exists():
        logger.debug("Directorio OpenDataBCN no encontrado: %s", opendata_dir)
        return pd.DataFrame()

    pattern = "opendatabcn_pad_mdb_lloc-naix-continent_edat-q_sexe_*.csv"
    candidates = sorted(opendata_dir.glob(pattern), key=lambda path: path.stat().st_mtime)

    if not candidates:
        pattern_alt = "opendatabcn_pad_mdb_nacionalitat-contintent_edat-q_sexe_*.csv"
        candidates = sorted(
            opendata_dir.glob(pattern_alt),
            key=lambda path: path.stat().st_mtime,
        )

    if not candidates:
        logger.debug("No se encontró archivo demográfico con edad quinquenal")
        return pd.DataFrame()

    raw_path = candidates[-1]
    logger.info("Calculando métricas de edad desde: %s", raw_path.name)

    try:
        df = pd.read_csv(raw_path)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Error leyendo archivo demográfico: %s", exc)
        return pd.DataFrame()

    required_cols = {"Codi_Barri", "EDAT_Q", "Valor", "Data_Referencia"}
    if not required_cols.issubset(df.columns):
        logger.warning(
            "Archivo demográfico no tiene columnas requeridas: %s",
            required_cols,
        )
        return pd.DataFrame()

    df["Valor"] = df["Valor"].replace("..", pd.NA)
    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce")
    df = df.dropna(subset=["Valor", "Codi_Barri", "EDAT_Q"])

    df["Codi_Barri"] = pd.to_numeric(df["Codi_Barri"], errors="coerce").astype("Int64")
    df["EDAT_Q"] = pd.to_numeric(df["EDAT_Q"], errors="coerce").astype("Int64")

    df["anio"] = pd.to_datetime(df["Data_Referencia"], errors="coerce").dt.year
    df = df.dropna(subset=["anio"])
    df["anio"] = df["anio"].astype(int)

    def clasificar_grupo_edad(edad_q: int) -> str:
        edad_min = edad_q * 5
        if edad_min < 15:
            return "menores_15"
        if edad_min >= 65:
            return "mayores_65"
        return "otros"

    df["grupo_demo"] = df["EDAT_Q"].apply(clasificar_grupo_edad)

    pivot = (
        df.groupby(["Codi_Barri", "anio", "grupo_demo"])["Valor"]
        .sum()
        .reset_index()
        .pivot(index=["Codi_Barri", "anio"], columns="grupo_demo", values="Valor")
        .reset_index()
    )

    for column in ["menores_15", "mayores_65", "otros"]:
        if column not in pivot.columns:
            pivot[column] = 0

    pivot["poblacion_total"] = (
        pivot["menores_15"] + pivot["mayores_65"] + pivot["otros"]
    )

    pivot["pct_mayores_65"] = np.where(
        pivot["poblacion_total"] > 0,
        (pivot["mayores_65"] / pivot["poblacion_total"]) * 100,
        np.nan,
    )

    pivot["pct_menores_15"] = np.where(
        pivot["poblacion_total"] > 0,
        (pivot["menores_15"] / pivot["poblacion_total"]) * 100,
        np.nan,
    )

    pivot["indice_envejecimiento"] = np.where(
        pivot["menores_15"] > 0,
        (pivot["mayores_65"] / pivot["menores_15"]) * 100,
        np.nan,
    )

    result = pivot.rename(columns={"Codi_Barri": "barrio_id"})[
        ["barrio_id", "anio", "pct_mayores_65", "pct_menores_15", "indice_envejecimiento"]
    ]

    valid_barrios = set(dim_barrios["barrio_id"].unique())
    result = result[result["barrio_id"].isin(valid_barrios)]

    logger.info(
        "Métricas de edad calculadas: %s registros (%s barrios, años %s-%s)",
        len(result),
        result["barrio_id"].nunique(),
        result["anio"].min(),
        result["anio"].max(),
    )

    return result


def enrich_fact_demografia(
    fact: pd.DataFrame,
    dim_barrios: pd.DataFrame,
    raw_base_dir: Path,
    reference_time: datetime,
) -> pd.DataFrame:
    """Completa campos faltantes de ``fact_demografia`` usando fuentes auxiliares."""
    enriched = fact.copy()
    portaldades_dir = Path(raw_base_dir) / "portaldades"

    if not portaldades_dir.exists():
        logger.info(
            "Sin datos del Portal de Dades en %s; se mantiene fact_demografia original",
            portaldades_dir,
        )
        return enriched

    hogares_initial_na = enriched["hogares_totales"].isna()
    edad_initial_na = enriched["edad_media"].isna()
    inmigracion_initial_na = enriched["porc_inmigracion"].isna()
    densidad_initial_na = enriched["densidad_hab_km2"].isna()

    households_info = _compute_household_metrics(
        portaldades_dir,
        dim_barrios,
        enriched,
    )
    if not households_info.empty:
        enriched = enriched.merge(
            households_info[["barrio_id", "anio", "hogares_observados"]],
            on=["barrio_id", "anio"],
            how="left",
        )
        hogares_combined = enriched["hogares_totales"].fillna(
            enriched["hogares_observados"],
        )
        enriched["hogares_totales"] = hogares_combined.infer_objects(copy=False)
        enriched = enriched.drop(columns=["hogares_observados"])

        avg_size_series = (
            households_info.dropna(subset=["avg_size"])
            .sort_values("anio")
            .groupby("barrio_id")["avg_size"]
            .last()
        )
        city_avg_size = (
            avg_size_series.dropna().mean()
            if not avg_size_series.dropna().empty
            else np.nan
        )

        missing_mask = enriched["hogares_totales"].isna() & enriched[
            "poblacion_total"
        ].notna()
        if missing_mask.any() and (
            not avg_size_series.empty or not np.isnan(city_avg_size)
        ):
            size_values = enriched.loc[missing_mask, "barrio_id"].map(avg_size_series)
            if not np.isnan(city_avg_size):
                size_values = size_values.fillna(city_avg_size)
            nonzero_sizes = size_values.replace(0, np.nan)
            enriched.loc[missing_mask, "hogares_totales"] = (
                enriched.loc[missing_mask, "poblacion_total"] / nonzero_sizes
            )

        enriched["hogares_totales"] = enriched["hogares_totales"].apply(
            lambda value: round(value) if pd.notna(value) else value,
        )

        hogares_filled = hogares_initial_na & enriched["hogares_totales"].notna()
        if hogares_filled.any():
            enriched.loc[hogares_filled, "dataset_id"] = enriched.loc[
                hogares_filled,
                "dataset_id",
            ].apply(lambda current: _append_tag(current, "hd7u1b68qj"))
            enriched.loc[hogares_filled, "source"] = enriched.loc[
                hogares_filled,
                "source",
            ].apply(lambda current: _append_tag(current, "portaldades"))

    immigration_info = _compute_foreign_purchase_share(portaldades_dir, dim_barrios)
    if not immigration_info.empty:
        enriched = enriched.merge(
            immigration_info[["barrio_id", "anio", "porc_inmigracion"]],
            on=["barrio_id", "anio"],
            how="left",
            suffixes=("", "_enriched"),
        )
        mask_imm = (
            inmigracion_initial_na & enriched["porc_inmigracion_enriched"].notna()
        )
        if mask_imm.any():
            enriched.loc[mask_imm, "porc_inmigracion"] = enriched.loc[
                mask_imm,
                "porc_inmigracion_enriched",
            ].clip(lower=0, upper=100)
            enriched.loc[mask_imm, "dataset_id"] = enriched.loc[
                mask_imm,
                "dataset_id",
            ].apply(lambda current: _append_tag(current, "uuxbxa7onv"))
            enriched.loc[mask_imm, "source"] = enriched.loc[
                mask_imm,
                "source",
            ].apply(lambda current: _append_tag(current, "portaldades"))
        enriched = enriched.drop(columns=["porc_inmigracion_enriched"])

    building_age = _compute_building_age_proxy(portaldades_dir, dim_barrios)
    if not building_age.empty:
        building_age_latest = (
            building_age.sort_values("anio")
            .groupby("barrio_id", as_index=False)
            .last()[["barrio_id", "edad_media_proxy"]]
        )
        enriched = enriched.merge(
            building_age_latest,
            on="barrio_id",
            how="left",
        )
        mask_age = edad_initial_na & enriched["edad_media_proxy"].notna()
        if mask_age.any():
            enriched.loc[mask_age, "edad_media"] = enriched.loc[
                mask_age,
                "edad_media_proxy",
            ]
            enriched.loc[mask_age, "dataset_id"] = enriched.loc[
                mask_age,
                "dataset_id",
            ].apply(lambda current: _append_tag(current, "ydtnyd6qhm"))
            enriched.loc[mask_age, "source"] = enriched.loc[
                mask_age,
                "source",
            ].apply(lambda current: _append_tag(current, "portaldades"))
        enriched = enriched.drop(columns=["edad_media_proxy"])

    area_info = _compute_area_by_barrio(portaldades_dir, dim_barrios)
    if not area_info.empty:
        area_latest = (
            area_info.sort_values("anio")
            .groupby("barrio_id", as_index=False)
            .last()[["barrio_id", "area_m2"]]
        )
        enriched = enriched.merge(area_latest, on="barrio_id", how="left")
        mask_density = (
            densidad_initial_na
            & enriched["area_m2"].notna()
            & enriched["area_m2"].gt(0)
            & enriched["poblacion_total"].notna()
        )
        if mask_density.any():
            enriched.loc[mask_density, "densidad_hab_km2"] = (
                enriched.loc[mask_density, "poblacion_total"] * 1_000_000.0
                / enriched.loc[mask_density, "area_m2"]
            )
            enriched.loc[mask_density, "dataset_id"] = enriched.loc[
                mask_density,
                "dataset_id",
            ].apply(lambda current: _append_tag(current, "wjnmk82jd9"))
            enriched.loc[mask_density, "source"] = enriched.loc[
                mask_density,
                "source",
            ].apply(lambda current: _append_tag(current, "portaldades"))
        enriched = enriched.drop(columns=["area_m2"])

    enriched["hogares_totales"] = enriched["hogares_totales"].astype("Float64")
    enriched["porc_inmigracion"] = enriched["porc_inmigracion"].astype("Float64")
    enriched["densidad_hab_km2"] = enriched["densidad_hab_km2"].astype("Float64")
    enriched["edad_media"] = enriched["edad_media"].astype("Float64")

    age_metrics = _compute_age_metrics_from_raw(raw_base_dir, dim_barrios)

    if not age_metrics.empty:
        for column in ["pct_mayores_65", "pct_menores_15", "indice_envejecimiento"]:
            if column not in enriched.columns:
                enriched[column] = pd.NA

        mayores_initial_na = enriched["pct_mayores_65"].isna()
        menores_initial_na = enriched["pct_menores_15"].isna()
        envej_initial_na = enriched["indice_envejecimiento"].isna()

        fact_years = set(enriched["anio"].unique())
        metric_years = set(age_metrics["anio"].unique())
        overlapping_years = fact_years & metric_years

        if not overlapping_years:
            latest_year = age_metrics["anio"].max()
            logger.info(
                "No hay overlap de años entre fact_demografia (%s) y métricas de edad (%s). "
                "Propagando métricas del año %s a todos los años.",
                sorted(fact_years),
                sorted(metric_years),
                latest_year,
            )

            age_metrics_latest = age_metrics[age_metrics["anio"] == latest_year].copy()
            age_metrics_latest = age_metrics_latest.drop(columns=["anio"])

            enriched = enriched.merge(
                age_metrics_latest,
                on=["barrio_id"],
                how="left",
                suffixes=("", "_new"),
            )
        else:
            enriched = enriched.merge(
                age_metrics,
                on=["barrio_id", "anio"],
                how="left",
                suffixes=("", "_new"),
            )

        for column in ["pct_mayores_65", "pct_menores_15", "indice_envejecimiento"]:
            new_col = f"{column}_new"
            if new_col in enriched.columns:
                mask = enriched[column].isna() & enriched[new_col].notna()
                if mask.any():
                    enriched.loc[mask, column] = enriched.loc[mask, new_col]
                enriched = enriched.drop(columns=[new_col])

        enriched["pct_mayores_65"] = enriched["pct_mayores_65"].astype("Float64")
        enriched["pct_menores_15"] = enriched["pct_menores_15"].astype("Float64")
        enriched["indice_envejecimiento"] = enriched[
            "indice_envejecimiento"
        ].astype("Float64")

        mayores_filled = int(
            (mayores_initial_na & enriched["pct_mayores_65"].notna()).sum(),
        )
        menores_filled = int(
            (menores_initial_na & enriched["pct_menores_15"].notna()).sum(),
        )
        envej_filled = int(
            (envej_initial_na & enriched["indice_envejecimiento"].notna()).sum(),
        )

        if mayores_filled or menores_filled or envej_filled:
            logger.info(
                "Métricas de edad enriquecidas: mayores_65=%s, menores_15=%s, "
                "envejecimiento=%s",
                mayores_filled,
                menores_filled,
                envej_filled,
            )
    else:
        for column in ["pct_mayores_65", "pct_menores_15", "indice_envejecimiento"]:
            if column not in enriched.columns:
                enriched[column] = pd.NA

    logger.info(
        "Enriquecimiento demográfico completado: hogares=%s, edad=%s, inmigración=%s, "
        "densidad=%s",
        int((hogares_initial_na & enriched["hogares_totales"].notna()).sum()),
        int((edad_initial_na & enriched["edad_media"].notna()).sum()),
        int((inmigracion_initial_na & enriched["porc_inmigracion"].notna()).sum()),
        int((densidad_initial_na & enriched["densidad_hab_km2"].notna()).sum()),
    )
    return enriched


def prepare_demografia_ampliada(
    demographics_df: pd.DataFrame,
    dim_barrios: pd.DataFrame,
    dataset_id: str,
    reference_time: datetime,
    source: str = "opendatabcn",
) -> pd.DataFrame:
    """
    Procesa datos demográficos ampliados con edad quinquenal y nacionalidad.

    Args:
        demographics_df: DataFrame con columnas:
            - ``Data_Referencia``, ``Codi_Barri``, ``Nom_Barri``
            - ``Valor`` (población, puede ser \"..\" para no disponible)
            - ``LLOC_NAIX_CONTINENT`` (código de continente)
            - ``EDAT_Q`` (edad quinquenal: 0-20)
            - ``SEXE`` (1=hombre, 2=mujer).
        dim_barrios: DataFrame con dimensión de barrios.
        dataset_id: ID del dataset.
        reference_time: Timestamp de referencia.
        source: Fuente de datos.

    Returns:
        DataFrame con datos agregados por barrio, año, sexo, grupo de edad y nacionalidad.
    """
    df = demographics_df.copy()

    required_cols = [
        "Data_Referencia",
        "Codi_Barri",
        "Valor",
        "LLOC_NAIX_CONTINENT",
        "EDAT_Q",
        "SEXE",
    ]
    missing = set(required_cols) - set(df.columns)
    if missing:
        raise ValueError(f"DataFrame faltan columnas: {missing}")

    df["año"] = pd.to_datetime(df["Data_Referencia"], errors="coerce").dt.year
    df = df.dropna(subset=["año"])

    df["Valor"] = df["Valor"].replace("..", pd.NA)
    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce")
    df = df.dropna(subset=["Valor", "Codi_Barri"])

    df["Codi_Barri"] = pd.to_numeric(df["Codi_Barri"], errors="coerce").astype("Int64")
    df["año"] = df["año"].astype("Int64")
    df["EDAT_Q"] = pd.to_numeric(df["EDAT_Q"], errors="coerce").astype("Int64")
    df["LLOC_NAIX_CONTINENT"] = pd.to_numeric(
        df["LLOC_NAIX_CONTINENT"],
        errors="coerce",
    ).astype("Int64")

    df["grupo_edad"] = df["EDAT_Q"].apply(_edad_quinquenal_to_custom_group)

    df["nacionalidad"] = df["LLOC_NAIX_CONTINENT"].apply(
        _map_continente_to_nacionalidad,
    )

    df["sexo"] = df["SEXE"].map({1: "hombre", 2: "mujer"}).fillna("desconocido")

    df = df[df["grupo_edad"].notna()]

    aggregated = (
        df.groupby(
            ["Codi_Barri", "año", "sexo", "grupo_edad", "nacionalidad"],
            as_index=False,
        )["Valor"]
        .sum()
        .rename(
            columns={
                "Codi_Barri": "barrio_id",
                "Valor": "poblacion",
                "año": "anio",
            },
        )
    )

    aggregated = aggregated.merge(
        dim_barrios[["barrio_id", "barrio_nombre_normalizado"]],
        on="barrio_id",
        how="inner",
    )

    aggregated["dataset_id"] = dataset_id
    aggregated["source"] = source
    aggregated["etl_loaded_at"] = reference_time.isoformat()

    aggregated = aggregated.sort_values(
        ["anio", "barrio_id", "sexo", "grupo_edad", "nacionalidad"],
    ).reset_index(drop=True)

    logger.info(
        "Datos demográficos ampliados preparados: %s registros (%s barrios, %s años)",
        len(aggregated),
        aggregated["barrio_id"].nunique(),
        aggregated["anio"].nunique(),
    )

    return aggregated


__all__ = [
    "prepare_fact_demografia",
    "enrich_fact_demografia",
    "prepare_demografia_ampliada",
]


