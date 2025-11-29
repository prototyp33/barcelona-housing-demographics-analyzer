"""Data cleaning, normalization and validation utilities for the ETL pipeline."""

from __future__ import annotations

import json
import logging
import math
import re
import unicodedata
from datetime import datetime
from difflib import get_close_matches
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from src.transform.cleaners import HousingCleaner

logger = logging.getLogger(__name__)

# Initialize cleaner
cleaner = HousingCleaner()


def _parse_household_size(label: Optional[str]) -> Optional[float]:
    """Convierte el descriptor de tamaño de hogar en un valor numérico aproximado."""

    if label is None:
        return None
    normalized = str(label).strip().lower()
    if not normalized or normalized in {"sense dades", "no consta"}:
        return None

    if normalized.startswith(">"):
        digits = re.findall(r"\d+", normalized)
        if digits:
            return max(float(digits[0]) + 1.0, float(digits[0]) + 0.5)
        return None

    if "o més" in normalized or "mes de" in normalized:
        digits = re.findall(r"\d+", normalized)
        if digits:
            base = float(digits[0])
            return max(base, base + 1.0)
        return None

    digits = re.findall(r"\d+", normalized)
    if digits:
        return float(digits[0])

    return None


def _load_geojson_for_barrios(geojson_path: Optional[Path]) -> Optional[Dict[int, str]]:
    """
    Carga un archivo GeoJSON y crea un diccionario que mapea barrio_id a geometría JSON.
    
    Args:
        geojson_path: Ruta al archivo GeoJSON
    
    Returns:
        Diccionario {barrio_id: geometry_json_string} o None si no se puede cargar
    """
    if geojson_path is None or not geojson_path.exists():
        return None
    
    try:
        with open(geojson_path, 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)
        
        if geojson_data.get('type') != 'FeatureCollection':
            logger.warning(f"GeoJSON no es FeatureCollection: {geojson_path}")
            return None
        
        geometry_map = {}
        features = geojson_data.get('features', [])
        
        for feature in features:
            if feature.get('type') != 'Feature':
                continue
            
            properties = feature.get('properties', {})
            geometry = feature.get('geometry')
            
            # Intentar obtener barrio_id de diferentes formas
            barrio_id = None
            if 'codi_barri' in properties:
                barrio_id = properties.get('codi_barri')
            elif 'Codi_Barri' in properties:
                barrio_id = properties.get('Codi_Barri')
            
            if barrio_id is None or geometry is None:
                continue
            
            # Convertir barrio_id a int
            try:
                barrio_id = int(barrio_id)
            except (ValueError, TypeError):
                continue
            
            # Convertir geometría a JSON string
            geometry_json_str = json.dumps(geometry, ensure_ascii=False)
            geometry_map[barrio_id] = geometry_json_str
        
        logger.info(
            "GeoJSON cargado: %s features mapeados a barrios",
            len(geometry_map)
        )
        return geometry_map
        
    except Exception as e:
        logger.warning(f"Error cargando GeoJSON {geojson_path}: {e}")
        return None


