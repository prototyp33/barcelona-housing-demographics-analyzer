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
    # Normalización agresiva: minúsculas y sin espacios
    df.columns = [c.strip().lower() for c in df.columns]
    
    # Manejar caso especial: si hay tanto "data_referencia" como "año"
    # Si "año" ya es numérico y tiene valores, usarlo directamente
    # Si no, extraer de "data_referencia"
    if "data_referencia" in df.columns and "año" in df.columns:
        # Verificar si "año" es numérico y tiene valores válidos
        año_is_numeric = pd.api.types.is_numeric_dtype(df["año"])
        año_has_values = not df["año"].isna().all()
        
        if año_is_numeric and año_has_values:
            # "año" ya es numérico y tiene valores, eliminar "data_referencia"
            df = df.drop(columns=["data_referencia"])
        else:
            # Extraer año de Data_Referencia y reemplazar "año"
            try:
                df["año"] = pd.to_datetime(df["data_referencia"], errors="coerce").dt.year
                df = df.drop(columns=["data_referencia"], errors="ignore")
            except Exception:
                # Si falla, mantener "año" original
                df = df.drop(columns=["data_referencia"], errors="ignore")
    
    rename_map = {
        "any": "año", "data_referencia": "año", "anio": "año",
        "codi_barri": "Codi_Barri", "barrio_id": "Codi_Barri",
        "sexe": "SEXE", "sexo": "SEXE", "valor": "Valor"
    }
    for col_old, col_new in rename_map.items():
        if col_old in df.columns and col_new not in df.columns:
            df = df.rename(columns={col_old: col_new})

    # Eliminar columnas duplicadas (especialmente 'año' si existía Data_Referencia y Any)
    df = df.loc[:, ~df.columns.duplicated()]

    # Asegurar que tenemos lo mínimo
    for column in ("Valor", "año", "Codi_Barri", "SEXE"):
        if column not in df.columns:
            raise ValueError(f"Demographics dataframe missing column '{column}'. Columns found: {list(df.columns)}")

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
    fact["pct_mayores_65"] = pd.NA
    fact["pct_menores_15"] = pd.NA
    fact["indice_envejecimiento"] = pd.NA
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
            "pct_mayores_65",
            "pct_menores_15",
            "indice_envejecimiento",
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


