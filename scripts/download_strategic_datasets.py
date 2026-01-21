import sys
import os
from pathlib import Path
import logging

# Añadir el raíz del proyecto al path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.extraction.opendata import OpenDataBCNExtractor
from src.extraction.portaldades import PortalDadesExtractor

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("🚀 Iniciando descarga de Datasets Estratégicos (Corrección)...")
    
    # Limpiar archivo corrupto previo
    corrupted_file = PROJECT_ROOT / "data/raw/opendatabcn/tourism_intensity_intensitat-activitat-turistica.csv"
    if corrupted_file.exists():
        logger.info(f"🗑️ Eliminando archivo corrupto: {corrupted_file}")
        corrupted_file.unlink()

    # 1. Inicializar extractores
    client_id = "22a421cfc4cf7e3dc07e1feb2a96fdbf"
    
    od_extractor = OpenDataBCNExtractor()
    pd_extractor = PortalDadesExtractor(client_id=client_id)
    
    # --- BLOQUE 1: PORTAL DE DADES (API) ---
    pd_indicators = [
        {"id": "bxtvnxvukh", "name": "Precio m2 Transmisiones Compraventa"},
        {"id": "u25rr7oxh6", "name": "Precio m2 Venta Registrada"},
        {"id": "b37xv8wcjh", "name": "Alquiler Medio Mensual Incasol"},
        {"id": "mrslyp5pcq", "name": "Venta por Tipo m2"}
    ]
    
    for ind in pd_indicators:
        logger.info(f"📥 Descargando desde Portal de Dades: {ind['id']} ({ind['name']})")
        try:
            path = pd_extractor.descargar_indicador(ind['id'], ind['name'])
            if path:
                logger.info(f"✅ Éxito: Guardado en {path}")
        except Exception as e:
            logger.error(f"❌ Error en Portal de Dades para {ind['id']}: {e}")

    # --- BLOQUE 2: OPEN DATA BCN (CKAN) ---
    od_datasets = {
        "catastro_usos": "est-cadastre-locals-us-desti",
        "renta_seccion_censal": "renda-disponible-llars-bcn",
        "oferta_idealista": "habitatges-2na-ma",
        "turismo_huts": "habitatges-us-turistic",
        "catastro_superficie": "est-cadastre-habitatges-superficie-mitjana"
    }
    
    for key, ds_id in od_datasets.items():
        logger.info(f"📥 Verificando/Descargando desde OpenData BCN: {ds_id} ({key})")
        try:
            df, meta = od_extractor.download_dataset(ds_id)
            if df is not None:
                logger.info(f"✅ Éxito: {len(df)} registros obtenidos para {ds_id}")
        except Exception as e:
            logger.error(f"❌ Error descargando {ds_id}: {e}")

    logger.info("🏁 Proceso de descarga finalizado.")

if __name__ == "__main__":
    main()