def prepare_dim_barrios(
    demographics: pd.DataFrame,
    dataset_id: str,
    reference_time: datetime,
    geojson_path: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Build the barrios dimension from the raw demographics dataframe.
    
    Args:
        demographics: DataFrame con datos demográficos
        dataset_id: ID del dataset
        reference_time: Timestamp de referencia
        geojson_path: Ruta opcional al archivo GeoJSON con geometrías de barrios
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
            }
        )
    )

    dim["barrio_id"] = pd.to_numeric(dim["barrio_id"], errors="coerce").astype("Int64")
    dim["distrito_id"] = pd.to_numeric(dim["distrito_id"], errors="coerce").astype("Int64")
    dim = dim.dropna(subset=["barrio_id"])

    # Fix encoding issues in barrio names
    dim["barrio_nombre"] = dim["barrio_nombre"].apply(cleaner._fix_mojibake)
    dim["distrito_nombre"] = dim["distrito_nombre"].apply(cleaner._fix_mojibake)
    
    dim["barrio_nombre_normalizado"] = dim["barrio_nombre"].apply(cleaner.normalize_neighborhoods)
    dim["codi_barri"] = dim["barrio_id"].astype(str).str.zfill(2)
    dim["codi_districte"] = dim["distrito_id"].astype(str).str.zfill(2)
    dim["municipio"] = "Barcelona"
    dim["ambito"] = "barri"
    dim["geometry_json"] = None
    dim["source_dataset"] = dataset_id
    timestamp = reference_time.isoformat()
    dim["etl_created_at"] = timestamp
    dim["etl_updated_at"] = timestamp

    # Cargar geometrías del GeoJSON si está disponible
    if geojson_path:
        geometry_map = _load_geojson_for_barrios(geojson_path)
        if geometry_map:
            # Mapear geometrías a barrios
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
        logger.debug("No se proporcionó ruta a GeoJSON, geometry_json permanece como None")

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

    # Use normalize_neighborhoods directly as it handles cleaning patterns too
    venta_df["match_key"] = venta_df["Barris"].apply(cleaner.normalize_neighborhoods)

    dim_lookup = dim_barrios[["barrio_id", "barrio_nombre_normalizado"]].rename(
        columns={"barrio_nombre_normalizado": "match_key"}
    )

    merged = venta_df.merge(dim_lookup, on="match_key", how="left")

    unmatched = merged[merged["barrio_id"].isna()]
    if not unmatched.empty:
        # Convertir a string para evitar errores de comparación con NaN/float
        barrios_unicos = [str(b) for b in unmatched["Barris"].unique() if pd.notna(b)]
        logger.warning(
            "%s registros de venta no pudieron asociarse a un barrio: %s",
            len(unmatched),
            sorted(barrios_unicos),
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
    portaldades_venta: Optional[pd.DataFrame] = None,
    portaldades_alquiler: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    Build the housing prices fact table from multiple sources.
    
    Combina datos de:
    - Open Data BCN (venta, alquiler)
    - Portal de Dades (venta, alquiler)
    """
    fact_venta_base = _prepare_venta_prices(
        venta, dim_barrios, dataset_id_venta, reference_time
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
            "Datos de alquiler de Open Data BCN encontrados pero sin métrica de precio identificable. Se omiten."
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
        # Filtrar DataFrames vacíos antes de concatenar para evitar FutureWarning
        non_empty_frames = [f for f in fact_frames if not f.empty]
        if non_empty_frames:
            fact = pd.concat(non_empty_frames, ignore_index=True, sort=False)
        else:
            fact = pd.DataFrame()
        
        if not fact.empty:
            # =================================================================
            # DEDUPLICACIÓN SEMÁNTICA (Preserva granularidad multi-fuente)
            # =================================================================
            # Granularidad objetivo: (barrio_id, anio, trimestre, dataset_id, source)
            # 
            # Esto permite que coexistan múltiples registros para el mismo
            # barrio-año-trimestre cuando provienen de diferentes datasets o fuentes.
            # Ejemplo: El Raval 2023 puede tener 11 filas, una por cada indicador
            # de precio del Portal de Dades.
            #
            # Solo eliminamos duplicados EXACTOS (mismo valor, misma fuente, misma fecha)
            # =================================================================
            
            dedup_columns = [
                "barrio_id",
                "anio",
                "trimestre",
                "dataset_id",
                "source",
            ]
            
            rows_before = len(fact)
            fact = (
                fact.sort_values(["anio", "barrio_id", "etl_loaded_at"], ascending=[True, True, False])
                .drop_duplicates(subset=dedup_columns, keep="first")
                .reset_index(drop=True)
            )
            rows_after = len(fact)
            
            if rows_before != rows_after:
                logger.info(
                    "Deduplicación semántica: %s -> %s registros (eliminados %s duplicados exactos)",
                    rows_before,
                    rows_after,
                    rows_before - rows_after,
                )
            
            # Validación de integridad: verificar que no hay pipes en source/dataset_id
            # (esto indicaría que el anti-patrón de concatenación sigue activo)
            if fact["source"].astype(str).str.contains(r"\|").any():
                logger.error(
                    "⚠️ ALERTA: Se detectaron pipes '|' en columna 'source'. "
                    "Esto indica un problema de agregación upstream."
                )
            if fact["dataset_id"].astype(str).str.contains(r"\|").any():
                logger.error(
                    "⚠️ ALERTA: Se detectaron pipes '|' en columna 'dataset_id'. "
                    "Esto indica un problema de agregación upstream."
                )
    else:
        fact = pd.DataFrame()

    # Asegurar que todas las columnas requeridas estén presentes
    required_columns = [
        'barrio_id', 'anio', 'periodo', 'trimestre',
        'precio_m2_venta', 'precio_mes_alquiler',
        'dataset_id', 'source', 'etl_loaded_at'
    ]
    if fact.empty:
        return pd.DataFrame(columns=required_columns)

    for col in required_columns:
        if col not in fact.columns:
            if col in ["precio_m2_venta", "precio_mes_alquiler"]:
                fact[col] = pd.NA
            elif col == "periodo":
                fact[col] = fact["anio"].astype(str)
            elif col == "trimestre":
                fact[col] = pd.NA
            elif col == "etl_loaded_at":
                fact[col] = reference_time.isoformat()

    fact = fact[required_columns].sort_values(["anio", "barrio_id"]).reset_index(drop=True)
    logger.info("Tabla de hechos de precios preparada con %s registros", len(fact))
    return fact


def _load_portaldades_csv(filepath: Path) -> pd.DataFrame:
    """Carga un archivo CSV del Portal de Dades con detección automática de encoding."""
    try:
        import chardet
    except ImportError:
        logger.warning("Module 'chardet' not found. Falling back to 'utf-8'. Install it with 'pip install chardet'.")
        return pd.read_csv(filepath, encoding="utf-8", low_memory=False)
    
    # Detectar encoding
    with open(filepath, 'rb') as f:
        raw_data = f.read(10000)
        detected = chardet.detect(raw_data)
        encoding = detected.get('encoding', 'utf-8')
    
    # Intentar leer con diferentes encodings
    encodings_to_try = [encoding, 'utf-8', 'latin-1', 'iso-8859-1']
    for enc in encodings_to_try:
        try:
            return pd.read_csv(filepath, encoding=enc, low_memory=False)
        except (UnicodeDecodeError, pd.errors.ParserError):
            continue
    
    raise ValueError(f"No se pudo leer el archivo {filepath} con ningún encoding")


def _append_tag(current: Optional[str], new_tag: str) -> str:
    """
    Agrega una etiqueta de forma idempotente a una cadena delimitada por '|'.
    """
    if not new_tag:
        return "" if current is None or pd.isna(current) else str(current)

    tags: List[str] = []
    if current is not None and not pd.isna(current):
        tags = [token for token in str(current).split("|") if token]
    if new_tag not in tags:
        tags.append(new_tag)
    return "|".join(tags)


def _find_portaldades_file(portaldades_dir: Path, indicator_id: str) -> Optional[Path]:
    """
    Devuelve la última versión disponible de un indicador del Portal de Dades.
    """
    pattern = f"portaldades_*_{indicator_id}.csv"
    candidates = sorted(portaldades_dir.glob(pattern), key=lambda p: p.stat().st_mtime)
    return candidates[-1] if candidates else None


def _extract_year_from_temps(temps_str: str) -> Optional[int]:
    """Extrae el año de una cadena de tiempo ISO del Portal de Dades."""
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(temps_str.replace('Z', '+00:00'))
        return dt.year
    except (ValueError, AttributeError, TypeError):
        return None


def _map_territorio_to_barrio_id(
    territorio: str,
    territorio_type: str,
    dim_barrios: pd.DataFrame
) -> Optional[int]:
    """
    Mapea un nombre de territorio del Portal de Dades a un barrio_id.
    
    Args:
        territorio: Nombre del territorio (barrio, distrito, municipio)
        territorio_type: Tipo de territorio ("Barri", "Districte", "Municipi")
        dim_barrios: DataFrame con la dimensión de barrios
    
    Returns:
        barrio_id si se encuentra, None si no
    """
    if territorio_type == "Barri":
        territorio_normalizado = cleaner.normalize_neighborhoods(territorio)

        alias_target = cleaner.barrio_alias_overrides.get(territorio_normalizado)
        if alias_target:
            match = dim_barrios[
                dim_barrios["barrio_nombre_normalizado"] == alias_target
            ]
            if not match.empty:
                return int(match.iloc[0]["barrio_id"])

        # 1. Coincidencia exacta normalizada
        match = dim_barrios[
            dim_barrios["barrio_nombre_normalizado"] == territorio_normalizado
        ]
        if not match.empty:
            return int(match.iloc[0]["barrio_id"])

        # 2. Coincidencia exacta sin normalizar (case-insensitive)
        match = dim_barrios[
            dim_barrios["barrio_nombre"]
            .str.strip()
            .str.lower()
            == territorio.strip().lower()
        ]
        if not match.empty:
            return int(match.iloc[0]["barrio_id"])

        # 3. Coincidencia parcial (contiene)
        match = dim_barrios[
            dim_barrios["barrio_nombre"].str.contains(
                territorio, case=False, na=False, regex=False
            )
        ]
        if not match.empty:
            match = match.sort_values(
                "barrio_nombre", key=lambda x: x.str.len()
            )
            return int(match.iloc[0]["barrio_id"])

        # 4. Coincidencia parcial con texto normalizado
        territorio_parts = territorio_normalizado.split()
        if len(territorio_parts) > 1:
            for part in territorio_parts:
                if len(part) > 3:
                    match = dim_barrios[
                        dim_barrios["barrio_nombre_normalizado"].str.contains(
                            part, na=False, regex=False
                        )
                    ]
                    if not match.empty:
                        match = match.sort_values(
                            "barrio_nombre", key=lambda x: x.str.len()
                        )
                        return int(match.iloc[0]["barrio_id"])

        # 5. Búsqueda aproximada (fuzzy)
        candidates = (
            dim_barrios["barrio_nombre_normalizado"].dropna().unique().tolist()
        )
        # Usamos un cutoff de 0.8 para permitir variaciones leves pero evitar falsos positivos
        close = get_close_matches(
            territorio_normalizado, candidates, n=1, cutoff=0.8
        )
        if close:
            match = dim_barrios[
                dim_barrios["barrio_nombre_normalizado"] == close[0]
            ]
            if not match.empty:
                logger.info(f"Fuzzy match: '{territorio}' -> '{match.iloc[0]['barrio_nombre']}'")
                return int(match.iloc[0]["barrio_id"])

        # Si llegamos aquí, no se pudo mapear
        logger.warning(f"No se pudo mapear el territorio '{territorio}' (normalizado: '{territorio_normalizado}') a ningún barrio conocido.")
        return None

    elif territorio_type == "Districte":
        # No asignamos distritos directamente a un solo barrio para evitar sesgos.
        return None

    # Para municipio u otros niveles agregados, no mapeamos.
    return None


def prepare_portaldades_precios(
    portaldades_dir: Path,
    dim_barrios: pd.DataFrame,
    reference_time: datetime,
    metadata_file: Optional[Path] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Procesa archivos de precios del Portal de Dades y los prepara para fact_precios.
    
    Args:
        portaldades_dir: Directorio donde están los archivos CSV del Portal de Dades
        dim_barrios: DataFrame con la dimensión de barrios
        reference_time: Timestamp de referencia para ETL
        metadata_file: Archivo CSV con metadatos de indicadores (opcional)
    
    Returns:
        Tupla con (DataFrame de venta, DataFrame de alquiler)
    """
    import json
    from pathlib import Path
    
    venta_records = []
    alquiler_records = []
    
    # Cargar metadatos si está disponible
    indicadores_metadata = {}
    if metadata_file and metadata_file.exists():
        try:
            metadata_df = pd.read_csv(metadata_file)
            for _, row in metadata_df.iterrows():
                indicadores_metadata[row['id_indicador']] = {
                    'nombre': row.get('nombre', ''),
                    'categoria': row.get('categoria', 'estadístiques')
                }
        except Exception as e:
            logger.warning(f"Error cargando metadatos: {e}")
    
    # Identificar archivos de precios
    csv_files = list(portaldades_dir.glob("portaldades_*.csv"))
    
    # IDs de indicadores de precios identificados
    venta_ids = {
        'bxtvnxvukh',  # Preu mitjà per superfície (€/m²) dels habitatges transmesos per compravenda
        'hostlmjrdo',  # Preu unitari mitjà (€) dels habitatges transmesos per compravenda
        'mrslyp5pcq',  # Preu mitjà per superfície (€/m²) dels habitatges transmesos per compravenda per tipus de propietat
        'idjhkx1ruj',  # Preu mitjà per superfície (€/m²) dels habitatges transmesos per compravenda per any de construcció
        'u25rr7oxh6',  # Preu mitjà per superfície (€/m²) de les compravendes d'habitatge registrades
        'cq4causxvu',  # Preu mitjà per superfície (€/m²) de les compravendes d'habitatge registrades per estat
        'la6s9fp57r',  # Preu mitjà (€) de les compravendes d'habitatge registrades
        '9ap8lewvtt',  # Preu mitjà (€) de les compravendes d'habitatge registrades per estat
        'bhl3ulphi5',  # Preu mitjà per superfície (€/m²) d'oferta d'habitatges de segona mà en venda
    }
    
    alquiler_ids = {
        'b37xv8wcjh',  # Preu mitjà (€) del lloguer d'habitatges
        '5ibudgqbrb',  # Preu mitjà per superfície (€/m²) del lloguer d'habitatges
        '4waxpjj3uo',  # Preu (€) de lloguer dels béns immobles arrendats per a habitatge habitual
        'jc3tvqfyum',  # Preu de lloguer per superfície (€/m²) dels béns immobles arrendats
    }
    
    logger.info(f"Procesando {len(csv_files)} archivos del Portal de Dades...")
    
    for csv_file in csv_files:
        # Extraer ID del indicador del nombre del archivo
        file_id = csv_file.stem.split('_')[-1]
        
        is_venta = file_id in venta_ids
        is_alquiler = file_id in alquiler_ids
        
        if not (is_venta or is_alquiler):
            continue
        
        try:
            df = _load_portaldades_csv(csv_file)
            
            if df.empty or 'VALUE' not in df.columns:
                logger.debug(f"Archivo {csv_file.name} vacío o sin columna VALUE")
                continue
            
            # Verificar que tenga las columnas necesarias
            required_cols = ['Dim-00:TEMPS', 'Dim-01:TERRITORI', 'Dim-01:TERRITORI (type)', 'VALUE']
            if not all(col in df.columns for col in required_cols):
                logger.warning(f"Archivo {csv_file.name} no tiene todas las columnas requeridas")
                continue
            
            # Filtrar solo barrios y distritos (excluir municipio agregado)
            df = df[df['Dim-01:TERRITORI (type)'].isin(['Barri', 'Districte'])]
            
            if df.empty:
                continue
            
            # Extraer año
            df['anio'] = df['Dim-00:TEMPS'].apply(_extract_year_from_temps)
            df = df.dropna(subset=['anio', 'VALUE'])
            
            # Mapear territorio a barrio_id
            df['barrio_id'] = df.apply(
                lambda row: _map_territorio_to_barrio_id(
                    row['Dim-01:TERRITORI'],
                    row['Dim-01:TERRITORI (type)'],
                    dim_barrios
                ),
                axis=1
            )
            
            # Filtrar solo los que tienen barrio_id válido
            df = df.dropna(subset=['barrio_id'])
            
            if df.empty:
                logger.debug(f"No se pudieron mapear territorios en {csv_file.name}")
                continue
            
            # Determinar si es precio por m² o precio total
            nombre_indicador = indicadores_metadata.get(file_id, {}).get('nombre', csv_file.name)
            is_precio_m2 = 'superfície' in nombre_indicador.lower() or 'm²' in nombre_indicador or 'm2' in nombre_indicador.lower()
            
            # Preparar registros
            for _, row in df.iterrows():
                record = {
                    'barrio_id': int(row['barrio_id']),
                    'anio': int(row['anio']),
                    'periodo': str(int(row['anio'])),
                    'trimestre': pd.NA,
                    'precio_m2_venta': pd.NA,
                    'precio_mes_alquiler': pd.NA,
                    'dataset_id': file_id,
                    'source': 'portaldades',
                    'etl_loaded_at': reference_time.isoformat(),
                }
                
                if is_venta:
                    if is_precio_m2:
                        record['precio_m2_venta'] = float(row['VALUE'])
                        venta_records.append(record)
                    else:
                        # Skip total price indicators to avoid polluting m2 metrics
                        # logger.debug(f"Skipping total price record from {file_id} for m2 column")
                        pass
                elif is_alquiler:
                    if not is_precio_m2:
                        record['precio_mes_alquiler'] = float(row['VALUE'])
                        alquiler_records.append(record)
                    else:
                        # Skip m2 price indicators for total rent column
                        # logger.debug(f"Skipping rent/m2 record from {file_id} for total rent column")
                        pass
            
            logger.debug(f"Procesado {csv_file.name}: {len(df)} registros válidos")
            
        except Exception as e:
            logger.warning(f"Error procesando {csv_file.name}: {e}")
            continue
    
    # Crear DataFrames
    venta_df = pd.DataFrame(venta_records) if venta_records else pd.DataFrame()
    alquiler_df = pd.DataFrame(alquiler_records) if alquiler_records else pd.DataFrame()
    
    if not venta_df.empty:
        logger.info(f"Preparados {len(venta_df)} registros de precios de VENTA del Portal de Dades")
    if not alquiler_df.empty:
        logger.info(f"Preparados {len(alquiler_df)} registros de precios de ALQUILER del Portal de Dades")
    
    return venta_df, alquiler_df


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
            )
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
            distrito_key=dim_barrios["distrito_nombre"].apply(cleaner.normalize_neighborhoods)
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
                }
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
                }
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
        ["barrio_id", "anio", "priority"], ascending=[True, True, False]
    )
    households_df = households_df.drop_duplicates(
        subset=["barrio_id", "anio"], keep="first"
    ).drop(columns=["priority"])

    households_df["dataset_id"] = indicator_id
    households_df["source"] = "portaldades"
    return households_df


