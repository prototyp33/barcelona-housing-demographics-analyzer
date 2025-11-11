#!/usr/bin/env python3
"""CLI para ejecutar la transformación y carga del pipeline ETL."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.etl import run_etl


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ejecuta la etapa de Transformación y Carga hacia SQLite",
    )
    parser.add_argument(
        "--raw-dir",
        default="data/raw",
        help="Directorio base donde se encuentran los datos crudos",
    )
    parser.add_argument(
        "--processed-dir",
        default="data/processed",
        help="Directorio donde se guardarán los datos procesados y la base de datos",
    )
    parser.add_argument(
        "--db-path",
        default=None,
        help="Ruta del archivo SQLite a generar (por defecto data/processed/database.db)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Nivel de logging para la ejecución",
    )
    return parser


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    configure_logging(args.log_level)

    try:
        db_path = run_etl(
            raw_base_dir=Path(args.raw_dir),
            processed_dir=Path(args.processed_dir),
            db_path=Path(args.db_path) if args.db_path else None,
        )
        logging.info("ETL finalizado. Base de datos disponible en %s", db_path)
        print(f"✅ ETL completado. Base de datos: {db_path}")
        return 0
    except Exception as exc:  # noqa: BLE001
        logging.exception("La ejecución del ETL falló: %s", exc)
        print(f"❌ Error durante el ETL: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
