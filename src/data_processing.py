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
    portaldades_venta: Optional[pd.DataFrame] = None,
    portaldades_alquiler: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    Build the housing prices fact table from multiple sources.
    
    Combina datos de:
    - Open Data BCN (venta, alquiler)
    - Portal de Dades (venta, alquiler)
    """
    fact_venta = _prepare_venta_prices(venta, dim_barrios, dataset_id_venta, reference_time)

    # Combinar datos de venta del Portal de Dades
    if portaldades_venta is not None and not portaldades_venta.empty:
        logger.info(f"Combinando {len(portaldades_venta)} registros de venta del Portal de Dades")
        # Agregar datos del Portal de Dades, priorizando Open Data BCN si hay duplicados
        fact_venta = pd.concat([fact_venta, portaldades_venta], ignore_index=True)
        # Eliminar duplicados: si hay mismo barrio_id, anio, trimestre, mantener el de Open Data BCN
        fact_venta = fact_venta.drop_duplicates(
            subset=['barrio_id', 'anio', 'trimestre'],
            keep='first'  # Mantener el primero (Open Data BCN tiene prioridad)
        )

    # Procesar datos de alquiler
    fact_alquiler_list = []
    
    # Alquiler del Portal de Dades
    if portaldades_alquiler is not None and not portaldades_alquiler.empty:
        logger.info(f"Agregando {len(portaldades_alquiler)} registros de alquiler del Portal de Dades")
        fact_alquiler_list.append(portaldades_alquiler)
    
    # Alquiler de Open Data BCN (si está disponible en el futuro)
    if alquiler is not None and not alquiler.empty:
        logger.warning(
            "Datos de alquiler de Open Data BCN encontrados pero sin métrica de precio identificable. Se omiten."
        )

    # Combinar todos los datos de alquiler
    if fact_alquiler_list:
        fact_alquiler = pd.concat(fact_alquiler_list, ignore_index=True)
        # Eliminar duplicados en alquiler también
        fact_alquiler = fact_alquiler.drop_duplicates(
            subset=['barrio_id', 'anio', 'trimestre'],
            keep='first'
        )
        
        # Si fact_venta tiene datos, combinar con alquiler
        if not fact_venta.empty:
            # Hacer merge para combinar venta y alquiler por barrio_id, anio, trimestre
            # Usar outer join para mantener todos los registros
            fact = fact_venta.merge(
                fact_alquiler[['barrio_id', 'anio', 'trimestre', 'precio_mes_alquiler']],
                on=['barrio_id', 'anio', 'trimestre'],
                how='outer',
                suffixes=('', '_alq')
            )
            # Combinar precio_mes_alquiler
            if 'precio_mes_alquiler_alq' in fact.columns:
                fact['precio_mes_alquiler'] = fact['precio_mes_alquiler_alq'].fillna(fact['precio_mes_alquiler'])
                fact = fact.drop(columns=['precio_mes_alquiler_alq'])
            
            # Para dataset_id y source: si el registro viene solo de alquiler, usar esos valores
            # Si viene de ambos o solo de venta, mantener los de venta
            fact_alquiler_only = fact[
                (fact['precio_m2_venta'].isna()) & (fact['precio_mes_alquiler'].notna())
            ]
            if not fact_alquiler_only.empty:
                # Para registros que solo tienen alquiler, actualizar dataset_id y source
                alquiler_lookup = fact_alquiler.set_index(['barrio_id', 'anio', 'trimestre'])[['dataset_id', 'source']]
                for idx in fact_alquiler_only.index:
                    key = (fact.loc[idx, 'barrio_id'], fact.loc[idx, 'anio'], fact.loc[idx, 'trimestre'])
                    if key in alquiler_lookup.index:
                        fact.loc[idx, 'dataset_id'] = alquiler_lookup.loc[key, 'dataset_id']
                        fact.loc[idx, 'source'] = alquiler_lookup.loc[key, 'source']
        else:
            fact = fact_alquiler
    else:
        fact = fact_venta

    # Asegurar que todas las columnas requeridas estén presentes
    required_columns = [
        'barrio_id', 'anio', 'periodo', 'trimestre',
        'precio_m2_venta', 'precio_mes_alquiler',
        'dataset_id', 'source', 'etl_loaded_at'
    ]
    for col in required_columns:
        if col not in fact.columns:
            if col in ['precio_m2_venta', 'precio_mes_alquiler']:
                fact[col] = pd.NA
            elif col == 'periodo':
                fact[col] = fact['anio'].astype(str)
            elif col == 'trimestre':
                fact[col] = pd.NA
            elif col == 'etl_loaded_at':
                fact[col] = reference_time.isoformat()

    fact = fact[required_columns].sort_values(["anio", "barrio_id"]).reset_index(drop=True)
    logger.info("Tabla de hechos de precios preparada con %s registros", len(fact))
    return fact


def _load_portaldades_csv(filepath: Path) -> pd.DataFrame:
    """Carga un archivo CSV del Portal de Dades con detección automática de encoding."""
    import chardet
    
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
        # Normalizar el territorio
        territorio_normalizado = _normalize_text(territorio)
        
        # 1. Buscar coincidencia exacta normalizada
        match = dim_barrios[
            dim_barrios["barrio_nombre_normalizado"] == territorio_normalizado
        ]
        if not match.empty:
            return int(match.iloc[0]["barrio_id"])
        
        # 2. Buscar coincidencia exacta sin normalizar (case-insensitive)
        match = dim_barrios[
            dim_barrios["barrio_nombre"].str.strip().str.lower() == territorio.strip().lower()
        ]
        if not match.empty:
            return int(match.iloc[0]["barrio_id"])
        
        # 3. Buscar coincidencia parcial (contiene)
        match = dim_barrios[
            dim_barrios["barrio_nombre"].str.contains(territorio, case=False, na=False, regex=False)
        ]
        if not match.empty:
            # Si hay múltiples coincidencias, preferir la más corta (más específica)
            match = match.sort_values('barrio_nombre', key=lambda x: x.str.len())
            return int(match.iloc[0]["barrio_id"])
        
        # 4. Buscar por nombre normalizado parcial
        territorio_parts = territorio_normalizado.split()
        if len(territorio_parts) > 1:
            for part in territorio_parts:
                if len(part) > 3:  # Ignorar palabras muy cortas
                    match = dim_barrios[
                        dim_barrios["barrio_nombre_normalizado"].str.contains(part, na=False, regex=False)
                    ]
                    if not match.empty:
                        match = match.sort_values('barrio_nombre', key=lambda x: x.str.len())
                        return int(match.iloc[0]["barrio_id"])
    
    elif territorio_type == "Districte":
        # Para distritos, buscar el primer barrio del distrito
        territorio_clean = territorio.strip()
        
        # Mapeo manual de variaciones comunes
        distrito_mapping = {
            'Les Corts': 'les Corts',
            'Sant Andreu': 'Sant Andreu',
            'Sant Martí': 'Sant Martí',
            'Sants-Montjuïc': 'Sants-Montjuïc',
            'Sarrià-Sant Gervasi': 'Sarrià-Sant Gervasi',
            'Horta-Guinardó': 'Horta-Guinardó',
            'Nou Barris': 'Nou Barris',
        }
        
        territorio_to_search = distrito_mapping.get(territorio_clean, territorio_clean)
        
        match = dim_barrios[
            dim_barrios["distrito_nombre"].str.contains(territorio_to_search, case=False, na=False, regex=False)
        ]
        if not match.empty:
            # Retornar el primer barrio del distrito como representativo
            # En el futuro se podría agregar a nivel de distrito
            return int(match.iloc[0]["barrio_id"])
    
    # Para municipio, no mapeamos (es demasiado agregado)
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
                    else:
                        # Si es precio total, intentar calcular m² si tenemos superficie
                        # Por ahora, lo guardamos como precio total aproximado
                        record['precio_m2_venta'] = float(row['VALUE'])  # Asumimos que es por m²
                    venta_records.append(record)
                elif is_alquiler:
                    if is_precio_m2:
                        # Precio por m² de alquiler - convertir a precio mensual estimado
                        # (necesitaríamos superficie promedio, por ahora lo dejamos como está)
                        record['precio_mes_alquiler'] = float(row['VALUE'])
                    else:
                        record['precio_mes_alquiler'] = float(row['VALUE'])
                    alquiler_records.append(record)
            
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

