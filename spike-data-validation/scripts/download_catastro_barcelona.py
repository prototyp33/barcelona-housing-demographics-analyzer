#!/usr/bin/env python3
"""
Fase 2 (Issue #200): intento de descarga programática municipal (Barcelona 08-019).

Contexto (evidencia runtime):
El endpoint `ConsultaMunicipio` ha respondido 200 pero devolviendo XML de error con:
  - cod=12, des="LA PROVINCIA NO EXISTE"

Por tanto, este script NO es la vía principal para obtener datos reales. Se deja como:
- herramienta de diagnóstico (reproducir el error y guardar la respuesta)
- posible fallback si el servicio se repara en el futuro

Vía recomendada para datos reales:
- Consulta masiva oficial asíncrona vía Sede Electrónica (`catastro_oficial_client.py`)

Uso:
  .venv-spike/bin/python spike-data-validation/scripts/download_catastro_barcelona.py
"""

from __future__ import annotations

import argparse
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

import requests

LOG_DIR = Path("spike-data-validation/data/logs")
RAW_DIR = Path("spike-data-validation/data/raw")

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """Configura logging del script."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler = logging.FileHandler(LOG_DIR / "download_catastro_barcelona.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = []
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)


def parse_args() -> argparse.Namespace:
    """Parsea argumentos CLI."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--provincia", type=str, default="08")
    parser.add_argument("--municipio", type=str, default="019")
    parser.add_argument(
        "--output",
        type=str,
        default=str(RAW_DIR / "catastro_barcelona_019_full.xml"),
        help="Ruta de salida. Si el servidor devuelve error, se guardará igualmente el XML de error.",
    )
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument(
        "--max-bytes",
        type=int,
        default=2_000_000,
        help="Límite de bytes a descargar (seguridad).",
    )
    return parser.parse_args()


def _extract_error_code(xml_text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extrae (cod, des) si la respuesta contiene lerr/err.
    """
    # parsing minimalista por substrings para evitar dependencia de parser aquí
    if "<cod>" not in xml_text or "<des>" not in xml_text:
        return None, None
    try:
        cod = xml_text.split("<cod>", 1)[1].split("</cod>", 1)[0].strip()
        des = xml_text.split("<des>", 1)[1].split("</des>", 1)[0].strip()
        return cod, des
    except Exception:  # noqa: BLE001
        return None, None


def download_consulta_municipio(
    provincia: str,
    municipio: str,
    output_path: Path,
    timeout: int,
    max_bytes: int,
) -> int:
    """
    Lanza request a ConsultaMunicipio y guarda la respuesta (parcial si supera max_bytes).
    """
    url = (
        "http://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/"
        "OVCCallejero.asmx/ConsultaMunicipio"
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Solicitando ConsultaMunicipio provincia=%s municipio=%s", provincia, municipio)
    logger.info("URL: %s", url)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    tmp_path = output_path.with_name(f"{output_path.stem}_{ts}{output_path.suffix}")

    with requests.post(
        url,
        data={"Provincia": provincia, "Municipio": municipio},
        stream=True,
        timeout=timeout,
    ) as r:
        logger.info("HTTP %s | Content-Type=%s", r.status_code, r.headers.get("Content-Type"))
        r.raise_for_status()

        downloaded = 0
        with tmp_path.open("wb") as f:
            for chunk in r.iter_content(chunk_size=64 * 1024):
                if not chunk:
                    continue
                f.write(chunk)
                downloaded += len(chunk)
                if downloaded >= max_bytes:
                    logger.warning("Cortando descarga por max-bytes=%s (descargados=%s)", max_bytes, downloaded)
                    break

    # Detectar error 12 si es un XML pequeño de error
    try:
        text_preview = tmp_path.read_text(encoding="utf-8", errors="replace")[:4000]
        cod, des = _extract_error_code(text_preview)
        if cod:
            logger.warning("Respuesta contiene error cod=%s des=%s", cod, des)
            if cod == "12":
                logger.warning(
                    "ConsultaMunicipio NO es viable ahora (mismo error 12). "
                    "Usa consulta masiva asíncrona en Sede (catastro_oficial_client.py)."
                )
                return 2
    except OSError:
        pass

    logger.info("Respuesta guardada: %s", tmp_path)
    return 0


def main() -> int:
    setup_logging()
    args = parse_args()
    return download_consulta_municipio(
        provincia=args.provincia,
        municipio=args.municipio,
        output_path=Path(args.output),
        timeout=int(args.timeout),
        max_bytes=int(args.max_bytes),
    )


if __name__ == "__main__":
    raise SystemExit(main())


