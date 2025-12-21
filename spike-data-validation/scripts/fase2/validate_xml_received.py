#!/usr/bin/env python3
"""
Validación rápida del XML recibido de la Sede Electrónica.

Ejecutar inmediatamente después de descargar el XML para verificar:
- Que el archivo existe y es válido XML
- Estructura básica (tags principales)
- Número aproximado de inmuebles
- Tamaño del archivo

Issue: #202 (Fase 2)
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict

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
    """Parsea argumentos CLI."""
    parser = argparse.ArgumentParser(
        description="Validación rápida del XML recibido de Catastro",
    )
    parser.add_argument(
        "--xml",
        type=str,
        default="spike-data-validation/data/raw/catastro_oficial/ECLTI250200147801.XML",
        help="Ruta al XML descargado",
    )
    parser.add_argument(
        "--max-elements",
        type=int,
        default=10_000,
        help="Máximo de elementos a procesar para validación rápida",
    )
    return parser.parse_args()


def _strip_ns(tag: str) -> str:
    """Elimina namespace de una etiqueta."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def validate_xml(xml_path: Path, max_elements: int) -> Dict[str, Any]:
    """
    Valida el XML y extrae información básica.

    Args:
        xml_path: Ruta al archivo XML.
        max_elements: Máximo de elementos a procesar.

    Returns:
        Diccionario con resultados de validación.
    """
    if not xml_path.exists():
        return {
            "valid": False,
            "error": f"Archivo no encontrado: {xml_path}",
        }

    file_size_mb = xml_path.stat().st_size / (1024 * 1024)

    try:
        # Intentar parsear el XML
        tree = ET.parse(xml_path)
        root = tree.getroot()
        root_tag = _strip_ns(root.tag)

        # Contar elementos relevantes
        inmueble_tags = {"INMUEBLE", "inmueble", "urbana", "URBANA", "DAT", "dat"}
        rc_tags = {"RC", "RefCat", "ref_catastral"}

        inmueble_count = 0
        rc_count = 0
        elements_processed = 0
        tags_seen = set()

        for event, elem in ET.iterparse(xml_path, events=("end",)):
            elements_processed += 1
            tag = _strip_ns(elem.tag)
            tags_seen.add(tag)

            if tag in inmueble_tags:
                inmueble_count += 1

            if tag in rc_tags and elem.text:
                rc_count += 1

            elem.clear()

            if elements_processed >= max_elements:
                break

        return {
            "valid": True,
            "file_size_mb": round(file_size_mb, 2),
            "root_tag": root_tag,
            "elements_processed": elements_processed,
            "inmueble_count_approx": inmueble_count,
            "rc_count_approx": rc_count,
            "tags_seen": sorted(list(tags_seen))[:20],  # Primeros 20 tags
            "max_elements_reached": elements_processed >= max_elements,
        }

    except ET.ParseError as exc:
        return {
            "valid": False,
            "error": f"Error al parsear XML: {exc}",
            "file_size_mb": round(file_size_mb, 2),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "valid": False,
            "error": f"Error inesperado: {exc}",
            "file_size_mb": round(file_size_mb, 2),
        }


def main() -> int:
    """Punto de entrada principal."""
    setup_logging()
    args = parse_args()

    xml_path = Path(args.xml)
    max_elements = int(args.max_elements)

    logger.info("=" * 70)
    logger.info("VALIDACIÓN RÁPIDA: XML Catastro Masivo")
    logger.info("=" * 70)
    logger.info("XML: %s", xml_path)
    logger.info("")

    result = validate_xml(xml_path, max_elements)

    if not result["valid"]:
        logger.error("✗ VALIDACIÓN FALLÓ")
        logger.error("  Error: %s", result.get("error"))
        if "file_size_mb" in result:
            logger.info("  Tamaño archivo: %s MB", result["file_size_mb"])
        return 1

    logger.info("✓ XML VÁLIDO")
    logger.info("  Tamaño: %s MB", result["file_size_mb"])
    logger.info("  Tag raíz: %s", result["root_tag"])
    logger.info("  Elementos procesados: %s", result["elements_processed"])
    logger.info("  Inmuebles aproximados: %s", result["inmueble_count_approx"])
    logger.info("  Referencias catastrales aproximadas: %s", result["rc_count_approx"])

    if result["max_elements_reached"]:
        logger.warning("  ⚠️  Se alcanzó el límite de elementos (%s)", max_elements)
        logger.warning("     El archivo puede ser más grande. Usa --max-elements para aumentar.")

    logger.info("")
    logger.info("Tags encontrados (primeros 20):")
    for tag in result["tags_seen"]:
        logger.info("  - %s", tag)

    # Guardar resultado en JSON
    json_path = LOG_DIR / "xml_validation_result.json"
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("")
    logger.info("✓ Resultado guardado: %s", json_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

