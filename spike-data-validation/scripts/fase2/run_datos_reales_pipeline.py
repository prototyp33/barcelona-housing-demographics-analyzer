#!/usr/bin/env python3
"""
Pipeline completo para datos reales de Idealista (Fase 2 - Issue #202).

Ejecuta secuencialmente:
1. Verificación de credenciales
2. Extracción de datos reales de Idealista
3. Matching con Catastro
4. EDA comparativo (opcional)
5. Re-entrenamiento del modelo

Uso:
    python3 spike-data-validation/scripts/fase2/run_datos_reales_pipeline.py
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """Configura logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def check_credentials() -> tuple[bool, str, str]:
    """
    Verifica si hay credenciales API disponibles.
    
    Returns:
        Tupla con (hay_credenciales, api_key, api_secret)
    """
    api_key = os.getenv("IDEALISTA_API_KEY")
    api_secret = os.getenv("IDEALISTA_API_SECRET")
    
    has_creds = bool(api_key and api_secret)
    
    if has_creds:
        logger.info("✅ Credenciales API encontradas en variables de entorno")
    else:
        logger.warning("⚠️  Credenciales API no encontradas")
        logger.warning("   Configura: export IDEALISTA_API_KEY=key export IDEALISTA_API_SECRET=secret")
        logger.warning("   O usa argumentos: --api-key KEY --api-secret SECRET")
    
    return has_creds, api_key or "", api_secret or ""


def run_extraction(api_key: str, api_secret: str, max_properties: int = 100) -> bool:
    """
    Ejecuta extracción de datos reales de Idealista.
    
    Returns:
        True si la extracción fue exitosa
    """
    logger.info("")
    logger.info("=" * 70)
    logger.info("PASO 1: EXTRACCIÓN IDEALISTA API")
    logger.info("=" * 70)
    
    script_path = Path("spike-data-validation/scripts/fase2/extract_idealista_api_gracia.py")
    
    cmd = [
        sys.executable,
        str(script_path),
        "--max-properties", str(max_properties),
    ]
    
    if api_key:
        cmd.extend(["--api-key", api_key])
    if api_secret:
        cmd.extend(["--api-secret", api_secret])
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error("❌ Error en extracción:")
        logger.error(e.stderr)
        return False


def run_matching() -> bool:
    """
    Ejecuta matching Catastro ↔ Idealista con datos reales.
    
    Returns:
        True si el matching fue exitoso
    """
    logger.info("")
    logger.info("=" * 70)
    logger.info("PASO 2: MATCHING CATASTRO ↔ IDEALISTA (REAL)")
    logger.info("=" * 70)
    
    script_path = Path("spike-data-validation/scripts/fase2/match_catastro_idealista.py")
    
    catastro_path = Path("spike-data-validation/data/processed/fase2/catastro_gracia_real.csv")
    idealista_path = Path("spike-data-validation/data/processed/fase2/idealista_gracia_api.csv")
    output_csv = Path("spike-data-validation/data/processed/fase2/catastro_idealista_matched_REAL.csv")
    output_metadata = Path("spike-data-validation/data/processed/fase2/matching_REAL_metadata.json")
    
    if not catastro_path.exists():
        logger.error("❌ No se encuentra: %s", catastro_path)
        logger.error("   Ejecuta primero el pipeline de Catastro")
        return False
    
    if not idealista_path.exists():
        logger.error("❌ No se encuentra: %s", idealista_path)
        logger.error("   Ejecuta primero la extracción de Idealista")
        return False
    
    cmd = [
        sys.executable,
        str(script_path),
        "--catastro-path", str(catastro_path),
        "--idealista-path", str(idealista_path),
        "--output-csv-path", str(output_csv),
        "--output-metadata-path", str(output_metadata),
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error("❌ Error en matching:")
        logger.error(e.stderr)
        return False


def run_training() -> bool:
    """
    Re-entrena el modelo con datos reales.
    
    Returns:
        True si el entrenamiento fue exitoso
    """
    logger.info("")
    logger.info("=" * 70)
    logger.info("PASO 3: RE-ENTRENAMIENTO MODELO (DATOS REALES)")
    logger.info("=" * 70)
    
    script_path = Path("spike-data-validation/scripts/fase2/train_micro_hedonic.py")
    input_csv = Path("spike-data-validation/data/processed/fase2/catastro_idealista_matched_REAL.csv")
    
    if not input_csv.exists():
        logger.error("❌ No se encuentra: %s", input_csv)
        logger.error("   Ejecuta primero el matching")
        return False
    
    cmd = [
        sys.executable,
        str(script_path),
        "--input", str(input_csv),
        "--model", "linear",
        "--log-transform",
        "--interactions",
        "--use-cv",
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error("❌ Error en entrenamiento:")
        logger.error(e.stderr)
        return False


def main() -> int:
    """Punto de entrada principal."""
    setup_logging()
    
    logger.info("=" * 70)
    logger.info("PIPELINE DATOS REALES - IDEALISTA API")
    logger.info("=" * 70)
    logger.info("")
    
    # Paso 0: Verificar credenciales
    has_creds, api_key, api_secret = check_credentials()
    
    if not has_creds:
        logger.error("")
        logger.error("❌ No se pueden continuar sin credenciales API")
        logger.error("")
        logger.error("Siguiente paso:")
        logger.error("1. Obtener credenciales en: https://developers.idealista.com/")
        logger.error("2. Configurar variables de entorno:")
        logger.error("   export IDEALISTA_API_KEY=your_key")
        logger.error("   export IDEALISTA_API_SECRET=your_secret")
        logger.error("3. Re-ejecutar este script")
        return 1
    
    # Paso 1: Extracción
    if not run_extraction(api_key, api_secret, max_properties=100):
        logger.error("❌ Pipeline detenido: Error en extracción")
        return 1
    
    # Paso 2: Matching
    if not run_matching():
        logger.error("❌ Pipeline detenido: Error en matching")
        return 1
    
    # Paso 3: Re-entrenamiento
    if not run_training():
        logger.error("❌ Pipeline detenido: Error en entrenamiento")
        return 1
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("✅ PIPELINE COMPLETADO")
    logger.info("=" * 70)
    logger.info("")
    logger.info("📊 Próximos pasos:")
    logger.info("   1. Revisar resultados en:")
    logger.info("      - catastro_idealista_matched_REAL.csv")
    logger.info("      - micro_hedonic_linear_results.json")
    logger.info("   2. Comparar con resultados mock")
    logger.info("   3. Actualizar documentación")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

