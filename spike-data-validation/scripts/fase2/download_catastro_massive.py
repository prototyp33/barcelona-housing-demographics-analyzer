#!/usr/bin/env python3
"""
Fase 2 - Descarga masiva Catastro (entrada para consulta oficial).

Este script NO descarga directamente el XML masivo desde la Sede (el flujo es
asíncrono y requiere autenticación), sino que:

1. Construye un fichero XML de ENTRADA con referencias catastrales (RC) usando
   el cliente oficial `CatastroOficialClient`.
2. Imprime instrucciones claras para:
   - Subir el XML a la Sede Electrónica.
   - Esperar el procesamiento.
   - Descargar el XML de salida.

Está pensado como envoltorio de alto nivel para la Fase 2 del spike (Issue #202),
reutilizando el trabajo previo de `catastro_oficial_client.py`.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import List

import pandas as pd
import sys

# Añadir directorio padre para importar scripts comunes del spike
# NOTA: Este import es temporal. Idealmente, cuando el código se migre a producción,
# CatastroOficialClient estará en src/extraction/catastro/oficial_client.py
# y este script importará desde ahí. Ver docs/architecture/DEPENDENCIES.md
SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from catastro_oficial_client import CatastroOficialClient  # noqa: E402

LOG_DIR = Path("spike-data-validation/data/logs")
RAW_DIR = Path("spike-data-validation/data/raw")

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """Configura logging básico para el script."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def parse_args() -> argparse.Namespace:
    """Parsea argumentos CLI."""
    parser = argparse.ArgumentParser(
        description="Genera fichero XML de entrada para consulta masiva oficial del Catastro (Fase 2).",
    )
    parser.add_argument(
        "--refs-csv",
        type=str,
        default=str(RAW_DIR / "gracia_refs_seed.csv"),
        help="CSV con referencias catastrales (por defecto, seed de Gràcia).",
    )
    parser.add_argument(
        "--rc-column",
        type=str,
        default="referencia_catastral",
        help="Nombre de la columna que contiene la referencia catastral.",
    )
    parser.add_argument(
        "--out-xml",
        type=str,
        default=str(RAW_DIR / "catastro_oficial/consulta_masiva_entrada.xml"),
        help="Ruta de salida para el XML de entrada.",
    )
    parser.add_argument(
        "--max-refs",
        type=int,
        default=0,
        help="Máximo de referencias a incluir (0 = sin límite).",
    )
    return parser.parse_args()


def load_referencias(path: Path, rc_column: str, max_refs: int) -> List[str]:
    """
    Carga referencias catastrales desde un CSV.

    Args:
        path: Ruta al CSV con referencias.
        rc_column: Nombre de la columna de referencia catastral.
        max_refs: Máximo de referencias a devolver (0 = sin límite).

    Returns:
        Lista de referencias catastrales como strings.

    Raises:
        FileNotFoundError: Si el CSV no existe.
        ValueError: Si la columna no está presente o no hay referencias válidas.
    """
    if not path.exists():
        raise FileNotFoundError(f"CSV de referencias no encontrado: {path}")

    df = pd.read_csv(path)
    if rc_column not in df.columns:
        raise ValueError(f"Columna '{rc_column}' no encontrada en {path} (cols={list(df.columns)})")

    refs = (
        df[rc_column]
        .dropna()
        .astype(str)
        .str.strip()
        .replace("", pd.NA)
        .dropna()
        .unique()
        .tolist()
    )

    if max_refs and len(refs) > max_refs:
        refs = refs[:max_refs]

    if not refs:
        raise ValueError("No se encontraron referencias catastrales válidas en el CSV.")

    logger.info("Referencias cargadas: %s (usando columna '%s')", len(refs), rc_column)
    return refs


def main() -> int:
    """Punto de entrada principal."""
    setup_logging()
    args = parse_args()

    refs_csv = Path(args.refs_csv)
    out_xml = Path(args.out_xml)
    max_refs = int(args.max_refs)

    try:
        referencias = load_referencias(refs_csv, args.rc_column, max_refs)
    except (FileNotFoundError, ValueError) as exc:
        logger.error("Error al cargar referencias: %s", exc)
        return 1

    client = CatastroOficialClient()
    try:
        # Generar XML con formato correcto según documentación oficial (Anexo 1)
        # Formato: LISTADATOS con FEC, FIN y bloques DAT/RC
        xml_path = client.generate_input_xml(referencias, output_file=out_xml)
        
    except ValueError as exc:
        logger.error("Error generando XML de entrada: %s", exc)
        return 1

    instrucciones = client.generate_instructions(xml_path)
    print(instrucciones)

    logger.info("XML de entrada generado correctamente: %s", xml_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


