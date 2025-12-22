"""
Extrae datos de regulación de alquileres para Barcelona.

Fuentes:
- Portal de Dades: Precio medio alquiler (Incasòl fianzas) - Dataset b37xv8wcjh
- Open Data BCN: Licencias VUT por barrio (habitatges-us-turistic)

REQUISITOS:
- Variable de entorno PORTALDADES_CLIENT_ID configurada
- Para obtener el CLIENT_ID:
  1. Visita https://portaldades.ajuntament.barcelona.cat/
  2. Regístrate y solicita acceso a la API
  3. Obtén tu Client ID desde el panel de desarrollador
  4. Configura: export PORTALDADES_CLIENT_ID="tu_client_id"
"""

import logging
import os
import sys
from pathlib import Path

# Añadir raíz del proyecto al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.extraction.opendata import OpenDataBCNExtractor
from src.extraction.portaldades import PortalDadesExtractor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_portaldades_client_id() -> bool:
    """Verifica que PORTALDADES_CLIENT_ID esté configurado."""
    client_id = os.getenv("PORTALDADES_CLIENT_ID")
    if not client_id:
        logger.error("=" * 80)
        logger.error("ERROR: PORTALDADES_CLIENT_ID no está configurado")
        logger.error("=" * 80)
        logger.error("")
        logger.error("Para obtener el CLIENT_ID:")
        logger.error("1. Visita https://portaldades.ajuntament.barcelona.cat/")
        logger.error("2. Regístrate y solicita acceso a la API")
        logger.error("3. Obtén tu Client ID desde el panel de desarrollador")
        logger.error("4. Configura la variable de entorno:")
        logger.error("")
        logger.error("   export PORTALDADES_CLIENT_ID='tu_client_id'")
        logger.error("")
        logger.error("O añádela a tu archivo .env o .bashrc/.zshrc")
        logger.error("=" * 80)
        return False
    return True


def main():
    """Extrae datos de regulación desde Portal de Dades y Open Data BCN."""
    output_dir = project_root / "data" / "raw" / "regulacion"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("=== Extracción de datos de regulación ===")
    
    # Verificar CLIENT_ID antes de continuar
    if not check_portaldades_client_id():
        return 1
    
    # 1. Precio alquiler (índice referencia de facto) desde Portal de Dades
    logger.info("1. Extrayendo precio medio alquiler desde Portal de Dades...")
    logger.info("   Dataset ID: b37xv8wcjh")
    try:
        pd_extractor = PortalDadesExtractor(output_dir=output_dir)
        
        # Verificar que el extractor tenga client_id válido
        if not pd_extractor.client_id:
            logger.error("✗ PortalDadesExtractor no tiene CLIENT_ID configurado")
            return 1
        
        # Descargar dataset específico por ID
        precio_path = pd_extractor.descargar_indicador(
            id_indicador="b37xv8wcjh",
            nombre="precio_medio_alquiler_barrio",
            formato="CSV"
        )
        
        if precio_path and precio_path.exists():
            logger.info(f"✓ Precio alquiler descargado: {precio_path}")
        else:
            logger.error("✗ Error descargando precio alquiler desde Portal de Dades")
            logger.error("  Verifica que:")
            logger.error("  - El CLIENT_ID sea válido")
            logger.error("  - El dataset ID 'b37xv8wcjh' exista y esté accesible")
            logger.error("  - Tengas permisos para acceder a este dataset")
            return 1
    except Exception as e:
        logger.error(f"Error extrayendo precio alquiler: {e}", exc_info=True)
        return 1
    
    # 2. Licencias VUT (Open Data BCN) - Opcional, puede no estar disponible
    logger.info("2. Extrayendo licencias VUT desde Open Data BCN...")
    try:
        bcn_extractor = OpenDataBCNExtractor(output_dir=output_dir)
        
        # Intentar descargar dataset de VUT
        vut_df, metadata = bcn_extractor.download_dataset(
            dataset_id="habitatges-us-turistic",
            resource_format="csv",
            year_start=2020,
            year_end=2024
        )
        
        if vut_df is not None and not vut_df.empty:
            vut_path = output_dir / "licencias_vut.csv"
            vut_df.to_csv(vut_path, index=False)
            logger.info(f"✓ Licencias VUT guardadas: {vut_path} ({len(vut_df)} registros)")
        else:
            logger.warning("⚠ No se encontraron datos de licencias VUT (opcional)")
    except Exception as e:
        logger.warning(f"Error extrayendo licencias VUT (opcional): {e}")
        # No fallar si VUT no está disponible
    
    logger.info("✅ Extracción de datos de regulación completada")
    logger.info(f"   Datos guardados en: {output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

