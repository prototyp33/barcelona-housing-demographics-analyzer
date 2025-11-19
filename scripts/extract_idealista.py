#!/usr/bin/env python3
"""
Script para extraer datos de oferta inmobiliaria de Idealista API.

Este script requiere:
1. Registro en https://developers.idealista.com/
2. Obtener API key y secret
3. Configurar variables de entorno:
   export IDEALISTA_API_KEY=your_api_key
   export IDEALISTA_API_SECRET=your_api_secret

Uso:
    python scripts/extract_idealista.py --operation sale
    python scripts/extract_idealista.py --operation rent
    python scripts/extract_idealista.py --operation both
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_extraction import IdealistaExtractor

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/extract_idealista.log')
    ]
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Extrae datos de oferta inmobiliaria de Idealista API"
    )
    parser.add_argument(
        '--operation',
        type=str,
        choices=['sale', 'rent', 'both'],
        default='both',
        help='Tipo de operación: venta (sale), alquiler (rent), o ambos (both)'
    )
    parser.add_argument(
        '--barrios',
        type=str,
        nargs='+',
        default=None,
        help='Lista de nombres de barrios (opcional, por defecto busca en toda Barcelona)'
    )
    parser.add_argument(
        '--max-items',
        type=int,
        default=50,
        help='Máximo de resultados por barrio (máx 50 por request de API)'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('data/raw'),
        help='Directorio donde guardar los datos extraídos'
    )
    parser.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Nivel de logging'
    )
    
    args = parser.parse_args()
    
    # Configurar nivel de logging
    log_level = getattr(logging, args.log_level.upper())
    logging.getLogger().setLevel(log_level)
    
    # Verificar credenciales
    api_key = os.getenv("IDEALISTA_API_KEY")
    api_secret = os.getenv("IDEALISTA_API_SECRET")
    
    if not api_key or not api_secret:
        logger.error(
            "❌ API credentials de Idealista no encontradas.\n"
            "Por favor, configura las variables de entorno:\n"
            "  export IDEALISTA_API_KEY=your_api_key\n"
            "  export IDEALISTA_API_SECRET=your_api_secret\n\n"
            "Para obtener las credenciales:\n"
            "1. Regístrate en https://developers.idealista.com/\n"
            "2. Crea una aplicación\n"
            "3. Obtén tu API key y secret"
        )
        sys.exit(1)
    
    logger.info("=== Extracción de datos de Idealista ===")
    logger.info(f"Operation: {args.operation}")
    logger.info(f"Barrios: {args.barrios or 'Todos (Barcelona)'}")
    logger.info(f"Max items por barrio: {args.max_items}")
    
    # Crear extractor
    extractor = IdealistaExtractor(
        api_key=api_key,
        api_secret=api_secret,
        output_dir=args.output_dir
    )
    
    results = {}
    
    # Extraer según operación
    if args.operation in ['sale', 'both']:
        logger.info("\n=== Extrayendo oferta de VENTA ===")
        df_venta, metadata_venta = extractor.extract_offer_by_barrio(
            barrio_names=args.barrios,
            operation="sale",
            max_items_per_barrio=args.max_items
        )
        
        if df_venta is not None and not df_venta.empty:
            results['venta'] = df_venta
            logger.info(f"✓ Venta: {len(df_venta)} propiedades extraídas")
            logger.info(f"  Archivo guardado: {metadata_venta.get('filepath', 'N/A')}")
        else:
            logger.warning("⚠️  No se obtuvieron datos de venta")
    
    if args.operation in ['rent', 'both']:
        logger.info("\n=== Extrayendo oferta de ALQUILER ===")
        df_alquiler, metadata_alquiler = extractor.extract_offer_by_barrio(
            barrio_names=args.barrios,
            operation="rent",
            max_items_per_barrio=args.max_items
        )
        
        if df_alquiler is not None and not df_alquiler.empty:
            results['alquiler'] = df_alquiler
            logger.info(f"✓ Alquiler: {len(df_alquiler)} propiedades extraídas")
            logger.info(f"  Archivo guardado: {metadata_alquiler.get('filepath', 'N/A')}")
        else:
            logger.warning("⚠️  No se obtuvieron datos de alquiler")
    
    # Resumen
    logger.info("\n=== Resumen de Extracción ===")
    total = sum(len(df) for df in results.values())
    logger.info(f"Total de propiedades extraídas: {total}")
    for operation, df in results.items():
        logger.info(f"  {operation}: {len(df)} propiedades")
    
    if not results:
        logger.warning(
            "\n⚠️  No se extrajeron datos. Posibles causas:\n"
            "  - API credentials inválidas\n"
            "  - Rate limit alcanzado\n"
            "  - Error de conexión\n"
            "  - No hay propiedades disponibles para los criterios especificados"
        )
        sys.exit(1)
    
    logger.info("\n✅ Extracción completada correctamente")


if __name__ == "__main__":
    main()

