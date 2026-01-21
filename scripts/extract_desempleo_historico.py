#!/usr/bin/env python3
"""
Extracción histórica de desempleo (atur registrat) a `data/raw/`.

Este script descarga el dataset de desempleo desde Open Data BCN, normaliza y limpia
columnas (usando `DesempleoExtractor`), filtra por rango de años y guarda el resultado
como CSV en `data/raw/opendatabcn/` (vía `BaseExtractor._save_raw_data`), registrándolo
también en `data/raw/manifest.json`.

Uso:
    python scripts/extract_desempleo_historico.py --year-start 2015 --year-end 2024
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Tuple

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.extraction.base import setup_logging
from src.extraction.desempleo_extractor import DesempleoExtractor


def _filter_year_range(df: pd.DataFrame, year_start: int, year_end: int) -> pd.DataFrame:
    """
    Filtra un DataFrame por rango de años usando la columna `anio`.

    Args:
        df: DataFrame con columna `anio`.
        year_start: Año inicial (inclusive).
        year_end: Año final (inclusive).

    Returns:
        DataFrame filtrado (copia).

    Raises:
        ValueError: Si no existe la columna `anio`.
    """
    if "anio" not in df.columns:
        raise ValueError("El DataFrame de desempleo no contiene columna 'anio'")

    df_work = df.copy()
    df_work["anio"] = pd.to_numeric(df_work["anio"], errors="coerce")
    df_work = df_work[df_work["anio"].notna()].copy()
    df_work["anio"] = df_work["anio"].astype(int)

    return df_work[(df_work["anio"] >= year_start) & (df_work["anio"] <= year_end)].copy()


def extract_desempleo_historico(
    year_start: int,
    year_end: int,
    output_dir: Path,
) -> Tuple[Path, pd.DataFrame]:
    """
    Extrae desempleo histórico y lo guarda como CSV en `data/raw/opendatabcn/`.

    Args:
        year_start: Año inicial (inclusive).
        year_end: Año final (inclusive).
        output_dir: Directorio base `data/raw`.

    Returns:
        Tupla con (path del CSV guardado, DataFrame filtrado).

    Raises:
        RuntimeError: Si la extracción no devuelve registros.
    """
    extractor = DesempleoExtractor(rate_limit_delay=1.5, output_dir=output_dir)
    df_raw, metadata = extractor.extract_all()

    if df_raw is None or df_raw.empty:
        raise RuntimeError("No se pudieron extraer datos de desempleo desde Open Data BCN")

    df_filtered = _filter_year_range(df_raw, year_start=year_start, year_end=year_end)
    if df_filtered.empty:
        raise RuntimeError(
            f"Extracción exitosa pero sin registros en el rango {year_start}-{year_end}. "
            f"Años detectados: {sorted(df_raw['anio'].dropna().unique().tolist()) if 'anio' in df_raw.columns else 'N/A'}"
        )

    # Guardar CSV y registrar en manifest.json
    saved_path = extractor._save_raw_data(
        data=df_filtered,
        filename="opendatabcn_desempleo",
        format="csv",
        year_start=year_start,
        year_end=year_end,
        data_type="desempleo",
    )

    logging.getLogger(__name__).info(
        "✅ Desempleo histórico guardado: %s (%s registros, años %s-%s)",
        saved_path,
        len(df_filtered),
        df_filtered["anio"].min(),
        df_filtered["anio"].max(),
    )
    logging.getLogger(__name__).debug("Metadata extracción desempleo: %s", metadata)

    return saved_path, df_filtered


def main() -> int:
    """CLI principal."""
    parser = argparse.ArgumentParser(description="Extraer desempleo histórico (Open Data BCN) a data/raw/")
    parser.add_argument("--year-start", type=int, default=2015, help="Año inicial (default: 2015)")
    parser.add_argument("--year-end", type=int, default=2024, help="Año final (default: 2024)")
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(Path("data") / "raw"),
        help="Directorio base de salida (default: data/raw)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Nivel de logging (default: INFO)",
    )
    args = parser.parse_args()

    log_level = getattr(logging, args.log_level)
    setup_logging(log_to_file=True, log_level=log_level)
    logger = logging.getLogger(__name__)

    year_start = int(args.year_start)
    year_end = int(args.year_end)
    if year_end < year_start:
        logger.error("year-end (%s) no puede ser menor que year-start (%s)", year_end, year_start)
        return 2

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        saved_path, df_filtered = extract_desempleo_historico(
            year_start=year_start,
            year_end=year_end,
            output_dir=output_dir,
        )
        logger.info(
            "Resumen: %s registros, %s barrios, %s años. Archivo: %s",
            len(df_filtered),
            df_filtered["barrio_nombre"].nunique() if "barrio_nombre" in df_filtered.columns else "N/A",
            df_filtered["anio"].nunique() if "anio" in df_filtered.columns else "N/A",
            saved_path,
        )
        return 0
    except (ValueError, RuntimeError) as exc:
        logger.error("Error en extracción de desempleo: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

