#!/usr/bin/env python3
"""
Extract Tourism Data from OpenData BCN.

Extracts datasets:
- tourism_intensity: intensitat-activitat-turistica
- tourism_hut: habitatges-us-turistic
"""

import sys
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def extract_tourism_datasets():
    """Extract tourism datasets from OpenData BCN."""
    try:
        # Import using normal import (project root already in sys.path)
        from src.extraction.opendata import OpenDataBCNExtractor
        
        extractor = OpenDataBCNExtractor(output_dir=PROJECT_ROOT / "data" / "raw" / "opendatabcn")
        
        datasets_to_extract = {
            "tourism_intensity": "intensitat-activitat-turistica",
            "tourism_hut": "habitatges-us-turistic",
        }
        
        results = {}
        
        for key, dataset_id in datasets_to_extract.items():
            logger.info(f"\n{'='*60}")
            logger.info(f"Extrayendo: {key} (dataset_id: {dataset_id})")
            logger.info(f"{'='*60}")
            
            try:
                # Try to extract historical data first (2015-2025)
                df, metadata = extractor.download_dataset_historical(
                    dataset_id=dataset_id,
                    year_start=2015,
                    year_end=2025,
                    resource_format='csv'
                )
                
                # If historical method doesn't work, try regular download
                if df is None or df.empty:
                    logger.info(f"  Método histórico no funcionó, intentando método regular...")
                    df, metadata = extractor.download_dataset(
                        dataset_id=dataset_id,
                        resource_format='csv'
                    )
                
                if df is not None and not df.empty:
                    logger.info(f"✅ {key}: {len(df)} registros extraídos")
                    logger.info(f"   Columnas: {list(df.columns)[:5]}...")
                    
                    # Save to file
                    output_file = PROJECT_ROOT / "data" / "raw" / "opendatabcn" / f"{key}_{dataset_id}.csv"
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    df.to_csv(output_file, index=False)
                    logger.info(f"   Guardado en: {output_file.name}")
                    
                    results[key] = df
                else:
                    logger.warning(f"⚠️  {key}: No se extrajeron datos")
                    results[key] = None
                    
            except Exception as e:
                logger.error(f"❌ Error extrayendo {key}: {e}")
                import traceback
                logger.debug(traceback.format_exc())
                results[key] = None
        
        # Summary
        logger.info(f"\n{'='*60}")
        logger.info("RESUMEN DE EXTRACCIÓN")
        logger.info(f"{'='*60}")
        for key, df in results.items():
            if df is not None:
                logger.info(f"✅ {key}: {len(df)} registros")
            else:
                logger.info(f"❌ {key}: No extraído")
        
        return results
        
    except Exception as e:
        logger.error(f"Error en extracción de turismo: {e}")
        import traceback
        traceback.print_exc()
        return {}


def verify_dataset_ids():
    """Verify if dataset IDs are correct by searching OpenData BCN."""
    logger.info("Verificando dataset IDs en OpenData BCN...")
    
    try:
        import requests
        
        API_URL = "https://opendata-ajuntament.barcelona.cat/data/api/3/action"
        dataset_ids = {
            "tourism_intensity": "intensitat-activitat-turistica",
            "tourism_hut": "habitatges-us-turistic",
        }
        
        for key, dataset_id in dataset_ids.items():
            try:
                url = f"{API_URL}/package_show"
                response = requests.get(url, params={"id": dataset_id}, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        pkg = data.get("result", {})
                        logger.info(f"✅ {key}: Dataset encontrado - '{pkg.get('title', 'N/A')}'")
                        logger.info(f"   ID: {dataset_id}")
                        logger.info(f"   Recursos: {len(pkg.get('resources', []))}")
                    else:
                        logger.warning(f"⚠️  {key}: API retornó success=False")
                else:
                    logger.warning(f"⚠️  {key}: HTTP {response.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ Error verificando {key}: {e}")
                
    except ImportError:
        logger.warning("requests no disponible. No se puede verificar dataset IDs.")


def main() -> int:
    """Main function."""
    logger.info("🔍 Tourism Data Extraction Script")
    logger.info("=" * 60)
    
    # First verify dataset IDs
    verify_dataset_ids()
    
    # Then extract
    results = extract_tourism_datasets()
    
    if any(df is not None for df in results.values()):
        logger.info("\n✅ Extracción completada. Los datos están en data/raw/opendatabcn/")
        logger.info("   Ejecuta el ETL para procesarlos: python scripts/process_and_load.py")
        return 0
    else:
        logger.error("\n❌ No se extrajeron datos. Verifica los dataset IDs.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
