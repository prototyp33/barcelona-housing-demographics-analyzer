"""
Script de extracción de precios de vivienda para el barrio de Gràcia (2020-2025)
usando el ecosistema existente del proyecto (Portal Dades + transformaciones ETL).

Issue: #199
Author: Equipo A - Data Infrastructure
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import pandas as pd

import sys

# Asegurar imports del proyecto (src/) cuando se ejecuta desde spike-data-validation/scripts
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database_setup import create_connection, ensure_database_path
from src.extraction import PortalDadesExtractor
from src.extraction.base import DATA_RAW_DIR
from src.etl.transformations.enrichment import prepare_portaldades_precios


LOG_DIR = Path("spike-data-validation/data/logs")
RAW_DIR = Path("spike-data-validation/data/raw")
PROCESSED_DB_DIR = Path("data/processed")

LOG_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """
    Configura logging básico para el script.

    Se escribe tanto a consola como a un archivo en ``spike-data-validation/data/logs``.
    """
    log_path = LOG_DIR / "ine_extraction.log"

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = []
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)


@dataclass(frozen=True)
class GraciaConfig:
    """
    Configuración de barrios y rango temporal para el spike de Gràcia.

    Attributes:
        year_start: Año inicial (incluido).
        year_end: Año final (incluido).
        gracia_district_name: Nombre del distrito en ``dim_barrios.distrito_nombre``.
    """

    year_start: int = 2020
    year_end: int = 2025
    gracia_district_name: str = "Gràcia"


def load_dim_barrios() -> pd.DataFrame:
    """
    Carga la tabla ``dim_barrios`` desde la base de datos principal del proyecto.

    Returns:
        DataFrame con la dimensión de barrios.

    Raises:
        FileNotFoundError: Si la base de datos no existe.
        ValueError: Si la tabla ``dim_barrios`` está vacía.
    """
    # 1) Intentar cargar desde SQLite
    try:
        db_path = ensure_database_path(
            db_path=Path("database.db"),
            processed_dir=PROCESSED_DB_DIR,
        )
        if db_path.exists():
            conn = create_connection(db_path)
            try:
                df = pd.read_sql_query("SELECT * FROM dim_barrios", conn)
            finally:
                conn.close()

            if not df.empty:
                logger.info("dim_barrios cargada desde SQLite con %s registros", len(df))
                return df
    except Exception as exc:  # noqa: BLE001
        logger.warning("No se pudo cargar dim_barrios desde SQLite (%s). Se usará fallback CSV.", exc)

    # 2) Fallback: CSV de dimensión en data/processed
    fallback_csv = Path("data/processed/barrio_location_ids.csv")
    if not fallback_csv.exists():
        raise FileNotFoundError(
            "No se pudo cargar dim_barrios desde SQLite y no existe el fallback CSV: "
            f"{fallback_csv}",
        )

    df = pd.read_csv(fallback_csv)
    if df.empty:
        raise ValueError(f"El fallback CSV de dim_barrios está vacío: {fallback_csv}")

    logger.info("dim_barrios cargada desde CSV con %s registros", len(df))
    return df


def get_gracia_barrio_ids(dim_barrios: pd.DataFrame, config: GraciaConfig) -> List[int]:
    """
    Obtiene los ``barrio_id`` pertenecientes al distrito de Gràcia.

    Args:
        dim_barrios: DataFrame con la dimensión de barrios.
        config: Configuración del spike (incluye nombre del distrito).

    Returns:
        Lista de identificadores de barrio para el distrito de Gràcia.

    Raises:
        ValueError: Si no se encuentran barrios para el distrito indicado.
    """
    if dim_barrios.empty:
        raise ValueError("dim_barrios está vacío al buscar barrios de Gràcia")

    df = dim_barrios.copy()
    if "distrito_nombre" not in df.columns:
        raise ValueError(
            "La tabla dim_barrios no tiene la columna 'distrito_nombre', "
            "necesaria para filtrar el distrito de Gràcia.",
        )

    mask = df["distrito_nombre"].str.strip().str.lower() == config.gracia_district_name.lower()
    gracia_rows = df.loc[mask]

    if gracia_rows.empty:
        raise ValueError(
            "No se encontraron barrios para el distrito de Gràcia en dim_barrios. "
            "Revisa los datos de dimensión.",
        )

    barrio_ids = sorted(int(value) for value in gracia_rows["barrio_id"].unique())
    logger.info("Barrios de Gràcia detectados: %s", barrio_ids)
    return barrio_ids


def ensure_portaldades_indicator(
    indicator_id: str,
) -> Tuple[List[Dict[str, str]], Dict[str, Path]]:
    """
    Garantiza que el indicador de Portal de Dades esté descargado como CSV.

    Usa ``PortalDadesExtractor.extraer_y_descargar_habitatge`` con el
    ``output_dir`` global de extracción del proyecto.

    Args:
        indicator_id: Identificador del indicador en Portal Dades
            (por ejemplo ``bxtvnxvukh``).

    Returns:
        Tupla ``(indicadores, archivos)`` tal y como devuelve el extractor.

    Raises:
        RuntimeError: Si no se puede descargar ni localizar el indicador requerido.
    """
    # Si el indicador ya está en disco, evitamos llamadas a red (y dependencias de credenciales)
    portaldades_dir = DATA_RAW_DIR / "portaldades"
    if portaldades_dir.exists():
        matches = list(portaldades_dir.glob(f"*_{indicator_id}.csv"))
        if matches:
            logger.info("Indicador %s ya existe en disco (%s). Se omite descarga.", indicator_id, matches[0])
            return [], {indicator_id: matches[0]}

    extractor = PortalDadesExtractor(output_dir=DATA_RAW_DIR)
    indicadores, archivos = extractor.extraer_y_descargar_habitatge(
        descargar=True,
        formato="CSV",
        max_pages=None,
    )

    if indicator_id not in archivos or archivos[indicator_id] is None:
        # Como fallback, confiamos en que el CSV exista ya en el directorio.
        portaldades_dir = DATA_RAW_DIR / "portaldades"
        if not portaldades_dir.exists():
            raise RuntimeError(
                f"No se encontró el indicador {indicator_id} ni el directorio "
                f"{portaldades_dir}",
            )
        logger.warning(
            "El indicador %s no se descargó explícitamente; se asumirá que su CSV "
            "ya existe en %s",
            indicator_id,
            portaldades_dir,
        )
    else:
        logger.info("Indicador %s descargado correctamente en %s", indicator_id, archivos[indicator_id])

    return indicadores, archivos


def filter_gracia_prices(
    venta_df: pd.DataFrame,
    gracia_barrio_ids: Iterable[int],
    config: GraciaConfig,
) -> pd.DataFrame:
    """
    Filtra el DataFrame de precios del Portal de Dades para Gràcia 2020-2025.

    Args:
        venta_df: DataFrame de precios de venta generado por
            ``prepare_portaldades_precios``.
        gracia_barrio_ids: Identificadores de barrio pertenecientes a Gràcia.
        config: Configuración con rango temporal.

    Returns:
        DataFrame filtrado con columnas mínimas para el spike.
    """
    if venta_df.empty:
        logger.warning("DataFrame de venta vacío; no hay datos para filtrar")
        return pd.DataFrame()

    df = venta_df.copy()
    required_cols = {"barrio_id", "anio", "precio_m2_venta", "dataset_id", "source"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Columnas faltantes en venta_df: {missing}")

    df = df[df["barrio_id"].isin(list(gracia_barrio_ids))]
    df = df[(df["anio"] >= config.year_start) & (df["anio"] <= config.year_end)]

    if df.empty:
        logger.warning(
            "No se encontraron registros de precios para Gràcia en el rango %s-%s",
            config.year_start,
            config.year_end,
        )
        return pd.DataFrame()

    # Selección y renombrado de columnas mínimas para el spike
    df = df[
        [
            "barrio_id",
            "anio",
            "periodo",
            "trimestre",
            "precio_m2_venta",
            "dataset_id",
            "source",
        ]
    ].copy()
    df = df.rename(columns={"precio_m2_venta": "precio_m2"})

    logger.info(
        "Filtrado de precios para Gràcia %s-%s: %s registros",
        config.year_start,
        config.year_end,
        len(df),
    )
    return df


def save_gracia_prices(df: pd.DataFrame) -> Path:
    """
    Guarda el DataFrame de precios de Gràcia en CSV para el spike.

    Args:
        df: DataFrame con precios filtrados.

    Returns:
        Ruta del archivo CSV generado.
    """
    output_path = RAW_DIR / "ine_precios_gracia.csv"
    df.to_csv(output_path, index=False, encoding="utf-8")
    logger.info("Datos de precios de Gràcia guardados en %s", output_path)
    return output_path


def write_summary(
    df: pd.DataFrame,
    gracia_barrio_ids: Iterable[int],
    config: GraciaConfig,
) -> Path:
    """
    Genera un resumen estadístico de la extracción para el Issue #199.

    Args:
        df: DataFrame con precios filtrados.
        gracia_barrio_ids: Lista de ``barrio_id`` de Gràcia.
        config: Configuración del spike.

    Returns:
        Ruta del archivo JSON con el resumen.
    """
    if df.empty:
        summary = {
            "total_registros": 0,
            "barrios_ids": list(gracia_barrio_ids),
            "años_unicos": [],
            "precio_m2_min": None,
            "precio_m2_max": None,
            "precio_m2_media": None,
            "cobertura_temporal": None,
            "warning": "DataFrame vacío tras filtrado para Gràcia",
        }
    else:
        summary = {
            "total_registros": int(len(df)),
            "barrios_ids": sorted(int(value) for value in df["barrio_id"].unique()),
            "años_unicos": sorted(int(value) for value in df["anio"].unique()),
            "precio_m2_min": float(df["precio_m2"].min()),
            "precio_m2_max": float(df["precio_m2"].max()),
            "precio_m2_media": float(df["precio_m2"].mean()),
            "cobertura_temporal": f"{int(df['anio'].min())}-{int(df['anio'].max())}",
        }

    summary_path = LOG_DIR / "extraction_summary_199.json"
    with open(summary_path, "w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2, ensure_ascii=False)

    logger.info("Resumen de extracción guardado en %s", summary_path)

    if summary["total_registros"] < 100:
        logger.warning(
            "Solo se extrajeron %s registros para Gràcia (objetivo: ≥100).",
            summary["total_registros"],
        )
    else:
        logger.info(
            "✓ Criterio de tamaño cumplido: %s registros (≥100).",
            summary["total_registros"],
        )

    return summary_path


def main() -> int:
    """
    Función principal del script.

    Orquesta la descarga de Portal Dades, el procesamiento mediante las
    transformaciones existentes y el filtrado para Gràcia 2020-2025.

    Returns:
        Código de salida del proceso (0 si todo va bien, 1 si hay errores).
    """
    setup_logging()
    config = GraciaConfig()

    logger.info("=== Issue #199: Extracción de precios para Gràcia %s-%s ===", config.year_start, config.year_end)

    try:
        # 1) Asegurar que el indicador de precios por m² está disponible
        indicator_id = "bxtvnxvukh"
        ensure_portaldades_indicator(indicator_id)

        # 2) Cargar dim_barrios desde la base de datos principal
        dim_barrios = load_dim_barrios()
        gracia_barrio_ids = get_gracia_barrio_ids(dim_barrios, config)

        # 3) Preparar datos de precios del Portal de Dades usando la ETL existente
        portaldades_dir = DATA_RAW_DIR / "portaldades"
        reference_time = datetime.now(timezone.utc)
        metadata_file = portaldades_dir / "indicadores_habitatge.csv"

        venta_df, _ = prepare_portaldades_precios(
            portaldades_dir=portaldades_dir,
            dim_barrios=dim_barrios,
            reference_time=reference_time,
            metadata_file=metadata_file if metadata_file.exists() else None,
        )

        # 4) Filtrar solo Gràcia y rango temporal 2020-2025
        gracia_df = filter_gracia_prices(
            venta_df=venta_df,
            gracia_barrio_ids=gracia_barrio_ids,
            config=config,
        )

        if gracia_df.empty:
            logger.error(
                "No se obtuvieron datos de precios para Gràcia en el rango %s-%s.",
                config.year_start,
                config.year_end,
            )
            # Aun así generamos un resumen vacío para facilitar el debugging.
            write_summary(gracia_df, gracia_barrio_ids, config)
            return 1

        # 5) Guardar CSV y resumen
        save_gracia_prices(gracia_df)
        write_summary(gracia_df, gracia_barrio_ids, config)

        logger.info("✓ Extracción completada correctamente para Gràcia %s-%s", config.year_start, config.year_end)
        return 0

    except Exception as exc:  # noqa: BLE001
        logger.error("Error inesperado en la extracción de precios para Gràcia: %s", exc, exc_info=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())


