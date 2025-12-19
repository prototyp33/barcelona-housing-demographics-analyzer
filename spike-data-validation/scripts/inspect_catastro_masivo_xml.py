#!/usr/bin/env python3
"""
Inspector del XML de salida de la consulta masiva oficial del Catastro (Fase 2).

Objetivo:
- No asumimos estructura exacta del XML descargado desde la Sede.
- Este script genera evidencia (conteos de tags y paths) para implementar un parser robusto.

Uso:
  .venv-spike/bin/python spike-data-validation/scripts/inspect_catastro_masivo_xml.py --xml path/al/salida.xml

Output:
- spike-data-validation/data/logs/masivo_xml_inspection.json
"""

from __future__ import annotations

import argparse
import json
import logging
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import xml.etree.ElementTree as ET

LOG_DIR = Path("spike-data-validation/data/logs")
logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """Configura logging."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def parse_args() -> argparse.Namespace:
    """Parsea argumentos."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--xml", type=str, required=True, help="Ruta al XML descargado desde la Sede")
    parser.add_argument(
        "--max-elements",
        type=int,
        default=200_000,
        help="Máximo de elementos a procesar (seguridad).",
    )
    return parser.parse_args()


def _strip_ns(tag: str) -> str:
    """Elimina namespace de una etiqueta ET."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def inspect_xml(xml_path: Path, max_elements: int) -> Dict[str, Any]:
    """
    Inspecciona tags y captura algunos ejemplos.
    """
    if not xml_path.exists():
        raise FileNotFoundError(f"XML no encontrado: {xml_path}")

    tag_counts: Counter[str] = Counter()
    sample_values: Dict[str, str] = {}
    elements_processed = 0

    # iterparse para no cargar todo en RAM
    for event, elem in ET.iterparse(xml_path, events=("end",)):
        elements_processed += 1
        tag = _strip_ns(elem.tag)
        tag_counts[tag] += 1

        # Capturar algunos textos relevantes
        if elem.text and elem.text.strip():
            txt = elem.text.strip()
            if tag in {"RC", "RefCat", "SUP", "ANYO", "PLANTAS", "DIRECCION", "cod", "des"}:
                sample_values.setdefault(tag, txt[:200])

        if elements_processed >= max_elements:
            break

        # liberar memoria
        elem.clear()

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "xml_path": str(xml_path),
        "elements_processed": elements_processed,
        "top_tags": tag_counts.most_common(40),
        "sample_values": sample_values,
    }


def main() -> int:
    setup_logging()
    args = parse_args()
    xml_path = Path(args.xml)

    logger.info("Inspeccionando XML masivo: %s", xml_path)
    result = inspect_xml(xml_path, max_elements=int(args.max_elements))

    out_path = LOG_DIR / "masivo_xml_inspection.json"
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("✓ Inspección guardada: %s", out_path)

    # Mostrar resumen por consola
    logger.info("Top tags: %s", result["top_tags"][:10])
    logger.info("Samples: %s", result["sample_values"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


