"""
Procesa datos de criminalidad del ICGC y crea fact_seguridad.

Fuentes:
- ICGC: Datos de criminalidad por barrio
- fact_demografia: Población para calcular tasas por 1000 habitantes
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


def _load_icgc_data(raw_data_path: Path) -> pd.DataFrame:
    """
    Carga datos de criminalidad desde archivos CSV en el directorio ICGC.
    
    Busca archivos CSV con patrones relacionados con criminalidad en:
    - data/raw/icgc/
    - data/raw/seguridad/
    
    Args:
        raw_data_path: Directorio base donde se encuentran los datos raw.
    
    Returns:
        DataFrame con datos de criminalidad.
    """
    search_paths = [
        raw_data_path / "icgc",
        raw_data_path / "seguridad",
        raw_data_path.parent / "icgc",
        raw_data_path.parent / "seguridad",
    ]
    
    frames = []
    
    for search_path in search_paths:
        if not search_path.exists():
            continue
        
        # Buscar archivos CSV relacionados con criminalidad
        csv_files = list(search_path.glob("*criminalidad*.csv"))
        csv_files.extend(list(search_path.glob("*delitos*.csv")))
        csv_files.extend(list(search_path.glob("*seguridad*.csv")))
        csv_files.extend(list(search_path.glob("icgc_*.csv")))
        
        for csv_file in csv_files:
            try:
                logger.info("Cargando datos de criminalidad desde: %s", csv_file)
                df = pd.read_csv(csv_file, low_memory=False)
                logger.info("Datos cargados: %s registros, %s columnas", len(df), len(df.columns))
                frames.append(df)
            except Exception as exc:
                logger.warning("Error leyendo CSV de criminalidad %s: %s", csv_file, exc)
    
    if not frames:
        logger.warning("No se pudieron cargar archivos de criminalidad del ICGC")
        return pd.DataFrame()
    
    df = pd.concat(frames, ignore_index=True)
    logger.info("Total datos de criminalidad cargados: %s registros", len(df))
    
    return df


def _map_barrio_from_criminalidad_data(
    df: pd.DataFrame,
    barrios_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Mapea nombres de barrios en datos de criminalidad a barrio_id.
    
    Args:
        df: DataFrame con datos de criminalidad.
        barrios_df: DataFrame con dimensión de barrios.
    
    Returns:
        DataFrame con columna barrio_id añadida.
    """
    from src.transform.cleaners import HousingCleaner
    
    cleaner = HousingCleaner()
    
    # Buscar columna de barrio en datos de criminalidad
    barrio_col = None
    for col in ["barrio", "barri", "neighbourhood", "barrio_nombre", "nom_barri"]:
        if col in df.columns:
            barrio_col = col
            break
    
    if barrio_col is None:
        # Buscar por codi_barri
        codi_col = None
        for col in ["codi_barri", "codi_barri", "barrio_id"]:
            if col in df.columns:
                codi_col = col
                break
        
        if codi_col:
            # Mapear directamente por código
            df["barrio_id"] = pd.to_numeric(df[codi_col], errors="coerce")
            return df
        else:
            logger.warning("No se encontró columna de barrio en datos de criminalidad")
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
            "Seguridad: %s registros sin mapeo a barrio_id", missing_fk
        )
    
    return merged


