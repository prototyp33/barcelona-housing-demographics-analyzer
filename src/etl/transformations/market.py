"""Transformaciones para tablas de hechos relacionadas con mercado (precios, renta)."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

import numpy as np
import pandas as pd

from .utils import cleaner, logger


def _normalize_pipe_tags(value: object) -> object:
    """
    Normaliza valores con separador '|' eliminando etiquetas duplicadas.

    Ejemplo:
        "FuenteA|FuenteA|FuenteB" -> "FuenteA|FuenteB"
    """
    if not isinstance(value, str) or "|" not in value:
        return value

    tokens = [token for token in value.split("|") if token]
    seen: List[str] = []
    for token in tokens:
        if token not in seen:
            seen.append(token)
    return "|".join(seen)


def _prepare_venta_prices(
    venta: pd.DataFrame,
    dim_barrios: pd.DataFrame,
    dataset_id: str,
    reference_time: datetime,
) -> pd.DataFrame:
    """Normaliza y prepara series de precios de venta a nivel de barrio y año."""
    if venta is None or venta.empty:
        return pd.DataFrame(
            columns=[
                "barrio_id",
                "anio",
                "periodo",
                "trimestre",
                "precio_m2_venta",
                "precio_mes_alquiler",
                "dataset_id",
                "source",
                "etl_loaded_at",
            ],
        )

    venta_df = venta.copy()
    value_columns = [
        column for column in venta_df.columns if isinstance(column, str) and column.isdigit()
    ]
    
    # Determine value column: first try numeric year columns, then common value column names
    value_column = None
    if value_columns:
        value_column = value_columns[0]
    else:
        # Try common value column names (case-sensitive first, then case-insensitive)
        # Include Portal de Dades specific column names
        value_column_candidates = [
            "values_value", "VALUE", "Valor", "valor", "value", 
            "precio", "Precio", "PRECIO", "precio_m2", "Precio_m2",
            "Nombre", "nombre", "NOMBRE"
        ]
        for candidate in value_column_candidates:
            if candidate in venta_df.columns:
                value_column = candidate
                break
        
        # If still not found, check for any column that might be a value column
        if value_column is None:
            excluded_cols = {
                "Barris", "barris", "año", "anio", "Any", "any", "source", "Source", 
                "dataset_id", "Codi_Barri", "codi_barri", "barrio_id", "match_key",
                "register_id", "name", "institution_id", "institution_name", "created", "modified",
                "addresses_roadtype_id", "addresses_roadtype_name", "addresses_road_id", 
                "addresses_road_name", "addresses_start_street_number", "addresses_end_street_number",
                "addresses_neighborhood_id", "addresses_neighborhood_name", "addresses_district_id",
                "addresses_district_name", "addresses_zip_code", "addresses_town", 
                "addresses_main_address", "addresses_type", "values_id", "values_attribute_id",
                "values_category", "values_attribute_name", "values_outstanding", "values_description"
            }
            # Look for numeric columns or columns with 'value' in the name
            possible_value_cols = [
                col for col in venta_df.columns 
                if col not in excluded_cols 
                and ('value' in col.lower() or venta_df[col].dtype in ['float64', 'int64'])
            ]
            if possible_value_cols:
                value_column = possible_value_cols[0]
                logger.warning(
                    "No se encontró columna de valor estándar. Usando '%s'. Columnas disponibles: %s",
                    value_column,
                    list(venta_df.columns)[:10]  # Show first 10 columns only
                )
            else:
                raise ValueError(
                    f"No se pudo identificar columna de valor en datos de venta. "
                    f"Columnas disponibles: {list(venta_df.columns)[:20]}"
                )

    if value_column not in venta_df.columns:
        raise ValueError(
            f"Columna de valor '{value_column}' no encontrada. "
            f"Columnas disponibles: {list(venta_df.columns)}"
        )

    venta_df[value_column] = (
        venta_df[value_column]
        .apply(lambda value: np.nan if str(value).strip().lower() in {"n.d.", ""} else value)
        .astype(str)
        .str.replace(".", "", regex=False)
    )
    venta_df[value_column] = (
        venta_df[value_column]
        .str.replace(",", ".", regex=False)
        .apply(lambda value: value.replace(" ", ""))
    )
    venta_df[value_column] = pd.to_numeric(venta_df[value_column], errors="coerce")

    # Convert year column - handle both 'año' and 'anio' column names
    year_col = None
    for col_name in ["año", "anio", "Any", "any", "year", "Year"]:
        if col_name in venta_df.columns:
            year_col = col_name
            break
    
    if year_col and year_col in venta_df.columns:
        # Convert to numeric first, then to nullable Int64
        venta_df["año"] = pd.to_numeric(venta_df[year_col], errors="coerce")
        # Use nullable integer type (Int64) - works in pandas >= 1.0
        venta_df["año"] = venta_df["año"].astype("Int64")
    else:
        # Try to extract year from other columns if available
        logger.warning("No se encontró columna de año. Intentando inferir desde otras columnas...")
        # Create empty año column
        venta_df["año"] = pd.NA

    # Handle neighborhood mapping - support multiple formats
    # If barrio_id already exists, use it directly
    if "barrio_id" in venta_df.columns and venta_df["barrio_id"].notna().any():
        # Already has barrio_id, skip neighborhood name mapping
        merged = venta_df.copy()
        merged["barrio_id"] = pd.to_numeric(merged["barrio_id"], errors="coerce")
    else:
        # Need to map via neighborhood name
        # Try different column names for neighborhood
        barrio_name_col = None
        for col_name in ["Barris", "barris", "barrio_nombre", "neighborhood", "addresses_neighborhood_name"]:
            if col_name in venta_df.columns:
                barrio_name_col = col_name
                break
        
        if barrio_name_col:
            venta_df["match_key"] = venta_df[barrio_name_col].apply(
                lambda x: cleaner.normalize_neighborhoods(x) if pd.notna(x) else None
            )
            
            dim_lookup = dim_barrios[["barrio_id", "barrio_nombre_normalizado"]].rename(
                columns={"barrio_nombre_normalizado": "match_key"},
            )
            
            merged = venta_df.merge(dim_lookup, on="match_key", how="left")
            
            unmatched = merged[merged["barrio_id"].isna()]
            if not unmatched.empty:
                barrios_unicos = [str(b) for b in unmatched[barrio_name_col].unique() if pd.notna(b)]
                logger.warning(
                    "%s registros de venta no pudieron asociarse a un barrio: %s",
                    len(unmatched),
                    sorted(barrios_unicos)[:10],  # Show first 10 only
                )
        else:
            # No neighborhood column found
            logger.warning(
                "No se encontró columna de barrio. Columnas disponibles: %s",
                list(venta_df.columns)[:10]
            )
            merged = venta_df.copy()
            merged["barrio_id"] = pd.NA

    source_series = (
        merged["source"]
        if "source" in merged.columns
        else pd.Series(index=merged.index, dtype="object")
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
        },
    )

    return result


def prepare_fact_precios(
    venta: pd.DataFrame,
    dim_barrios: pd.DataFrame,
    dataset_id_venta: str,
    reference_time: datetime,
    alquiler: Optional[pd.DataFrame] = None,
    dataset_id_alquiler: Optional[str] = None,
    portaldades_venta: Optional[pd.DataFrame] = None,
    portaldades_alquiler: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    Construye la tabla de hechos de precios de vivienda combinando múltiples fuentes.

    Combina datos de:
    - Open Data BCN (venta, alquiler)
    - Portal de Dades (venta, alquiler)
    """
    fact_venta_base = _prepare_venta_prices(
        venta,
        dim_barrios,
        dataset_id_venta,
        reference_time,
    )

    venta_frames: List[pd.DataFrame] = []
    if not fact_venta_base.empty:
        venta_frames.append(fact_venta_base)

    if portaldades_venta is not None and not portaldades_venta.empty:
        logger.info(
            "Agregando %s registros de venta del Portal de Dades",
            len(portaldades_venta),
        )
        venta_frames.append(portaldades_venta.copy())

    if venta_frames:
        fact_venta = pd.concat(venta_frames, ignore_index=True, sort=False)
        fact_venta = (
            fact_venta.sort_values(["anio", "barrio_id", "source"])
            .drop_duplicates(
                subset=["barrio_id", "anio", "trimestre", "dataset_id", "source"],
                keep="first",
            )
            .reset_index(drop=True)
        )
    else:
        fact_venta = pd.DataFrame()

    alquiler_frames: List[pd.DataFrame] = []
    if portaldades_alquiler is not None and not portaldades_alquiler.empty:
        logger.info(
            "Agregando %s registros de alquiler del Portal de Dades",
            len(portaldades_alquiler),
        )
        alquiler_frames.append(portaldades_alquiler.copy())

    if alquiler is not None and not alquiler.empty:
        logger.warning(
            "Datos de alquiler de Open Data BCN encontrados pero sin métrica de precio "
            "identificable. Se omiten.",
        )

    fact_frames: List[pd.DataFrame] = []
    if not fact_venta.empty:
        fact_frames.append(fact_venta)

    if alquiler_frames:
        fact_alquiler = pd.concat(alquiler_frames, ignore_index=True, sort=False)
        fact_alquiler = (
            fact_alquiler.sort_values(["anio", "barrio_id", "source"])
            .drop_duplicates(
                subset=["barrio_id", "anio", "trimestre", "dataset_id", "source"],
                keep="first",
            )
            .reset_index(drop=True)
        )
        fact_frames.append(fact_alquiler)

    if fact_frames:
        # Filtrar DataFrames realmente vacíos o sin información útil
        non_empty_frames = [
            frame
            for frame in fact_frames
            if not frame.empty and not frame.isna().all().all()
        ]
        if non_empty_frames:
            fact = pd.concat(non_empty_frames, ignore_index=True, sort=False)
        else:
            fact = pd.DataFrame()

        if not fact.empty:
            dedup_columns = [
                "barrio_id",
                "anio",
                "trimestre",
                "dataset_id",
                "source",
            ]

            rows_before = len(fact)
            fact = (
                fact.sort_values(
                    ["anio", "barrio_id", "etl_loaded_at"],
                    ascending=[True, True, False],
                )
                .drop_duplicates(subset=dedup_columns, keep="first")
                .reset_index(drop=True)
            )
            rows_after = len(fact)

            if rows_before != rows_after:
                logger.info(
                    "Deduplicación semántica: %s -> %s registros (eliminados %s "
                    "duplicados exactos)",
                    rows_before,
                    rows_after,
                    rows_before - rows_after,
                )

            # Normalizar posibles valores concatenados con '|' eliminando duplicados
            if "source" in fact.columns:
                fact["source"] = fact["source"].apply(_normalize_pipe_tags)
            if "dataset_id" in fact.columns:
                fact["dataset_id"] = fact["dataset_id"].apply(_normalize_pipe_tags)

            if fact["source"].astype(str).str.contains(r"\|").any():
                logger.debug(
                    "Se detectaron múltiples fuentes legitimamente concatenadas en 'source'.",
                )
            if fact["dataset_id"].astype(str).str.contains(r"\|").any():
                logger.debug(
                    "Se detectaron múltiples datasets legitimamente concatenados en 'dataset_id'.",
                )
    else:
        fact = pd.DataFrame()

    required_columns = [
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
    if fact.empty:
        return pd.DataFrame(columns=required_columns)

    for column in required_columns:
        if column not in fact.columns:
            if column in ["precio_m2_venta", "precio_mes_alquiler"]:
                fact[column] = pd.NA
            elif column == "periodo":
                fact[column] = fact["anio"].astype(str)
            elif column == "trimestre":
                fact[column] = pd.NA
            elif column == "etl_loaded_at":
                fact[column] = reference_time.isoformat()

    fact = fact[required_columns].sort_values(["anio", "barrio_id"]).reset_index(drop=True)
    logger.info("Tabla de hechos de precios preparada con %s registros", len(fact))
    return fact


def prepare_renta_barrio(
    renta_df: pd.DataFrame,
    dim_barrios: pd.DataFrame,
    dataset_id: str,
    reference_time: datetime,
    source: str = "opendatabcn",
    metric: str = "mean",
) -> pd.DataFrame:
    """
    Procesa datos de renta por sección censal y los agrega a nivel de barrio.

    Args:
        renta_df: DataFrame con columnas:
            - ``Any`` (año)
            - ``Codi_Barri``, ``Nom_Barri``
            - ``Seccio_Censal``
            - ``Import_Euros`` o ``Import_Renda_Bruta_€`` (renta en euros).
        dim_barrios: DataFrame con dimensión de barrios.
        dataset_id: ID del dataset.
        reference_time: Timestamp de referencia.
        source: Fuente de datos.
        metric: Métrica a usar para agregación (\"mean\", \"median\" o \"both\").

    Returns:
        DataFrame con renta agregada por barrio y año.
    """
    df = renta_df.copy()

    required_cols = ["Any", "Codi_Barri"]
    missing = set(required_cols) - set(df.columns)
    if missing:
        raise ValueError(f"DataFrame faltan columnas requeridas: {missing}")

    renta_col: Optional[str] = None
    for column in ["Import_Euros", "Import_Renda_Bruta_€", "Import"]:
        if column in df.columns:
            renta_col = column
            break

    if renta_col is None:
        raise ValueError(
            "No se encontró columna de renta (busca: Import_Euros, "
            "Import_Renda_Bruta_€, Import)",
        )

    df["Any"] = pd.to_numeric(df["Any"], errors="coerce").astype("Int64")
    df["Codi_Barri"] = pd.to_numeric(df["Codi_Barri"], errors="coerce").astype("Int64")
    df[renta_col] = pd.to_numeric(df[renta_col], errors="coerce")

    df = df.dropna(subset=["Any", "Codi_Barri", renta_col])

    if df.empty:
        logger.warning("No hay datos válidos de renta después de la limpieza")
        return pd.DataFrame()

    aggregated = (
        df.groupby(["Codi_Barri", "Any"], as_index=False)
        .agg(
            renta_promedio=(renta_col, "mean"),
            renta_mediana=(renta_col, "median"),
            renta_min=(renta_col, "min"),
            renta_max=(renta_col, "max"),
            num_secciones=(renta_col, "count"),
        )
        .reset_index(drop=True)
    )

    aggregated = aggregated.rename(columns={"Any": "anio", "Codi_Barri": "barrio_id"})

    if metric == "mean":
        aggregated["renta_euros"] = aggregated["renta_promedio"]
    elif metric == "median":
        aggregated["renta_euros"] = aggregated["renta_mediana"]
    elif metric == "both":
        aggregated["renta_euros"] = aggregated["renta_promedio"]
    else:
        logger.warning("Métrica '%s' no reconocida, usando promedio", metric)
        aggregated["renta_euros"] = aggregated["renta_promedio"]

    aggregated = aggregated.merge(
        dim_barrios[["barrio_id", "barrio_nombre_normalizado"]],
        on="barrio_id",
        how="inner",
    )

    aggregated["dataset_id"] = dataset_id
    aggregated["source"] = source
    aggregated["etl_loaded_at"] = reference_time.isoformat()

    column_order = [
        "barrio_id",
        "anio",
        "renta_euros",
        "renta_promedio",
        "renta_mediana",
        "renta_min",
        "renta_max",
        "num_secciones",
        "barrio_nombre_normalizado",
        "dataset_id",
        "source",
        "etl_loaded_at",
    ]
    available_columns = [column for column in column_order if column in aggregated.columns]
    aggregated = aggregated[available_columns]

    aggregated = aggregated.sort_values(["anio", "barrio_id"]).reset_index(drop=True)

    logger.info(
        "Datos de renta preparados: %s registros (%s barrios, %s años, métrica: %s)",
        len(aggregated),
        aggregated["barrio_id"].nunique(),
        aggregated["anio"].nunique(),
        metric,
    )

    return aggregated


def load_idescat_income(
    idescat_df: pd.DataFrame,
    dim_barrios: pd.DataFrame,
    dataset_id: str,
    reference_time: datetime,
    source: str = "idescat",
) -> pd.DataFrame:
    """
    Procesa datos de renta de IDESCAT y los mapea a nivel de barrio.

    Los datos de IDESCAT vienen con columnas:
    - ``Codi_Barri``: Código de barrio como string (ej: "01", "02")
    - ``Nom_Barri``: Nombre del barrio
    - ``anio``: Año
    - ``Import_Renda_Bruta_€``: Renta bruta en euros

    Args:
        idescat_df: DataFrame con datos de IDESCAT.
        dim_barrios: DataFrame con dimensión de barrios.
        dataset_id: ID del dataset.
        reference_time: Timestamp de referencia.
        source: Fuente de datos (default: "idescat").

    Returns:
        DataFrame con renta por barrio y año compatible con fact_renta.
    """
    df = idescat_df.copy()

    # Find the renta column (handles encoding variations)
    renta_col: Optional[str] = None
    possible_renta_cols = [
        "Import_Renda_Bruta_€",
        "Import_Renda_Bruta_â¬",  # Encoding issue
        "Import_Renda_Bruta",
        "Import_Euros",
    ]
    for col in possible_renta_cols:
        if col in df.columns:
            renta_col = col
            break
    
    # Verificar columnas requeridas
    required_cols = ["Codi_Barri", "anio"]
    missing = set(required_cols) - set(df.columns)
    if missing:
        raise ValueError(f"DataFrame faltan columnas requeridas: {missing}")
    
    if renta_col is None:
        available_cols = ", ".join(df.columns)
        raise ValueError(
            f"No se encontró columna de renta. Columnas disponibles: {available_cols}"
        )

    logger.info(f"Usando columna de renta: '{renta_col}'")

    # Limpiar y convertir tipos
    df["anio"] = pd.to_numeric(df["anio"], errors="coerce").astype("Int64")
    df[renta_col] = pd.to_numeric(
        df[renta_col], errors="coerce"
    )

    # Normalizar Codi_Barri: asegurar formato "01", "02" etc. (zero-padded)
    df["Codi_Barri"] = df["Codi_Barri"].astype(str).str.strip().str.zfill(2)

    
    # Eliminar filas con valores nulos
    df = df.dropna(subset=["Codi_Barri", "anio", renta_col])

    if df.empty:
        logger.warning("No hay datos válidos de IDESCAT después de la limpieza")
        return pd.DataFrame()

    # Mapear Codi_Barri a barrio_id usando dim_barrios
    # dim_barrios.codi_barri contiene valores como "01", "02" que coinciden con IDESCAT
    dim_mapping = dim_barrios[["barrio_id", "codi_barri", "barrio_nombre_normalizado"]].copy()
    
    # Asegurar que codi_barri es string para el merge
    dim_mapping["codi_barri"] = dim_mapping["codi_barri"].astype(str).str.strip()
    
    # Merge con dim_barrios
    merged = df.merge(
        dim_mapping,
        left_on="Codi_Barri",
        right_on="codi_barri",
        how="left"
    )

    # Verificar registros sin mapeo
    unmatched = merged[merged["barrio_id"].isna()]
    if not unmatched.empty:
        codis_unicos = sorted(unmatched["Codi_Barri"].unique())
        logger.warning(
            "%s registros de IDESCAT no pudieron asociarse a un barrio. Códigos: %s",
            len(unmatched),
            codis_unicos,
        )
        # Eliminar registros sin mapeo
        merged = merged[merged["barrio_id"].notna()]

    if merged.empty:
        logger.error("No se pudo mapear ningún registro de IDESCAT a dim_barrios")
        return pd.DataFrame()

    # Agregar por barrio y año (por si hay duplicados)
    aggregated = (
        merged.groupby(["barrio_id", "anio"], as_index=False)
        .agg(
            renta_promedio=(renta_col, "mean"),
            renta_mediana=(renta_col, "median"),
            renta_min=(renta_col, "min"),
            renta_max=(renta_col, "max"),
            num_secciones=(renta_col, "count"),
            barrio_nombre_normalizado=("barrio_nombre_normalizado", "first"),
        )
        .reset_index(drop=True)
    )

    # La columna principal renta_euros es el promedio
    aggregated["renta_euros"] = aggregated["renta_promedio"]

    # Agregar metadatos
    aggregated["dataset_id"] = dataset_id
    aggregated["source"] = source
    aggregated["etl_loaded_at"] = reference_time.isoformat()

    # Asegurar tipos correctos
    aggregated["barrio_id"] = aggregated["barrio_id"].astype(int)
    aggregated["anio"] = aggregated["anio"].astype(int)

    # Ordenar columnas según schema de fact_renta
    column_order = [
        "barrio_id",
        "anio",
        "renta_euros",
        "renta_promedio",
        "renta_mediana",
        "renta_min",
        "renta_max",
        "num_secciones",
        "barrio_nombre_normalizado",
        "dataset_id",
        "source",
        "etl_loaded_at",
    ]
    available_columns = [col for col in column_order if col in aggregated.columns]
    aggregated = aggregated[available_columns]

    # Ordenar por año y barrio
    aggregated = aggregated.sort_values(["anio", "barrio_id"]).reset_index(drop=True)

    logger.info(
        "Datos de IDESCAT preparados: %s registros (%s barrios, %s años)",
        len(aggregated),
        aggregated["barrio_id"].nunique(),
        aggregated["anio"].nunique(),
    )

    return aggregated


def prepare_fact_alquiler_mensual(
    alquiler_mensual: pd.DataFrame,
    dim_barrios: pd.DataFrame,
    dataset_id: str,
    reference_time: datetime,
    source: str = "opendatabcn",
) -> pd.DataFrame:
    """
    Prepara alquiler mensual por barrio, año y mes.

    Args:
        alquiler_mensual: DataFrame crudo con datos mensuales de alquiler.
        dim_barrios: Dimensión de barrios para validar IDs.
        dataset_id: ID del dataset (ej. ``est-lloguer-mitja-mensual``).
        reference_time: Timestamp de referencia del ETL.
        source: Fuente de datos (default: ``opendatabcn``).

    Returns:
        DataFrame con columnas: barrio_id, anio, mes, precio_mes_alquiler, dataset_id, source, etl_loaded_at.

    Raises:
        ValueError: Si no se pueden identificar columnas clave.
    """
    if alquiler_mensual is None or alquiler_mensual.empty:
        return pd.DataFrame(
            columns=[
                "barrio_id",
                "anio",
                "mes",
                "precio_mes_alquiler",
                "dataset_id",
                "source",
                "etl_loaded_at",
            ],
        )

    df = alquiler_mensual.copy()
    df.columns = [c.strip() for c in df.columns]
    lower_map = {c.lower(): c for c in df.columns}

    def pick(candidates: List[str]) -> Optional[str]:
        for cand in candidates:
            if cand in df.columns:
                return cand
            if cand.lower() in lower_map:
                return lower_map[cand.lower()]
        return None

    year_col = pick(["Any", "anio", "año", "year"])
    month_col = pick(["Mes", "mes", "month"])
    barrio_col = pick(["Codi_Barri", "codi_barri", "barrio_id"])

    value_col = None
    for cand in ["Preu", "preu", "precio", "Precio", "Valor", "valor", "value", "VALUE"]:
        if cand in df.columns:
            value_col = cand
            break
        if cand.lower() in lower_map:
            value_col = lower_map[cand.lower()]
            break

    missing = [
        name
        for name, col in [
            ("anio", year_col),
            ("mes", month_col),
            ("barrio", barrio_col),
            ("valor", value_col),
        ]
        if col is None
    ]
    if missing:
        raise ValueError(
            "No se pudieron identificar columnas requeridas para alquiler mensual. "
            f"Faltan: {missing}. Columnas disponibles: {list(df.columns)[:25]}"
        )

    df["anio"] = pd.to_numeric(df[year_col], errors="coerce").astype("Int64")
    df["mes"] = pd.to_numeric(df[month_col], errors="coerce").astype("Int64")
    df["barrio_id"] = pd.to_numeric(df[barrio_col], errors="coerce").astype("Int64")

    values = df[value_col].astype(str).str.strip()
    values = values.replace({"": np.nan, "n.d.": np.nan, "N.D.": np.nan})
    values = values.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    df["precio_mes_alquiler"] = pd.to_numeric(values, errors="coerce")

    df = df.dropna(subset=["barrio_id", "anio", "mes", "precio_mes_alquiler"]).copy()
    df = df[(df["mes"] >= 1) & (df["mes"] <= 12)].copy()

    valid_barrios = set(dim_barrios["barrio_id"].dropna().astype(int).unique())
    df = df[df["barrio_id"].astype(int).isin(valid_barrios)].copy()

    result = pd.DataFrame(
        {
            "barrio_id": df["barrio_id"].astype(int),
            "anio": df["anio"].astype(int),
            "mes": df["mes"].astype(int),
            "precio_mes_alquiler": df["precio_mes_alquiler"].astype(float),
            "dataset_id": dataset_id,
            "source": source,
            "etl_loaded_at": reference_time.isoformat(),
        },
    ).sort_values(["anio", "mes", "barrio_id"]).reset_index(drop=True)

    logger.info(
        "Alquiler mensual preparado: %s registros (%s barrios, años %s-%s)",
        len(result),
        result["barrio_id"].nunique() if not result.empty else 0,
        result["anio"].min() if not result.empty else None,
        result["anio"].max() if not result.empty else None,
    )

    return result


__all__ = [
    "prepare_fact_precios",
    "prepare_renta_barrio",
    "load_idescat_income",
    "prepare_fact_alquiler_mensual",
]

