#!/usr/bin/env python3
"""
Script maestro para ejecutar el pipeline completo de Fase 2.

Ejecuta en orden:
1. Validar XML recibido
2. Parsear XML → CSV
3. Filtrar para Gràcia
4. Comparar con datos imputados (opcional)

Issue: #202 (Fase 2)
"""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from pathlib import Path

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
        description="Pipeline completo Fase 2: XML → CSV → Gràcia",
    )
    parser.add_argument(
        "--xml",
        type=str,
        default="spike-data-validation/data/raw/catastro_oficial/ECLTI250200147801.XML",
        help="Ruta al XML descargado",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Saltar validación del XML",
    )
    parser.add_argument(
        "--skip-comparison",
        action="store_true",
        help="Saltar comparación con datos imputados",
    )
    parser.add_argument(
        "--python",
        type=str,
        default=".venv-spike/bin/python",
        help="Interprete Python a usar",
    )
    return parser.parse_args()


def run_command(cmd: list[str], description: str) -> bool:
    """
    Ejecuta un comando y registra el resultado.

    Args:
        cmd: Comando a ejecutar como lista.
        description: Descripción del paso.

    Returns:
        True si el comando fue exitoso, False en caso contrario.
    """
    logger.info("")
    logger.info("=" * 70)
    logger.info("PASO: %s", description)
    logger.info("=" * 70)
    logger.info("Comando: %s", " ".join(cmd))

    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )
        logger.info("✓ %s completado exitosamente", description)
        if result.stdout:
            logger.debug("STDOUT:\n%s", result.stdout)
        return True
    except subprocess.CalledProcessError as exc:
        logger.error("✗ %s falló", description)
        logger.error("Código de salida: %s", exc.returncode)
        if exc.stdout:
            logger.error("STDOUT:\n%s", exc.stdout)
        if exc.stderr:
            logger.error("STDERR:\n%s", exc.stderr)
        return False
    except FileNotFoundError:
        logger.error("✗ Comando no encontrado: %s", cmd[0])
        logger.error("Verifica que el interprete Python esté disponible")
        return False


def main() -> int:
    """Punto de entrada principal."""
    setup_logging()
    args = parse_args()

    xml_path = Path(args.xml)
    python_cmd = args.python

    logger.info("=" * 70)
    logger.info("PIPELINE FASE 2: Catastro Masivo → Gràcia")
    logger.info("=" * 70)
    logger.info("XML: %s", xml_path)
    logger.info("Python: %s", python_cmd)
    logger.info("")

    if not xml_path.exists():
        logger.error("XML no encontrado: %s", xml_path)
        logger.error("Descarga el XML desde la Sede Electrónica primero")
        return 1

    # Paso 1: Validar XML
    if not args.skip_validation:
        scripts_dir = Path(__file__).parent
        validate_script = scripts_dir / "validate_xml_received.py"
        if not run_command(
            [python_cmd, str(validate_script), "--xml", str(xml_path)],
            "Validación XML",
        ):
            logger.error("Validación falló. Revisa el XML antes de continuar.")
            return 1

    # Paso 2: Parsear XML → CSV
    scripts_dir = Path(__file__).parent
    parse_script = scripts_dir / "parse_catastro_xml.py"
    parsed_csv = Path("spike-data-validation/data/processed/fase2/catastro_barcelona_parsed.csv")

    if not run_command(
        [
            python_cmd,
            str(parse_script),
            "--xml",
            str(xml_path),
            "--out",
            str(parsed_csv),
            "--validate",
        ],
        "Parsear XML → CSV",
    ):
        logger.error("Parseo falló")
        return 1

    if not parsed_csv.exists():
        logger.error("CSV parseado no se generó: %s", parsed_csv)
        return 1

    # Paso 3: Filtrar para Gràcia
    scripts_root = Path(__file__).resolve().parents[1]
    filter_script = scripts_root / "filter_gracia_real.py"

    gracia_csv = Path("spike-data-validation/data/processed/catastro_gracia_real.csv")

    if not run_command(
        [
            python_cmd,
            str(filter_script),
            "--input",
            str(parsed_csv),
            "--output",
            str(gracia_csv),
        ],
        "Filtrar para Gràcia",
    ):
        logger.error("Filtrado falló")
        return 1

    if not gracia_csv.exists():
        logger.error("CSV de Gràcia no se generó: %s", gracia_csv)
        return 1

    # Paso 4: Comparar con imputados (opcional)
    if not args.skip_comparison:
        compare_script = scripts_root / "compare_imputed_vs_real.py"
        if compare_script.exists():
            run_command(
                [python_cmd, str(compare_script)],
                "Comparar imputado vs real",
            )
        else:
            logger.warning("Script de comparación no encontrado: %s", compare_script)

    logger.info("")
    logger.info("=" * 70)
    logger.info("✓ PIPELINE COMPLETADO")
    logger.info("=" * 70)
    logger.info("Archivos generados:")
    logger.info("  - CSV parseado: %s", parsed_csv)
    logger.info("  - CSV Gràcia: %s", gracia_csv)
    logger.info("")
    logger.info("Próximos pasos:")
    logger.info("  1. Revisar calidad de datos en %s", gracia_csv)
    logger.info("  2. Continuar con matching Idealista (Issue #202)")
    logger.info("  3. Entrenar modelo MICRO hedónico")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