def prepare_seguridad(
    raw_data_path: Path,
    barrios_df: pd.DataFrame,
    poblacion_df: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """
    Prepara tabla fact_seguridad desde datos brutos de criminalidad del ICGC.
    
    Args:
        raw_data_path: Directorio base donde se encuentran los datos raw de ICGC.
        barrios_df: DataFrame con dimensión de barrios (debe incluir barrio_id,
            barrio_nombre_normalizado).
        poblacion_df: DataFrame opcional con datos de población por barrio y año.
            Si no se proporciona, se intentará cargar desde fact_demografia.
            Debe tener columnas: barrio_id, anio, poblacion_total (o similar).
    
    Returns:
        DataFrame con columnas:
        - barrio_id
        - anio
        - trimestre
        - delitos_patrimonio
        - delitos_seguridad_personal
        - tasa_criminalidad_1000hab
        - percepcion_inseguridad (opcional)
    
    Raises:
        ValueError: Si faltan columnas clave en ``barrios_df``.
    """
    if barrios_df.empty:
        raise ValueError("barrios_df no puede estar vacío en prepare_seguridad")
    
    required_dim_cols = {"barrio_id", "barrio_nombre_normalizado"}
    missing_dim = required_dim_cols - set(barrios_df.columns)
    if missing_dim:
        raise ValueError(
            f"Dimensión de barrios incompleta para seguridad. "
            f"Faltan columnas: {sorted(missing_dim)}"
        )
    
    # 1. Cargar datos de criminalidad
    df = _load_icgc_data(raw_data_path)
    
    if df.empty:
        logger.warning("No se encontraron datos de criminalidad del ICGC")
        return pd.DataFrame(columns=[
            "barrio_id", "anio", "trimestre",
            "delitos_patrimonio", "delitos_seguridad_personal",
            "tasa_criminalidad_1000hab", "percepcion_inseguridad"
        ])
    
    # 2. Mapear barrios
    df = _map_barrio_from_criminalidad_data(df, barrios_df)
    df = df[df["barrio_id"].notna()].copy()
    
    if df.empty:
        logger.warning("No se pudieron mapear datos de criminalidad a barrios")
        return pd.DataFrame(columns=[
            "barrio_id", "anio", "trimestre",
            "delitos_patrimonio", "delitos_seguridad_personal",
            "tasa_criminalidad_1000hab", "percepcion_inseguridad"
        ])
    
    # 3. Extraer año y trimestre
    # Buscar columna de fecha/año
    anio_col = None
    for col in ["anio", "any", "year", "año", "fecha"]:
        if col in df.columns:
            anio_col = col
            break
    
    if anio_col:
        df["anio"] = pd.to_numeric(df[anio_col], errors="coerce")
    else:
        logger.warning("No se encontró columna de año, usando año actual")
        from datetime import datetime
        df["anio"] = datetime.now().year
    
    # Buscar columna de trimestre
    trimestre_col = None
    for col in ["trimestre", "trimestre", "quarter", "q"]:
        if col in df.columns:
            trimestre_col = col
            break
    
    if trimestre_col:
        df["trimestre"] = pd.to_numeric(df[trimestre_col], errors="coerce")
    else:
        # Si no hay trimestre, usar trimestre 1 por defecto
        df["trimestre"] = 1
    
    # 4. Identificar y clasificar delitos
    # Buscar columnas de delitos
    delitos_patrimonio_cols = []
    delitos_personal_cols = []
    
    # Delitos contra el patrimonio: robos, hurtos, estafas
    patrimonio_keywords = ["robo", "hurto", "estafa", "patrimonio", "sustraccion"]
    # Delitos contra la seguridad personal: agresiones, violencia, lesiones
    personal_keywords = ["agresion", "violencia", "lesion", "personal", "fisica"]
    
    for col in df.columns:
        col_lower = col.lower()
        if any(keyword in col_lower for keyword in patrimonio_keywords):
            delitos_patrimonio_cols.append(col)
        elif any(keyword in col_lower for keyword in personal_keywords):
            delitos_personal_cols.append(col)
    
    # Si no se encuentran columnas específicas, buscar columnas genéricas
    if not delitos_patrimonio_cols and not delitos_personal_cols:
        # Buscar columnas con "delito", "delictes", "crimen"
        for col in df.columns:
            col_lower = col.lower()
            if "delito" in col_lower or "delictes" in col_lower or "crimen" in col_lower:
                # Asumir que es delito total si no hay clasificación
                if "total" in col_lower or "total" in col_lower:
                    delitos_patrimonio_cols.append(col)  # Usar como proxy
    
    # 5. Agregar delitos por barrio, año y trimestre
    groupby_cols = ["barrio_id", "anio", "trimestre"]
    
    agg_dict = {}
    
    if delitos_patrimonio_cols:
        # Sumar todas las columnas de delitos contra el patrimonio
        for col in delitos_patrimonio_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        df["delitos_patrimonio"] = df[delitos_patrimonio_cols].sum(axis=1)
        agg_dict["delitos_patrimonio"] = "sum"
    else:
        df["delitos_patrimonio"] = 0
    
    if delitos_personal_cols:
        # Sumar todas las columnas de delitos contra la seguridad personal
        for col in delitos_personal_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        df["delitos_seguridad_personal"] = df[delitos_personal_cols].sum(axis=1)
        agg_dict["delitos_seguridad_personal"] = "sum"
    else:
        df["delitos_seguridad_personal"] = 0
    
    # Buscar columna de percepción de inseguridad (opcional)
    percepcion_col = None
    for col in ["percepcion", "inseguridad", "seguridad", "satisfaccion"]:
        if col in df.columns:
            percepcion_col = col
            break
    
    if percepcion_col:
        agg_dict["percepcion_inseguridad"] = "mean"
    else:
        df["percepcion_inseguridad"] = None
    
    # Agregar
    result = df.groupby(groupby_cols, as_index=False).agg(agg_dict)
    
    # 6. Calcular tasa de criminalidad por 1000 habitantes
    # Cargar datos de población si no se proporcionaron
    if poblacion_df is None or poblacion_df.empty:
        logger.info("Intentando cargar datos de población desde fact_demografia...")
        try:
            import sqlite3
            from ..database_setup import DEFAULT_DB_NAME
            
            db_path = raw_data_path.parent.parent / "processed" / DEFAULT_DB_NAME
            if db_path.exists():
                conn = sqlite3.connect(db_path)
                poblacion_df = pd.read_sql_query(
                    """
                    SELECT barrio_id, anio, poblacion_total
                    FROM fact_demografia
                    WHERE poblacion_total IS NOT NULL
                    """,
                    conn
                )
                conn.close()
                logger.info("Datos de población cargados: %s registros", len(poblacion_df))
            else:
                logger.warning("Base de datos no encontrada, no se puede calcular tasa por 1000hab")
                poblacion_df = pd.DataFrame()
        except Exception as e:
            logger.warning("Error cargando datos de población: %s", e)
            poblacion_df = pd.DataFrame()
    
    # Calcular tasa de criminalidad por 1000 habitantes
    if not poblacion_df.empty and "poblacion_total" in poblacion_df.columns:
        # Merge con población
        result = result.merge(
            poblacion_df[["barrio_id", "anio", "poblacion_total"]],
            on=["barrio_id", "anio"],
            how="left"
        )
        
        # Calcular total de delitos
        result["total_delitos"] = (
            result["delitos_patrimonio"].fillna(0) +
            result["delitos_seguridad_personal"].fillna(0)
        )
        
        # Calcular tasa por 1000 habitantes
        result["tasa_criminalidad_1000hab"] = (
            (result["total_delitos"] / result["poblacion_total"]) * 1000
        ).fillna(0.0)
        
        result = result.drop(columns=["total_delitos", "poblacion_total"])
    else:
        logger.warning("No hay datos de población, tasa_criminalidad_1000hab será None")
        result["tasa_criminalidad_1000hab"] = None
    
    # 7. Rellenar valores nulos y asegurar tipos correctos
    result["delitos_patrimonio"] = result["delitos_patrimonio"].fillna(0).astype(int)
    result["delitos_seguridad_personal"] = result["delitos_seguridad_personal"].fillna(0).astype(int)
    result["tasa_criminalidad_1000hab"] = result["tasa_criminalidad_1000hab"].fillna(0.0).astype(float)
    if "percepcion_inseguridad" in result.columns:
        result["percepcion_inseguridad"] = result["percepcion_inseguridad"].fillna(None)
    
    # 8. Filtrar solo registros válidos
    result = result[
        result["barrio_id"].notna() &
        result["anio"].notna() &
        result["trimestre"].notna()
    ].copy()
    
    # Asegurar tipos
    result["barrio_id"] = result["barrio_id"].astype(int)
    result["anio"] = result["anio"].astype(int)
    result["trimestre"] = result["trimestre"].astype(int)
    
    logger.info(
        "Seguridad: %s registros procesados para %s barrios únicos",
        len(result),
        result["barrio_id"].nunique()
    )
    
    return result