def _compute_demographic_stats_from_raw(
    raw_base_dir: Path,
    dim_barrios: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calcula métricas demográficas detalladas basadas en edad y nacionalidad desde datos raw.

    Calcula por barrio y año:
    - pct_mayores_65: Porcentaje de población ≥65 años.
    - pct_menores_15: Porcentaje de población <15 años.
    - indice_envejecimiento: (Población 65+ / Población 0-14) * 100.
    - edad_media: Edad media estimada de la población (usando puntos medios de grupos).
    - porc_inmigracion: Porcentaje de población con nacionalidad extranjera (continente != 1).
    """
    opendata_dir = Path(raw_base_dir) / "opendatabcn"

    if not opendata_dir.exists():
        logger.debug("Directorio OpenDataBCN no encontrado: %s", opendata_dir)
        return pd.DataFrame()

    # Priorizamos el dataset de nacionalidad que tiene tanto edad como origen
    pattern = "opendatabcn_pad_mdb_nacionalitat-contintent_edat-q_sexe_*.csv"
    candidates = sorted(opendata_dir.glob(pattern), key=lambda path: path.stat().st_mtime)

    if not candidates:
        pattern_alt = "opendatabcn_pad_mdb_lloc-naix-continent_edat-q_sexe_*.csv"
        candidates = sorted(
            opendata_dir.glob(pattern_alt),
            key=lambda path: path.stat().st_mtime,
        )

    if not candidates:
        logger.debug("No se encontró archivo demográfico con edad quinquenal")
        return pd.DataFrame()

    raw_path = candidates[-1]
    logger.info("Calculando métricas demográficas desde: %s", raw_path.name)

    try:
        df = pd.read_csv(raw_path)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Error leyendo archivo demográfico: %s", exc)
        return pd.DataFrame()

    # Buscar columna de continente/nacionalidad
    orig_col = None
    for col in ["NACIONALITAT_CONTINENT", "LLOC_NAIX_CONTINENT"]:
        if col in df.columns:
            orig_col = col
            break

    required_cols = {"Codi_Barri", "EDAT_Q", "Valor", "Data_Referencia"}
    if not required_cols.issubset(df.columns) or orig_col is None:
        logger.warning(
            "Archivo demográfico no tiene columnas requeridas: %s o falta columna de origen",
            required_cols,
        )
        return pd.DataFrame()

    df["Valor"] = df["Valor"].replace("..", pd.NA)
    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce")
    df = df.dropna(subset=["Valor", "Codi_Barri", "EDAT_Q"])

    df["Codi_Barri"] = pd.to_numeric(df["Codi_Barri"], errors="coerce").astype("Int64")
    df["EDAT_Q"] = pd.to_numeric(df["EDAT_Q"], errors="coerce").astype("Int64")
    df[orig_col] = pd.to_numeric(df[orig_col], errors="coerce").astype("Int64")

    df["anio"] = pd.to_datetime(df["Data_Referencia"], errors="coerce").dt.year
    df = df.dropna(subset=["anio"])
    df["anio"] = df["anio"].astype(int)

    # Definir pesos para edad media (puntos medios)
    def age_midpoint(q):
        if q < 20:
            return (q * 5) + 2.5
        return 102.5  # 100+

    # Identificar el grupo mayoritario (Doméstico/España) de forma dinámica para evitar errores de codificación
    group_totals = df.groupby(orig_col)["Valor"].sum()
    domestic_group = group_totals.idxmax()
    logger.debug("Identificado grupo doméstico mayoritario: %s (Valor=%s)", domestic_group, group_totals.max())

    df["edad_weight"] = df["EDAT_Q"].apply(age_midpoint)
    df["total_years"] = df["Valor"] * df["edad_weight"]
    df["es_extranjero"] = (df[orig_col] != domestic_group).astype(int)
    df["valor_extranjero"] = df["Valor"] * df["es_extranjero"]

    def clasificar_grupo_edad(edad_q: int) -> str:
        edad_min = edad_q * 5
        if edad_min < 15:
            return "menores_15"
        if edad_min >= 65:
            return "mayores_65"
        return "otros"

    df["grupo_demo"] = df["EDAT_Q"].apply(clasificar_grupo_edad)

    # Agregación completa
    stats = (
        df.groupby(["Codi_Barri", "anio"])
        .agg(
            poblacion_total=("Valor", "sum"),
            poblacion_extranjera=("valor_extranjero", "sum"),
            suma_edades=("total_years", "sum"),
        )
        .reset_index()
    )

    # Agregación por grupos de edad para índices
    age_groups = (
        df.groupby(["Codi_Barri", "anio", "grupo_demo"])["Valor"]
        .sum()
        .reset_index()
        .pivot(index=["Codi_Barri", "anio"], columns="grupo_demo", values="Valor")
        .reset_index()
        .fillna(0)
    )

    result_df = stats.merge(age_groups, on=["Codi_Barri", "anio"], how="left")

    # Cálculos finales
    result_df["pct_mayores_65"] = np.where(
        result_df["poblacion_total"] > 0,
        (result_df["mayores_65"] / result_df["poblacion_total"]) * 100.0,
        np.nan,
    )
    result_df["pct_menores_15"] = np.where(
        result_df["poblacion_total"] > 0,
        (result_df["menores_15"] / result_df["poblacion_total"]) * 100.0,
        np.nan,
    )
    result_df["indice_envejecimiento"] = np.where(
        result_df["menores_15"] > 0,
        (result_df["mayores_65"] / result_df["menores_15"]) * 100.0,
        np.nan,
    )
    result_df["edad_media"] = np.where(
        result_df["poblacion_total"] > 0,
        result_df["suma_edades"] / result_df["poblacion_total"],
        np.nan,
    )
    result_df["porc_inmigracion"] = np.where(
        result_df["poblacion_total"] > 0,
        (result_df["poblacion_extranjera"] / result_df["poblacion_total"]) * 100.0,
        np.nan,
    )

    result = result_df.rename(columns={"Codi_Barri": "barrio_id"})[
        [
            "barrio_id", "anio", "pct_mayores_65", "pct_menores_15", 
            "indice_envejecimiento", "edad_media", "porc_inmigracion"
        ]
    ]

    valid_barrios = set(dim_barrios["barrio_id"].unique())
    result = result[result["barrio_id"].isin(valid_barrios)]

    logger.info(
        "Métricas demográficas completas calculadas: %s registros (%s barrios)",
        len(result),
        result["barrio_id"].nunique(),
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

    # 1. Obtener métricas detalladas desde OpenData BCN (Edad media, Inmigración actual, etc.)
    demographic_stats = _compute_demographic_stats_from_raw(raw_base_dir, dim_barrios)
    
    if not demographic_stats.empty:
        # Marcamos métricas que intentaremos llenar desde aquí
        target_cols = ["edad_media", "porc_inmigracion", "pct_mayores_65", "pct_menores_15", "indice_envejecimiento"]
        
        # Guardamos estados iniciales para logging
        initial_nas = {col: enriched[col].isna() for col in target_cols}
        
        # Merge inteligente: si el año coincide, genial. Si no, propagamos el último.
        fact_years = set(enriched["anio"].unique())
        stats_years = set(demographic_stats["anio"].unique())
        overlapping_years = fact_years & stats_years
        
        if not overlapping_years and not stats_years:
             pass 
        elif not overlapping_years:
            latest_year = demographic_stats["anio"].max()
            logger.info("Propagando métricas demográficas desde el año %s", latest_year)
            stats_latest = demographic_stats[demographic_stats["anio"] == latest_year].drop(columns=["anio"])
            enriched = enriched.merge(stats_latest, on="barrio_id", how="left", suffixes=("", "_raw"))
        else:
            enriched = enriched.merge(demographic_stats, on=["barrio_id", "anio"], how="left", suffixes=("", "_raw"))
            
        # Llenar huecos con los datos de los CSVs raw
        for col in target_cols:
            raw_col = f"{col}_raw"
            if raw_col in enriched.columns:
                mask = enriched[col].isna() & enriched[raw_col].notna()
                if mask.any():
                    enriched.loc[mask, col] = enriched.loc[mask, raw_col]
                    # Actualizar metadatos
                    enriched.loc[mask, "source"] = enriched.loc[mask, "source"].apply(lambda s: _append_tag(s, "opendatabcn_raw"))
                enriched = enriched.drop(columns=[raw_col])

    # 2. Hogares y Tamaño de Hogar (Portal de Dades)
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

        # Para años sin datos de hogares (como 2025), estimar usando el último avg_size conocido
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

    # 3. Inmigración / Compras Extranjeras (Fallback si no hay datos demográficos directos)
    immigration_info = _compute_foreign_purchase_share(portaldades_dir, dim_barrios)
    if not immigration_info.empty:
        enriched = enriched.merge(
            immigration_info[["barrio_id", "anio", "porc_inmigracion"]],
            on=["barrio_id", "anio"],
            how="left",
            suffixes=("", "_enriched"),
        )
        mask_imm = (
            enriched["porc_inmigracion"].isna() & enriched["porc_inmigracion_enriched"].notna()
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

    # 4. Edad Media de Edificaciones (Solo como último recurso si no hay edad media demográfica)
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
        mask_age = enriched["edad_media"].isna() & enriched["edad_media_proxy"].notna()
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

    # 5. Superficie y Densidad (Usar última área conocida)
    area_info = _compute_area_by_barrio(portaldades_dir, dim_barrios)
    if not area_info.empty:
        area_latest = (
            area_info.sort_values("anio")
            .groupby("barrio_id", as_index=False)
            .last()[["barrio_id", "area_m2"]]
        )
        enriched = enriched.merge(area_latest, on="barrio_id", how="left")
        mask_density = (
            enriched["densidad_hab_km2"].isna()
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

    logger.info(
        "Enriquecimiento demográfico completado: hogares=%s, edad=%s, inmigración=%s, densidad=%s",
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


def populate_fact_demografia_from_ampliada(
    fact_demografia_ampliada: pd.DataFrame,
    dim_barrios: pd.DataFrame,
    reference_time: datetime,
) -> pd.DataFrame:
    """
    Pobla fact_demografia desde fact_demografia_ampliada agregando datos.
    
    Agrega los datos desagregados de fact_demografia_ampliada para crear
    registros agregados en fact_demografia con las métricas principales.
    
    Args:
        fact_demografia_ampliada: DataFrame con datos desagregados por sexo, edad y nacionalidad
        dim_barrios: DataFrame con dimensión de barrios
        reference_time: Timestamp de referencia para etl_loaded_at
        
    Returns:
        DataFrame con datos agregados para fact_demografia
    """
    if fact_demografia_ampliada.empty:
        logger.warning("fact_demografia_ampliada está vacía, no se puede poblar fact_demografia")
        return pd.DataFrame()
    
    df_ampliada = fact_demografia_ampliada.copy()
    
    # Agregar por barrio y año
    aggregated = df_ampliada.groupby(['barrio_id', 'anio']).agg({
        'poblacion': 'sum',
        'dataset_id': 'first',
        'source': 'first',
    }).reset_index()
    
    # Calcular poblacion_hombres y poblacion_mujeres
    hombres = df_ampliada[df_ampliada['sexo'] == 'hombre'].groupby(['barrio_id', 'anio'])['poblacion'].sum().reset_index()
    hombres.columns = ['barrio_id', 'anio', 'poblacion_hombres']
    
    mujeres = df_ampliada[df_ampliada['sexo'] == 'mujer'].groupby(['barrio_id', 'anio'])['poblacion'].sum().reset_index()
    mujeres.columns = ['barrio_id', 'anio', 'poblacion_mujeres']
    
    # Calcular pct_mayores_65
    mayores_65 = df_ampliada[df_ampliada['grupo_edad'] == '65+'].groupby(['barrio_id', 'anio'])['poblacion'].sum().reset_index()
    mayores_65.columns = ['barrio_id', 'anio', 'poblacion_mayores_65']
    
    # Merge todos los datos
    fact = aggregated.merge(hombres, on=['barrio_id', 'anio'], how='left')
    fact = fact.merge(mujeres, on=['barrio_id', 'anio'], how='left')
    fact = fact.merge(mayores_65, on=['barrio_id', 'anio'], how='left')
    
    # Renombrar y calcular campos
    fact = fact.rename(columns={'poblacion': 'poblacion_total'})
    fact['poblacion_hombres'] = fact['poblacion_hombres'].fillna(0).astype(int)
    fact['poblacion_mujeres'] = fact['poblacion_mujeres'].fillna(0).astype(int)
    fact['poblacion_total'] = fact['poblacion_total'].fillna(0).astype(int)
    
    # Calcular porcentajes
    fact['pct_mayores_65'] = (
        fact.apply(
            lambda row: (row['poblacion_mayores_65'] * 100.0 / row['poblacion_total'])
            if row['poblacion_total'] > 0 and pd.notna(row['poblacion_mayores_65'])
            else None,
            axis=1
        )
    )
    
    # Campos que no podemos calcular desde fact_demografia_ampliada
    fact['hogares_totales'] = None
    fact['edad_media'] = None
    fact['porc_inmigracion'] = None
    fact['densidad_hab_km2'] = None
    fact['pct_menores_15'] = None
    fact['indice_envejecimiento'] = None
    fact['etl_loaded_at'] = reference_time.isoformat()
    
    # Eliminar columna temporal
    fact = fact.drop(columns=['poblacion_mayores_65'], errors='ignore')
    
    # Seleccionar columnas en el orden correcto
    fact = fact[[
        'barrio_id', 'anio', 'poblacion_total', 'poblacion_hombres', 'poblacion_mujeres',
        'hogares_totales', 'edad_media', 'porc_inmigracion', 'densidad_hab_km2',
        'pct_mayores_65', 'pct_menores_15', 'indice_envejecimiento',
        'dataset_id', 'source', 'etl_loaded_at'
    ]]
    
    logger.info(
        "fact_demografia poblada desde ampliada: %s registros (años %s-%s)",
        len(fact),
        fact["anio"].min() if not fact.empty else None,
        fact["anio"].max() if not fact.empty else None,
    )
    
    return fact


__all__ = [
    "prepare_fact_demografia",
    "enrich_fact_demografia",
    "prepare_demografia_ampliada",
    "populate_fact_demografia_from_ampliada",
]


