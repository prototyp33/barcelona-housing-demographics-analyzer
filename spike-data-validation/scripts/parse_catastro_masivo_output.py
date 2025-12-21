#!/usr/bin/env python3
"""
Parser del XML de salida de la consulta masiva oficial del Catastro (Fase 2).

Este parser está diseñado para ser robusto y *no asumir* una única estructura.
Estrategia:
- Intentar primero el parser actual de `CatastroOficialClient.parse_output_xml` (si encaja).
- Si devuelve 0 resultados, usar un modo heurístico iterativo buscando bloques tipo INMUEBLE.

Inputs:
- XML descargado desde la Sede (consulta masiva NO protegidos).

Outputs:
- JSONL/CSV con columnas: referencia_catastral, superficie_m2, ano_construccion, plantas, direccion_normalizada

Uso:
  .venv-spike/bin/python spike-data-validation/scripts/parse_catastro_masivo_output.py \\
    --xml spike-data-validation/data/raw/catastro_oficial/consulta_masiva_salida.xml \\
    --out spike-data-validation/data/processed/catastro_barcelona_parsed.csv
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import xml.etree.ElementTree as ET

import sys

scripts_dir = Path(__file__).parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from catastro_oficial_client import CatastroOficialClient

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """Configura logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def parse_args() -> argparse.Namespace:
    """Parsea argumentos CLI."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--xml", type=str, required=True)
    parser.add_argument("--out", type=str, required=True)
    parser.add_argument("--limit", type=int, default=0, help="Limitar número de inmuebles parseados (0=sin límite)")
    return parser.parse_args()


def _strip_ns(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _try_client_parser(xml_path: Path) -> List[Dict[str, Any]]:
    client = CatastroOficialClient()
    try:
        return client.parse_output_xml(xml_path)
    except Exception as exc:  # noqa: BLE001
        logger.warning("parse_output_xml falló: %s", exc)
        return []


def _heuristic_iterparse(xml_path: Path, limit: int) -> List[Dict[str, Any]]:
    """
    Parser heurístico: busca elementos BIE (bienes/inmuebles) en el XML de salida.
    
    Estructura esperada:
    DS -> LDS -> DSA -> LBI -> BIE -> IBI (datos), DTR (dirección), FIN (finca), etc.
    """
    if not xml_path.exists():
        raise FileNotFoundError(f"XML no encontrado: {xml_path}")

    results: List[Dict[str, Any]] = []
    # Buscar BIE (bienes/inmuebles) en el XML
    inmueble_like = {"BIE", "INMUEBLE", "inmueble"}

    for event, elem in ET.iterparse(xml_path, events=("end",)):
        tag = _strip_ns(elem.tag)
        if tag not in inmueble_like:
            continue

        # Extraer datos por tags hijos conocidos
        # Usar iter() para buscar recursivamente en todos los descendientes
        text_by_tag: Dict[str, str] = {}
        for descendant in elem.iter():
            dtag = _strip_ns(descendant.tag)
            if descendant.text and descendant.text.strip():
                # Guardar el texto del tag, pero priorizar PCA para referencia catastral
                if dtag == "PCA":
                    text_by_tag["PCA"] = descendant.text.strip()
                elif dtag not in text_by_tag:  # Solo guardar si no existe ya
                    text_by_tag[dtag] = descendant.text.strip()

        # Extraer referencia catastral (puede estar en PCA dentro de RCA dentro de IBI)
        rc = (
            text_by_tag.get("PCA") or 
            text_by_tag.get("RC") or 
            text_by_tag.get("RefCat") or 
            text_by_tag.get("ref_catastral")
        )
        
        # Extraer dirección (DTR contiene la dirección completa)
        direccion = text_by_tag.get("DTR") or text_by_tag.get("DIRECCION") or text_by_tag.get("ldt")
        
        # Extraer superficie (SUP dentro de IBI)
        sup = text_by_tag.get("SUP")
        
        # Extraer año construcción (ACO dentro de IBI)
        anyo = text_by_tag.get("ACO")
        
        # Extraer plantas (buscar en LEC/ELEMENTOS COMUNES o usar heurística)
        # El número de plantas puede estar en PLA dentro de ELC
        plantas = text_by_tag.get("PLA") or text_by_tag.get("PLANTAS") or text_by_tag.get("planta")

        if rc:
            row: Dict[str, Any] = {
                "referencia_catastral": rc,
                "direccion_normalizada": direccion,
                "superficie_m2": pd.to_numeric(sup, errors="coerce") if sup else None,
                "ano_construccion": pd.to_numeric(anyo, errors="coerce") if anyo else None,
                "plantas": pd.to_numeric(plantas, errors="coerce") if plantas else None,
            }
            results.append(row)

        elem.clear()
        if limit and len(results) >= limit:
            break

    return results


def main() -> int:
    setup_logging()
    args = parse_args()
    xml_path = Path(args.xml)
    out_path = Path(args.out)
    limit = int(args.limit)

    logger.info("Parseando XML masivo: %s", xml_path)

    rows = _try_client_parser(xml_path)
    if rows:
        logger.info("✓ parse_output_xml devolvió %s inmuebles", len(rows))
    else:
        logger.warning("parse_output_xml devolvió 0; usando parser heurístico...")
        rows = _heuristic_iterparse(xml_path, limit=limit)
        logger.info("✓ Parser heurístico devolvió %s inmuebles", len(rows))

    df = pd.DataFrame(rows)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False, encoding="utf-8")
    logger.info("CSV guardado: %s", out_path)
    return 0 if not df.empty else 1


if __name__ == "__main__":
    raise SystemExit(main())


