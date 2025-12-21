#!/usr/bin/env python3
"""
Fase 2 - Parser XML Catastro Masivo → CSV.

Wrapper mejorado del parser existente, específico para Fase 2.
Incluye validación y logging mejorado.

Issue: #202 (Fase 2)
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Dict

import pandas as pd

# Añadir directorio padre para importar scripts comunes del spike
# NOTA: Estos imports son temporales. Idealmente, cuando el código se migre a producción,
# estos módulos estarán en src/extraction/catastro/ y los scripts importarán desde ahí.
# Ver docs/architecture/DEPENDENCIES.md para reglas de dependencias.
SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from parse_catastro_masivo_output import (  # noqa: E402
    _heuristic_iterparse,
    _try_client_parser,
)

LOG_DIR = Path("spike-data-validation/data/logs")
PROCESSED_DIR = Path("spike-data-validation/data/processed")

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """Configura logging."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def parse_args() -> argparse.Namespace:
    """Parsea argumentos CLI."""
    parser = argparse.ArgumentParser(
        description="Parser XML Catastro Masivo → CSV (Fase 2)",
    )
    parser.add_argument(
        "--xml",
        type=str,
        default="spike-data-validation/data/raw/catastro_oficial/ECLTI250200147801.XML",
        help="Ruta al XML descargado de la Sede Electrónica",
    )
    parser.add_argument(
        "--out",
        type=str,
        default=str(PROCESSED_DIR / "fase2/catastro_barcelona_parsed.csv"),
        help="Ruta de salida para el CSV parseado",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limitar número de inmuebles parseados (0=sin límite, útil para testing)",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Ejecutar validaciones después del parseo",
    )
    return parser.parse_args()


def validate_parsed_data(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Valida el DataFrame parseado y genera métricas.

    Args:
        df: DataFrame con datos parseados.

    Returns:
        Diccionario con métricas de validación.
    """
    if df.empty:
        return {
            "valid": False,
            "error": "DataFrame vacío",
            "total_rows": 0,
        }

    total = len(df)
    required_cols = ["referencia_catastral"]
    optional_cols = ["superficie_m2", "ano_construccion", "plantas", "direccion_normalizada"]

    # Validar columnas requeridas
    missing_required = [col for col in required_cols if col not in df.columns]
    if missing_required:
        return {
            "valid": False,
            "error": f"Columnas requeridas faltantes: {missing_required}",
            "total_rows": total,
        }

    # Calcular completitud
    completitud = {}
    for col in optional_cols:
        if col in df.columns:
            non_null = df[col].notna().sum()
            completitud[col] = {
                "non_null": int(non_null),
                "null": int(total - non_null),
                "pct_complete": round(100 * non_null / total, 2) if total > 0 else 0.0,
            }

    # Validar referencias catastrales
    refs_valid = df["referencia_catastral"].notna().sum()
    refs_unique = df["referencia_catastral"].nunique()

    # Validar tipos de datos
    type_issues = []
    if "superficie_m2" in df.columns:
        if not pd.api.types.is_numeric_dtype(df["superficie_m2"]):
            type_issues.append("superficie_m2 no es numérico")
    if "ano_construccion" in df.columns:
        if not pd.api.types.is_numeric_dtype(df["ano_construccion"]):
            type_issues.append("ano_construccion no es numérico")

    return {
        "valid": True,
        "total_rows": total,
        "referencias_validas": int(refs_valid),
        "referencias_unicas": int(refs_unique),
        "completitud": completitud,
        "type_issues": type_issues,
    }


def main() -> int:
    """Punto de entrada principal."""
    setup_logging()
    args = parse_args()

    xml_path = Path(args.xml)
    out_path = Path(args.out)
    limit = int(args.limit)

    if not xml_path.exists():
        logger.error("XML no encontrado: %s", xml_path)
        return 1

    logger.info("=" * 70)
    logger.info("FASE 2: Parseando XML Catastro Masivo")
    logger.info("=" * 70)
    logger.info("XML: %s", xml_path)
    logger.info("Output: %s", out_path)
    logger.info("")

    # Intentar parser del cliente primero
    logger.info("Intentando parser del cliente oficial...")
    rows = _try_client_parser(xml_path)

    if rows:
        logger.info("✓ Parser del cliente devolvió %s inmuebles", len(rows))
    else:
        logger.warning("Parser del cliente devolvió 0 resultados")
        logger.info("Usando parser heurístico...")
        rows = _heuristic_iterparse(xml_path, limit=limit)
        logger.info("✓ Parser heurístico devolvió %s inmuebles", len(rows))

    if not rows:
        logger.error("No se encontraron inmuebles en el XML")
        return 1

    # Convertir a DataFrame
    df = pd.DataFrame(rows)
    logger.info("DataFrame creado: %s filas, %s columnas", len(df), len(df.columns))

    # Validar si se solicita
    if args.validate:
        logger.info("")
        logger.info("Ejecutando validaciones...")
        validation = validate_parsed_data(df)
        if validation["valid"]:
            logger.info("✓ Validación pasada")
            logger.info("  Total filas: %s", validation["total_rows"])
            logger.info("  Referencias únicas: %s", validation["referencias_unicas"])
            for col, stats in validation["completitud"].items():
                logger.info(
                    "  %s: %s%% completo (%s/%s)",
                    col,
                    stats["pct_complete"],
                    stats["non_null"],
                    validation["total_rows"],
                )
            if validation["type_issues"]:
                logger.warning("  Issues de tipos: %s", validation["type_issues"])
        else:
            logger.error("✗ Validación falló: %s", validation.get("error"))
            return 1

    # Guardar CSV
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False, encoding="utf-8")
    logger.info("")
    logger.info("✓ CSV guardado: %s", out_path)
    logger.info("  Tamaño: %s KB", round(out_path.stat().st_size / 1024, 2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

