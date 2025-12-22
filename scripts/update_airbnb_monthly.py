#!/usr/bin/env python3
"""
Script de actualización mensual para datos de Inside Airbnb.

Este script:
1. Descarga los datos más recientes de Inside Airbnb
2. Procesa los datos y los carga en la base de datos
3. Puede ejecutarse manualmente o mediante cron/scheduler

Uso:
    python -m scripts.update_airbnb_monthly
    
Para ejecutar mensualmente con cron:
    0 2 1 * * cd /path/to/project && python -m scripts.update_airbnb_monthly >> logs/airbnb_update.log 2>&1
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Añadir el directorio raíz al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.extraction.airbnb_extractor import AirbnbExtractor
from src.etl.pipeline import run_etl


def main() -> int:
    """
    Ejecuta la actualización mensual de datos de Airbnb.
    
    Returns:
        0 si la actualización fue exitosa, 1 si hubo errores.
    """
    logger.info("=" * 80)
    logger.info("ACTUALIZACIÓN MENSUAL DE DATOS DE INSIDE AIRBNB")
    logger.info("=" * 80)
    logger.info("Fecha: %s", datetime.now().isoformat())
    
    try:
        # 1. Extraer datos más recientes
        logger.info("\n--- Paso 1: Extracción de datos ---")
        output_dir = project_root / "data" / "raw" / "airbnb"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        extractor = AirbnbExtractor(output_dir=output_dir)
        results, metadata = extractor.extract_barcelona_data()
        
        if not metadata.get("success", False):
            logger.error("Error en la extracción de datos")
            logger.error("Archivos fallidos: %s", metadata.get("files_failed", []))
            return 1
        
        logger.info("✓ Extracción completada")
        logger.info("Archivos descargados: %s", metadata.get("files_downloaded", []))
        
        # 2. Ejecutar ETL para procesar y cargar datos
        logger.info("\n--- Paso 2: Procesamiento y carga en base de datos ---")
        
        raw_base_dir = project_root / "data" / "raw"
        processed_dir = project_root / "data" / "processed"
        
        db_path = run_etl(raw_base_dir=raw_base_dir, processed_dir=processed_dir)
        
        if db_path and db_path.exists():
            logger.info("✓ ETL completado exitosamente")
            logger.info("Base de datos actualizada: %s", db_path)
            
            # 3. Validar datos cargados
            logger.info("\n--- Paso 3: Validación de datos ---")
            from scripts.validate_presion_turistica import main as validate_main
            
            validation_result = validate_main()
            if validation_result == 0:
                logger.info("✓ Validación pasada")
            else:
                logger.warning("⚠ Validación falló, pero los datos se cargaron")
            
            logger.info("\n" + "=" * 80)
            logger.info("ACTUALIZACIÓN COMPLETADA EXITOSAMENTE")
            logger.info("=" * 80)
            return 0
        else:
            logger.error("Error en el ETL: no se creó la base de datos")
            return 1
            
    except Exception as e:
        logger.exception("Error durante la actualización mensual: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())

