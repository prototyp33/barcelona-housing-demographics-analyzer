#!/usr/bin/env python3
"""
Extracción histórica de renta per cápita por barrio (2015-2024) a `data/raw/opendatabcn/`.

Motivación:
- El dataset CKAN `renda-disponible-llars-bcn` que usamos en `extract_priority_sources.py`
  suele traer solo el último año disponible (p.ej. 2022).
- Para correlaciones temporales necesitamos la serie histórica 2015-2024.

Estrategia:
- Usar `BcnIncomeExtractor` (URLs anuales conocidas + patrones) para descargar por año.
- Unificar el resultado en un DataFrame con columnas compatibles con el pipeline actual:
  `Any`, `Codi_Barri`, `Nom_Barri`, `Import_Euros`.
- Guardar el CSV vía `BaseExtractor._save_raw_data` bajo `data/raw/opendatabcn/` y registrar
  en `data/raw/manifest.json` con tipo `renta`.

Uso:
    python scripts/extract_renta_historica.py --year-start 2015 --year-end 2024
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.extraction.base import BaseExtractor, setup_logging  # noqa: E402
from src.extraction.bcn_income import BcnIncomeExtractor  # noqa: E402


def build_renta_historica_df(year_start: int, year_end: int) -> pd.DataFrame:
    """
    Construye un DataFrame histórico de renta per cápita por barrio.

    Args:
        year_start: Año inicial (inclusive).
        year_end: Año final (inclusive).

    Returns:
        DataFrame con columnas: Any, Codi_Barri, Nom_Barri, Import_Euros.

    Raises:
        RuntimeError: Si no se pudieron descargar datos.
    """
    extractor = BcnIncomeExtractor(rate_limit_delay=2.0, output_dir=Path("data") / "raw")

    # Nota: `BcnIncomeExtractor._fetch_year` puede lanzar excepción cuando no existe CSV para un año.
    # Para extracción histórica queremos best-effort: continuar y registrar los años faltantes.
    frames: list[pd.DataFrame] = []
    for year in range(year_start, year_end + 1):
        try:
            df_year = extractor._fetch_year(year)  # noqa: SLF001 (acceso controlado para robustez)
        except Exception as exc:  # noqa: BLE001
            logging.getLogger(__name__).warning("No se pudo obtener renta para %s: %s", year, exc)
            continue
        if df_year is None or df_year.empty:
            logging.getLogger(__name__).warning("No se obtuvieron datos (vacío) para %s", year)
            continue
        frames.append(df_year)

    if not frames:
        raise RuntimeError("No se pudo obtener ningún CSV de renta desde Open Data BCN")

    df = pd.concat(frames, ignore_index=True)

    # Normalizar al esquema esperado por el resto del pipeline (renta por sección/barrio)
    df_out = df.copy()
    df_out = df_out.rename(
        columns={
            "anio": "Any",
            "codigo_barrio": "Codi_Barri",
            "barrio_nombre": "Nom_Barri",
            "renta_per_capita": "Import_Euros",
        }
    )

    # Validaciones mínimas
    required = {"Any", "Codi_Barri", "Nom_Barri", "Import_Euros"}
    missing = required - set(df_out.columns)
    if missing:
        raise RuntimeError(f"Columnas faltantes tras normalización: {missing}")

    df_out["Any"] = pd.to_numeric(df_out["Any"], errors="coerce").astype("Int64")
    df_out["Codi_Barri"] = pd.to_numeric(df_out["Codi_Barri"], errors="coerce").astype("Int64")
    df_out["Import_Euros"] = pd.to_numeric(df_out["Import_Euros"], errors="coerce")
    df_out["Nom_Barri"] = df_out["Nom_Barri"].astype(str)

    df_out = df_out.dropna(subset=["Any", "Codi_Barri", "Import_Euros"]).copy()
    df_out["Any"] = df_out["Any"].astype(int)
    df_out["Codi_Barri"] = df_out["Codi_Barri"].astype(int)

    return df_out[["Any", "Codi_Barri", "Nom_Barri", "Import_Euros"]].sort_values(
        ["Any", "Codi_Barri"]
    )


def main() -> int:
    """CLI principal."""
    parser = argparse.ArgumentParser(description="Extraer renta histórica 2015-2024 a data/raw/opendatabcn/")
    parser.add_argument("--year-start", type=int, default=2015, help="Año inicial (default: 2015)")
    parser.add_argument("--year-end", type=int, default=2024, help="Año final (default: 2024)")
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Nivel de logging (default: INFO)",
    )
    args = parser.parse_args()

    setup_logging(log_to_file=True, log_level=getattr(logging, args.log_level))
    logger = logging.getLogger(__name__)

    year_start = int(args.year_start)
    year_end = int(args.year_end)
    if year_end < year_start:
        logger.error("year-end (%s) no puede ser menor que year-start (%s)", year_end, year_start)
        return 2

    try:
        df_out = build_renta_historica_df(year_start=year_start, year_end=year_end)
    except Exception as exc:  # noqa: BLE001
        logger.error("Error extrayendo renta histórica: %s", exc, exc_info=True)
        return 1

    if df_out.empty:
        logger.error("Extracción final vacía. No se guardará ningún archivo.")
        return 1

    # Guardar bajo opendatabcn para que el ETL lo descubra automáticamente
    saver = BaseExtractor(source_name="OpenDataBCN", rate_limit_delay=0.0, output_dir=Path("data") / "raw")
    saved_path = saver._save_raw_data(
        data=df_out,
        filename="opendatabcn_renda-disponible-llars-bcn",
        format="csv",
        year_start=year_start,
        year_end=year_end,
        data_type="renta",
    )

    logger.info(
        "✅ Renta histórica guardada: %s (%s registros, %s barrios, años %s-%s)",
        saved_path,
        len(df_out),
        df_out["Codi_Barri"].nunique(),
        df_out["Any"].min(),
        df_out["Any"].max(),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