def _compute_foreign_purchase_share(
    portaldades_dir: Path, dim_barrios: pd.DataFrame
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
        lambda terr: _map_territorio_to_barrio_id(str(terr), "Barri", dim_barrios)
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
    portaldades_dir: Path, dim_barrios: pd.DataFrame
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
        lambda terr: _map_territorio_to_barrio_id(str(terr), "Barri", dim_barrios)
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
    portaldades_dir: Path, dim_barrios: pd.DataFrame
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
        lambda terr: _map_territorio_to_barrio_id(str(terr), "Barri", dim_barrios)
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
    - pct_mayores_65: Porcentaje de población ≥65 años
    - pct_menores_15: Porcentaje de población <15 años
    - indice_envejecimiento: (Población 65+ / Población 0-14) * 100
    
    Args:
        raw_base_dir: Directorio base de datos raw
        dim_barrios: DataFrame con la dimensión de barrios
    
    Returns:
        DataFrame con métricas por barrio y año
    """
    opendata_dir = Path(raw_base_dir) / "opendatabcn"
    
    if not opendata_dir.exists():
        logger.debug("Directorio OpenDataBCN no encontrado: %s", opendata_dir)
        return pd.DataFrame()
    
    # Buscar archivo demográfico con edad quinquenal
    pattern = "opendatabcn_pad_mdb_lloc-naix-continent_edat-q_sexe_*.csv"
    candidates = sorted(opendata_dir.glob(pattern), key=lambda p: p.stat().st_mtime)
    
    if not candidates:
        # Intentar con patrón alternativo
        pattern_alt = "opendatabcn_pad_mdb_nacionalitat-contintent_edat-q_sexe_*.csv"
        candidates = sorted(opendata_dir.glob(pattern_alt), key=lambda p: p.stat().st_mtime)
    
    if not candidates:
        logger.debug("No se encontró archivo demográfico con edad quinquenal")
        return pd.DataFrame()
    
    raw_path = candidates[-1]  # Usar el más reciente
    logger.info("Calculando métricas de edad desde: %s", raw_path.name)
    
    try:
        df = pd.read_csv(raw_path)
    except Exception as e:
        logger.warning("Error leyendo archivo demográfico: %s", e)
        return pd.DataFrame()
    
    # Validar columnas requeridas
    required_cols = {"Codi_Barri", "EDAT_Q", "Valor", "Data_Referencia"}
    if not required_cols.issubset(df.columns):
        logger.warning("Archivo demográfico no tiene columnas requeridas: %s", required_cols)
        return pd.DataFrame()
    
    # Limpiar datos
    df["Valor"] = df["Valor"].replace("..", pd.NA)
    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce")
    df = df.dropna(subset=["Valor", "Codi_Barri", "EDAT_Q"])
    
    df["Codi_Barri"] = pd.to_numeric(df["Codi_Barri"], errors="coerce").astype("Int64")
    df["EDAT_Q"] = pd.to_numeric(df["EDAT_Q"], errors="coerce").astype("Int64")
    
    # Extraer año
    df["anio"] = pd.to_datetime(df["Data_Referencia"], errors="coerce").dt.year
    df = df.dropna(subset=["anio"])
    df["anio"] = df["anio"].astype(int)
    
    # Clasificar por grupos de edad demográficos
    def clasificar_grupo_edad(edad_q: int) -> str:
        """Clasifica código de edad quinquenal en grupo demográfico."""
        edad_min = edad_q * 5
        if edad_min < 15:
            return "menores_15"
        elif edad_min >= 65:
            return "mayores_65"
        else:
            return "otros"
    
    df["grupo_demo"] = df["EDAT_Q"].apply(clasificar_grupo_edad)
    
    # Agregar por barrio, año y grupo demográfico
    pivot = (
        df.groupby(["Codi_Barri", "anio", "grupo_demo"])["Valor"]
        .sum()
        .reset_index()
        .pivot(index=["Codi_Barri", "anio"], columns="grupo_demo", values="Valor")
        .reset_index()
    )
    
    # Asegurar que todas las columnas existan
    for col in ["menores_15", "mayores_65", "otros"]:
        if col not in pivot.columns:
            pivot[col] = 0
    
    # Calcular totales y métricas
    pivot["poblacion_total"] = pivot["menores_15"] + pivot["mayores_65"] + pivot["otros"]
    
    # Evitar división por cero
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
    
    # Renombrar y seleccionar columnas
    result = pivot.rename(columns={"Codi_Barri": "barrio_id"})[
        ["barrio_id", "anio", "pct_mayores_65", "pct_menores_15", "indice_envejecimiento"]
    ]
    
    # Filtrar solo barrios válidos
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
    """
    Completa campos faltantes de fact_demografia usando fuentes auxiliares.
    """

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
        portaldades_dir, dim_barrios, enriched
    )
    if not households_info.empty:
        enriched = enriched.merge(
            households_info[["barrio_id", "anio", "hogares_observados"]],
            on=["barrio_id", "anio"],
            how="left",
        )
        hogares_combined = enriched["hogares_totales"].fillna(
            enriched["hogares_observados"]
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
        if missing_mask.any() and (not avg_size_series.empty or not np.isnan(city_avg_size)):
            size_values = enriched.loc[missing_mask, "barrio_id"].map(avg_size_series)
            if not np.isnan(city_avg_size):
                size_values = size_values.fillna(city_avg_size)
            nonzero_sizes = size_values.replace(0, np.nan)
            enriched.loc[missing_mask, "hogares_totales"] = (
                enriched.loc[missing_mask, "poblacion_total"] / nonzero_sizes
            )

        enriched["hogares_totales"] = enriched["hogares_totales"].apply(
            lambda val: round(val) if pd.notna(val) else val
        )

        hogares_filled = hogares_initial_na & enriched["hogares_totales"].notna()
        if hogares_filled.any():
            enriched.loc[hogares_filled, "dataset_id"] = enriched.loc[
                hogares_filled, "dataset_id"
            ].apply(lambda current: _append_tag(current, "hd7u1b68qj"))
            enriched.loc[hogares_filled, "source"] = enriched.loc[
                hogares_filled, "source"
            ].apply(lambda current: _append_tag(current, "portaldades"))

    immigration_info = _compute_foreign_purchase_share(portaldades_dir, dim_barrios)
    if not immigration_info.empty:
        enriched = enriched.merge(
            immigration_info[["barrio_id", "anio", "porc_inmigracion"]],
            on=["barrio_id", "anio"],
            how="left",
            suffixes=("", "_enriched"),
        )
        mask_imm = inmigracion_initial_na & enriched["porc_inmigracion_enriched"].notna()
        if mask_imm.any():
            enriched.loc[mask_imm, "porc_inmigracion"] = enriched.loc[
                mask_imm, "porc_inmigracion_enriched"
            ].clip(lower=0, upper=100)
            enriched.loc[mask_imm, "dataset_id"] = enriched.loc[
                mask_imm, "dataset_id"
            ].apply(lambda current: _append_tag(current, "uuxbxa7onv"))
            enriched.loc[mask_imm, "source"] = enriched.loc[
                mask_imm, "source"
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
            building_age_latest, on="barrio_id", how="left"
        )
        mask_age = edad_initial_na & enriched["edad_media_proxy"].notna()
        if mask_age.any():
            enriched.loc[mask_age, "edad_media"] = enriched.loc[
                mask_age, "edad_media_proxy"
            ]
            enriched.loc[mask_age, "dataset_id"] = enriched.loc[
                mask_age, "dataset_id"
            ].apply(lambda current: _append_tag(current, "ydtnyd6qhm"))
            enriched.loc[mask_age, "source"] = enriched.loc[
                mask_age, "source"
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
                mask_density, "dataset_id"
            ].apply(lambda current: _append_tag(current, "wjnmk82jd9"))
            enriched.loc[mask_density, "source"] = enriched.loc[
                mask_density, "source"
            ].apply(lambda current: _append_tag(current, "portaldades"))
        enriched = enriched.drop(columns=["area_m2"])

    enriched["hogares_totales"] = enriched["hogares_totales"].astype("Float64")
    enriched["porc_inmigracion"] = enriched["porc_inmigracion"].astype("Float64")
    enriched["densidad_hab_km2"] = enriched["densidad_hab_km2"].astype("Float64")
    enriched["edad_media"] = enriched["edad_media"].astype("Float64")

    # =================================================================
    # Enriquecimiento de métricas basadas en edad (desde datos raw)
    # =================================================================
    age_metrics = _compute_age_metrics_from_raw(raw_base_dir, dim_barrios)
    
    if not age_metrics.empty:
        # Asegurar que las columnas existan en el DataFrame enriched
        for col in ["pct_mayores_65", "pct_menores_15", "indice_envejecimiento"]:
            if col not in enriched.columns:
                enriched[col] = pd.NA
        
        # Guardar estado inicial de nulls
        mayores_initial_na = enriched["pct_mayores_65"].isna()
        menores_initial_na = enriched["pct_menores_15"].isna()
        envej_initial_na = enriched["indice_envejecimiento"].isna()
        
        # Verificar si hay overlap de años entre fact_demografia y age_metrics
        fact_years = set(enriched["anio"].unique())
        metric_years = set(age_metrics["anio"].unique())
        overlapping_years = fact_years & metric_years
        
        if not overlapping_years:
            # Si no hay overlap, propagar el año más reciente a todos los años
            # Las proporciones de edad cambian lentamente, así que es una aproximación razonable
            latest_year = age_metrics["anio"].max()
            logger.info(
                "No hay overlap de años entre fact_demografia (%s) y métricas de edad (%s). "
                "Propagando métricas del año %s a todos los años.",
                sorted(fact_years),
                sorted(metric_years),
                latest_year,
            )
            
            # Usar solo los datos del año más reciente por barrio
            age_metrics_latest = age_metrics[age_metrics["anio"] == latest_year].copy()
            age_metrics_latest = age_metrics_latest.drop(columns=["anio"])
            
            # Merge sin el año (propagar a todos los años)
            enriched = enriched.merge(
                age_metrics_latest,
                on=["barrio_id"],
                how="left",
                suffixes=("", "_new"),
            )
        else:
            # Merge normal con años específicos
            enriched = enriched.merge(
                age_metrics,
                on=["barrio_id", "anio"],
                how="left",
                suffixes=("", "_new"),
            )
        
        # Aplicar valores nuevos donde había nulls
        for col in ["pct_mayores_65", "pct_menores_15", "indice_envejecimiento"]:
            new_col = f"{col}_new"
            if new_col in enriched.columns:
                mask = enriched[col].isna() & enriched[new_col].notna()
                if mask.any():
                    enriched.loc[mask, col] = enriched.loc[mask, new_col]
                enriched = enriched.drop(columns=[new_col])
        
        # Convertir a tipos correctos
        enriched["pct_mayores_65"] = enriched["pct_mayores_65"].astype("Float64")
        enriched["pct_menores_15"] = enriched["pct_menores_15"].astype("Float64")
        enriched["indice_envejecimiento"] = enriched["indice_envejecimiento"].astype("Float64")
        
        # Contar mejoras
        mayores_filled = int((mayores_initial_na & enriched["pct_mayores_65"].notna()).sum())
        menores_filled = int((menores_initial_na & enriched["pct_menores_15"].notna()).sum())
        envej_filled = int((envej_initial_na & enriched["indice_envejecimiento"].notna()).sum())
        
        if mayores_filled or menores_filled or envej_filled:
            logger.info(
                "Métricas de edad enriquecidas: mayores_65=%s, menores_15=%s, envejecimiento=%s",
                mayores_filled,
                menores_filled,
                envej_filled,
            )
    else:
        # Si no hay métricas de edad, asegurar que las columnas existan con nulls
        for col in ["pct_mayores_65", "pct_menores_15", "indice_envejecimiento"]:
            if col not in enriched.columns:
                enriched[col] = pd.NA

    logger.info(
        "Enriquecimiento demográfico completado: hogares=%s, edad=%s, inmigración=%s, densidad=%s",
        int((hogares_initial_na & enriched["hogares_totales"].notna()).sum()),
        int((edad_initial_na & enriched["edad_media"].notna()).sum()),
        int((inmigracion_initial_na & enriched["porc_inmigracion"].notna()).sum()),
        int((densidad_initial_na & enriched["densidad_hab_km2"].notna()).sum()),
    )
    return enriched


def _edad_quinquenal_to_range(edad_q: int) -> Tuple[int, int]:
    """
    Convierte código de edad quinquenal (EDAT_Q) a rango de edad.
    
    Args:
        edad_q: Código de edad quinquenal (0-20)
            - 0 = 0-4 años
            - 1 = 5-9 años
            - 2 = 10-14 años
            - ... (cada código representa 5 años)
            - 20 = 100+ años
    
    Returns:
        Tupla (edad_min, edad_max)
    """
    if edad_q < 0 or edad_q > 20:
        return (0, 0)
    edad_min = edad_q * 5
    edad_max = edad_min + 4 if edad_q < 20 else 999
    return (edad_min, edad_max)


def _edad_quinquenal_to_custom_group(edad_q: int) -> Optional[str]:
    """
    Agrupa edad quinquenal en grupos personalizados.
    
    Args:
        edad_q: Código de edad quinquenal (0-20)
    
    Returns:
        Grupo de edad personalizado o None si no aplica
    """
    edad_min, _ = _edad_quinquenal_to_range(edad_q)
    
    if 18 <= edad_min <= 34:
        return "18-34"
    elif 35 <= edad_min <= 49:
        return "35-49"
    elif 50 <= edad_min <= 64:
        return "50-64"
    elif edad_min >= 65:
        return "65+"
    else:
        return None  # Menores de 18 años


def _map_continente_to_nacionalidad(continente_code: int) -> str:
    """
    Mapea código de continente de nacimiento a categoría de nacionalidad.
    
    Args:
        continente_code: Código de continente
            - 1 = Europa (probablemente incluye España)
            - 2 = América
            - 3 = África
            - 4 = Asia
            - 5 = Oceanía
            - 999 = No consta / Desconocido
    
    Returns:
        Categoría de nacionalidad
    """
    mapping = {
        1: "Europa",
        2: "América",
        3: "África",
        4: "Asia",
        5: "Oceanía",
        999: "No consta",
    }
    return mapping.get(continente_code, "Desconocido")


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
            - Data_Referencia, Codi_Barri, Nom_Barri
            - Valor (población, puede ser ".." para no disponible)
            - LLOC_NAIX_CONTINENT (código de continente)
            - EDAT_Q (edad quinquenal: 0-20)
            - SEXE (1=hombre, 2=mujer)
        dim_barrios: DataFrame con dimensión de barrios
        dataset_id: ID del dataset
        reference_time: Timestamp de referencia
        source: Fuente de datos
    
    Returns:
        DataFrame con datos agregados por barrio, año, sexo, grupo de edad y nacionalidad
    """
    df = demographics_df.copy()
    
    # Validar columnas requeridas
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
    
    # Extraer año de Data_Referencia
    df["año"] = pd.to_datetime(df["Data_Referencia"], errors="coerce").dt.year
    df = df.dropna(subset=["año"])
    
    # Limpiar y convertir Valor (puede ser ".." o número)
    df["Valor"] = df["Valor"].replace("..", pd.NA)
    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce")
    df = df.dropna(subset=["Valor", "Codi_Barri"])
    
    # Convertir tipos
    df["Codi_Barri"] = pd.to_numeric(df["Codi_Barri"], errors="coerce").astype("Int64")
    df["año"] = df["año"].astype("Int64")
    df["EDAT_Q"] = pd.to_numeric(df["EDAT_Q"], errors="coerce").astype("Int64")
    df["LLOC_NAIX_CONTINENT"] = pd.to_numeric(
        df["LLOC_NAIX_CONTINENT"], errors="coerce"
    ).astype("Int64")
    
    # Agregar grupos de edad personalizados
    df["grupo_edad"] = df["EDAT_Q"].apply(_edad_quinquenal_to_custom_group)
    
    # Agregar categoría de nacionalidad
    df["nacionalidad"] = df["LLOC_NAIX_CONTINENT"].apply(
        _map_continente_to_nacionalidad
    )
    
    # Mapear SEXE a texto
    df["sexo"] = df["SEXE"].map({1: "hombre", 2: "mujer"}).fillna("desconocido")
    
    # Filtrar solo grupos de edad válidos (mayores de 18) antes de agregar
    df = df[df["grupo_edad"].notna()]
    
    # Agregar por barrio, año, sexo, grupo de edad y nacionalidad
    aggregated = (
        df.groupby(
            ["Codi_Barri", "año", "sexo", "grupo_edad", "nacionalidad"],
            as_index=False,
        )["Valor"]
        .sum()
        .rename(columns={"Codi_Barri": "barrio_id", "Valor": "poblacion", "año": "anio"})
    )
    
    # Join con dim_barrios para validar barrios
    aggregated = aggregated.merge(
        dim_barrios[["barrio_id", "barrio_nombre_normalizado"]],
        on="barrio_id",
        how="inner",
    )
    
    # Agregar metadatos
    aggregated["dataset_id"] = dataset_id
    aggregated["source"] = source
    aggregated["etl_loaded_at"] = reference_time.isoformat()
    
    # Ordenar
    aggregated = aggregated.sort_values(
        ["anio", "barrio_id", "sexo", "grupo_edad", "nacionalidad"]
    ).reset_index(drop=True)
    
    logger.info(
        "Datos demográficos ampliados preparados: %s registros (%s barrios, %s años)",
        len(aggregated),
        aggregated["barrio_id"].nunique(),
        aggregated["anio"].nunique(),
    )
    
    return aggregated


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
            - Any (año)
            - Codi_Barri, Nom_Barri
            - Seccio_Censal
            - Import_Euros o Import_Renda_Bruta_€ (renta en euros)
        dim_barrios: DataFrame con dimensión de barrios
        dataset_id: ID del dataset
        reference_time: Timestamp de referencia
        source: Fuente de datos
        metric: Métrica a usar para agregación ("mean", "median", o "both")
    
    Returns:
        DataFrame con renta agregada por barrio y año
    """
    df = renta_df.copy()
    
    # Validar columnas requeridas
    required_cols = ["Any", "Codi_Barri"]
    missing = set(required_cols) - set(df.columns)
    if missing:
        raise ValueError(f"DataFrame faltan columnas requeridas: {missing}")
    
    # Identificar columna de renta
    renta_col = None
    for col in ["Import_Euros", "Import_Renda_Bruta_€", "Import"]:
        if col in df.columns:
            renta_col = col
            break
    
    if renta_col is None:
        raise ValueError(
            "No se encontró columna de renta (busca: Import_Euros, Import_Renda_Bruta_€, Import)"
        )
    
    # Limpiar y convertir tipos
    df["Any"] = pd.to_numeric(df["Any"], errors="coerce").astype("Int64")
    df["Codi_Barri"] = pd.to_numeric(df["Codi_Barri"], errors="coerce").astype("Int64")
    df[renta_col] = pd.to_numeric(df[renta_col], errors="coerce")
    
    # Filtrar datos válidos
    df = df.dropna(subset=["Any", "Codi_Barri", renta_col])
    
    if df.empty:
        logger.warning("No hay datos válidos de renta después de la limpieza")
        return pd.DataFrame()
    
    # Agregar por barrio y año
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
    
    # Renombrar Any a anio
    aggregated = aggregated.rename(columns={"Any": "anio"})
    
    # Renombrar Codi_Barri a barrio_id
    aggregated = aggregated.rename(columns={"Codi_Barri": "barrio_id"})
    
    # Seleccionar métrica principal según parámetro
    if metric == "mean":
        aggregated["renta_euros"] = aggregated["renta_promedio"]
    elif metric == "median":
        aggregated["renta_euros"] = aggregated["renta_mediana"]
    elif metric == "both":
        # Si se quiere ambas, mantener ambas columnas
        aggregated["renta_euros"] = aggregated["renta_promedio"]
    else:
        logger.warning(f"Métrica '{metric}' no reconocida, usando promedio")
        aggregated["renta_euros"] = aggregated["renta_promedio"]
    
    # Join con dim_barrios para validar barrios
    aggregated = aggregated.merge(
        dim_barrios[["barrio_id", "barrio_nombre_normalizado"]],
        on="barrio_id",
        how="inner",
    )
    
    # Agregar metadatos
    aggregated["dataset_id"] = dataset_id
    aggregated["source"] = source
    aggregated["etl_loaded_at"] = reference_time.isoformat()
    
    # Ordenar columnas
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
    
    # Solo incluir columnas que existen
    available_columns = [col for col in column_order if col in aggregated.columns]
    aggregated = aggregated[available_columns]
    
    # Ordenar
    aggregated = aggregated.sort_values(["anio", "barrio_id"]).reset_index(drop=True)
    
    logger.info(
        "Datos de renta preparados: %s registros (%s barrios, %s años, métrica: %s)",
        len(aggregated),
        aggregated["barrio_id"].nunique(),
        aggregated["anio"].nunique(),
        metric,
    )
    
    return aggregated


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
        idealista_df: DataFrame con datos raw de Idealista (de extract_offer_by_barrio)
        dim_barrios: DataFrame con la dimensión de barrios
        dataset_id: ID del dataset
        reference_time: Timestamp de referencia
        source: Fuente de los datos
        
    Returns:
        DataFrame procesado con datos agregados por barrio
    """
    if idealista_df.empty:
        logger.warning("DataFrame de Idealista vacío")
        return pd.DataFrame()
    
    df = idealista_df.copy()
    
    # Mapear barrios de Idealista a barrio_id
    # Intentar usar 'barrio_idealista' primero, luego 'barrio_busqueda', luego 'district'
    barrio_col = None
    for col in ['barrio_idealista', 'barrio_busqueda', 'district', 'distrito']:
        if col in df.columns:
            barrio_col = col
            break
    
    if barrio_col is None:
        logger.warning("No se encontró columna de barrio en datos de Idealista")
        return pd.DataFrame()
    
    logger.info(f"Mapeando barrios de Idealista usando columna '{barrio_col}'...")
    
    df['barrio_id'] = df[barrio_col].apply(
        lambda x: _map_territorio_to_barrio_id(str(x), "Barri", dim_barrios) if pd.notna(x) else None
    )
    
    # Filtrar solo los que tienen barrio_id válido
    df = df.dropna(subset=['barrio_id'])
    
    if df.empty:
        logger.warning("No se pudieron mapear barrios de Idealista a barrio_id")
        return pd.DataFrame()
    
    logger.info(f"✓ {len(df)} propiedades mapeadas a {df['barrio_id'].nunique()} barrios")
    
    # Extraer fecha de extracción (usar fecha_extraccion o fecha_publicacion)
    if 'fecha_extraccion' in df.columns:
        df['fecha'] = pd.to_datetime(df['fecha_extraccion'], errors='coerce')
    elif 'fecha_publicacion' in df.columns:
        df['fecha'] = pd.to_datetime(df['fecha_publicacion'], errors='coerce')
    else:
        df['fecha'] = pd.to_datetime(reference_time)
    
    df['anio'] = df['fecha'].dt.year
    df['mes'] = df['fecha'].dt.month
    
    # Limpiar y convertir tipos
    numeric_cols = ['precio', 'precio_m2', 'superficie', 'habitaciones', 'banos']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Agregar por barrio, operación, año y mes
    group_cols = ['barrio_id', 'operacion', 'anio', 'mes']
    
    # Calcular métricas agregadas
    agg_dict = {}
    
    if 'precio' in df.columns:
        agg_dict['precio_medio'] = ('precio', 'mean')
        agg_dict['precio_mediano'] = ('precio', 'median')
        agg_dict['precio_min'] = ('precio', 'min')
        agg_dict['precio_max'] = ('precio', 'max')
    
    if 'precio_m2' in df.columns:
        agg_dict['precio_m2_medio'] = ('precio_m2', 'mean')
        agg_dict['precio_m2_mediano'] = ('precio_m2', 'median')
    
    if 'superficie' in df.columns:
        agg_dict['superficie_media'] = ('superficie', 'mean')
        agg_dict['superficie_mediana'] = ('superficie', 'median')
    
    if 'habitaciones' in df.columns:
        agg_dict['habitaciones_media'] = ('habitaciones', 'mean')
    
    # Contar número de anuncios
    agg_dict['num_anuncios'] = ('precio', 'count')
    
    # Agregar por tipología si está disponible
    if 'tipologia' in df.columns:
        # Agregar también por tipología
        tipologia_counts = df.groupby(group_cols + ['tipologia']).size().reset_index(name='num_anuncios_tipologia')
    else:
        tipologia_counts = pd.DataFrame()
    
    # Realizar agregación
    aggregated = df.groupby(group_cols).agg(agg_dict).reset_index()
    
    # Renombrar columnas multi-index
    aggregated.columns = [col[0] if col[1] == '' else f"{col[0]}_{col[1]}" for col in aggregated.columns]
    
    # Merge con dim_barrios para obtener nombres normalizados
    aggregated = aggregated.merge(
        dim_barrios[['barrio_id', 'barrio_nombre_normalizado']],
        on='barrio_id',
        how='inner'
    )
    
    # Agregar metadata
    aggregated['dataset_id'] = dataset_id
    aggregated['source'] = source
    aggregated['etl_loaded_at'] = reference_time.isoformat()
    
    # Ordenar
    aggregated = aggregated.sort_values(['anio', 'mes', 'barrio_id', 'operacion']).reset_index(drop=True)
    
    logger.info(
        "Datos de Idealista preparados: %s registros (%s barrios, %s operaciones, %s años)",
        len(aggregated),
        aggregated['barrio_id'].nunique(),
        aggregated['operacion'].nunique() if 'operacion' in aggregated.columns else 0,
        aggregated['anio'].nunique(),
    )
    
    return aggregated
